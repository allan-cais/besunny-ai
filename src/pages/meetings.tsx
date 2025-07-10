import React, { useState, useEffect } from 'react';
import CalendarView from '@/components/dashboard/CalendarView';
import { calendarService, Meeting } from '@/lib/calendar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { useAuth } from '@/providers/AuthProvider';
import PageHeader from '@/components/dashboard/PageHeader';

const MeetingsPage: React.FC = () => {
  const { user } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  // Remove all sync-related state
  // const [syncing, setSyncing] = useState(false);
  // const [error, setError] = useState<string | null>(null);
  // const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadMeetings();
    loadProjects();
    // Remove loadSyncStatus();
  }, [user?.id]);

  const loadProjects = async () => {
    if (!user?.id) return;
    
    try {
      const userProjects = await getProjectsForUser(user.id);
      setProjects(userProjects);
    } catch (error) {
      console.error('Error loading user projects:', error);
    }
  };

  // Remove syncStatus state and loadSyncStatus

  const loadMeetings = async () => {
    try {
      setLoading(true);
      // setError(null);
      // Load current week meetings for display
      const loadedMeetings = await calendarService.getCurrentWeekMeetings();
      setMeetings(loadedMeetings);
    } catch (err: any) {
      // setError(err.message || 'Failed to load meetings');
    } finally {
      setLoading(false);
    }
  };

  // Remove all sync functions (setupRealTimeSync, initialSync, fullSync)

  const handleMeetingUpdate = () => {
    loadMeetings();
  };

  return (
    <div className="flex-1 max-w-[90rem] mx-auto px-4 py-8 font-sans">
      <div className="flex items-center justify-between mb-6">
        <PageHeader title="MEETINGS" path="~/sunny.ai/meetings" />
      </div>
      {/* Remove sync status, error, and success alerts */}
      <CalendarView
        meetings={meetings}
        // Remove onSyncCalendar, syncing props
        onMeetingUpdate={handleMeetingUpdate}
        projects={projects}
      />
    </div>
  );
};

export default MeetingsPage; 