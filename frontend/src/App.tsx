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
import EnvironmentDebug from "./components/EnvironmentDebug";
import RailwayEnvironmentTest from "./components/RailwayEnvironmentTest";

const queryClient = new QueryClient();

const App = () => (
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
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                } 
              >
                <Route index element={<Dashboard />} />
              </Route>
              <Route 
                path="/integrations" 
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                } 
              >
                <Route index element={<IntegrationsPage />} />
              </Route>
              <Route 
                path="/oauth/callback" 
                element={
                  <OAuthCallback />
                } 
              />
              <Route 
                path="/oauth-login-callback" 
                element={
                  <OAuthLoginCallback />
                } 
              />
              <Route 
                path="/project/:projectId" 
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                } 
              >
                <Route index element={<ProjectDashboard />} />
              </Route>
              <Route 
                path="/settings" 
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                } 
              >
                <Route index element={<SettingsPage />} />
              </Route>
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
          
          {/* Temporary debug component for staging troubleshooting */}
          <EnvironmentDebug show={true} />
          <RailwayEnvironmentTest />
        </TooltipProvider>
      </ThemeProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
