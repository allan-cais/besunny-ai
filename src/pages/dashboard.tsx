import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Home, 
  FileText, 
  Database, 
  Terminal, 
  Settings, 
  ChevronDown, 
  ChevronRight, 
  ChevronLeft,
  ChevronRightIcon,
  MessageSquare,
  Plus,
  MoreHorizontal,
  Edit,
  Trash2,
  User,
  LogOut,
  Search
} from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { useSupabase } from '@/hooks/use-supabase';
import { Project, ChatSession } from '@/lib/supabase';
import CreateProjectDialog from '@/components/CreateProjectDialog';
import AIAssistant from '@/components/AIAssistant';
import { useTheme } from "@/providers/ThemeProvider";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Sun, Moon, Monitor } from "lucide-react";
import UserAccountMenu from "@/components/auth/UserAccountMenu";

// Header Component
const Header = () => {
  const { theme, setTheme } = useTheme();

  return (
    <header className="relative h-[61px] border-b border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 px-4 flex items-center justify-between flex-shrink-0">
      <h2 className="text-base font-bold">sunny.ai</h2>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md px-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder="Search..."
            className="w-full bg-white dark:bg-zinc-700 border-[#4a5565] dark:border-zinc-700 pl-10 h-8 text-xs"
          />
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <UserAccountMenu />

        <ToggleGroup 
          type="single" 
          value={theme}
          onValueChange={(value) => {
            if (value) setTheme(value);
          }}
          className="border border-[#4a5565] dark:border-zinc-700 rounded-md p-0.5"
        >
          <ToggleGroupItem value="light" className="p-1 h-auto data-[state=on]:bg-stone-300 dark:data-[state=on]:bg-zinc-600">
            <Sun className="w-4 h-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="dark" className="p-1 h-auto data-[state=on]:bg-stone-300 dark:data-[state=on]:bg-zinc-600">
            <Moon className="w-4 h-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="system" className="p-1 h-auto data-[state=on]:bg-stone-300 dark:data-[state=on]:bg-zinc-600">
            <Monitor className="w-4 h-4" />
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
    </header>
  );
};

// Navigation Sidebar Component
interface NavigationSidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  openSubmenus: { [key: string]: boolean };
  onToggleSubmenu: (label: string) => void;
  onNavItemClick: (item: { icon: React.ComponentType; label: string; active: boolean; subItems?: string[] }) => void;
  onNewChat: () => void;
  onNewProject: () => void;
  chats: DashboardChatSession[];
  projects: Project[];
  activeChatId: string | null;
  activeProjectId: string | null;
  onChatSelect: (chatId: string) => void;
  onProjectSelect: (projectId: string) => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
  onDeleteChat: (chatId: string) => void;
}

interface DashboardChatSession {
  id: string;
  title: string;
  createdAt: string;
  lastMessageAt: string;
  unreadCount: number;
}

// Interface for AIAssistant component
interface AIChatSession {
  id: string;
  user_id?: string;
  project_id?: string;
  started_at: string;
  ended_at?: string;
}

