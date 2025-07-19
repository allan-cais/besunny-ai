-- Master SQL file to fix all Supabase security errors
-- This migration addresses RLS issues across all tables

-- ============================================================================
-- 1. DOCUMENT_CHUNKS TABLE - Fix RLS and Policies
-- ============================================================================

-- Enable RLS on document_chunks table
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to recreate them properly
DROP POLICY IF EXISTS "Users can insert document chunks" ON document_chunks;
DROP POLICY IF EXISTS "Users can read chunks in their projects" ON document_chunks;

-- Create comprehensive RLS policies for document_chunks
-- Users can only access chunks from projects they own
CREATE POLICY "Users can view chunks in their projects" ON document_chunks
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can insert chunks in their projects" ON document_chunks
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can update chunks in their projects" ON document_chunks
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can delete chunks in their projects" ON document_chunks
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage document chunks" ON document_chunks
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 2. DOCUMENTS TABLE - Fix RLS and Policies
-- ============================================================================

-- Enable RLS on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to recreate them properly
DROP POLICY IF EXISTS "Users can insert documents" ON documents;
DROP POLICY IF EXISTS "Users can read documents in their projects" ON documents;

-- Create comprehensive RLS policies for documents
-- Users can only access documents from projects they own
CREATE POLICY "Users can view documents in their projects" ON documents
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can insert documents in their projects" ON documents
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can update documents in their projects" ON documents
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can delete documents in their projects" ON documents
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage documents" ON documents
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 3. SYNC_TRACKING TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on sync_tracking table
ALTER TABLE sync_tracking ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for sync_tracking
-- Users can only access their own sync tracking data
CREATE POLICY "Users can view own sync tracking" ON sync_tracking
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sync tracking" ON sync_tracking
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sync tracking" ON sync_tracking
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sync tracking" ON sync_tracking
  FOR DELETE USING (auth.uid() = user_id);

-- Service role policy for backend operations
CREATE POLICY "Service role can manage sync tracking" ON sync_tracking
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 4. KNOWLEDGE_SPACES TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on knowledge_spaces table
ALTER TABLE knowledge_spaces ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for knowledge_spaces
-- Users can only access knowledge spaces from projects they own
CREATE POLICY "Users can view knowledge spaces in their projects" ON knowledge_spaces
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can insert knowledge spaces in their projects" ON knowledge_spaces
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can update knowledge spaces in their projects" ON knowledge_spaces
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can delete knowledge spaces in their projects" ON knowledge_spaces
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage knowledge spaces" ON knowledge_spaces
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 5. USERS TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for users table
-- Users can only access their own user record
CREATE POLICY "Users can view own user record" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own user record" ON users
  FOR UPDATE USING (auth.uid() = id);

-- Users cannot insert or delete their own records (handled by auth system)
-- Service role policy for backend operations
CREATE POLICY "Service role can manage users" ON users
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 6. DOCUMENT_TAGS TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on document_tags table
ALTER TABLE document_tags ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for document_tags
-- Users can only access tags for documents in their projects
CREATE POLICY "Users can view document tags in their projects" ON document_tags
  FOR SELECT USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = auth.uid()
    )
  );

CREATE POLICY "Users can insert document tags in their projects" ON document_tags
  FOR INSERT WITH CHECK (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = auth.uid()
    )
  );

CREATE POLICY "Users can update document tags in their projects" ON document_tags
  FOR UPDATE USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = auth.uid()
    )
  );

CREATE POLICY "Users can delete document tags in their projects" ON document_tags
  FOR DELETE USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage document tags" ON document_tags
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 7. SUMMARIES TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on summaries table
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for summaries
-- Users can only access summaries from projects they own
CREATE POLICY "Users can view summaries in their projects" ON summaries
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can insert summaries in their projects" ON summaries
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can update summaries in their projects" ON summaries
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can delete summaries in their projects" ON summaries
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage summaries" ON summaries
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 8. RECEIPTS TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on receipts table
ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for receipts
-- Users can only access receipts from projects they own
CREATE POLICY "Users can view receipts in their projects" ON receipts
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can insert receipts in their projects" ON receipts
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can update receipts in their projects" ON receipts
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

CREATE POLICY "Users can delete receipts in their projects" ON receipts
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage receipts" ON receipts
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 9. TAGS TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on tags table
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for tags
-- Users can only access tags they created
CREATE POLICY "Users can view own tags" ON tags
  FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert own tags" ON tags
  FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update own tags" ON tags
  FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete own tags" ON tags
  FOR DELETE USING (auth.uid() = created_by);

-- Service role policy for backend operations
CREATE POLICY "Service role can manage tags" ON tags
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 10. AGENT_LOGS TABLE - Enable RLS and Create Policies
-- ============================================================================

