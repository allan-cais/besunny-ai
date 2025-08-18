-- Migration: Add AI and Classification Tables
-- Description: Adds tables for enhanced AI classification, document workflows, and bot scheduling
-- Date: 2024-01-01
-- Author: System

-- Enable required extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create classification workflows table
CREATE TABLE IF NOT EXISTS classification_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    document_types TEXT[] NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    steps JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create classification batches table
CREATE TABLE IF NOT EXISTS classification_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id TEXT NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    documents JSONB NOT NULL,
    workflow TEXT DEFAULT 'standard',
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0
);

-- Create classification results table
CREATE TABLE IF NOT EXISTS classification_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id TEXT NOT NULL REFERENCES classification_batches(batch_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    classification_result JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create document workflows table
CREATE TABLE IF NOT EXISTS document_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    document_types TEXT[] NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    steps JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id TEXT NOT NULL UNIQUE,
    workflow_id TEXT NOT NULL REFERENCES document_workflows(workflow_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'paused')),
    current_step TEXT,
    step_results JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create workflow approvals table
CREATE TABLE IF NOT EXISTS workflow_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_execution_id TEXT NOT NULL REFERENCES workflow_executions(execution_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    approver_id UUID REFERENCES users(id) ON DELETE CASCADE,
    approval_type TEXT DEFAULT 'manual' CHECK (approval_type IN ('manual', 'automatic', 'ai')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    comments TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create AI processing logs table
CREATE TABLE IF NOT EXISTS ai_processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    processing_type TEXT NOT NULL CHECK (processing_type IN ('classification', 'analysis', 'workflow', 'bot_scheduling')),
    model_used TEXT NOT NULL,
    processing_time_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,6),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    result_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create bot scheduling logs table
CREATE TABLE IF NOT EXISTS bot_scheduling_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    scheduling_type TEXT NOT NULL CHECK (scheduling_type IN ('auto', 'manual', 'batch')),
    bot_configuration JSONB NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_classification_workflows_user_id ON classification_workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_classification_workflows_project_id ON classification_workflows(project_id);
CREATE INDEX IF NOT EXISTS idx_classification_workflows_is_active ON classification_workflows(is_active);

CREATE INDEX IF NOT EXISTS idx_classification_batches_user_id ON classification_batches(user_id);
CREATE INDEX IF NOT EXISTS idx_classification_batches_status ON classification_batches(status);
CREATE INDEX IF NOT EXISTS idx_classification_batches_created_at ON classification_batches(created_at);

CREATE INDEX IF NOT EXISTS idx_classification_results_batch_id ON classification_results(batch_id);
CREATE INDEX IF NOT EXISTS idx_classification_results_document_id ON classification_results(document_id);

CREATE INDEX IF NOT EXISTS idx_document_workflows_user_id ON document_workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_document_workflows_project_id ON document_workflows(project_id);
CREATE INDEX IF NOT EXISTS idx_document_workflows_is_active ON document_workflows(is_active);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_id ON workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_created_at ON workflow_executions(created_at);

CREATE INDEX IF NOT EXISTS idx_workflow_approvals_execution_id ON workflow_approvals(workflow_execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_status ON workflow_approvals(status);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_approver_id ON workflow_approvals(approver_id);

CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_user_id ON ai_processing_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_processing_type ON ai_processing_logs(processing_type);
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_created_at ON ai_processing_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_bot_scheduling_logs_user_id ON bot_scheduling_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_bot_scheduling_logs_meeting_id ON bot_scheduling_logs(meeting_id);
CREATE INDEX IF NOT EXISTS idx_bot_scheduling_logs_scheduling_type ON bot_scheduling_logs(scheduling_type);

-- Enable Row Level Security (RLS)
ALTER TABLE classification_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE classification_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE classification_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_processing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_scheduling_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own classification workflows" ON classification_workflows
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own classification workflows" ON classification_workflows
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own classification workflows" ON classification_workflows
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own classification workflows" ON classification_workflows
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own classification batches" ON classification_batches
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own classification batches" ON classification_batches
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own classification batches" ON classification_batches
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own classification results" ON classification_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM classification_batches cb 
            WHERE cb.batch_id = classification_results.batch_id 
            AND cb.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own classification results" ON classification_results
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM classification_batches cb 
            WHERE cb.batch_id = classification_results.batch_id 
            AND cb.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own document workflows" ON document_workflows
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own document workflows" ON document_workflows
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own document workflows" ON document_workflows
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own document workflows" ON document_workflows
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own workflow executions" ON workflow_executions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workflow executions" ON workflow_executions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workflow executions" ON workflow_executions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own workflow approvals" ON workflow_approvals
    FOR SELECT USING (auth.uid() = user_id OR auth.uid() = approver_id);

CREATE POLICY "Users can insert own workflow approvals" ON workflow_approvals
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workflow approvals" ON workflow_approvals
    FOR UPDATE USING (auth.uid() = user_id OR auth.uid() = approver_id);

CREATE POLICY "Users can view own AI processing logs" ON ai_processing_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own AI processing logs" ON ai_processing_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own bot scheduling logs" ON bot_scheduling_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own bot scheduling logs" ON bot_scheduling_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_classification_workflows_updated_at 
    BEFORE UPDATE ON classification_workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_workflows_updated_at 
    BEFORE UPDATE ON document_workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_executions_updated_at 
    BEFORE UPDATE ON workflow_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_approvals_updated_at 
    BEFORE UPDATE ON workflow_approvals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE classification_workflows IS 'Stores AI-powered document classification workflow definitions';
COMMENT ON TABLE classification_batches IS 'Tracks batch classification operations for multiple documents';
COMMENT ON TABLE classification_results IS 'Stores individual document classification results from batch operations';
COMMENT ON TABLE document_workflows IS 'Defines custom document processing workflows with multiple steps';
COMMENT ON TABLE workflow_executions IS 'Tracks the execution of document processing workflows';
COMMENT ON TABLE workflow_approvals IS 'Manages approval steps within document processing workflows';
COMMENT ON TABLE ai_processing_logs IS 'Logs AI processing operations for monitoring and cost tracking';
COMMENT ON TABLE bot_scheduling_logs IS 'Tracks bot scheduling operations and configurations';

-- Insert sample data for testing (optional)
-- INSERT INTO classification_workflows (workflow_id, name, description, document_types, user_id, steps) VALUES
-- ('standard-workflow', 'Standard Classification', 'Basic document classification workflow', ARRAY['document', 'email'], 'sample-user-id', '[]');

-- Migration completed successfully
