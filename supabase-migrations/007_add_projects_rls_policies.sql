-- Add Row Level Security policies for projects table
-- This migration ensures users can only access their own projects

-- Enable Row Level Security on projects table
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for projects table
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can insert own projects" ON projects
  FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE USING (auth.uid() = created_by);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by); 