-- Enable RLS on agent_logs table
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for agent_logs
-- Users can only access agent logs related to their projects
-- Note: This assumes agent_logs.input_id relates to documents or projects
-- You may need to adjust this based on your actual data model
CREATE POLICY "Users can view agent logs in their projects" ON agent_logs
  FOR SELECT USING (
    -- Allow service role to access all logs
    auth.role() = 'service_role' OR
    -- For now, restrict to service role only - adjust based on your needs
    false
  );

CREATE POLICY "Users can insert agent logs" ON agent_logs
  FOR INSERT WITH CHECK (
    -- Allow service role to insert logs
    auth.role() = 'service_role' OR
    -- For now, restrict to service role only - adjust based on your needs
    false
  );

CREATE POLICY "Users can update agent logs" ON agent_logs
  FOR UPDATE USING (
    -- Allow service role to update logs
    auth.role() = 'service_role' OR
    -- For now, restrict to service role only - adjust based on your needs
    false
  );

CREATE POLICY "Users can delete agent logs" ON agent_logs
  FOR DELETE USING (
    -- Allow service role to delete logs
    auth.role() = 'service_role' OR
    -- For now, restrict to service role only - adjust based on your needs
    false
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage agent logs" ON agent_logs
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 11. PROJECT_METADATA TABLE - Handle if it exists
-- ============================================================================

-- Check if project_metadata table exists and enable RLS if it does
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'project_metadata'
  ) THEN
    -- Enable RLS on project_metadata table
    EXECUTE 'ALTER TABLE project_metadata ENABLE ROW LEVEL SECURITY';
    
    -- Create RLS policies for project_metadata
    EXECUTE 'CREATE POLICY "Users can view project metadata in their projects" ON project_metadata
      FOR SELECT USING (
        project_id IN (
          SELECT id FROM projects WHERE created_by = auth.uid()
        )
      )';
    
    EXECUTE 'CREATE POLICY "Users can insert project metadata in their projects" ON project_metadata
      FOR INSERT WITH CHECK (
        project_id IN (
          SELECT id FROM projects WHERE created_by = auth.uid()
        )
      )';
    
    EXECUTE 'CREATE POLICY "Users can update project metadata in their projects" ON project_metadata
      FOR UPDATE USING (
        project_id IN (
          SELECT id FROM projects WHERE created_by = auth.uid()
        )
      )';
    
    EXECUTE 'CREATE POLICY "Users can delete project metadata in their projects" ON project_metadata
      FOR DELETE USING (
        project_id IN (
          SELECT id FROM projects WHERE created_by = auth.uid()
        )
      )';
    
    EXECUTE 'CREATE POLICY "Service role can manage project metadata" ON project_metadata
      FOR ALL USING (auth.role() = ''service_role'')';
  END IF;
END $$;

-- ============================================================================
-- 12. CREATE PERFORMANCE INDEXES FOR RLS
-- ============================================================================

-- Indexes for better RLS performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_project_id ON document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_sync_tracking_user_id ON sync_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_spaces_project_id ON knowledge_spaces(project_id);
CREATE INDEX IF NOT EXISTS idx_users_id ON users(id);
CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_summaries_project_id ON summaries(project_id);
CREATE INDEX IF NOT EXISTS idx_receipts_project_id ON receipts(project_id);
CREATE INDEX IF NOT EXISTS idx_tags_created_by ON tags(created_by);

-- ============================================================================
-- 13. CREATE UTILITY FUNCTIONS FOR PROJECT ACCESS
-- ============================================================================

-- Function to check if user has access to a project
CREATE OR REPLACE FUNCTION user_has_project_access(project_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM projects 
    WHERE id = project_uuid AND created_by = auth.uid()
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's accessible project IDs
CREATE OR REPLACE FUNCTION get_user_project_ids()
RETURNS TABLE(project_id UUID) AS $$
BEGIN
  RETURN QUERY
  SELECT id FROM projects WHERE created_by = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 14. VERIFICATION QUERIES (for testing)
-- ============================================================================

-- Uncomment these queries to verify RLS is working properly
/*
-- Test queries to verify RLS policies
SELECT 'document_chunks' as table_name, COUNT(*) as total_rows FROM document_chunks;
SELECT 'documents' as table_name, COUNT(*) as total_rows FROM documents;
SELECT 'sync_tracking' as table_name, COUNT(*) as total_rows FROM sync_tracking;
SELECT 'knowledge_spaces' as table_name, COUNT(*) as total_rows FROM knowledge_spaces;
SELECT 'users' as table_name, COUNT(*) as total_rows FROM users;
SELECT 'document_tags' as table_name, COUNT(*) as total_rows FROM document_tags;
SELECT 'summaries' as table_name, COUNT(*) as total_rows FROM summaries;
SELECT 'receipts' as table_name, COUNT(*) as total_rows FROM receipts;
SELECT 'tags' as table_name, COUNT(*) as total_rows FROM tags;
SELECT 'agent_logs' as table_name, COUNT(*) as total_rows FROM agent_logs;
*/ 