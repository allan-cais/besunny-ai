import axios from 'axios';
import { supabase } from './supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      await supabase.auth.signOut();
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Documents
  getDocuments: (projectId: string, params?: any) =>
    apiClient.get(`/documents?projectId=${projectId}`, { params }),
  
  getDocument: (documentId: string) =>
    apiClient.get(`/documents/${documentId}`),
  
  uploadDocument: (projectId: string, file: File, metadata?: any) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('projectId', projectId);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }
    return apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Chat
  sendMessage: (projectId: string, message: string, context?: any) =>
    apiClient.post('/chat/message', { projectId, message, context }),
  
  getChatHistory: (projectId: string) =>
    apiClient.get(`/chat/history?projectId=${projectId}`),

  // Tags
  getTags: (projectId: string) =>
    apiClient.get(`/tags?projectId=${projectId}`),
  
  createTag: (projectId: string, tag: any) =>
    apiClient.post('/tags', { projectId, ...tag }),

  // Projects
  getProjects: () => apiClient.get('/projects'),
  getProject: (projectId: string) => apiClient.get(`/projects/${projectId}`),
  createProject: (project: any) => apiClient.post('/projects', project),
  updateProject: (projectId: string, updates: any) =>
    apiClient.put(`/projects/${projectId}`, updates),
}; 