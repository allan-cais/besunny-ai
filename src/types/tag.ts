export interface Tag {
  id: string;
  name: string;
  color?: string;
  project_id: string;
  created_at: string;
  usage_count: number;
}

export interface TagCategory {
  id: string;
  name: string;
  description?: string;
  tags: Tag[];
}

export interface TagFilter {
  tags: string[];
  exclude_tags?: string[];
  operator: 'AND' | 'OR';
} 