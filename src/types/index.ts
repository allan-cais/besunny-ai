// Core Types
export interface User {
  id: string;
  email: string;
  username?: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  entity_patterns?: EntityPatterns;
  classification_signals?: ClassificationSignals;
  pinecone_document_count?: number;
  last_classification_at?: string | null;
  classification_feedback?: ClassificationFeedback;
}

export interface Meeting {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  meeting_url: string;
  user_id: string;
  project_id?: string;
  bot_status: BotStatus;
  attendee_bot_id?: string;
  google_calendar_event_id?: string;
  transcript?: string;
  transcript_retrieved_at?: string;
  transcript_duration_seconds?: number;
  transcript_metadata?: TranscriptMetadata;
  bot_configuration?: BotConfiguration;
  created_at: string;
  updated_at: string;
  event_status: 'accepted' | 'declined' | 'tentative' | 'needsAction';
  bot_deployment_method?: 'manual' | 'automatic' | 'scheduled';
  auto_scheduled_via_email?: boolean;
  virtual_email_attendee?: string;
  auto_bot_notification_sent?: boolean;
  bot_name?: string;
  bot_chat_message?: string;
}

export interface Document {
  id: string;
  title: string;
  summary?: string;
  source: string;
  type: DocumentType;
  author?: string;
  file_size?: number;
  project_id?: string;
  meeting_id?: string;
  transcript_duration_seconds?: number;
  transcript_metadata?: TranscriptMetadata;
  created_at: string;
  updated_at: string;
  received_at?: string;
  last_synced_at?: string;
  file_id?: string;
  file_url?: string;
  status?: 'active' | 'updated' | 'deleted' | 'error';
  watch_active?: boolean;
}

export interface ChatSession {
  id: string;
  user_id: string;
  project_id?: string;
  name?: string;
  started_at: string;
  ended_at?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  created_at: string;
}

// Enums
export type BotStatus = 'pending' | 'bot_scheduled' | 'bot_joined' | 'transcribing' | 'completed' | 'failed';

export type DocumentType = 'email' | 'meeting_transcript' | 'document' | 'drive_file' | 'spreadsheet' | 'presentation' | 'image' | 'folder' | 'unknown';

export type SyncStatus = 'idle' | 'syncing' | 'completed' | 'failed';

export type WebhookStatus = 'active' | 'expired' | 'failed' | 'pending';

// Complex Types
export interface EntityPatterns {
  domains?: string[];
  people?: Record<string, PersonData>;
  organizations?: string[];
  locations?: string[];
  technologies?: string[];
}

export interface PersonData {
  role: 'internal_lead' | 'agency_lead' | 'client_lead' | 'team_member' | 'stakeholder';
  email?: string;
  department?: string;
  seniority?: 'junior' | 'mid' | 'senior' | 'executive';
}

export interface ClassificationSignals {
  confidence: number;
  categories: string[];
  keywords: string[];
  sentiment?: 'positive' | 'negative' | 'neutral';
  urgency?: 'low' | 'medium' | 'high' | 'critical';
}

export interface ClassificationFeedback {
  user_rating?: number;
  user_notes?: string;
  corrected_categories?: string[];
  feedback_date?: string;
}

export interface TranscriptMetadata {
  participants?: Participant[];
  speakers?: Speaker[];
  segments?: TranscriptSegment[];
  audio_url?: string;
  recording_url?: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed' | 'not_available';
  quality_score?: number;
  language?: string;
  confidence_score?: number;
}

export interface Participant {
  id: string;
  name: string;
  email?: string;
  role?: string;
  join_time?: string;
  leave_time?: string;
}

export interface Speaker {
  id: string;
  name: string;
  total_speaking_time: number;
  segments_count: number;
}

export interface TranscriptSegment {
  id: string;
  speaker_id: string;
  start_time: number;
  end_time: number;
  text: string;
  confidence: number;
}

export interface BotConfiguration {
  transcription_settings?: TranscriptionSettings;
  recording_settings?: RecordingSettings;
  teams_settings?: TeamsSettings;
  debug_settings?: DebugSettings;
}

