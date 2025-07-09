import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Calendar, 
  Video, 
  Clock, 
  RefreshCw, 
  Send, 
  CheckCircle, 
  XCircle, 
  Loader2,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { calendarService, Meeting } from '@/lib/calendar';
import { apiKeyService } from '@/lib/api-keys';

interface ProjectMeetingsCardProps {
  projectId?: string;
}

function stripHtml(html: string): string {
  if (!html) return '';
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const ProjectMeetingsCard: React.FC<ProjectMeetingsCardProps> = ({ projectId }) => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadMeetings();
  }, [projectId]);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError(null);
      let loadedMeetings: Meeting[];
      if (projectId) {
        loadedMeetings = await calendarService.getProjectMeetings(projectId);
      } else {
        loadedMeetings = await calendarService.getUpcomingMeetings();
      }
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
      
      const result = await calendarService.syncCalendarEvents(projectId);
      setSuccess(`Synced ${result.meetings_with_urls} meetings with video URLs from ${result.total_events} total events`);
      
      // Reload meetings after sync
      await loadMeetings();
    } catch (err: any) {
      setError(err.message || 'Failed to sync calendar events');
    } finally {
      setSyncing(false);
    }
  };

  const sendBotToMeeting = async (meeting: Meeting) => {
    if (!meeting.meeting_url) {
      setError('No meeting URL available for this meeting');
      return;
    }

    try {
      setSendingBot(meeting.id);
      setError(null);
      
      // Send bot to meeting
      const result = await apiKeyService.sendBotToMeeting(meeting.meeting_url, {
        bot_name: meeting.bot_name || 'Kirit Notetaker',
        bot_chat_message: {
          to: 'everyone',
          message: meeting.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!',
        },
      });

      // Update meeting status to bot_scheduled
      await calendarService.updateMeetingStatus(
        meeting.id, 
        'bot_scheduled', 
        result.id || result.bot_id
      );

      setSuccess(`Bot scheduled for "${meeting.title}" successfully!`);
      
      // Reload meetings to show updated status
      await loadMeetings();
    } catch (err: any) {
      setError(err.message || 'Failed to send bot to meeting');
    } finally {
      setSendingBot(null);
    }
  };

  const formatDateTime = (dateTime: string) => {
    const date = new Date(dateTime);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getStatusBadge = (status: Meeting['status']) => {
    switch (status) {
      case 'accepted':
        return <Badge variant="secondary" className="bg-green-100 text-green-800">Attending</Badge>;
      case 'declined':
        return <Badge variant="secondary" className="bg-red-100 text-red-800">Declined</Badge>;
      case 'tentative':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Tentative</Badge>;
      case 'needsAction':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800">Invited</Badge>;
      case 'pending':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800">Pending</Badge>;
      case 'bot_scheduled':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800">Bot Scheduled</Badge>;
      case 'bot_joined':
        return <Badge variant="secondary" className="bg-green-100 text-green-800">Bot Joined</Badge>;
      case 'transcribing':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Transcribing</Badge>;
      case 'completed':
        return <Badge variant="secondary" className="bg-green-100 text-green-800">Completed</Badge>;
      case 'failed':
        return <Badge variant="secondary" className="bg-red-100 text-red-800">Failed</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const canSendBot = (meeting: Meeting) => {
    return meeting.meeting_url && 
           (meeting.status === 'pending' || meeting.status === 'accepted') && 
           !sendingBot;
  };

  return (
    <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 mb-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-base font-bold">PROJECT MEETINGS</CardTitle>
            </div>
          </div>
          <Button
            onClick={syncCalendarEvents}
            disabled={syncing}
            variant="outline"
            size="sm"
            className="font-mono text-xs"
          >
            {syncing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                SYNCING...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                SYNC CALENDAR
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
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

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span className="text-sm">Loading meetings...</span>
          </div>
        ) : meetings.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              No meetings found for this project
            </p>
            <Button
              onClick={syncCalendarEvents}
              disabled={syncing}
              variant="outline"
              size="sm"
            >
              {syncing ? 'Syncing...' : 'Sync Calendar Events'}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {meetings.map((meeting) => (
              <div key={meeting.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm mb-1">{meeting.title}</h4>
                    <div className="flex items-center space-x-4 text-xs text-gray-600 dark:text-gray-400">
                      <div className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDateTime(meeting.start_time)}
                      </div>
                      {getStatusBadge(meeting.status)}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {canSendBot(meeting) && (
                      <Button
                        onClick={() => sendBotToMeeting(meeting)}
                        disabled={sendingBot === meeting.id}
                        size="sm"
                        className="font-mono text-xs bg-purple-600 hover:bg-purple-700 text-white"
                      >
                        {sendingBot === meeting.id ? (
                          <>
                            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                            SENDING...
                          </>
                        ) : (
                          <>
                            <Send className="mr-1 h-3 w-3" />
                            SEND BOT
                          </>
                        )}
                      </Button>
                    )}
                    {meeting.meeting_url && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(meeting.meeting_url, '_blank')}
                        className="font-mono text-xs"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </div>
                
                {meeting.description && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {stripHtml(meeting.description)}
                  </p>
                )}
                
                {meeting.meeting_url && (
                  <div className="flex items-center text-xs text-gray-600 dark:text-gray-400">
                    <Video className="w-3 h-3 mr-1" />
                    <span className="truncate">{meeting.meeting_url}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ProjectMeetingsCard; 