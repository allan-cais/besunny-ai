import React from 'react';
import { Button } from '@/components/ui/button';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "@/providers/ThemeProvider";
import UserAccountMenu from "@/components/auth/UserAccountMenu";
import PythonBackendStatus from "@/components/PythonBackendStatus";

const Header = () => {
  const { theme, setTheme } = useTheme();

  return (
    <header className="relative h-[61px] border-b border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 px-6 flex items-center justify-between flex-shrink-0">
              <h2 className="font-mono text-lg font-bold tracking-tight">sunny.ai</h2>
      <div className="flex items-center space-x-4">
        {/* <PythonBackendStatus /> */}
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

export default Header; 