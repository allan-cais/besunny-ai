import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { 
  Home, 
  FileText, 
  Settings, 
  Database,
  Terminal,
  ChevronRight,
  ChevronDown,
  Search,
  Github,
  Sun,
  Moon,
  Monitor,
  ChevronLeft,
  ChevronRight as ChevronRightIcon
} from "lucide-react";
import { useTheme } from "@/providers/ThemeProvider";
import AIAssistant from "@/components/AIAssistant";

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
  );
};

// Navigation Sidebar Component
interface NavigationSidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  openSubmenus: { [key: string]: boolean };
  onToggleSubmenu: (label: string) => void;
  onNavItemClick: (item: any) => void;
}

const NavigationSidebar = ({ 
  isCollapsed, 
  onToggle, 
  openSubmenus, 
  onToggleSubmenu, 
  onNavItemClick 
}: NavigationSidebarProps) => {
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

  return (
    <div className={`relative transition-all duration-300 ease-in-out ${
      isCollapsed ? 'w-16' : 'w-64'
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
                {item.subItems.map((subItem: string, subIndex: number) => (
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
  const [openSubmenus, setOpenSubmenus] = useState<{ [key: string]: boolean }>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isChatSidebarCollapsed, setIsChatSidebarCollapsed] = useState(true);

  const toggleSubmenu = (label: string) => {
    setOpenSubmenus(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleNavItemClick = (item: any) => {
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
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <NavigationSidebar 
          isCollapsed={isSidebarCollapsed}
          onToggle={toggleSidebar}
          openSubmenus={openSubmenus}
          onToggleSubmenu={toggleSubmenu}
          onNavItemClick={handleNavItemClick}
        />

        <MainWorkspace />

        <AIAssistant 
          isCollapsed={isChatSidebarCollapsed}
          onToggle={toggleChatSidebar}
        />
      </div>
    </div>
  );
};

export default Dashboard; 