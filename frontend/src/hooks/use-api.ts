import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { api, ApiError } from '@/lib/api';
import { toast } from 'sonner';

// Query keys for React Query
export const queryKeys = {
  // Auth
  auth: ['auth'] as const,
  profile: ['profile'] as const,
  
  // Projects
  projects: ['projects'] as const,
  project: (id: string) => ['projects', id] as const,
  
  // Documents
  documents: ['documents'] as const,
  documentsByProject: (projectId: string) => ['documents', 'project', projectId] as const,
  document: (id: string) => ['documents', id] as const,
  
  // Meetings
  meetings: ['meetings'] as const,
  meetingsByProject: (projectId: string) => ['meetings', 'project', projectId] as const,
  meeting: (id: string) => ['meetings', id] as const,
  transcript: (meetingId: string) => ['meetings', meetingId, 'transcript'] as const,
  
  // Emails
  emails: ['emails'] as const,
  emailsByProject: (projectId: string) => ['emails', 'project', projectId] as const,
  email: (id: string) => ['emails', id] as const,
  
  // AI
  aiClassifications: ['ai', 'classifications'] as const,
  aiClassification: (id: string) => ['ai', 'classifications', id] as const,
  
  // Integrations
  integrations: ['integrations'] as const,
  googleIntegrations: ['integrations', 'google'] as const,
};

// Error handler for API calls
const handleApiError = (error: unknown, defaultMessage = 'An error occurred') => {
  if (error instanceof ApiError) {
    toast.error(error.message || defaultMessage);
    return error.message;
  }
  
  const message = error instanceof Error ? error.message : defaultMessage;
  toast.error(message);
  return message;
};

// Success handler for API calls
const handleApiSuccess = (message: string) => {
  toast.success(message);
};

// Projects hooks
export const useProjects = (options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => api.projects.getProjects(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
};

export const useProject = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: () => api.projects.getProject(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
};

export const useCreateProject = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (project: any) => api.projects.createProject(project),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      handleApiSuccess('Project created successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to create project');
    },
    ...options,
  });
};

export const useUpdateProject = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) => 
      api.projects.updateProject(id, updates),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.project(id) });
      handleApiSuccess('Project updated successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to update project');
    },
    ...options,
  });
};

export const useDeleteProject = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.projects.deleteProject(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.removeQueries({ queryKey: queryKeys.project(id) });
      handleApiSuccess('Project deleted successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to delete project');
    },
    ...options,
  });
};

// Documents hooks
export const useDocuments = (projectId?: string, options?: UseQueryOptions) => {
  const queryKey = projectId ? queryKeys.documentsByProject(projectId) : queryKeys.documents;
  
  return useQuery({
    queryKey,
    queryFn: () => api.documents.getDocuments(projectId),
    enabled: !projectId || !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
};

export const useDocument = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.document(id),
    queryFn: () => api.documents.getDocument(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
};

export const useUploadDocument = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ file, projectId }: { file: File; projectId?: string }) => 
      api.documents.uploadDocument(file, projectId),
    onSuccess: (data, { projectId }) => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.documentsByProject(projectId) });
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      handleApiSuccess('Document uploaded successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to upload document');
    },
    ...options,
  });
};

export const useUpdateDocument = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) => 
      api.documents.updateDocument(id, updates),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      queryClient.invalidateQueries({ queryKey: queryKeys.document(id) });
      handleApiSuccess('Document updated successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to update document');
    },
    ...options,
  });
};

export const useDeleteDocument = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.documents.deleteDocument(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      queryClient.removeQueries({ queryKey: queryKeys.document(id) });
      handleApiSuccess('Document deleted successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to delete document');
    },
    ...options,
  });
};

// Meetings hooks
export const useMeetings = (projectId?: string, options?: UseQueryOptions) => {
  const queryKey = projectId ? queryKeys.meetingsByProject(projectId) : queryKeys.meetings;
  
  return useQuery({
    queryKey,
    queryFn: () => api.meetings.getMeetings(projectId),
    enabled: !projectId || !!projectId,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
};

export const useMeeting = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.meeting(id),
    queryFn: () => api.meetings.getMeeting(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
};

export const useTranscript = (meetingId: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.transcript(meetingId),
    queryFn: () => api.meetings.getTranscript(meetingId),
    enabled: !!meetingId,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
};

export const useCreateMeeting = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (meeting: any) => api.meetings.createMeeting(meeting),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.meetings });
      handleApiSuccess('Meeting created successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to create meeting');
    },
    ...options,
  });
};

