import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { useSupabase } from '@/hooks/use-supabase';
import {
  MainWorkspace,
} from '@/components/dashboard';
import PageHeader from '@/components/dashboard/PageHeader';

const Dashboard = () => {
  const { user } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [projects, setProjects] = useState<any[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeCenterPanel, setActiveCenterPanel] = useState('');
  const [activeFeedItemId, setActiveFeedItemId] = useState<string | null>(null);
  const location = useLocation();

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

  // Check URL parameters for panel
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const panel = searchParams.get('panel');
    if (panel === 'data') {
      setActiveCenterPanel('data');
    }
  }, [location.search]);

  return (
    <div className="px-4 py-8 font-sans">
      <MainWorkspace
        activeCenterPanel={activeCenterPanel}
        setActiveCenterPanel={setActiveCenterPanel}
        activeProjectId={activeProjectId}
        activeFeedItemId={activeFeedItemId}
        setActiveFeedItemId={setActiveFeedItemId}
        projects={projects}
      />
    </div>
  );
};

export default Dashboard; 