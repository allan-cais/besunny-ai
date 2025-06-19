import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';
import { useProject } from '../providers/ProjectProvider';

// Import pages
import IndexPage from '../pages/index';
import ChatPage from '../pages/chat';
import DashboardPage from '../pages/dashboard';
import DocumentsPage from '../pages/documents';
import DigestsPage from '../pages/digests';
import ReceiptsPage from '../pages/receipts';
import SpacesPage from '../pages/spaces';
import UploadPage from '../pages/upload';
import SettingsPage from '../pages/settings';

// Auth guard component
const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

// Project guard component
const ProjectGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentProject, loading } = useProject();
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading project...</div>;
  }
  
  if (!currentProject) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <IndexPage />,
  },
  {
    path: '/dashboard',
    element: <DashboardPage />,
  },
  {
    path: '/chat',
    element: (
      <AuthGuard>
        <ProjectGuard>
          <ChatPage />
        </ProjectGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/documents',
    element: (
      <AuthGuard>
        <ProjectGuard>
          <DocumentsPage />
        </ProjectGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/digests',
    element: (
      <AuthGuard>
        <ProjectGuard>
          <DigestsPage />
        </ProjectGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/receipts',
    element: (
      <AuthGuard>
        <ProjectGuard>
          <ReceiptsPage />
        </ProjectGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/spaces',
    element: (
      <AuthGuard>
        <ProjectGuard>
          <SpacesPage />
        </ProjectGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/upload',
    element: (
      <AuthGuard>
        <ProjectGuard>
          <UploadPage />
        </ProjectGuard>
      </AuthGuard>
    ),
  },
  {
    path: '/settings',
    element: (
      <AuthGuard>
        <SettingsPage />
      </AuthGuard>
    ),
  },
]); 