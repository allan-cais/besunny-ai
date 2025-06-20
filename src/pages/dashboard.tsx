import { useState, useRef, useLayoutEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { 
  Home, 
  FileText, 
  Settings, 
  Database,
  Terminal,
  Send,
  ChevronRight,
  ChevronDown,
  Search,
  Github,
  Sun,
  Moon,
  Monitor,
  ChevronLeft,
  ChevronRight as ChevronRightIcon,
  MessageSquare
} from "lucide-react";
import { useTheme } from "@/providers/ThemeProvider";

const Dashboard = () => {
  const { theme, setTheme } = useTheme();
  const [chatMessage, setChatMessage] = useState("");
  const [messages, setMessages] = useState([
    { type: "assistant", content: "Hello! How can I help you today?" }
  ]);
  const [isChatVisible, setIsChatVisible] = useState(true);
  const [openSubmenus, setOpenSubmenus] = useState<{ [key: string]: boolean }>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isChatSidebarCollapsed, setIsChatSidebarCollapsed] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    if (textareaRef.current) {
      const event = new Event('input', { bubbles: true });
      textareaRef.current.dispatchEvent(event);
    }
  }, [isChatSidebarCollapsed]);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const navItems = [
    { icon: Home, label: "Home", active: true },
    { 
      icon: FileText, 
      label: "Projects", 
      active: false,
      subItems: ["Spinbrush", "Iberdrola", "Abridge"]
    },
    { icon: Database, label: "Data", active: false },
    { icon: Terminal, label: "Terminal", active: false },
    { icon: Settings, label: "Settings", active: false },
  ];

  const handleSendMessage = () => {
    if (chatMessage.trim()) {
      setMessages([...messages, { type: "user", content: chatMessage }]);
      setChatMessage("");
      setTimeout(() => {
        setMessages(prev => [...prev, { type: "assistant", content: "I understand. Let me help you with that." }]);
      }, 1000);
    }
  };

  const toggleSubmenu = (label: string) => {
    setOpenSubmenus(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleNavItemClick = (item: typeof navItems[0]) => {
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
    setIsChatSidebarCollapsed(!isChatSidebarCollapsed);
  };

  return (
    <div className="min-h-screen bg-stone-100 text-[#4a5565] dark:bg-zinc-800 dark:text-zinc-50 font-mono flex flex-col text-xs">
      {/* Full-width Header */}
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
          <Button
            size="icon"
            variant="ghost"
            className="border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700"
            onClick={() => window.open("https://github.com", "_blank")}
          >
            <Github className="w-4 h-4" />
          </Button>

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

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Navigation */}
        <div className={`relative transition-all duration-300 ease-in-out ${
          isSidebarCollapsed ? 'w-16' : 'w-64'
        } border-r border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800`}>
          <div className="p-2">
            {navItems.map((item, index) => (
              <div key={index} className="mb-1">
                <Button
                  variant="ghost"
                  className={`w-full flex items-center justify-between font-mono text-left px-3 py-2 h-auto text-xs ${
                    item.active 
                      ? 'bg-[#4a5565] text-stone-100 dark:bg-zinc-50 dark:text-zinc-900' 
                      : 'hover:bg-stone-300 dark:hover:bg-zinc-700'
                  } border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700`}
                  onClick={() => handleNavItemClick(item)}
                >
                  <div className="flex items-center">
                    <item.icon className="w-4 h-4 mr-3" />
                    {!isSidebarCollapsed && item.label}
                  </div>
                  {!isSidebarCollapsed && item.subItems && (
                    openSubmenus[item.label] 
                      ? <ChevronDown className="w-4 h-4" /> 
                      : <ChevronRight className="w-4 h-4" />
                  )}
                </Button>
                {!isSidebarCollapsed && item.subItems && openSubmenus[item.label] && (
                  <div className="pl-8 mt-1 space-y-1">
                    {item.subItems.map((subItem, subIndex) => (
                      <Button
                        key={subIndex}
                        variant="ghost"
                        className="w-full justify-start font-mono text-left px-3 py-1 h-auto text-xs hover:bg-stone-300 dark:hover:bg-zinc-700"
                      >
                        {subItem}
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Sidebar Toggle Button */}
          <button
            onClick={toggleSidebar}
            className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-10"
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isSidebarCollapsed ? (
              <ChevronRightIcon className="w-3 h-3" />
            ) : (
              <ChevronLeft className="w-3 h-3" />
            )}
          </button>
        </div>

        {/* Main Workspace */}
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

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4 mt-12">
                <div className="border border-[#4a5565] dark:border-zinc-700 p-6">
                  <div className="text-lg font-bold">24</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">ACTIVE PROJECTS</div>
                </div>
                <div className="border border-[#4a5565] dark:border-zinc-700 p-6">
                  <div className="text-lg font-bold">156</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">FILES PROCESSED</div>
                </div>
                <div className="border border-[#4a5565] dark:border-zinc-700 p-6">
                  <div className="text-lg font-bold">98%</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">UPTIME</div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="space-y-4">
                <h3 className="text-base font-bold">QUICK ACTIONS</h3>
                <div className="grid grid-cols-2 gap-4">
                  <Button 
                    variant="outline" 
                    className="border border-[#4a5565] hover:bg-[#4a5565] hover:text-stone-100 dark:border-zinc-700 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors p-4 h-auto font-mono text-xs"
                  >
                    [ NEW PROJECT ]
                  </Button>
                  <Button 
                    variant="outline" 
                    className="border border-[#4a5565] hover:bg-[#4a5565] hover:text-stone-100 dark:border-zinc-700 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors p-4 h-auto font-mono text-xs"
                  >
                    [ OPEN TERMINAL ]
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - AI Assistant */}
        <div className={`relative transition-all duration-300 ease-in-out ${
          isChatSidebarCollapsed ? 'w-0' : 'w-[25rem]'
        }`}>
          {!isChatSidebarCollapsed && (
            <div className="h-full w-full border-l border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 flex flex-col">
              {/* Chat Messages */}
              <ScrollArea className="flex-1 p-2">
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div key={index} className={`space-y-2`}>
                      <div className={`text-xs font-bold ${
                        message.type === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        {message.type === 'user' ? 'USER' : 'ASSISTANT'}
                      </div>
                      <div className={`p-2 text-xs whitespace-pre-wrap break-words ${
                        message.type === 'user' 
                          ? 'border border-[#4a5565] bg-[#4a5565] text-stone-100 ml-8' 
                          : 'text-[#4a5565] dark:text-zinc-50 mr-8'
                      }`}>
                        {message.content}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {/* Chat Input */}
              <div className="p-2 border-t border-[#4a5565] dark:border-zinc-700">
                <div className="flex items-end space-x-2">
                  <div className="flex-1">
                    <textarea
                      value={chatMessage}
                      onChange={handleTextareaChange}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      placeholder="Type message..."
                      className="w-full bg-transparent border border-[#4a5565] dark:border-zinc-700 font-mono text-xs resize-none p-2 overflow-hidden"
                      rows={1}
                    />
                  </div>
                  <Button
                    onClick={handleSendMessage}
                    size="icon"
                    className="border border-[#4a5565] bg-stone-100 text-[#4a5565] hover:bg-[#4a5565] hover:text-stone-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 w-8 h-8 flex-shrink-0"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Chat Sidebar Toggle Button */}
          {!isChatSidebarCollapsed && (
            <button
              onClick={toggleChatSidebar}
              className="absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-10"
              title="Collapse chat"
            >
              <ChevronRightIcon className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Floating sunnyAI Button (when chat sidebar is collapsed) */}
        {isChatSidebarCollapsed && (
          <button
            onClick={toggleChatSidebar}
            className="fixed right-4 bottom-4 w-12 h-12 bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-20 shadow-lg"
            title="Open sunnyAI"
          >
            <MessageSquare className="w-6 h-6" />
          </button>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 