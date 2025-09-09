/**
 * Meeting Classification Service
 * Handles manual classification of meeting transcripts
 */

import { supabase } from './supabase';

export interface UnclassifiedMeeting {
  id: string;
  bot_id: string;
  user_id: string;
  meeting_url: string;
  bot_name: string;
  transcript: string;
  metadata: any;
  created_at: string;
  updated_at: string;
  meetings: {
    id: string;
    title: string;
    start_time: string;
    end_time: string;
    meeting_url: string;
  };
}

export interface Project {
  id: string;
  name: string;
  description: string;
}

export interface ClassificationRequest {
  bot_id: string;
  project_id: string;
}

export interface ClassificationResponse {
  success: boolean;
  message: string;
  project_id?: string;
  error?: string;
}

class MeetingClassificationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000';
  }

  /**
   * Get meetings that need manual classification
   */
  async getUnclassifiedMeetings(): Promise<UnclassifiedMeeting[]> {
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${this.baseUrl}/api/v1/meeting-classification/unclassified`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data || [];
    } catch (error) {
      console.error('Error fetching unclassified meetings:', error);
      return [];
    }
  }

  /**
   * Manually classify a meeting transcript to a project
   */
  async classifyMeeting(request: ClassificationRequest): Promise<ClassificationResponse> {
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${this.baseUrl}/api/v1/meeting-classification/classify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error classifying meeting:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get user's projects for classification
   */
  async getUserProjects(): Promise<Project[]> {
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${this.baseUrl}/api/v1/meeting-classification/projects`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data || [];
    } catch (error) {
      console.error('Error fetching user projects:', error);
      return [];
    }
  }
}

export const meetingClassificationService = new MeetingClassificationService();
