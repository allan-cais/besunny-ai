export const APP_NAME = 'Kirit Askuno';

export const FILE_TYPES = {
  PDF: 'application/pdf',
  DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  TXT: 'text/plain',
  PNG: 'image/png',
  JPG: 'image/jpeg',
  JPEG: 'image/jpeg',
} as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const TAG_COLORS = [
  '#3B82F6', // blue
  '#10B981', // emerald
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // violet
  '#06B6D4', // cyan
  '#84CC16', // lime
  '#F97316', // orange
  '#EC4899', // pink
  '#6B7280', // gray
] as const;

export const ROUTES = {
  HOME: '/',
  CHAT: '/chat',
  DASHBOARD: '/dashboard',
  DOCUMENTS: '/documents',
  DIGESTS: '/digests',
  RECEIPTS: '/receipts',
  SPACES: '/spaces',
  UPLOAD: '/upload',
  SETTINGS: '/settings',
} as const;

export const API_ENDPOINTS = {
  AUTH: '/auth',
  PROJECTS: '/projects',
  DOCUMENTS: '/documents',
  CHAT: '/chat',
  TAGS: '/tags',
  UPLOAD: '/upload',
} as const; 