const NavigationSidebar = ({ 
  isCollapsed, 
  onToggle, 
  openSubmenus, 
  onToggleSubmenu, 
  onNavItemClick,
  onNewChat,
  onNewProject,
  chats,
  projects,
  activeChatId,
  activeProjectId,
  onChatSelect,
  onProjectSelect,
  onRenameChat,
  onDeleteChat
}: NavigationSidebarProps) => {
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedChat, setSelectedChat] = useState<DashboardChatSession | null>(null);
  const [newTitle, setNewTitle] = useState("");

  const navItems = [
    { icon: Home, label: "Home", active: true },
    { 
      icon: FileText, 
      label: "Projects", 
      active: false,
      subItems: projects.map(p => p.name)
    },
    { icon: Database, label: "Data", active: false },
    { icon: Terminal, label: "Terminal", active: false },
    { icon: Settings, label: "Settings", active: false },
  ];

  const handleRenameClick = (chat: DashboardChatSession) => {
    setSelectedChat(chat);
    setNewTitle(chat.title);
    setRenameDialogOpen(true);
  };

  const handleDeleteClick = (chat: DashboardChatSession) => {
    setSelectedChat(chat);
    setDeleteDialogOpen(true);
  };

  const handleRenameConfirm = () => {
    if (selectedChat && newTitle.trim()) {
      onRenameChat(selectedChat.id, newTitle.trim());
      setRenameDialogOpen(false);
      setSelectedChat(null);
      setNewTitle("");
    }
  };

  const handleDeleteConfirm = () => {
    if (selectedChat) {
      onDeleteChat(selectedChat.id);
      setDeleteDialogOpen(false);
      setSelectedChat(null);
    }
  };

  return (
    <>
      <div className={`relative transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-16' : 'w-64'
      } border-r border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800`}>
        <div className="p-2">
          {/* Regular Navigation Items */}
          {navItems.map((item, index) => (
            <div key={index} className="mb-1">
              <Button
                variant="ghost"
                className={`w-full flex items-center justify-between font-mono text-left px-3 py-2 h-auto text-xs
                  ${item.active
                    ? 'bg-stone-300 text-[#4a5565] border border-transparent hover:border-[#4a5565] hover:!bg-stone-300'
                    : 'hover:bg-stone-300 dark:hover:bg-zinc-700 border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700'}
                `}
                onClick={() => onNavItemClick(item)}
              >
                <div className="flex items-center">
                  <item.icon className="w-4 h-4 mr-3" />
                  {!isCollapsed && item.label}
                </div>
                {!isCollapsed && item.subItems && (
                  openSubmenus[item.label] 
                    ? <ChevronDown className="w-4 h-4" /> 
                    : <ChevronRight className="w-4 h-4" />
                )}
              </Button>
              {!isCollapsed && item.subItems && openSubmenus[item.label] && (
                <div className="pl-8 mt-1 space-y-1">
                  {/* New Project Button - First item under Projects */}
                  <div
                    className="w-full flex items-center justify-start font-mono text-left px-3 py-2 h-auto text-xs cursor-pointer hover:bg-stone-300 dark:hover:bg-zinc-700 border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700 rounded-md transition-colors"
                    onClick={onNewProject}
                  >
                    <Plus className="w-4 h-4 mr-3" />
                    New Project
                  </div>
                  
                  {/* Existing Projects */}
                  {projects.map((project) => (
                    <Button
                      key={project.id}
                      variant="ghost"
                      className={`w-full justify-start font-mono text-left px-3 py-1 h-auto text-xs ${
                        activeProjectId === project.id
                          ? 'bg-stone-300 dark:bg-zinc-700'
                          : 'hover:bg-stone-300 dark:hover:bg-zinc-700'
                      }`}
                      onClick={() => onProjectSelect(project.id)}
                    >
                      {project.name}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Chats Section */}
          <div className="mt-6">
            <div className="px-3 py-2 text-xs font-mono text-gray-600 dark:text-gray-400">
              Chats
            </div>
            <div className="space-y-1">
              {/* New Chat Button - First item under Chats */}
              <div
                className="w-full flex items-center justify-start font-mono text-left px-3 py-2 h-auto text-xs cursor-pointer hover:bg-stone-300 dark:hover:bg-zinc-700 border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700 rounded-md transition-colors"
                onClick={onNewChat}
              >
                <Plus className="w-4 h-4 mr-3" />
                {!isCollapsed && "New Chat"}
              </div>
              
              {/* Existing Chats */}
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group relative flex items-center justify-between font-mono text-left px-3 py-2 h-auto text-xs ${
                    activeChatId === chat.id
                      ? 'bg-stone-300 dark:bg-zinc-700'
                      : 'hover:bg-stone-300 dark:hover:bg-zinc-700'
                  } border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700 rounded-md`}
                >
                  <Button
                    variant="ghost"
                    className={`w-full flex items-center justify-start h-auto p-0 font-mono text-xs bg-transparent ${
                      activeChatId === chat.id
                        ? 'hover:bg-transparent'
                        : 'hover:bg-transparent'
                    }`}
                    onClick={() => onChatSelect(chat.id)}
                  >
                    <MessageSquare className="w-4 h-4 mr-3 flex-shrink-0" />
                    <span className="truncate">{chat.title}</span>
                  </Button>
                  
                  <div className="flex items-center">
                    {chat.unreadCount > 0 && (
                      <div className="mr-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0">
                        {chat.unreadCount}
                      </div>
                    )}
                    
                    {/* Three-dot menu - only visible on hover */}
                    {!isCollapsed && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-stone-400 dark:hover:bg-zinc-600"
                          >
                            <MoreHorizontal className="h-3 w-3" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs p-1">
                          <DropdownMenuItem 
                            onClick={() => handleRenameClick(chat)}
                            className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 cursor-pointer font-mono text-xs text-[#222] dark:text-zinc-100"
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            <span className="font-bold">Rename chat</span>
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteClick(chat)}
                            className="flex items-center gap-2 px-3 py-2 rounded-md text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 focus:bg-red-100 dark:focus:bg-red-900 cursor-pointer font-mono text-xs"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            <span>Delete chat</span>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Sidebar Toggle Button */}
        <button
          onClick={onToggle}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-10"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRightIcon className="w-3 h-3" />
          ) : (
            <ChevronLeft className="w-3 h-3" />
          )}
        </button>
      </div>

      {/* Rename Chat Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent className="sm:max-w-[425px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
          <DialogHeader>
            <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
              RENAME CHAT
            </DialogTitle>
            <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
              Enter a new name for your chat.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name" className="text-[#4a5565] dark:text-zinc-300 font-mono text-xs font-bold">
                CHAT NAME
              </Label>
              <Input
                id="name"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Enter chat name..."
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleRenameConfirm();
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button 
              variant="outline" 
              onClick={() => setRenameDialogOpen(false)}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              CANCEL
            </Button>
            <Button 
              onClick={handleRenameConfirm} 
              disabled={!newTitle.trim()}
              className="font-mono text-xs bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 hover:bg-[#3a4555] dark:hover:bg-zinc-200 disabled:opacity-50"
            >
              RENAME
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Chat Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[425px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
          <DialogHeader>
            <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
              DELETE CHAT
            </DialogTitle>
            <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
              Are you sure you want to delete "{selectedChat?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button 
              variant="outline" 
              onClick={() => setDeleteDialogOpen(false)}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              CANCEL
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteConfirm}
              className="font-mono text-xs bg-red-600 dark:bg-red-700 text-white hover:bg-red-700 dark:hover:bg-red-800"
            >
              DELETE
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

// Stats Grid Component
const StatsGrid = () => {
  const stats = [
    { value: "24", label: "ACTIVE PROJECTS" },
    { value: "156", label: "FILES PROCESSED" },
    { value: "98%", label: "UPTIME" }
  ];

  return (
    <div className="grid grid-cols-3 gap-4 mt-12">
      {stats.map((stat, index) => (
        <div key={index} className="border border-[#4a5565] dark:border-zinc-700 p-6">
          <div className="text-lg font-bold">{stat.value}</div>
          <div className="text-xs text-gray-600 dark:text-gray-400">{stat.label}</div>
        </div>
      ))}
    </div>
  );
};

// Quick Actions Component
const QuickActions = () => {
  const actions = [
    { label: "[ NEW PROJECT ]" },
    { label: "[ OPEN TERMINAL ]" }
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-base font-bold">QUICK ACTIONS</h3>
      <div className="grid grid-cols-2 gap-4">
        {actions.map((action, index) => (
          <Button 
            key={index}
            variant="outline" 
            className="border border-[#4a5565] hover:bg-[#4a5565] hover:text-stone-100 dark:border-zinc-700 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors p-4 h-auto font-mono text-xs"
          >
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
};

// Main Workspace Component
const MainWorkspace = () => {
  return (
    <div className="flex-1 flex flex-col overflow-y-auto">
      {/* Workspace Header */}
      <div className="p-4 flex items-center">
        <div>
          <span className="text-xs font-medium">WORKSPACE</span>
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            ~/sunny.ai/dashboard
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 p-8 pt-4">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold">Welcome to Workspace</h1>
            <div className="w-24 h-px bg-[#4a5565] dark:bg-zinc-700 mx-auto"></div>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Your intelligent development environment
            </p>
          </div>

          <StatsGrid />
          <QuickActions />
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const { getProjectsForUser, getChatSessions, createChatSession, endChatSession } = useSupabase();
  const [openSubmenus, setOpenSubmenus] = useState<{ [key: string]: boolean }>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isChatSidebarCollapsed, setIsChatSidebarCollapsed] = useState(true);
  const [chats, setChats] = useState<DashboardChatSession[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [createProjectDialogOpen, setCreateProjectDialogOpen] = useState(false);

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
      const dashboardChats: DashboardChatSession[] = sessions.map(session => ({
        id: session.id,
        title: session.id.startsWith('chat_') ? `Chat ${session.id.split('_')[1]}` : session.id,
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
    if (!user?.id) return;
    const newId = `chat_${Date.now()}`;
    const session: Omit<ChatSession, 'started_at'> = {
      id: newId,
      user_id: user.id,
      project_id: activeProjectId || undefined
    };
    try {
      const newSession = await createChatSession(session);
      const newChat: DashboardChatSession = {
        id: newSession.id,
        title: `Chat ${chats.length + 1}`,
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
    // Optionally, you can add a title field to chat_sessions in DB, but for now, just update local state
    setChats(prev => prev.map(chat => chat.id === chatId ? { ...chat, title: newTitle } : chat));
  };

  // Delete chat session and its messages in Supabase
  const deleteChat = async (chatId: string) => {
    try {
      // End the chat session (soft delete)
      await endChatSession(chatId);
      // Optionally, you can also delete all messages for this session
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
  };

  const handleProjectCreated = (newProject: Project) => {
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
    // If opening the chat sidebar and there are no chats, create a new chat
    if (isChatSidebarCollapsed && chats.length === 0) {
      const newChat: DashboardChatSession = {
        id: `chat_${Date.now()}`,
        title: `Chat 1`,
        createdAt: new Date().toISOString(),
        lastMessageAt: new Date().toISOString(),
        unreadCount: 0
      };
      setChats([newChat]);
      setActiveChatId(newChat.id);
      setIsChatSidebarCollapsed(false);
    } else {
      setIsChatSidebarCollapsed(!isChatSidebarCollapsed);
    }
  };

  const selectChat = (chatId: string) => {
    setActiveChatId(chatId);
    setIsChatSidebarCollapsed(false);
    
    // Mark chat as read
    setChats(prev => 
      prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, unreadCount: 0 }
          : chat
      )
    );
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
        />

        <MainWorkspace />

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