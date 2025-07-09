import React from 'react';
import { Project } from '@/lib/supabase';

export interface DashboardChatSession {
  id: string;
  title: string;
  createdAt: string;
  lastMessageAt: string;
  unreadCount: number;
}

export interface AIChatSession {
  id: string;
  user_id?: string;
  project_id?: string;
  started_at: string;
  ended_at?: string;
}

export interface NavigationSidebarProps {
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
  onRenameProject: (projectId: string, newName: string, newDescription: string) => void;
  onDeleteProject: (projectId: string) => void;
  activeNavItem: string;
}

export interface MainWorkspaceProps {
  activeProjectId: string | null;
  activeCenterPanel: string;
  setActiveCenterPanel: (panel: string) => void;
  activeFeedItemId: string | null;
  setActiveFeedItemId: (id: string | null) => void;
  projects: any[];
} 