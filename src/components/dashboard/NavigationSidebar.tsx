import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
} from 'lucide-react';
import { NavigationSidebarProps, DashboardChatSession } from './types';
import { Project } from '@/lib/supabase';

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
  onDeleteChat,
  onRenameProject,
  onDeleteProject
}: NavigationSidebarProps) => {
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedChat, setSelectedChat] = useState<DashboardChatSession | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [renameProjectDialogOpen, setRenameProjectDialogOpen] = useState(false);
  const [deleteProjectDialogOpen, setDeleteProjectDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const navItems = [
    { icon: Home, label: "Home", active: true },
    { 
      icon: FileText, 
      label: "Projects", 
      active: false,
      subItems: projects.map(p => p.name)
    },
    { icon: Database, label: "Data", active: false },
    { icon: Terminal, label: "Playbooks", active: false },
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

  const handleProjectRenameClick = (project: Project) => {
    setSelectedProject(project);
    setNewProjectName(project.name);
    setRenameProjectDialogOpen(true);
  };

  const handleProjectDeleteClick = (project: Project) => {
    setSelectedProject(project);
    setDeleteConfirmText("");
    setDeleteProjectDialogOpen(true);
  };

  const handleProjectRenameConfirm = () => {
    if (selectedProject && newProjectName.trim()) {
      onRenameProject(selectedProject.id, newProjectName.trim(), selectedProject.description || '');
      setRenameProjectDialogOpen(false);
      setSelectedProject(null);
      setNewProjectName("");
    }
  };

  const handleProjectDeleteConfirm = () => {
    if (selectedProject) {
      onDeleteProject(selectedProject.id);
      setDeleteProjectDialogOpen(false);
      setSelectedProject(null);
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
                <div className="pl-4 mt-1 space-y-1">
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
                    <div
                      key={project.id}
                      className={`group flex items-center w-full rounded-md transition-colors border border-transparent
                        ${activeProjectId === project.id
                          ? 'bg-stone-300 text-[#4a5565] border border-[#4a5565] dark:bg-zinc-700 dark:text-zinc-50'
                          : 'hover:bg-stone-300 dark:hover:bg-zinc-700 hover:border-[#4a5565] dark:hover:border-zinc-700'}
                      `}
                    >
                      <Button
                        variant="ghost"
                        className={`flex-1 justify-start font-mono text-left px-3 py-2 h-auto text-xs bg-transparent shadow-none hover:bg-transparent focus:bg-transparent border-none`}
                        onClick={() => onProjectSelect(project.id)}
                      >
                        {project.name}
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 p-0 m-0 bg-transparent shadow-none border-none opacity-70 group-hover:opacity-100 group-active:opacity-100 transition-opacity hover:bg-transparent focus:bg-transparent"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs p-1">
                          <DropdownMenuItem onClick={() => handleProjectRenameClick(project)} className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 cursor-pointer font-mono text-xs text-[#222] dark:text-zinc-100">
                            <Edit className="mr-2 h-4 w-4" />
                            <span className="font-bold">Edit Project</span>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleProjectDeleteClick(project)} className="flex items-center gap-2 px-3 py-2 rounded-md text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 focus:bg-red-100 dark:focus:bg-red-900 cursor-pointer font-mono text-xs">
                            <Trash2 className="mr-2 h-4 w-4" />
                            <span>Delete project</span>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
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
            <div className="pl-4 space-y-1">
              {/* New Chat Button - First item under Chats */}
              <div
                className="w-full flex items-center font-mono text-left px-3 h-9 text-xs cursor-pointer border border-transparent hover:bg-stone-300 dark:hover:bg-zinc-700 hover:border-[#4a5565] dark:hover:border-zinc-700 rounded-md transition-colors mb-2"
                onClick={onNewChat}
              >
                <Plus className="w-4 h-4 mr-3" />
                <span className="truncate">New Chat</span>
              </div>
              
              {/* Existing Chats */}
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group flex items-center w-full max-w-full rounded-md transition-colors border px-3 h-9 text-xs font-mono text-left mb-2 cursor-pointer ${activeChatId === chat.id ? 'bg-stone-300 dark:bg-zinc-700 border-[#4a5565] dark:border-zinc-700 text-[#4a5565] dark:text-zinc-50' : 'border-[#4a5565] dark:border-zinc-700 hover:bg-stone-300 dark:hover:bg-zinc-700 hover:border-[#4a5565] dark:hover:border-zinc-700'}`}
                  onClick={() => onChatSelect(chat.id)}
                >
                  <MessageSquare className="w-4 h-4 mr-3 flex-shrink-0" />
                  <span className="truncate text-xs font-mono flex-1" style={{ minWidth: 0 }}>{chat.title}</span>
                  {!isCollapsed && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 p-0 m-0 bg-transparent shadow-none border-none opacity-70 group-hover:opacity-100 group-active:opacity-100 transition-opacity hover:bg-transparent focus:bg-transparent flex items-center justify-center max-w-none ml-2"
                        >
                          <MoreHorizontal className="h-4 w-4" />
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

      {/* Edit Project Dialog */}
      <Dialog open={renameProjectDialogOpen} onOpenChange={setRenameProjectDialogOpen}>
        <DialogContent className="sm:max-w-[480px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
          <DialogHeader>
            <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
              EDIT PROJECT
            </DialogTitle>
            <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
              Update your project details below and click Save to apply changes.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="project-name" className="text-[#4a5565] dark:text-zinc-300 font-mono text-xs font-bold">
                PROJECT NAME
              </Label>
              <Input
                id="project-name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Enter project name..."
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="project-description" className="text-[#4a5565] dark:text-zinc-300 font-mono text-xs font-bold">
                DESCRIPTION
              </Label>
              <Input
                id="project-description"
                value={selectedProject?.description || ''}
                onChange={(e) => {
                  if (selectedProject) setSelectedProject({ ...selectedProject, description: e.target.value });
                }}
                placeholder="Enter project description..."
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button 
              variant="outline" 
              onClick={() => setRenameProjectDialogOpen(false)}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              CANCEL
            </Button>
            <Button 
              onClick={() => {
                if (selectedProject && newProjectName.trim()) {
                  onRenameProject(selectedProject.id, newProjectName.trim(), selectedProject.description || '');
                  setRenameProjectDialogOpen(false);
                  setSelectedProject(null);
                  setNewProjectName("");
                }
              }}
              disabled={!newProjectName.trim()}
              className="font-mono text-xs bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 hover:bg-[#3a4555] dark:hover:bg-zinc-200 disabled:opacity-50"
            >
              SAVE
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Project Dialog */}
      <Dialog open={deleteProjectDialogOpen} onOpenChange={setDeleteProjectDialogOpen}>
        <DialogContent className="sm:max-w-[480px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
          <DialogHeader>
            <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
              DELETE PROJECT
            </DialogTitle>
            <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
              <span className="font-bold text-red-600">Warning:</span> This operation will <span className="font-bold">permanently and irreversibly</span> delete this project and all associated data from the system. This action is <span className="font-bold">not reversible</span> and cannot be undone. Please type the project name (<span className="font-mono font-bold">{selectedProject?.name}</span>) below to confirm deletion.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <Input
              id="delete-confirm"
              value={deleteConfirmText}
              onChange={e => setDeleteConfirmText(e.target.value)}
              placeholder={`Type "${selectedProject?.name}" to confirm`}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600"
            />
          </div>
          <DialogFooter className="gap-2">
            <Button 
              variant="outline" 
              onClick={() => setDeleteProjectDialogOpen(false)}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              CANCEL
            </Button>
            <Button 
              onClick={() => {
                if (selectedProject && deleteConfirmText === selectedProject.name) {
                  onDeleteProject(selectedProject.id);
                  setDeleteProjectDialogOpen(false);
                  setSelectedProject(null);
                }
              }}
              disabled={!selectedProject || deleteConfirmText !== selectedProject?.name}
              className="font-mono text-xs bg-red-600 dark:bg-red-400 text-stone-100 dark:text-zinc-900 hover:bg-red-700 dark:hover:bg-red-500 disabled:opacity-50"
            >
              DELETE
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default NavigationSidebar; 