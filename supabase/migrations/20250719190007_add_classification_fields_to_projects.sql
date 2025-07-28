-- SUPABASE PROJECTS SCHEMA FOR CLASSIFICATION AGENT
-- Optimized for webhook-based classification with Pinecone integration

-- Add new columns if they don't exist
DO $$ 
BEGIN
    -- Classification metadata that gets sent to the classification agent
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'normalized_tags') THEN
        ALTER TABLE projects ADD COLUMN normalized_tags TEXT[];
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'categories') THEN
        ALTER TABLE projects ADD COLUMN categories TEXT[];
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'reference_keywords') THEN
        ALTER TABLE projects ADD COLUMN reference_keywords TEXT[];
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'notes') THEN
        ALTER TABLE projects ADD COLUMN notes TEXT;
    END IF;
    
    -- Enhanced classification signals for the LLM agent
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'classification_signals') THEN
        ALTER TABLE projects ADD COLUMN classification_signals JSONB;
    END IF;
    
    -- Entity patterns for matching (emails, names, locations, etc.)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'entity_patterns') THEN
        ALTER TABLE projects ADD COLUMN entity_patterns JSONB;
    END IF;
    
    -- Pinecone namespace tracking (project_id = namespace)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'pinecone_document_count') THEN
        ALTER TABLE projects ADD COLUMN pinecone_document_count INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'last_classification_at') THEN
        ALTER TABLE projects ADD COLUMN last_classification_at TIMESTAMP;
    END IF;
    
    -- Classification performance and learning
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'classification_feedback') THEN
        ALTER TABLE projects ADD COLUMN classification_feedback JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'updated_at') THEN
        ALTER TABLE projects ADD COLUMN updated_at TIMESTAMP DEFAULT now();
    END IF;
END $$;

-- Add column descriptions
COMMENT ON COLUMN projects.normalized_tags IS 'Standardized tags sent to classification agent - semantic concepts that help match incoming content';
COMMENT ON COLUMN projects.categories IS 'High-level project categories for the classification LLM - broad classifications like Video Production, Marketing';
COMMENT ON COLUMN projects.reference_keywords IS 'Key terms that indicate content belongs to this project - specific deliverables and concepts';
COMMENT ON COLUMN projects.notes IS 'Human-readable project summary sent to classification agent - provides context for LLM decision making';
COMMENT ON COLUMN projects.classification_signals IS 'Advanced classification metadata: entity patterns, temporal signals, confidence thresholds';
COMMENT ON COLUMN projects.entity_patterns IS 'People, emails, locations, and organizations associated with this project';
COMMENT ON COLUMN projects.pinecone_document_count IS 'Number of documents stored in this project namespace in Pinecone';
COMMENT ON COLUMN projects.last_classification_at IS 'Timestamp of most recent document classified to this project';
COMMENT ON COLUMN projects.classification_feedback IS 'Learning data from classification results for improving future classifications';

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_projects_normalized_tags ON projects USING GIN (normalized_tags);
CREATE INDEX IF NOT EXISTS idx_projects_categories ON projects USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_projects_reference_keywords ON projects USING GIN (reference_keywords);
CREATE INDEX IF NOT EXISTS idx_projects_classification_signals ON projects USING GIN (classification_signals);
CREATE INDEX IF NOT EXISTS idx_projects_entity_patterns ON projects USING GIN (entity_patterns);
CREATE INDEX IF NOT EXISTS idx_projects_classification_activity ON projects (last_classification_at DESC, pinecone_document_count DESC);
CREATE INDEX IF NOT EXISTS idx_projects_user_active ON projects (created_by, status) WHERE status IN ('active', 'in_progress');

-- Full-text search index (simplified to avoid IMMUTABLE function issues)
-- Note: Array fields (normalized_tags, reference_keywords) are indexed separately with GIN indexes above
-- For full-text search including arrays, use a query like:
-- SELECT * FROM projects WHERE 
--   to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(notes, '')) @@ plainto_tsquery('english', 'search term')
--   OR normalized_tags && ARRAY['tag1', 'tag2']
--   OR reference_keywords && ARRAY['keyword1', 'keyword2']
CREATE INDEX IF NOT EXISTS idx_projects_text_search ON projects USING GIN (
    to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '') || ' ' ||
        COALESCE(notes, '')
    )
);

-- Trigger to maintain updated_at timestamp
CREATE OR REPLACE FUNCTION update_projects_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'projects_updated_at_trigger') THEN
        CREATE TRIGGER projects_updated_at_trigger
            BEFORE UPDATE ON projects
            FOR EACH ROW
            EXECUTE FUNCTION update_projects_timestamp();
    END IF;
END $$; 