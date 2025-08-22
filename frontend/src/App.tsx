import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/providers/AuthProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import Index from "./pages/index";
import DashboardLayout from "./components/layout/DashboardLayout";
import Dashboard from "./pages/dashboard";
import AuthPage from "./pages/auth";
import IntegrationsPage from "./pages/integrations";
import OAuthCallback from "./pages/oauth-callback";
import OAuthLoginCallback from "./pages/oauth-login-callback";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import ProjectDashboard from "./pages/project";
import SettingsPage from "./pages/settings";
import { updateConfigFromRuntime } from "./config";

const queryClient = new QueryClient();

const App = () => {
  // Update configuration from runtime when app starts
  React.useEffect(() => {
    updateConfigFromRuntime();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <ThemeProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/auth" element={<AuthPage />} />
              
              {/* Protected routes that use DashboardLayout */}
              <Route 
                path="/" 
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                } 
              >
                <Route index element={<Dashboard />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="integrations" element={<IntegrationsPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="project/:projectId" element={<ProjectDashboard />} />
                <Route path="debug" element={<div className="p-8">Debug Route - Current path: {window.location.pathname}</div>} />
              </Route>
              
              {/* OAuth callback routes - these don't use DashboardLayout */}
              <Route 
                path="/oauth/callback" 
                element={<OAuthCallback />} 
              />
              <Route 
                path="/oauth-login-callback" 
                element={<OAuthLoginCallback />} 
              />
              
              {/* Catch-all route */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </AuthProvider>
  </QueryClientProvider>
  );
};

export default App;
