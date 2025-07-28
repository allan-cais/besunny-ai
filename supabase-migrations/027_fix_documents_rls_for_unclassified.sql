-- Migration to fix documents RLS policy to allow viewing unclassified documents
-- This allows users to see documents that have no project_id assigned

-- Drop the existing restrictive policy
DROP POLICY IF EXISTS "Users can view documents in their projects" ON documents;

-- Create a new policy that allows users to see:
-- 1. Documents from projects they own
-- 2. Documents with no project_id (unclassified documents)
CREATE POLICY "Users can view documents in their projects or unclassified" ON documents
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
    OR project_id IS NULL
  );

-- Also update the insert policy to allow inserting unclassified documents
DROP POLICY IF EXISTS "Users can insert documents in their projects" ON documents;

CREATE POLICY "Users can insert documents in their projects or unclassified" ON documents
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
    OR project_id IS NULL
  );

-- Update the update policy to allow updating unclassified documents
DROP POLICY IF EXISTS "Users can update documents in their projects" ON documents;

CREATE POLICY "Users can update documents in their projects or unclassified" ON documents
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
    OR project_id IS NULL
  );

-- Update the delete policy to allow deleting unclassified documents
DROP POLICY IF EXISTS "Users can delete documents in their projects" ON documents;

CREATE POLICY "Users can delete documents in their projects or unclassified" ON documents
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()
    )
    OR project_id IS NULL
  ); 