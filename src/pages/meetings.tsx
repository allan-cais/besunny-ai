import React, { useState, useEffect } from 'react';
import CalendarView from '@/components/dashboard/CalendarView';
import { calendarService, Meeting } from '@/lib/calendar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertCircle } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { useAuth } from '@/providers/AuthProvider';

const MeetingsPage: React.FC = () => {
  const { user } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadMeetings();
    loadProjects();
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

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError(null);
      const loadedMeetings = await calendarService.getUpcomingMeetings();
      setMeetings(loadedMeetings);
    } catch (err: any) {
      setError(err.message || 'Failed to load meetings');
    } finally {
      setLoading(false);
    }
  };

  const syncCalendarEvents = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccess(null);
      
      const result = await calendarService.syncCalendarEvents();
      setSuccess(`Synced ${result.meetings_with_urls} meetings with video URLs from ${result.total_events} total events`);
      
      // Reload meetings after sync
      await loadMeetings();
    } catch (err: any) {
      setError(err.message || 'Failed to sync calendar events');
    } finally {
      setSyncing(false);
    }
  };

  const handleMeetingUpdate = () => {
    loadMeetings();
  };

  return (
    <>
      {error && (
        <Alert className="mb-4 border-red-500 bg-red-50 dark:bg-red-900/20">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-red-800 dark:text-red-200">{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert className="mb-4 border-green-500 bg-green-50 dark:bg-green-900/20">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription className="text-green-800 dark:text-green-200">{success}</AlertDescription>
        </Alert>
      )}
      <CalendarView
        meetings={meetings}
        onSyncCalendar={syncCalendarEvents}
        syncing={syncing}
        onMeetingUpdate={handleMeetingUpdate}
        projects={projects}
      />
    </>
  );
};

export default MeetingsPage; 