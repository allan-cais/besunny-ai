export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  metadata?: ChatMessageMetadata;
}

export interface ChatMessageMetadata {
  document_references?: string[];
  confidence_score?: number;
  processing_time?: number;
}

export interface ChatSession {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  context?: ChatContext;
}

export interface ChatContext {
  documents?: string[];
  tags?: string[];
  date_range?: {
    start: string;
    end: string;
  };
} 