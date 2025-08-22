import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import { AuthProvider } from './providers/AuthProvider';
import { ThemeProvider } from './providers/ThemeProvider';
import { AppInitializer } from './components/AppInitializer';
import AuthPage from './pages/auth';
import DashboardLayout from './components/layout/DashboardLayout';
import DashboardPage from './pages/dashboard';
import IntegrationsPage from './pages/integrations';
import ProjectPage from './pages/project';
import SettingsPage from './pages/settings';
import OAuthCallback from './pages/oauth-callback';
import OAuthLoginCallback from './pages/oauth-login-callback';
import NotFoundPage from './pages/NotFound';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <AppInitializer>
            <Routes>
              {/* Public routes */}
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/oauth/callback" element={<OAuthCallback />} />
              <Route path="/oauth-login-callback" element={<OAuthLoginCallback />} />
              
              {/* Protected routes with DashboardLayout */}
              <Route path="/" element={<DashboardLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="integrations" element={<IntegrationsPage />} />
                <Route path="project/:projectId" element={<ProjectPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
              
              {/* 404 route */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AppInitializer>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
