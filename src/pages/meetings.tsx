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
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { supabase } from '@/lib/supabase';
import BotConfigurationModal from '@/components/dashboard/BotConfigurationModal';
import { apiKeyService } from '@/lib/api-keys';
import { attendeePollingService } from '@/lib/attendee-polling';

const MeetingsPage: React.FC = () => {
  const { user } = useAuth();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null);
  
  // Modal states
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [meetingForConfig, setMeetingForConfig] = useState<Meeting | null>(null);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const [updatingProject, setUpdatingProject] = useState<string | null>(null);

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
    
    // Set up real-time subscription to meetings table
    const channel = supabase
      .channel('meetings_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'meetings',
          filter: `user_id=eq.${user?.id}`,
        },
        (payload) => {
          console.log('Meetings table change:', payload);
          
          if (payload.eventType === 'UPDATE' && payload.new) {
            // Update the specific meeting in the local state
            setMeetings(prevMeetings => 
              prevMeetings.map(meeting => 
                meeting.id === payload.new.id 
                  ? { ...meeting, ...payload.new }
                  : meeting
              )
            );
          } else if (payload.eventType === 'INSERT' && payload.new) {
            // Add new meeting to the local state
            setMeetings(prevMeetings => [...prevMeetings, payload.new]);
          } else if (payload.eventType === 'DELETE' && payload.old) {
            // Remove deleted meeting from the local state
            setMeetings(prevMeetings => 
              prevMeetings.filter(meeting => meeting.id !== payload.old.id)
            );
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
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
      console.log('Loaded meetings:', loadedMeetings.map(m => ({
        id: m.id,
        title: m.title,
        bot_status: m.bot_status,
        attendee_bot_id: m.attendee_bot_id,
        bot_deployment_method: m.bot_deployment_method,
        auto_scheduled_via_email: m.auto_scheduled_via_email
      })));
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

  const refreshBotStatuses = async () => {
    try {
      setSyncing(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      // Get meetings that have bots scheduled but might need status updates
      const { data: meetingsWithBots, error } = await supabase
        .from('meetings')
        .select('id, attendee_bot_id, bot_status')
        .not('attendee_bot_id', 'is', null)
        .in('bot_status', ['bot_scheduled', 'bot_joined', 'transcribing']);
      
      if (error) {
        throw error;
      }
      
      if (meetingsWithBots && meetingsWithBots.length > 0) {
        // Trigger polling for these meetings
        const { error: pollingError } = await supabase.functions.invoke('attendee-polling-service', {
          body: { 
            action: 'poll_meetings',
            meeting_ids: meetingsWithBots.map(m => m.id)
          }
        });
        
        if (pollingError) {
          console.warn('Polling error:', pollingError);
        }
        
        setSyncSuccess(`Refreshed status for ${meetingsWithBots.length} meetings with bots`);
      } else {
        setSyncSuccess('No meetings with scheduled bots found');
      }
      
      // Reload meetings to show updated statuses
      loadMeetings();
    } catch (err: any) {
      console.error('Refresh bot statuses error:', err);
      setSyncError(err.message || 'Failed to refresh bot statuses');
    } finally {
      setSyncing(false);
      // Clear success/error messages after 3 seconds
      setTimeout(() => {
        setSyncSuccess(null);
        setSyncError(null);
      }, 3000);
    }
  };

  const enablePollingForAllMeetings = async () => {
    try {
      setSyncing(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      // Get all meetings with bots that might have polling disabled
      const { data: meetingsWithBots, error } = await supabase
        .from('meetings')
        .select('id, title, attendee_bot_id, bot_status, polling_enabled')
        .not('attendee_bot_id', 'is', null)
        .in('bot_status', ['bot_scheduled', 'bot_joined', 'transcribing']);
      
      if (error) {
        throw error;
      }
      
      if (meetingsWithBots && meetingsWithBots.length > 0) {
        // Enable polling for all meetings with bots
        const { error: updateError } = await supabase
          .from('meetings')
          .update({ polling_enabled: true })
          .in('id', meetingsWithBots.map(m => m.id));
        
        if (updateError) {
          throw updateError;
        }
        
        setSyncSuccess(`Enabled polling for ${meetingsWithBots.length} meetings with bots`);
      } else {
        setSyncSuccess('No meetings with scheduled bots found');
      }
      
      // Reload meetings to show updated statuses
      loadMeetings();
    } catch (err: any) {
      console.error('Enable polling error:', err);
      setSyncError(err.message || 'Failed to enable polling');
    } finally {
      setSyncing(false);
      // Clear success/error messages after 3 seconds
      setTimeout(() => {
        setSyncSuccess(null);
        setSyncError(null);
      }, 3000);
    }
  };

  const syncAttendeeBots = async () => {
    try {
      setSyncing(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      // Instead of trying to list all bots, let's focus on meetings that might have bots
      // Get all meetings for the current user
      const { data: userMeetings, error: meetingsError } = await supabase
        .from('meetings')
        .select('id, title, meeting_url, bot_status, attendee_bot_id, bot_deployment_method, auto_scheduled_via_email')
        .eq('user_id', user?.id)
        .not('meeting_url', 'is', null);
      
      if (meetingsError) {
        throw meetingsError;
      }
      
      console.log('User meetings:', userMeetings);
      
      // For now, let's just refresh the status of meetings that already have bot IDs
      let updatedCount = 0;
      
      for (const meeting of userMeetings || []) {
        if (meeting.attendee_bot_id) {
          try {
            // Get bot details to check current status
            const session = (await supabase.auth.getSession()).data.session;
            if (!session) continue;
            
            const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/bot-details?bot_id=${meeting.attendee_bot_id}`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json',
              },
            });
            
            if (response.ok) {
              const result = await response.json();
              if (result.ok && result.data) {
                console.log(`Bot ${meeting.attendee_bot_id} status:`, result.data.status);
                updatedCount++;
              }
            }
          } catch (error) {
            console.warn(`Failed to get status for bot ${meeting.attendee_bot_id}:`, error);
          }
        }
      }
      
      
      // Reload meetings to show updated statuses
      loadMeetings();
    } catch (err: any) {
      console.error('Sync Attendee bots error:', err);
      setSyncError(err.message || 'Failed to sync Attendee bots');
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

  const updateMeetingInState = (meetingId: string, updates: Partial<Meeting>) => {
    setMeetings(prevMeetings => 
      prevMeetings.map(meeting => 
        meeting.id === meetingId 
          ? { ...meeting, ...updates }
          : meeting
      )
    );
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

  const getBotStatusBadge = (meeting: Meeting) => {
    const { bot_status, bot_deployment_method, auto_scheduled_via_email } = meeting;
    
    // Don't show any badge if there's no bot (bot_status is null/undefined or 'pending' without auto_scheduled_via_email)
    if (!bot_status || bot_status === 'pending') {
      if (auto_scheduled_via_email) {
        return <Badge className="border border-purple-500 rounded px-2 py-0.5 text-[10px] text-purple-500 bg-purple-50 dark:bg-purple-950 hover:bg-purple-50 dark:hover:bg-purple-950 uppercase font-mono">Auto-Scheduled</Badge>;
      } else {
        return null; // No badge for meetings without bots
      }
    }
    
    switch (bot_status) {
      case 'bot_scheduled':
        if (bot_deployment_method === 'automatic') {
          return <Badge className="border border-purple-500 rounded px-2 py-0.5 text-[10px] text-purple-500 bg-purple-50 dark:bg-purple-950 hover:bg-purple-50 dark:hover:bg-purple-950 uppercase font-mono">Auto Bot Scheduled</Badge>;
        } else {
          return <Badge className="border border-blue-500 rounded px-2 py-0.5 text-[10px] text-blue-500 bg-blue-50 dark:bg-blue-950 hover:bg-blue-50 dark:hover:bg-blue-950 uppercase font-mono">Bot Scheduled</Badge>;
        }
      case 'bot_joined':
        return <Badge className="border border-green-500 rounded px-2 py-0.5 text-[10px] text-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-50 dark:hover:bg-green-950 uppercase font-mono">Bot Joined</Badge>;
      case 'transcribing':
        return <Badge className="border border-yellow-500 rounded px-2 py-0.5 text-[10px] text-yellow-500 bg-yellow-50 dark:bg-yellow-950 hover:bg-yellow-50 dark:hover:bg-yellow-950 uppercase font-mono">Transcribing</Badge>;
      case 'completed':
        return <Badge className="border border-green-500 rounded px-2 py-0.5 text-[10px] text-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-50 dark:hover:bg-green-950 uppercase font-mono">Completed</Badge>;
      case 'failed':
        return <Badge className="border border-red-500 rounded px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 hover:bg-red-50 dark:hover:bg-red-950 uppercase font-mono">Failed</Badge>;
      default:
        return null;
    }
  };

  const getEventStatusBadge = (status: Meeting['event_status']) => {
    switch (status) {
      case 'accepted':
        return <Badge className="border border-green-500 rounded px-2 py-0.5 text-[10px] text-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-50 dark:hover:bg-green-950 uppercase font-mono">Accepted</Badge>;
      case 'declined':
        return <Badge className="border border-red-500 rounded px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 hover:bg-red-50 dark:hover:bg-red-950 uppercase font-mono">Declined</Badge>;
      case 'tentative':
        return <Badge className="border border-yellow-500 rounded px-2 py-0.5 text-[10px] text-yellow-500 bg-yellow-50 dark:bg-yellow-950 hover:bg-yellow-50 dark:hover:bg-yellow-950 uppercase font-mono">Tentative</Badge>;
      case 'needsAction':
        return <Badge className="border border-blue-500 rounded px-2 py-0.5 text-[10px] text-blue-500 bg-blue-50 dark:bg-blue-950 hover:bg-blue-50 dark:hover:bg-blue-950 uppercase font-mono">Needs Action</Badge>;
      default:
        return null;
    }
  };

  // Bot deployment functions
  const sendBotToMeeting = async (meeting: Meeting, configuration?: any) => {
    if (!meeting.meeting_url) return;
    try {
      setSendingBot(meeting.id);
      
      // Build basic bot options - only essential configuration
      const botOptions: any = {
        // Basic required fields
        meeting_url: meeting.meeting_url,
        bot_name: configuration?.bot_name || meeting.bot_name || 'Sunny AI Assistant',
        
        // Chat message configuration
        bot_chat_message: {
          to: configuration?.chat_message_recipient || 'everyone',
          message: configuration?.bot_chat_message || meeting.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!',
          ...(configuration?.to_user_uuid && { to_user_uuid: configuration.to_user_uuid })
        },
        
        // Future scheduling
        join_at: (() => {
          const meetingStartTime = new Date(meeting.start_time);
          const joinAtTime = new Date(meetingStartTime.getTime() - 2 * 60 * 1000); // Join 2 minutes before start
          return joinAtTime.toISOString();
        })(),
      };
      
      // Note: transcription_settings.language is not supported by Attendee API
      // Language will use API defaults

      const result = await apiKeyService.sendBotToMeeting(meeting.meeting_url, botOptions);
      
      // Handle different possible response structures from Attendee API
      let attendeeBotId = null;
      if (result && typeof result === 'object') {
        // Try different possible field names for the bot ID
        attendeeBotId = result.id || result.bot_id || result.botId || result.bot_id;
      }
      
      if (!attendeeBotId) {
        throw new Error('Failed to get bot ID from Attendee API response');
      }
      
      // Create a bot record in the bots table with basic settings
      const botRecord = await calendarService.createBot({
        name: configuration?.bot_name || meeting.bot_name || 'Sunny AI Assistant',
        description: 'Basic transcription bot with essential configuration',
        provider: 'attendee',
        provider_bot_id: attendeeBotId,
        settings: {
          attendee_bot_id: attendeeBotId,
          created_via: 'manual_deployment',
          meeting_id: meeting.id,
          configuration: configuration || {},
          join_at: botOptions.join_at,
          meeting_start_time: meeting.start_time,
        },
        is_active: true
      });
      
      // Update the meeting with the bot UUID and status
      await calendarService.updateBotStatus(
        meeting.id, 
        'bot_scheduled', 
        botRecord.id // Use the UUID from the bots table
      );
      
      // Also update the deployment method, configuration, and enable polling
      await calendarService.updateMeeting(meeting.id, {
        bot_deployment_method: 'manual',
        bot_configuration: configuration || {},
        polling_enabled: true
      });
      
      // Immediately update the local state to show the new bot status
      updateMeetingInState(meeting.id, {
        bot_status: 'bot_scheduled',
        attendee_bot_id: botRecord.id,
        bot_deployment_method: 'manual',
        bot_configuration: configuration || {},
        polling_enabled: true
      });
      
      handleMeetingUpdate();
    } catch (err: any) {
      console.error('Error sending bot to meeting:', err);
      // Handle error silently
    } finally {
      setSendingBot(null);
    }
  };

  const handleConfigureAndDeploy = (meeting: Meeting) => {
    setMeetingForConfig(meeting);
    setConfigModalOpen(true);
  };

  const handleDeployWithConfiguration = async (configuration: any) => {
    if (meetingForConfig) {
      await sendBotToMeeting(meetingForConfig, configuration);
      setConfigModalOpen(false);
      setMeetingForConfig(null);
    }
  };

  const canSendBot = (meeting?: Meeting | null) => {
    if (!meeting) return false;
    return meeting.meeting_url && 
           (meeting.bot_status === 'pending') && 
           !meeting.auto_scheduled_via_email && // Don't show button for auto-scheduled meetings
           !sendingBot;
  };

  const handleProjectChange = async (meetingId: string, projectId: string) => {
    try {
      setUpdatingProject(meetingId);
      await calendarService.associateMeetingWithProject(meetingId, projectId);
      if (selectedMeeting && selectedMeeting.id === meetingId) {
        setSelectedMeeting({
          ...selectedMeeting,
          project_id: projectId === 'none' ? undefined : projectId
        });
      }
      handleMeetingUpdate();
    } catch (error) {
      // Handle error silently
    } finally {
      setUpdatingProject(null);
    }
  };

  const stripHtml = (html: string) => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  return (
    <div className="px-4 py-8 font-sans h-full flex flex-col">
      {/* Fixed Header */}
      <div className="flex-shrink-0">
        <div className="flex items-center justify-between mb-6">
          <PageHeader title="MEETINGS" path="~/sunny.ai/meetings" />
          
          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Sync Attendee Bots Button */}
            <Button
              onClick={syncAttendeeBots}
              disabled={syncing}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {syncing ? 'Syncing...' : 'Sync Attendee Bots'}
            </Button>
            
            {/* Refresh Bot Statuses Button */}
            <Button
              onClick={refreshBotStatuses}
              disabled={syncing}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {syncing ? 'Refreshing...' : 'Refresh Bot Status'}
            </Button>
            
            {/* Enable Polling Button */}
            <Button
              onClick={enablePollingForAllMeetings}
              disabled={syncing}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {syncing ? 'Enabling...' : 'Enable Polling'}
            </Button>
            
            {/* Manual Sync Button */}
            <Button
              onClick={performManualSync}
              disabled={syncing}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {syncing ? 'Syncing...' : 'Sync Calendar'}
            </Button>
          </div>
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
      </div>

            {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        <CalendarView 
          meetings={meetings}
          onMeetingUpdate={handleMeetingUpdate}
          onMeetingStateUpdate={updateMeetingInState}
        />
      </div>

      {/* Meeting Detail Dialog */}
      <Dialog open={!!selectedMeeting} onOpenChange={() => setSelectedMeeting(null)}>
        <DialogContent className="sm:max-w-[480px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
          <DialogHeader>
            <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
              {selectedMeeting?.title}
            </DialogTitle>
            <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
              Meeting details and project association
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Meeting Details */}
            <div className="bg-white dark:bg-zinc-700 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-xs font-mono">
                  {formatDate(selectedMeeting?.start_time || '')} - {formatDate(selectedMeeting?.end_time || '')}
                </span>
              </div>
              
              {selectedMeeting?.description && (
                <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                  {stripHtml(selectedMeeting.description)}
                </div>
              )}

              {selectedMeeting?.meeting_url && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-gray-600 dark:text-gray-400">Meeting URL:</span>
                  <a 
                    href={selectedMeeting.meeting_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-mono"
                  >
                    Join Meeting
                  </a>
                </div>
              )}

              {/* Status Badges */}
              <div className="flex items-center gap-2">
                {selectedMeeting && getEventStatusBadge(selectedMeeting.event_status)}
                {selectedMeeting?.bot_status && getBotStatusBadge(selectedMeeting)}
              </div>
            </div>

            {/* Project Association */}
            <div className="bg-white dark:bg-zinc-700 rounded-lg p-4 space-y-3">
              <h3 className="text-xs font-bold text-[#4a5565] dark:text-zinc-50 font-mono">PROJECT ASSOCIATION</h3>
              <Select
                value={selectedMeeting?.project_id || 'none'}
                onValueChange={(value) => selectedMeeting && handleProjectChange(selectedMeeting.id, value)}
                disabled={updatingProject === selectedMeeting?.id}
              >
                <SelectTrigger className="text-xs bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                  <SelectItem value="none">No Project</SelectItem>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2 pt-4">
              {selectedMeeting && canSendBot(selectedMeeting) && (
                <Button
                  onClick={() => selectedMeeting && handleConfigureAndDeploy(selectedMeeting)}
                  disabled={sendingBot === selectedMeeting?.id}
                  size="sm"
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-mono text-xs"
                >
                  {sendingBot === selectedMeeting?.id ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      SENDING...
                    </>
                  ) : (
                    <>
                      <Calendar className="mr-2 h-4 w-4" />
                      DEPLOY BOT
                    </>
                  )}
                </Button>
              )}
              {selectedMeeting?.meeting_url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(selectedMeeting.meeting_url, '_blank')}
                  className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
                >
                  Join Meeting
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Bot Configuration Modal */}
      <BotConfigurationModal
        meeting={meetingForConfig}
        open={configModalOpen}
        onOpenChange={setConfigModalOpen}
        onDeploy={handleDeployWithConfiguration}
        deploying={sendingBot === meetingForConfig?.id}
      />
    </div>
  );
};

export default MeetingsPage; 