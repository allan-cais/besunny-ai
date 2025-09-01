import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './providers/ThemeProvider';
import { AuthProvider } from './providers/AuthProvider';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { PublicRoute } from './components/auth/PublicRoute';
import DashboardLayout from './components/layout/DashboardLayout';

// Lazy load page components
const AuthPage = lazy(() => import('./pages/auth'));
const DashboardPage = lazy(() => import('./pages/dashboard'));
const IntegrationsPage = lazy(() => import('./pages/integrations'));
const ProjectPage = lazy(() => import('./pages/project'));
const SettingsPage = React.lazy(() => import('./pages/settings'));
const NotFoundPage = lazy(() => import('./pages/NotFound'));

// Loading component
const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
  </div>
);

// Main app routes component
const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes */}
        <Route 
          path="/auth" 
          element={
            <PublicRoute>
              <AuthPage />
            </PublicRoute>
          } 
        />
        
        {/* Protected routes with DashboardLayout */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route 
            path="dashboard" 
            element={<DashboardPage />} 
          />
          <Route 
            path="integrations" 
            element={<IntegrationsPage />} 
          />
          <Route 
            path="project/:id" 
            element={<ProjectPage />} 
          />
          <Route 
            path="settings" 
            element={<SettingsPage />} 
          />
        </Route>
        
        {/* OAuth callback routes */}
        <Route 
          path="/oauth-callback" 
          element={
            <PublicRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <LoadingSpinner size="lg" />
                  <p className="mt-4 text-gray-600">Completing authentication...</p>
                </div>
              </div>
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/oauth-login-callback" 
          element={
            <PublicRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <LoadingSpinner size="lg" />
                  <p className="mt-4 text-gray-600">Completing login...</p>
                </div>
              </div>
            </PublicRoute>
          } 
        />
        

        
        {/* 404 route */}
        <Route 
          path="*" 
          element={<NotFoundPage />} 
        />
      </Routes>
    </Suspense>
  );
};

// Main App component
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
