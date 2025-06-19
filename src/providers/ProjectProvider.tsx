import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import { api } from '../lib/apiClient';
import type { Project } from '../types/project';

interface ProjectContextType {
  currentProject: Project | null;
  projects: Project[];
  loading: boolean;
  setCurrentProject: (project: Project | null) => void;
  createProject: (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => Promise<{ data?: Project; error?: any }>;
  updateProject: (projectId: string, updates: Partial<Project>) => Promise<{ data?: Project; error?: any }>;
  refreshProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

interface ProjectProviderProps {
  children: React.ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchProjects = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const response = await api.getProjects();
      setProjects(response.data || []);
      // Set first project as current if none selected
      if (!currentProject && response.data && response.data.length > 0) {
        setCurrentProject(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [user]);

  const createProject = async (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => {
    if (!user) return { error: 'User not authenticated' };

    try {
      const response = await api.createProject({
        ...project,
        owner_id: user.id,
      });
      
      const newProject = response.data;
      if (newProject) {
        setProjects(prev => [newProject, ...prev]);
        setCurrentProject(newProject);
      }
      
      return { data: newProject };
    } catch (error: any) {
      return { error: error.response?.data || error.message };
    }
  };

  const updateProject = async (projectId: string, updates: Partial<Project>) => {
    try {
      const response = await api.updateProject(projectId, updates);
      const updatedProject = response.data;
      
      if (updatedProject) {
        setProjects(prev => prev.map(p => p.id === projectId ? updatedProject : p));
        if (currentProject?.id === projectId) {
          setCurrentProject(updatedProject);
        }
      }
      
      return { data: updatedProject };
    } catch (error: any) {
      return { error: error.response?.data || error.message };
    }
  };

  const refreshProjects = async () => {
    await fetchProjects();
  };

  const value = {
    currentProject,
    projects,
    loading,
    setCurrentProject,
    createProject,
    updateProject,
    refreshProjects,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
}; 