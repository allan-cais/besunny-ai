export interface Document {
  id: string;
  project_id: string;
  title: string;
  content?: string;
  file_path?: string;
  file_type: string;
  file_size: number;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  metadata?: DocumentMetadata;
}

export interface DocumentMetadata {
  author?: string;
  date_created?: string;
  date_modified?: string;
  page_count?: number;
  language?: string;
  extracted_text?: string;
  ocr_processed?: boolean;
}

export interface DocumentSummary {
  id: string;
  title: string;
  created_at: string;
  file_type: string;
  tags: string[];
  summary?: string;
} 