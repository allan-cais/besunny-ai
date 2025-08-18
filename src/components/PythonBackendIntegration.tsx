/**
 * Python Backend Integration Component
 * Demonstrates the integration between React frontend and Python backend v15
 */

import React, { useState, useEffect } from 'react';
import { usePythonBackend } from '../hooks/use-python-backend';
import { pythonBackendConfig } from '../config/python-backend-config';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Separator } from './ui/separator';
import { 
  User, 
  Project, 
  Bot, 
  Settings, 
  Plus, 
  Trash2, 
  Edit, 
  Users, 
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';

export function PythonBackendIntegration() {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'projects' | 'ai'>('overview');
  const [newProject, setNewProject] = useState({ name: '', description: '', visibility: 'private' as const });
  const [aiPrompt, setAiPrompt] = useState('');
  const [selectedUserId, setSelectedUserId] = useState('user-001'); // Demo user ID

  const {
    // Connection state
    isConnected,
    isConnecting,
    connectionError,
    
    // API state
    isLoading,
    error,
    
    // Data
    health,
    userProfile,
    userPreferences,
    projects,
    currentProject,
    aiResponse,
    aiHistory,
    
    // Methods
    connect,
    disconnect,
    checkHealth,
    fetchUserProfile,
    updateUserProfile,
    updateUserPreferences,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    addProjectMember,
    removeProjectMember,
    orchestrateAI,
    fetchAIHistory,
    clearError,
    retryLastOperation,
  } = usePythonBackend({
    config: pythonBackendConfig,
    autoConnect: true,
    retryOnFailure: true,
  });

  // Load initial data
  useEffect(() => {
    if (isConnected && selectedUserId) {
      fetchUserProfile(selectedUserId);
      fetchProjects(selectedUserId);
      fetchAIHistory(selectedUserId);
    }
  }, [isConnected, selectedUserId, fetchUserProfile, fetchProjects, fetchAIHistory]);

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) return;
    
    await createProject({
      ...newProject,
      owner_id: selectedUserId,
      members: [],
    });
    
    setNewProject({ name: '', description: '', visibility: 'private' });
  };

  const handleOrchestrateAI = async () => {
    if (!aiPrompt.trim()) return;
    
    await orchestrateAI({
      prompt: aiPrompt,
      user_id: selectedUserId,
      context: currentProject ? `Project: ${currentProject.name}` : undefined,
      project_id: currentProject?.id,
    });
    
    setAiPrompt('');
  };

  const handleUpdatePreferences = async (updates: any) => {
    if (!userProfile) return;
    
    await updateUserPreferences(userProfile.id, updates);
  };

  if (isConnecting) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg font-medium">Connecting to Python Backend...</p>
        </div>
      </div>
    );
  }

  if (connectionError) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to connect to Python Backend: {connectionError}
          </AlertDescription>
        </Alert>
        
        <div className="flex gap-4">
          <Button onClick={connect} variant="default">
            Retry Connection
          </Button>
          <Button onClick={disconnect} variant="outline">
            Disconnect
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Python Backend Integration</h1>
          <p className="text-muted-foreground">
            BeSunny.ai v15 - AI Orchestration, User Management & Project Management
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <Badge variant={isConnected ? "default" : "secondary"}>
            {isConnected ? (
              <>
                <CheckCircle className="h-3 w-3 mr-1" />
                Connected
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Disconnected
              </>
            )}
          </Badge>
          
          {health && (
            <Badge variant="outline">
              <Activity className="h-3 w-3 mr-1" />
              v{health.version}
            </Badge>
          )}
          
          <Button onClick={disconnect} variant="outline" size="sm">
            Disconnect
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
            <Button onClick={retryLastOperation} variant="link" className="p-0 h-auto ml-2">
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'users', label: 'User Management', icon: User },
          { id: 'projects', label: 'Projects', icon: Project },
          { id: 'ai', label: 'AI Orchestration', icon: Bot },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === tab.id
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Connection Status</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Python Backend v15
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">User Profile</CardTitle>
                <User className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {userProfile ? userProfile.full_name : 'Not Loaded'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {userProfile ? userProfile.email : 'No user data'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Projects</CardTitle>
                <Project className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{projects.length}</div>
                <p className="text-xs text-muted-foreground">
                  Active projects
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">AI Responses</CardTitle>
                <Bot className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{aiHistory.length}</div>
                <p className="text-xs text-muted-foreground">
                  AI interactions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Backend Health</CardTitle>
                <Activity className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {health ? health.status : 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Last checked: {health ? new Date(health.timestamp * 1000).toLocaleTimeString() : 'Never'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Configuration</CardTitle>
                <Settings className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {pythonBackendConfig.baseUrl.includes('localhost') ? 'Local' : 'Remote'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {pythonBackendConfig.baseUrl}
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* User Management Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            {userProfile ? (
              <Card>
                <CardHeader>
                  <CardTitle>User Profile</CardTitle>
                  <CardDescription>Manage user information and preferences</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input
                        id="fullName"
                        value={userProfile.full_name}
                        onChange={(e) => updateUserProfile(userProfile.id, { full_name: e.target.value })}
                        disabled={isLoading}
                      />
                    </div>
                    <div>
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        value={userProfile.username}
                        onChange={(e) => updateUserProfile(userProfile.id, { username: e.target.value })}
                        disabled={isLoading}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      value={userProfile.email}
                      disabled
                      className="bg-muted"
                    />
                  </div>

                  <Separator />

                  <div>
                    <Label>Theme Preference</Label>
                    <div className="flex gap-2 mt-2">
                      {['light', 'dark', 'system'].map((theme) => (
                        <Button
                          key={theme}
                          variant={userPreferences?.theme === theme ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => handleUpdatePreferences({ theme: theme as any })}
                          disabled={isLoading}
                        >
                          {theme.charAt(0).toUpperCase() + theme.slice(1)}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label>Notifications</Label>
                    <div className="flex gap-4 mt-2">
                      {['email', 'push', 'sms'].map((type) => (
                        <div key={type} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={type}
                            checked={userPreferences?.notifications[type as keyof typeof userPreferences.notifications] || false}
                            onChange={(e) => handleUpdatePreferences({
                              notifications: {
                                ...userPreferences?.notifications,
                                [type]: e.target.checked
                              }
                            })}
                            disabled={isLoading}
                          />
                          <Label htmlFor={type} className="text-sm capitalize">
                            {type}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No user profile loaded</p>
                    <Button onClick={() => fetchUserProfile(selectedUserId)} className="mt-2">
                      Load Profile
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="space-y-6">
            {/* Create New Project */}
            <Card>
              <CardHeader>
                <CardTitle>Create New Project</CardTitle>
                <CardDescription>Start a new project with team collaboration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="projectName">Project Name</Label>
                    <Input
                      id="projectName"
                      value={newProject.name}
                      onChange={(e) => setNewProject(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter project name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="projectVisibility">Visibility</Label>
                    <select
                      id="projectVisibility"
                      value={newProject.visibility}
                      onChange={(e) => setNewProject(prev => ({ ...prev, visibility: e.target.value as any }))}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background"
                    >
                      <option value="private">Private</option>
                      <option value="team">Team</option>
                      <option value="public">Public</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="projectDescription">Description</Label>
                  <Textarea
                    id="projectDescription"
                    value={newProject.description}
                    onChange={(e) => setNewProject(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe your project"
                    rows={3}
                  />
                </div>
                
                <Button onClick={handleCreateProject} disabled={!newProject.name.trim() || isLoading}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                  Create Project
                </Button>
              </CardContent>
            </Card>

            {/* Projects List */}
            <Card>
              <CardHeader>
                <CardTitle>Your Projects</CardTitle>
                <CardDescription>Manage and collaborate on projects</CardDescription>
              </CardHeader>
              <CardContent>
                {projects.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Project className="h-12 w-12 mx-auto mb-4" />
                    <p>No projects yet. Create your first project above!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {projects.map((project) => (
                      <div key={project.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex-1">
                          <h3 className="font-medium">{project.name}</h3>
                          <p className="text-sm text-muted-foreground">{project.description}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline">{project.visibility}</Badge>
                            <Badge variant="secondary">
                              <Users className="h-3 w-3 mr-1" />
                              {project.members.length} members
                            </Badge>
                          </div>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentProject(project)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => deleteProject(project.id)}
                            disabled={isLoading}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* AI Orchestration Tab */}
        {activeTab === 'ai' && (
          <div className="space-y-6">
            {/* AI Chat Interface */}
            <Card>
              <CardHeader>
                <CardTitle>AI Orchestration</CardTitle>
                <CardDescription>Interact with AI services for project assistance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="aiPrompt">What would you like help with?</Label>
                  <Textarea
                    id="aiPrompt"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    placeholder="Describe your request, ask for help, or request analysis..."
                    rows={4}
                  />
                </div>
                
                <div className="flex gap-2">
                  <Button onClick={handleOrchestrateAI} disabled={!aiPrompt.trim() || isLoading}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Bot className="h-4 w-4 mr-2" />}
                    Ask AI
                  </Button>
                  
                  {currentProject && (
                    <Badge variant="outline">
                      <Project className="h-3 w-3 mr-1" />
                      {currentProject.name}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Latest AI Response */}
            {aiResponse && (
              <Card>
                <CardHeader>
                  <CardTitle>Latest AI Response</CardTitle>
                  <CardDescription>AI orchestration result</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="whitespace-pre-wrap">{aiResponse.response}</p>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Model: {aiResponse.model_used}</span>
                      <span>Tokens: {aiResponse.tokens_used}</span>
                      <span>Confidence: {(aiResponse.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                    
                    {aiResponse.suggestions && aiResponse.suggestions.length > 0 && (
                      <div>
                        <Label className="text-sm font-medium">Suggestions:</Label>
                        <div className="flex gap-2 mt-2">
                          {aiResponse.suggestions.map((suggestion, index) => (
                            <Badge key={index} variant="secondary">
                              {suggestion}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* AI History */}
            {aiHistory.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>AI Interaction History</CardTitle>
                  <CardDescription>Previous AI conversations and responses</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {aiHistory.slice(0, 5).map((response, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <p className="text-sm text-muted-foreground mb-2">
                          {new Date().toLocaleDateString()} - {response.model_used}
                        </p>
                        <p className="text-sm line-clamp-2">{response.response}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
