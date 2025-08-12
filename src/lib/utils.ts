// Utility Functions
// Provides common utilities for data transformation, formatting, and other operations

import { DocumentType, Meeting, Document, VirtualEmailActivity, RawTranscript } from '../types';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility function for combining class names with Tailwind CSS
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Date and Time Utilities
export const dateUtils = {
  // Format date for display
  formatDate(dateString: string, options: Intl.DateTimeFormatOptions = {}): string {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid date';
      }
      
      const defaultOptions: Intl.DateTimeFormatOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        ...options,
      };
      
      return date.toLocaleDateString('en-US', defaultOptions);
    } catch {
      return 'Invalid date';
    }
  },

  // Format time for display
  formatTime(dateString: string, options: Intl.DateTimeFormatOptions = {}): string {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid time';
      }
      
      const defaultOptions: Intl.DateTimeFormatOptions = {
        hour: '2-digit',
        minute: '2-digit',
        ...options,
      };
      
      return date.toLocaleTimeString('en-US', defaultOptions);
    } catch {
      return 'Invalid time';
    }
  },

  // Format date and time together
  formatDateTime(dateString: string): string {
    return `${this.formatDate(dateString)} • ${this.formatTime(dateString)}`;
  },

  // Get relative time (e.g., "2 hours ago")
  getRelativeTime(dateString: string): string {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffInMs = now.getTime() - date.getTime();
      const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
      const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
      const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

      if (diffInMinutes < 1) {
        return 'Just now';
      } else if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes === 1 ? '' : 's'} ago`;
      } else if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours === 1 ? '' : 's'} ago`;
      } else if (diffInDays < 7) {
        return `${diffInDays} day${diffInDays === 1 ? '' : 's'} ago`;
      } else {
        return this.formatDate(dateString);
      }
    } catch {
      return 'Invalid date';
    }
  },

  // Check if date is today
  isToday(dateString: string): boolean {
    try {
      const date = new Date(dateString);
      const today = new Date();
      return date.toDateString() === today.toDateString();
    } catch {
      return false;
    }
  },

  // Check if date is this week
  isThisWeek(dateString: string): boolean {
    try {
      const date = new Date(dateString);
      const today = new Date();
      const startOfWeek = new Date(today);
      startOfWeek.setDate(today.getDate() - today.getDay());
      startOfWeek.setHours(0, 0, 0, 0);
      
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      endOfWeek.setHours(23, 59, 59, 999);
      
      return date >= startOfWeek && date <= endOfWeek;
    } catch {
      return false;
    }
  },
};

// String Utilities
export const stringUtils = {
  // Truncate text with ellipsis
  truncate(text: string, maxLength: number, suffix: string = '...'): string {
    if (!text || text.length <= maxLength) {
      return text;
    }
    return text.substring(0, maxLength - suffix.length) + suffix;
  },

  // Capitalize first letter
  capitalize(text: string): string {
    if (!text) return text;
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  },

  // Convert to title case
  toTitleCase(text: string): string {
    if (!text) return text;
    return text
      .split(' ')
      .map(word => this.capitalize(word))
      .join(' ');
  },

  // Generate initials from name
  getInitials(name: string): string {
    if (!name) return '';
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .join('')
      .substring(0, 2);
  },

  // Clean HTML tags
  stripHtml(html: string): string {
    if (!html) return '';
    return html.replace(/<[^>]*>/g, '').trim();
  },

  // Generate slug from text
  toSlug(text: string): string {
    if (!text) return '';
    return text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  },
};

