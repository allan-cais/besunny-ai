// Core application types
export interface AppConfig {
  environment: 'development' | 'staging' | 'production';
  apiUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
  googleClientId: string;
  openaiApiKey?: string;
}

// User and authentication types
export interface User {
  id: string;
  email?: string;
  name?: string;
  avatar_url?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

export interface Session {
  access_token: string;
  refresh_token: string;
  expires_at?: number;
  user: User;
}

export interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  usernameStatus?: {
    hasUsername: boolean;
    username?: string;
    virtualEmail?: string;
  };
}

// Project types
export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'archived' | 'completed' | 'in_progress';
  created_at: string;
  updated_at: string;
  created_by: string;
  members?: ProjectMember[];
  settings?: ProjectSettings;
}

export interface ProjectMember {
  id: string;
  user_id: string;
  project_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
  user: User;
}

export interface ProjectSettings {
  ai_enabled: boolean;
  auto_classification: boolean;
  notification_preferences: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  slack: boolean;
}

// Document types
export interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'txt' | 'email' | 'meeting';
  content?: string;
  metadata: DocumentMetadata;
  project_id: string;
  created_at: string;
  updated_at: string;
  status: 'processing' | 'completed' | 'error';
  classification?: DocumentClassification;
}

export interface DocumentMetadata {
  size: number;
  mime_type: string;
  source: 'upload' | 'gmail' | 'drive' | 'calendar';
  source_id?: string;
  tags: string[];
  extracted_text?: string;
}

export interface DocumentClassification {
  category: string;
  confidence: number;
  tags: string[];
  summary?: string;
  entities: Entity[];
}

export interface Entity {
  name: string;
  type: 'person' | 'organization' | 'location' | 'date' | 'amount';
  value: string;
  confidence: number;
}

// Meeting types
export interface Meeting {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  attendees: MeetingAttendee[];
  project_id?: string;
  transcript?: MeetingTranscript;
  created_at: string;
  updated_at: string;
}

export interface MeetingAttendee {
  id: string;
  user_id: string;
  meeting_id: string;
  status: 'accepted' | 'declined' | 'pending';
  user: User;
}

export interface MeetingTranscript {
  id: string;
  meeting_id: string;
  content: string;
  segments: TranscriptSegment[];
  summary?: string;
  action_items: ActionItem[];
  created_at: string;
}

export interface TranscriptSegment {
  id: string;
  speaker_id: string;
  text: string;
  timestamp: number;
  confidence: number;
}

export interface ActionItem {
  id: string;
  description: string;
  assignee_id?: string;
  due_date?: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
}

// Email types
export interface Email {
  id: string;
  subject: string;
  sender: string;
  recipients: string[];
  content: string;
  html_content?: string;
  attachments: EmailAttachment[];
  project_id?: string;
  classification?: EmailClassification;
  created_at: string;
  read: boolean;
}

export interface EmailAttachment {
  id: string;
  name: string;
  size: number;
  mime_type: string;
  url?: string;
}

export interface EmailClassification {
  category: 'project_related' | 'personal' | 'spam' | 'newsletter';
  confidence: number;
  priority: 'low' | 'medium' | 'high';
  suggested_actions: string[];
}

// AI and classification types
export interface AIClassification {
  id: string;
  document_id: string;
  model: string;
  category: string;
  confidence: number;
  tags: string[];
  summary: string;
  entities: Entity[];
  metadata: Record<string, any>;
  created_at: string;
}

export interface AIOrchestration {
  id: string;
  type: 'document_processing' | 'meeting_analysis' | 'email_classification';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error?: string;
  created_at: string;
  updated_at: string;
}

// Integration types
export interface GoogleIntegration {
  id: string;
  user_id: string;
  service: 'calendar' | 'drive' | 'gmail';
  access_token: string;
  refresh_token: string;
  expires_at: number;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DriveFile {
  id: string;
  name: string;
  mime_type: string;
  size: number;
  web_view_link: string;
  created_at: string;
  modified_at: string;
  project_id?: string;
  watch_status: 'watching' | 'expired' | 'error';
}

// Chat and conversation types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatSession {
  id: string;
  project_id?: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

// Notification types
export interface Notification {
  id: string;
  user_id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  action_url?: string;
  created_at: string;
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

// Form types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface SignUpFormData {
  email: string;
  password: string;
  confirmPassword: string;
  name: string;
}

export interface ProjectFormData {
  name: string;
  description?: string;
  settings?: Partial<ProjectSettings>;
}

// Component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingState {
  loading: boolean;
  error: string | null;
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
}

// Utility types
export type Status = 'idle' | 'loading' | 'success' | 'error';

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: string;
  direction: SortDirection;
}

export interface FilterConfig {
  field: string;
  value: string | number | boolean;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'in';
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

export interface ThemeConfig {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

// Navigation types
export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  current?: boolean;
  children?: NavigationItem[];
}

// Dashboard types
export interface DashboardStats {
  totalProjects: number;
  activeProjects: number;
  totalDocuments: number;
  pendingClassifications: number;
  upcomingMeetings: number;
  unreadEmails: number;
}

export interface ActivityItem {
  id: string;
  type: 'document_upload' | 'meeting_scheduled' | 'email_received' | 'classification_completed';
  title: string;
  description: string;
  timestamp: string;
  project_id?: string;
  metadata?: Record<string, any>;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface WebSocketConnection {
  isConnected: boolean;
  send: (message: WebSocketMessage) => void;
  subscribe: (type: string, callback: (payload: any) => void) => () => void;
}
