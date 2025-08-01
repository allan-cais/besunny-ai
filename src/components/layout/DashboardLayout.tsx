import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { useSupabase } from '@/hooks/use-supabase';
import { ChatSession, supabaseService } from '@/lib/supabase';
import CreateProjectDialog from '@/components/CreateProjectDialog';
import AIAssistant from '@/components/AIAssistant';
import ProjectChat from '@/components/ProjectChat';
import { v4 as uuidv4 } from 'uuid';
import {
  Header,
  NavigationSidebar,
  MainWorkspace,
  DashboardChatSession,
  AIChatSession
} from '@/components/dashboard';

const DashboardLayout = () => {
  const { user } = useAuth();
  const { getProjectsForUser, getChatSessions, createChatSession, endChatSession, updateChatSession } = useSupabase();
  const [openSubmenus, setOpenSubmenus] = useState<{ [key: string]: boolean }>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  // const [isChatSidebarCollapsed, setIsChatSidebarCollapsed] = useState(true); // REMOVED: Now project-specific
  // const [chats, setChats] = useState<DashboardChatSession[]>([]); // REMOVED: Now project-specific
  const [projects, setProjects] = useState<any[]>([]);
  // const [activeChatId, setActiveChatId] = useState<string | null>(null); // REMOVED: Now project-specific
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [createProjectDialogOpen, setCreateProjectDialogOpen] = useState(false);
  const [activeCenterPanel, setActiveCenterPanel] = useState('');
  const [activeFeedItemId, setActiveFeedItemId] = useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  // Load projects for the current user
  useEffect(() => {
    if (user?.id) {
      loadUserProjects();
    }
  }, [user?.id]);

  const loadUserProjects = async () => {
    if (!user?.id) return;
    
    try {
      const userProjects = await getProjectsForUser(user.id);
      setProjects(userProjects);
    } catch (error) {
      console.error('Error loading user projects:', error);
    }
  };

  // Fetch chat sessions from Supabase on load
  useEffect(() => {
    if (user?.id) {
      loadUserChats();
    }
  }, [user?.id]);

  const loadUserChats = async () => {
    if (!user?.id) return;
    try {
      const sessions: ChatSession[] = await getChatSessions(user.id);
      // Only include active chats (ended_at is null)
      const activeSessions = sessions.filter(session => !session.ended_at);
      const dashboardChats: DashboardChatSession[] = activeSessions.map(session => ({
        id: session.id,
        title: session.name || (session.id.startsWith('chat_') ? `Chat ${session.id.split('_')[1]}` : session.id),
        createdAt: session.started_at,
        lastMessageAt: session.started_at,
        unreadCount: 0
      }));
      // setChats(dashboardChats); // REMOVED: Now project-specific
      if (dashboardChats.length > 0 && !activeProjectId) { // REMOVED: Now project-specific
        setActiveProjectId(dashboardChats[0].id);
      }
    } catch (error) {
      console.error('Error loading chat sessions:', error);
    }
  };

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

  // Create new chat session in Supabase
  const createNewChat = async () => {
    if (!user?.id) {
      return;
    }
    
    if (!supabaseService?.isConfigured?.()) {
      return;
    }
    
    const newId = uuidv4();
    const session: Omit<ChatSession, 'started_at'> = {
      id: newId,
      user_id: user.id,
      project_id: activeProjectId || undefined,
      name: 'New Chat'
    };
    try {
      const newSession = await createChatSession(session);
      const newChat: DashboardChatSession = {
        id: newSession.id,
        title: newSession.name || `Chat ${projects.length + 1}`, // REMOVED: Now project-specific
        createdAt: newSession.started_at,
        lastMessageAt: newSession.started_at,
        unreadCount: 0
      };
      // setChats(prev => [newChat, ...prev]); // REMOVED: Now project-specific
      setActiveProjectId(newChat.id);
    } catch (error) {
      console.error('Error creating chat session:', error);
    }
  };

  // Rename chat session in Supabase
  const renameChat = async (chatId: string, newTitle: string) => {
    try {
      await updateChatSession(chatId, { name: newTitle });
      // setChats(prev => prev.map(chat => chat.id === chatId ? { ...chat, title: newTitle } : chat)); // REMOVED: Now project-specific
    } catch (error) {
      console.error('Error renaming chat session:', error);
    }
  };

  // Delete chat session and its messages in Supabase
  const deleteChat = async (chatId: string) => {
    try {
      await endChatSession(chatId);
      // setChats(prev => prev.filter(chat => chat.id !== chatId)); // REMOVED: Now project-specific
      if (activeProjectId === chatId) {
        setActiveProjectId(projects.length > 1 ? projects[0].id : null);
      }
    } catch (error) {
      console.error('Error deleting chat session:', error);
    }
  };

  const createNewProject = () => {
    setCreateProjectDialogOpen(true);
  };

  const selectProject = (projectId: string) => {
    setActiveProjectId(projectId);
    setActiveCenterPanel('');
    // Navigate to the project page
    navigate(`/project/${projectId}`);
  };

  const handleProjectCreated = (newProject: any) => {
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
      await supabaseService.updateProject(projectId, { name: newName, description: newDescription });
      setProjects(prev => prev.map(project => 
        project.id === projectId 
          ? { ...project, name: newName, description: newDescription }
          : project
      ));
    } catch (error) {
      console.error('Error renaming project:', error);
    }
  };

  const deleteProject = async (projectId: string) => {
    try {
      await supabaseService.deleteProject(projectId);
      
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
              <div className="w-[70%] max-w-[90rem] mx-auto h-full flex flex-col">
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
            
            {/* Project Chat - Show only on project pages */}
            {isProjectPage && projectId && (
              <ProjectChat 
                projectId={projectId}
                userId={user?.id || ''}
                projectName={projects.find(p => p.id === projectId)?.name}
              />
            )}
          </div>
        </div>
      </div>
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