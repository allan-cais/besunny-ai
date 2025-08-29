import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/providers/AuthProvider';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useSupabase } from '@/hooks/use-supabase';
import type { Project, Meeting, Document, ChatSession } from '@/types';
import CreateProjectDialog from '@/components/CreateProjectDialog';
import AIAssistant from '@/components/AIAssistant';
import UsernameSetupManager from '@/components/UsernameSetupManager';
import { v4 as uuidv4 } from 'uuid';
import {
  Header,
  NavigationSidebar,
  MainWorkspace,
  DashboardChatSession,
  AIChatSession
} from '@/components/dashboard';

const DashboardLayout: React.FC = () => {
  const { user, session } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [openSubmenus, setOpenSubmenus] = useState<{ [key: string]: boolean }>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [createProjectDialogOpen, setCreateProjectDialogOpen] = useState(false);
  const [activeCenterPanel, setActiveCenterPanel] = useState('');
  const [activeFeedItemId, setActiveFeedItemId] = useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();



  // Load projects for the current user
  useEffect(() => {
    if (user?.id && session) {
      loadUserProjects();
    }
  }, [user?.id, session]);

  const loadUserProjects = async () => {
    if (!user?.id || !session) return;
    
    try {
      const userProjects = await getProjectsForUser(user.id);
      setProjects(userProjects);
    } catch (error) {
      // Error loading user projects
    }
  };

  // Chat functionality temporarily disabled during framework migration

  // Convert DashboardChatSession to AIChatSession
  const convertToAIChatSession = (chat: DashboardChatSession): AIChatSession => ({
    id: chat.id,
    user_id: undefined,
    project_id: undefined,
    started_at: chat.createdAt,
    ended_at: undefined
  });

  // Convert AIChatSession to DashboardChatSession
  const convertToDashboardChatSession = (chat: AIChatSession): DashboardChatSession => ({
    id: chat.id,
    title: `Chat ${chat.id}`,
    createdAt: chat.started_at,
    lastMessageAt: chat.started_at,
    unreadCount: 0
  });

  // Convert array of DashboardChatSession to AIChatSession
  const convertChatsToAI = (dashboardChats: DashboardChatSession[]): AIChatSession[] => {
    return dashboardChats.map(convertToAIChatSession);
  };

  // Handle chat updates from AIAssistant
  const handleAIChatUpdate = (updatedAIChats: AIChatSession[]) => {
    const updatedDashboardChats = updatedAIChats.map(convertToDashboardChatSession);
    // setChats(updatedDashboardChats); // REMOVED: Now project-specific
  };

  // Chat functionality temporarily disabled during framework migration

  const createNewProject = () => {
    setCreateProjectDialogOpen(true);
  };

  const selectProject = (projectId: string) => {
    setActiveProjectId(projectId);
    setActiveCenterPanel('');
    // Navigate to the project page
    navigate(`/project/${projectId}`);
  };

  const handleProjectCreated = (newProject: Project) => {
    setProjects(prev => [newProject, ...prev]);
    setActiveProjectId(newProject.id);
    // Navigate to the new project
    navigate(`/project/${newProject.id}`);
  };

  const toggleSubmenu = (label: string) => {
    setOpenSubmenus(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleNavItemClick = (item: { icon: React.ComponentType; label: string; active: boolean; subItems?: string[] }) => {
    if (item.label === 'Dashboard') {
      navigate('/dashboard');
      setActiveCenterPanel('');
      setActiveProjectId(null);
      setActiveFeedItemId(null);
      return;
    }
    if (item.label === 'Data') {
      navigate('/data');
      setActiveCenterPanel('');
      setActiveProjectId(null);
      setActiveFeedItemId(null);
      return;
    }
    if (item.label === 'Meetings') {
      navigate('/meetings');
      setActiveCenterPanel('');
      setActiveProjectId(null);
      setActiveFeedItemId(null);
      return;
    }
    if (item.subItems) {
      if (isSidebarCollapsed) {
        toggleSubmenu(item.label);
      } else {
        toggleSubmenu(item.label);
      }
    }
  };

  // const toggleChatSidebar = () => { // REMOVED: Now project-specific
  //   setIsChatSidebarCollapsed(!isChatSidebarCollapsed);
  // };

  // const selectChat = (chatId: string) => { // REMOVED: Now project-specific
  //   setActiveChatId(chatId);
  // };

  const renameProject = async (projectId: string, newName: string, newDescription: string) => {
    try {
      // For now, just update locally since we're not implementing full CRUD yet
      setProjects(prev => prev.map(project => 
        project.id === projectId 
          ? { ...project, name: newName, description: newDescription }
          : project
      ));
    } catch (error) {
      // Error renaming project
    }
  };

  const deleteProject = async (projectId: string) => {
    try {
      // For now, just update locally since we're not implementing full CRUD yet
      setProjects(prev => {
        const filtered = prev.filter(project => project.id !== projectId);
        return filtered;
      });
      
      if (activeProjectId === projectId) {
        setActiveProjectId(null);
        navigate('/dashboard');
      }
    } catch (error) {
      // Handle error silently
    }
  };

  // Determine active navigation item based on current route
  const getActiveNavItem = () => {
    const pathname = location.pathname;
    const searchParams = new URLSearchParams(location.search);
    
    if (pathname === '/dashboard') {
      if (searchParams.get('panel') === 'data') {
        return 'Data';
      }
      return 'Home';
    }
    if (pathname === '/data') {
      return 'Data';
    }
    if (pathname === '/meetings') {
      return 'Meetings';
    }
    if (pathname.startsWith('/project/')) {
      return 'Projects';
    }
    if (pathname === '/integrations') {
      return 'Settings';
    }
    return 'Home';
  };

  // Check if we're on a project page
  const isProjectPage = location.pathname.startsWith('/project/');
  const projectId = isProjectPage ? location.pathname.split('/')[2] : null;
  


  return (
    <div className="flex flex-col h-screen bg-stone-50 dark:bg-zinc-900">
      {/* Header at the very top, full width */}
      <Header />
      {/* Sidebar and main content below header */}
      <div className="flex flex-1 min-h-0">
        <NavigationSidebar
          isCollapsed={isSidebarCollapsed}
          onToggle={toggleSidebar}
          openSubmenus={openSubmenus}
          onToggleSubmenu={toggleSubmenu}
          onNavItemClick={handleNavItemClick}
          // onNewChat={createNewChat} // REMOVED: Now project-specific
          onNewProject={createNewProject}
          // chats={chats} // REMOVED: Now project-specific
          projects={projects}
          // activeChatId={activeChatId} // REMOVED: Now project-specific
          activeProjectId={activeProjectId}
          // onChatSelect={selectChat} // REMOVED: Now project-specific
          onProjectSelect={selectProject}
          // onRenameChat={renameChat} // REMOVED: Now project-specific
          // onDeleteChat={deleteChat} // REMOVED: Now project-specific
          onRenameProject={renameProject}
          onDeleteProject={deleteProject}
          activeNavItem={getActiveNavItem()}
        />
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <div className="flex-1 flex overflow-hidden min-w-0">
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">
              <div className={`h-full flex flex-col ${isProjectPage ? 'w-full' : 'w-[70%] max-w-[90rem] mx-auto'}`}>
                {/* Outlet for nested routes */}
                <Outlet />
              </div>
            </div>
            {/* AIAssistant - REMOVED: Now project-specific */}
            {/* <AIAssistant
              // isCollapsed={isChatSidebarCollapsed} // REMOVED: Now project-specific
              // onToggle={toggleChatSidebar} // REMOVED: Now project-specific
              chats={convertChatsToAI(projects.map(p => ({ // REMOVED: Now project-specific
                id: p.id,
                title: p.name || `Chat ${p.id}`,
                createdAt: p.created_at,
                lastMessageAt: p.updated_at,
                unreadCount: 0
              })))}
              activeChatId={activeProjectId}
              onChatUpdate={handleAIChatUpdate}
              currentUserId={user?.id}
              currentProjectId={activeProjectId}
            /> */}
            

          </div>
        </div>
      </div>
      {/* Username Setup Manager */}
      <UsernameSetupManager />
      
      <CreateProjectDialog
        open={createProjectDialogOpen}
        onOpenChange={setCreateProjectDialogOpen}
        onProjectCreated={handleProjectCreated}
        currentUserId={user?.id || ''}
      />
    </div>
  );
};

export default DashboardLayout; 