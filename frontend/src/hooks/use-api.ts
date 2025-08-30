import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { PythonBackendAPI } from '@/lib/python-backend-api';  // Updated to use Python backend API
import { toast } from 'sonner';

// Create a single instance of the Python backend API
const pythonBackendAPI = new PythonBackendAPI();

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
  
  // AI
  aiClassifications: ['ai', 'classifications'] as const,
  aiClassification: (id: string) => ['ai', 'classifications', id] as const,
};

// Error handler for API calls
const handleApiError = (error: unknown, defaultMessage = 'An error occurred') => {
  if (error && typeof error === 'object' && 'error' in error) {
    const apiError = error as { error?: string };
    toast.error(apiError.error || defaultMessage);
    return apiError.error;
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
    queryFn: () => pythonBackendAPI.getProjects(''), // TODO: Get actual user ID
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
};

export const useProject = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: () => pythonBackendAPI.getProject(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
};

export const useCreateProject = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (project: any) => pythonBackendAPI.createProject(project),
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
      pythonBackendAPI.updateProject(id, updates),
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
    mutationFn: (id: string) => pythonBackendAPI.deleteProject(id),
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
    queryFn: () => pythonBackendAPI.getDocuments('', projectId), // TODO: Get actual user ID
    enabled: !projectId || !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
};

export const useUploadDocument = (options?: UseMutationOptions) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ file, projectId }: { file: File; projectId?: string }) => 
      pythonBackendAPI.uploadDocument(file, '', projectId), // TODO: Get actual user ID
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

// AI hooks
export const useGenerateAIResponse = (options?: UseMutationOptions) => {
  return useMutation({
    mutationFn: ({ prompt, userId, model }: { prompt: string; userId: string; model?: string }) => 
      pythonBackendAPI.generateAIResponse(prompt, userId, model),
    onError: (error) => {
      handleApiError(error, 'Failed to generate AI response');
    },
    ...options,
  });
};

export const useAIHistory = (userId: string, limit = 50, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: ['ai', 'history', userId, limit],
    queryFn: () => pythonBackendAPI.getAIHistory(userId, limit),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
};

export const useProcessProjectOnboarding = (options?: UseMutationOptions) => {
  return useMutation({
    mutationFn: (payload: any) => pythonBackendAPI.processProjectOnboarding(payload),
    onError: (error) => {
      handleApiError(error, 'Failed to process project onboarding');
    },
    ...options,
  });
};