export const useUpdateMeeting = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) => 
      api.meetings.updateMeeting(id, updates),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.meetings });
      queryClient.invalidateQueries({ queryKey: queryKeys.meeting(id) });
      handleApiSuccess('Meeting updated successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to update meeting');
    },
    ...options,
  });
};

export const useDeleteMeeting = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.meetings.deleteMeeting(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.meetings });
      queryClient.removeQueries({ queryKey: queryKeys.meeting(id) });
      handleApiSuccess('Meeting deleted successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to delete meeting');
    },
    ...options,
  });
};

// Emails hooks
export const useEmails = (projectId?: string, options?: UseQueryOptions) => {
  const queryKey = projectId ? queryKeys.emailsByProject(projectId) : queryKeys.emails;
  
  return useQuery({
    queryKey,
    queryFn: () => api.emails.getEmails(projectId),
    enabled: !projectId || !!projectId,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  });
};

export const useEmail = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.email(id),
    queryFn: () => api.emails.getEmail(id),
    enabled: !!id,
    staleTime: 1 * 60 * 1000,
    ...options,
  });
};

export const useMarkEmailAsRead = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.emails.markAsRead(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.emails });
      queryClient.invalidateQueries({ queryKey: queryKeys.email(id) });
      handleApiSuccess('Email marked as read');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to mark email as read');
    },
    ...options,
  });
};

export const useDeleteEmail = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.emails.deleteEmail(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.emails });
      queryClient.removeQueries({ queryKey: queryKeys.email(id) });
      handleApiSuccess('Email deleted successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to delete email');
    },
    ...options,
  });
};

// AI hooks
export const useClassifyDocument = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (documentId: string) => api.ai.classifyDocument(documentId),
    onSuccess: (data, documentId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      queryClient.invalidateQueries({ queryKey: queryKeys.document(documentId) });
      handleApiSuccess('Document classified successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to classify document');
    },
    ...options,
  });
};

export const useProcessDocument = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (documentId: string) => api.ai.processDocument(documentId),
    onSuccess: (data, documentId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      queryClient.invalidateQueries({ queryKey: queryKeys.document(documentId) });
      handleApiSuccess('Document processed successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to process document');
    },
    ...options,
  });
};

export const useAIChat = (options?: UseMutationOptions) => {
  return useMutation({
    mutationFn: ({ message, context }: { message: string; context?: any }) => 
      api.ai.chat(message, context),
    onError: (error) => {
      handleApiError(error, 'Failed to send message');
    },
    ...options,
  });
};

// Integration hooks
export const useGoogleIntegrations = (options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.googleIntegrations,
    queryFn: () => api.integrations.getGoogleIntegrations(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
};

export const useConnectGoogle = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ service, code }: { service: string; code: string }) => 
      api.integrations.connectGoogle(service, code),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.googleIntegrations });
      handleApiSuccess('Google service connected successfully');
    },
    onError: (error) => {
      handleApiError(error, 'Failed to connect Google service');
    },
    ...options,
  });
};

export const useDisconnectGoogle = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (service: string) => api.integrations.disconnectGoogle(service),
    onSuccess: (data, service) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.googleIntegrations });
      handleApiSuccess(`${service} disconnected successfully`);
    },
    onError: (error) => {
      handleApiError(error, 'Failed to disconnect Google service');
    },
    ...options,
  });
};

export const useSyncGoogleData = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (service: string) => api.integrations.syncGoogleData(service),
    onSuccess: (data, service) => {
      // Invalidate relevant queries based on service
      if (service === 'gmail') {
        queryClient.invalidateQueries({ queryKey: queryKeys.emails });
      } else if (service === 'calendar') {
        queryClient.invalidateQueries({ queryKey: queryKeys.meetings });
      } else if (service === 'drive') {
        queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      }
      handleApiSuccess(`${service} data synced successfully`);
    },
    onError: (error) => {
      handleApiError(error, 'Failed to sync Google data');
    },
    ...options,
  });
};