export interface TranscriptionSettings {
  language: string;
  enable_speaker_diarization: boolean;
  enable_punctuation: boolean;
  enable_sentiment_analysis: boolean;
}

export interface RecordingSettings {
  quality: 'low' | 'medium' | 'high';
  format: 'mp4' | 'webm' | 'avi';
  enable_audio_only: boolean;
}

export interface TeamsSettings {
  enable_team_chat: boolean;
  enable_team_notifications: boolean;
  team_members?: string[];
}

export interface DebugSettings {
  create_debug_recording: boolean;
  log_level: 'debug' | 'info' | 'warn' | 'error';
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface CalendarSyncResult {
  success: boolean;
  type: 'calendar' | 'gmail' | 'drive' | 'attendee';
  processed: number;
  created: number;
  updated: number;
  deleted: number;
  skipped: boolean;
  virtualEmailsDetected: number;
  autoScheduledMeetings: number;
  error?: string;
}

export interface WebhookStatus {
  webhook_active: boolean;
  webhook_url?: string;
  last_sync?: string;
  sync_logs: SyncLog[];
  recent_errors: ErrorLog[];
  webhook_expires_at?: string;
  connectivity_test?: boolean;
}

export interface SyncLog {
  id: string;
  user_id: string;
  type: string;
  status: 'completed' | 'failed' | 'in_progress';
  processed_count: number;
  created_count: number;
  updated_count: number;
  deleted_count: number;
  error_message?: string;
  created_at: string;
}

export interface ErrorLog {
  id: string;
  user_id: string;
  error_type: string;
  error_message: string;
  stack_trace?: string;
  created_at: string;
}

// Google Integration Types
export interface GoogleCredentials {
  user_id: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
  scope: string;
  google_email: string;
  service: 'calendar' | 'gmail' | 'drive';
  created_at: string;
}

export interface GoogleCalendarEvent {
  id: string;
  summary?: string;
  description?: string;
  start: {
    dateTime?: string;
    date?: string;
  };
  end: {
    dateTime?: string;
    date?: string;
  };
  attendees?: GoogleCalendarAttendee[];
  creator?: {
    email: string;
  };
  entryPoints?: GoogleCalendarEntryPoint[];
  conferenceData?: {
    entryPoints?: GoogleCalendarEntryPoint[];
  };
}

export interface GoogleCalendarAttendee {
  email: string;
  displayName?: string;
  responseStatus?: 'needsAction' | 'declined' | 'tentative' | 'accepted';
  self?: boolean;
}

export interface GoogleCalendarEntryPoint {
  entryPointType: 'video' | 'phone' | 'sip' | 'more';
  uri: string;
  label?: string;
}

// Virtual Email Types
export interface VirtualEmailActivity {
  id: string;
  type: DocumentType;
  title: string;
  summary: string;
  source: string;
  sender?: string;
  file_size?: number;
  created_at: string;
  processed: boolean;
  project_id?: string;
  transcript_duration_seconds?: number;
  transcript_metadata?: TranscriptMetadata;
  rawTranscript?: RawTranscript;
}

export interface RawTranscript {
  id: string;
  title: string;
  transcript: string;
  transcript_summary: string;
  transcript_metadata?: TranscriptMetadata;
  transcript_duration_seconds?: number;
  transcript_retrieved_at: string;
  final_transcript_ready: boolean;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Nullable<T> = T | null;

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Component Props Types
export interface DashboardChatSession {
  id: string;
  title: string;
  createdAt: string;
  lastMessageAt: string;
  unreadCount: number;
}

export interface Bot {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  avatar_url?: string;
  provider: string;
  provider_bot_id?: string;
  settings?: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthSession {
  access_token: string;
  user: {
    id: string;
    email?: string;
  };
}

export interface AIChatSession {
  id: string;
  user_id?: string;
  project_id?: string;
  started_at: string;
  ended_at?: string;
}
