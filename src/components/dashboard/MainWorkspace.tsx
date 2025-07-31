import React from 'react';
import { MainWorkspaceProps } from './types';
import StatsGrid from './StatsGrid';
import QuickActions from './QuickActions';
import DataFeed from './DataFeed';
import FeedItemDetail from './FeedItemDetail';
import ProjectDashboard from '@/pages/project';

const MainWorkspace = ({ 
  activeProjectId, 
  activeCenterPanel, 
  setActiveCenterPanel, 
  activeFeedItemId, 
  setActiveFeedItemId 
}: MainWorkspaceProps) => {
  if (activeCenterPanel === 'data') {
    if (activeFeedItemId) {
      return <FeedItemDetail id={activeFeedItemId} onBack={() => setActiveFeedItemId(null)} />;
    }
    return <DataFeed onSelect={setActiveFeedItemId} />;
  }
  

  
  if (activeProjectId) {
    // Project dashboard should be full width, standardized spacing
    return (
      <div className="flex-1 flex flex-col overflow-y-auto scrollbar-hide">
        <div className="mb-6 flex items-center">
          <div>
            <span className="text-xs font-medium">PROJECT</span>
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {/* Project name will be rendered inside ProjectDashboard */}
            </div>
          </div>
        </div>
        <div className="flex-1">
          <div className="space-y-8">
            <ProjectDashboard projectId={activeProjectId} />
          </div>
        </div>
      </div>
    );
  }
  
  // Default workspace view (centered, full width, standardized spacing)
  return (
    <div className="flex-1 flex flex-col overflow-y-auto scrollbar-hide">

      {/* Content Area */}
      <div className="flex-1">
        <div className="space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold font-mono mb-6">Welcome to Sunny</h1>
            <div className="w-24 h-px bg-[#4a5565] dark:bg-zinc-700 mx-auto"></div>
            <p className="text-gray-600 dark:text-gray-400 text-sm font-mono">
              Your AI production dashboard
            </p>
          </div>
          <StatsGrid />
          {/* <QuickActions /> */}
        </div>
      </div>
    </div>
  );
};

export default MainWorkspace; 