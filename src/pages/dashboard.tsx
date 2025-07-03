import React, { useState, useEffect } from 'react';
import { useAuth } from '@/providers/AuthProvider';
import { useSupabase } from '@/hooks/use-supabase';
import { ChatSession, supabaseService } from '@/lib/supabase';
import CreateProjectDialog from '@/components/CreateProjectDialog';
import AIAssistant from '@/components/AIAssistant';
import { v4 as uuidv4 } from 'uuid';
import { useNavigate } from 'react-router-dom';
import {
  Header,
  NavigationSidebar,
  MainWorkspace,
  DashboardChatSession,
  AIChatSession
} from '@/components/dashboard';

const Dashboard = () => {
  const { user } = useAuth();
  const { getProjectsForUser, getChatSessions, createChatSession, endChatSession, updateChatSession } = useSupabase();
  const [openSubmenus, setOpenSubmenus] = useState<{ [key: string]: boolean }>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isChatSidebarCollapsed, setIsChatSidebarCollapsed] = useState(true);
  const [chats, setChats] = useState<DashboardChatSession[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [createProjectDialogOpen, setCreateProjectDialogOpen] = useState(false);
  const [activeCenterPanel, setActiveCenterPanel] = useState('');
  const [activeFeedItemId, setActiveFeedItemId] = useState<string | null>(null);
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
      setChats(dashboardChats);
      if (dashboardChats.length > 0 && !activeChatId) {
        setActiveChatId(dashboardChats[0].id);
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
    setChats(updatedDashboardChats);
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
        title: newSession.name || `Chat ${chats.length + 1}`,
        createdAt: newSession.started_at,
        lastMessageAt: newSession.started_at,
        unreadCount: 0
      };
      setChats(prev => [newChat, ...prev]);
      setActiveChatId(newChat.id);
    } catch (error) {
      console.error('Error creating chat session:', error);
    }
  };

  // Rename chat session in Supabase
  const renameChat = async (chatId: string, newTitle: string) => {
    try {
      await updateChatSession(chatId, { name: newTitle });
      setChats(prev => prev.map(chat => chat.id === chatId ? { ...chat, title: newTitle } : chat));
    } catch (error) {
      console.error('Error renaming chat session:', error);
    }
  };

  // Delete chat session and its messages in Supabase
  const deleteChat = async (chatId: string) => {
    try {
      await endChatSession(chatId);
      setChats(prev => prev.filter(chat => chat.id !== chatId));
      if (activeChatId === chatId) {
        setActiveChatId(chats.length > 1 ? chats[0].id : null);
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
  };

  const handleProjectCreated = (newProject: any) => {
    setProjects(prev => [newProject, ...prev]);
    setActiveProjectId(newProject.id);
  };

  const toggleSubmenu = (label: string) => {
    setOpenSubmenus(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleNavItemClick = (item: { icon: React.ComponentType; label: string; active: boolean; subItems?: string[] }) => {
    if (item.label === 'Data') {
      setActiveCenterPanel('data');
      setActiveProjectId(null);
      setActiveFeedItemId(null);
      return;
    }
    if (item.subItems) {
      if (isSidebarCollapsed) {
        setIsSidebarCollapsed(false);
        setOpenSubmenus(prev => ({ ...prev, [item.label]: true }));
      } else {
        toggleSubmenu(item.label);
      }
    }
  };

  const toggleChatSidebar = () => {
    if (isChatSidebarCollapsed && chats.length === 0) {
      createNewChat();
      setIsChatSidebarCollapsed(false);
    } else if (isChatSidebarCollapsed) {
      setIsChatSidebarCollapsed(false);
    } else {
      setIsChatSidebarCollapsed(true);
    }
  };

  const selectChat = (chatId: string) => {
    setActiveChatId(chatId);
    setIsChatSidebarCollapsed(false);
    
    setChats(prev => 
      prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, unreadCount: 0 }
          : chat
      )
    );
  };

  // Add handlers for project edit and delete
  const renameProject = async (projectId: string, newName: string, newDescription: string) => {
    try {
      const updated = await supabaseService.updateProject(projectId, { name: newName, description: newDescription });
      setProjects(prev => prev.map(p => p.id === projectId ? { ...p, name: updated.name, description: updated.description } : p));
    } catch (error) {
      console.error('Error updating project:', error);
    }
  };

  const deleteProject = async (projectId: string) => {
    try {
      await supabaseService.deleteProject(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
      if (activeProjectId === projectId) {
        setActiveProjectId(projects.length > 1 ? projects[0].id : null);
      }
    } catch (error) {
      console.error('Error deleting project:', error);
    }
  };

  return (
    <div className="h-screen bg-stone-100 text-[#4a5565] dark:bg-zinc-800 dark:text-zinc-50 font-mono flex flex-col text-xs">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <NavigationSidebar 
          isCollapsed={isSidebarCollapsed}
          onToggle={toggleSidebar}
          openSubmenus={openSubmenus}
          onToggleSubmenu={toggleSubmenu}
          onNavItemClick={handleNavItemClick}
          onNewChat={createNewChat}
          onNewProject={createNewProject}
          chats={chats}
          projects={projects}
          activeChatId={activeChatId}
          activeProjectId={activeProjectId}
          onChatSelect={selectChat}
          onProjectSelect={selectProject}
          onRenameChat={renameChat}
          onDeleteChat={deleteChat}
          onRenameProject={renameProject}
          onDeleteProject={deleteProject}
        />

        <MainWorkspace 
          activeProjectId={activeProjectId} 
          activeCenterPanel={activeCenterPanel} 
          setActiveCenterPanel={setActiveCenterPanel} 
          activeFeedItemId={activeFeedItemId} 
          setActiveFeedItemId={setActiveFeedItemId} 
        />

        <AIAssistant 
          isCollapsed={isChatSidebarCollapsed}
          onToggle={toggleChatSidebar}
          activeChatId={activeChatId}
          chats={convertChatsToAI(chats)}
          onChatUpdate={handleAIChatUpdate}
          currentUserId={user?.id}
          currentProjectId={activeProjectId}
        />
      </div>

      {/* Create Project Dialog */}
      <CreateProjectDialog
        open={createProjectDialogOpen}
        onOpenChange={setCreateProjectDialogOpen}
        onProjectCreated={handleProjectCreated}
        currentUserId={user?.id || ''}
      />
    </div>
  );
};

export default Dashboard; 