// Data Transformation Utilities
export const dataUtils = {
  // Transform document to virtual email activity
  documentToVirtualEmailActivity(document: Document): VirtualEmailActivity {
    return {
      id: document.id,
      type: document.type,
      title: document.title || 'Untitled Document',
      summary: document.summary ? stringUtils.truncate(document.summary, 150) : 'No content available',
      source: document.source || 'unknown',
      sender: document.author,
      file_size: document.file_size,
      created_at: document.created_at,
      processed: true,
      project_id: document.project_id,
      transcript_duration_seconds: document.transcript_duration_seconds,
      transcript_metadata: document.transcript_metadata,
      rawTranscript: document.type === 'meeting_transcript' ? {
        id: document.meeting_id || document.id,
        title: document.title,
        transcript: document.summary || '',
        transcript_summary: document.summary || '',
        transcript_metadata: document.transcript_metadata,
        transcript_duration_seconds: document.transcript_duration_seconds || 0,
        transcript_retrieved_at: document.received_at || document.created_at,
        final_transcript_ready: true,
      } : undefined,
    };
  },

  // Transform documents array to virtual email activities
  documentsToVirtualEmailActivities(documents: Document[]): VirtualEmailActivity[] {
    return documents.map(this.documentToVirtualEmailActivity);
  },

  // Get document type from source
  getDocumentType(source: string, document?: Partial<Document>): DocumentType {
    if (document?.type && document.type !== 'unknown') {
      return document.type;
    }

    const sourceLower = source.toLowerCase();
    
    if (sourceLower.includes('gmail') || sourceLower.includes('email')) {
      return 'email';
    }
    
    if (sourceLower.includes('meeting') || sourceLower.includes('transcript')) {
      return 'meeting_transcript';
    }
    
    if (sourceLower.includes('drive') || sourceLower.includes('google')) {
      return 'drive_file';
    }
    
    if (sourceLower.includes('document') || sourceLower.includes('file')) {
      return 'document';
    }
    
    return 'unknown';
  },

  // Sort meetings by start time
  sortMeetingsByStartTime(meetings: Meeting[]): Meeting[] {
    return [...meetings].sort((a, b) => 
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
  },

  // Sort documents by creation date
  sortDocumentsByDate(documents: Document[]): Document[] {
    return [...documents].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  },

  // Filter meetings by status
  filterMeetingsByStatus(meetings: Meeting[], status: string | string[]): Meeting[] {
    const statuses = Array.isArray(status) ? status : [status];
    return meetings.filter(meeting => statuses.includes(meeting.bot_status));
  },

  // Filter documents by type
  filterDocumentsByType(documents: Document[], type: DocumentType | DocumentType[]): Document[] {
    const types = Array.isArray(type) ? type : [type];
    return documents.filter(document => types.includes(document.type));
  },
};

// Validation Utilities
export const validationUtils = {
  // Validate email format
  isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  // Validate URL format
  isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },

  // Validate required fields
  hasRequiredFields<T extends Record<string, unknown>>(
    obj: T, 
    requiredFields: (keyof T)[]
  ): { isValid: boolean; missingFields: (keyof T)[] } {
    const missingFields = requiredFields.filter(field => 
      !obj[field] || (typeof obj[field] === 'string' && obj[field].trim() === '')
    );
    
    return {
      isValid: missingFields.length === 0,
      missingFields,
    };
  },

  // Validate object structure
  validateObjectStructure<T extends Record<string, unknown>>(
    obj: T,
    schema: Record<keyof T, 'string' | 'number' | 'boolean' | 'object' | 'array'>
  ): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    for (const [key, expectedType] of Object.entries(schema)) {
      if (!(key in obj)) {
        errors.push(`Missing required field: ${key}`);
        continue;
      }
      
      const value = obj[key];
      const actualType = Array.isArray(value) ? 'array' : typeof value;
      
      if (actualType !== expectedType) {
        errors.push(`Field ${key} should be ${expectedType}, got ${actualType}`);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
    };
  },
};

// Array Utilities
export const arrayUtils = {
  // Remove duplicates from array
  unique<T>(array: T[], key?: keyof T): T[] {
    if (!key) {
      return [...new Set(array)];
    }
    
    const seen = new Set();
    return array.filter(item => {
      const value = item[key];
      if (seen.has(value)) {
        return false;
      }
      seen.add(value);
      return true;
    });
  },

  // Group array by key
  groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
    return array.reduce((groups, item) => {
      const groupKey = String(item[key]);
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
      return groups;
    }, {} as Record<string, T[]>);
  },

  // Chunk array into smaller arrays
  chunk<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  },

  // Flatten nested arrays
  flatten<T>(array: T[][]): T[] {
    return array.reduce((flat, item) => flat.concat(item), [] as T[]);
  },
};

// Export all utilities
export default {
  date: dateUtils,
  string: stringUtils,
  data: dataUtils,
  validation: validationUtils,
  array: arrayUtils,
};
