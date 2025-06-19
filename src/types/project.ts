export interface Project {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  settings?: ProjectSettings;
}

export interface ProjectSettings {
  allow_public_access?: boolean;
  max_file_size?: number;
  allowed_file_types?: string[];
  retention_policy?: RetentionPolicy;
}

export interface RetentionPolicy {
  days: number;
  action: 'delete' | 'archive';
} 