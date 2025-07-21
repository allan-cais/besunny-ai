import React, { useState, useEffect } from 'react';
import CalendarView from '@/components/dashboard/CalendarView';
import { calendarService, Meeting } from '@/lib/calendar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { RefreshCw, Loader2, Calendar, Clock, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import PageHeader from '@/components/dashboard/PageHeader';
import { useAttendeePolling } from '@/hooks/use-attendee-polling';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { supabase } from '@/lib/supabase';

const MeetingsPage: React.FC = () => {
  const { user } = useAuth();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null);

  // Set up automatic polling
  const { pollNow } = useAttendeePolling({
    enabled: true,
    intervalMs: 30000, // Poll every 30 seconds
    onPollingComplete: (results) => {
      if (results.length > 0) {
        // Reload meetings to show updated status
        loadMeetings();
      }
    },
    onError: (error) => {
      console.error('Polling error:', error);
    }
  });

  useEffect(() => {
    loadMeetings();
    loadProjects();
  }, [user?.id]);

  const loadProjects = async () => {
    if (!user?.id) return;
    
    try {
      const userProjects = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', user.id);

      if (userProjects.data) {
        setProjects(userProjects.data);
      }
    } catch (error) {
      console.error('Error loading user projects:', error);
    }
  };

  const loadMeetings = async () => {
    try {
      setLoading(true);
      // Load upcoming meetings only (current and future)
      const loadedMeetings = await calendarService.getUpcomingMeetings();
      setMeetings(loadedMeetings);
    } catch (err: any) {
      console.error('Failed to load meetings:', err);
    } finally {
      setLoading(false);
    }
  };

  const performManualSync = async () => {
    try {
      setSyncing(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      // Perform a manual sync
      const result = await calendarService.performIncrementalSync(session.user.id, '');
      
      if (result.success) {
        setSyncSuccess('Calendar synced successfully');
        // Reload meetings to show any updates
        loadMeetings();
      } else {
        setSyncError(result.error || 'Sync failed');
      }
    } catch (err: any) {
      console.error('Manual sync error:', err);
      setSyncError(err.message || 'Failed to sync calendar');
    } finally {
      setSyncing(false);
      // Clear success/error messages after 3 seconds
      setTimeout(() => {
        setSyncSuccess(null);
        setSyncError(null);
      }, 3000);
    }
  };

  const handleMeetingUpdate = () => {
    loadMeetings();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="px-4 py-8 font-sans h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <PageHeader title="MEETINGS" path="~/sunny.ai/meetings" />
        
        {/* Manual Sync Button */}
        <Button
          onClick={performManualSync}
          disabled={syncing}
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          {syncing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {syncing ? 'Syncing...' : 'Sync Now'}
        </Button>
      </div>

      {/* Sync Status Messages */}
      {syncError && (
        <Alert className="mb-4" variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{syncError}</AlertDescription>
        </Alert>
      )}

      {syncSuccess && (
        <Alert className="mb-4">
          <Calendar className="h-4 w-4" />
          <AlertDescription>{syncSuccess}</AlertDescription>
        </Alert>
      )}

      {/* Meetings List */}
      <div className="flex-1 space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : meetings.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-32 text-center">
              <Calendar className="h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No meetings found</h3>
              <p className="text-gray-500 mb-4">
                Your calendar meetings will appear here once synced.
              </p>
              <Button onClick={performManualSync} variant="outline">
                Sync Calendar
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {meetings.map((meeting) => (
              <Card key={meeting.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-semibold text-gray-900 mb-1">
                        {meeting.title}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="h-4 w-4" />
                        {formatDate(meeting.start_time)} - {formatDate(meeting.end_time)}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {meeting.meeting_url && (
                        <Badge variant="secondary" className="text-xs">
                          Has Link
                        </Badge>
                      )}
                      <Badge 
                        variant={meeting.event_status === 'accepted' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {meeting.event_status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                {meeting.description && (
                  <CardContent className="pt-0">
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {meeting.description}
                    </p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Calendar View */}
      <div className="mt-8">
        <CalendarView 
          meetings={meetings}
          onMeetingUpdate={handleMeetingUpdate}
        />
      </div>
    </div>
  );
};

export default MeetingsPage; 