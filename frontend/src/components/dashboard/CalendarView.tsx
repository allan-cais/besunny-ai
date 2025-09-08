import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/providers/AuthProvider';
import { useToast } from '@/hooks/use-toast';
import { attendeeService } from '@/lib/attendee-service';
import type { Meeting, Project, BotConfiguration } from '@/types';
import { Loader2, Bot, Calendar, Clock, Users, MapPin, ExternalLink, Settings, Plus, Filter, Search, Send } from 'lucide-react';
import BotConfigurationModal from './BotConfigurationModal';

interface CalendarViewProps {
  meetings: Meeting[];
  onMeetingUpdate: () => void;
  onMeetingStateUpdate?: (meetingId: string, updates: Partial<Meeting>) => void;
  projects?: Project[];
}

function stripHtml(html: string): string {
  if (!html) return '';
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const CalendarView: React.FC<CalendarViewProps> = ({ 
  meetings, 
  onMeetingUpdate,
  onMeetingStateUpdate,
  projects = []
}) => {
  const { user } = useAuth();
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const [updatingProject, setUpdatingProject] = useState<string | null>(null);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [meetingForConfig, setMeetingForConfig] = useState<Meeting | null>(null);
  const { toast } = useToast();

  // Set up real-time subscription to meetings table for immediate UI updates
  useEffect(() => {
    if (!user?.id) return;

    const channel = supabase
      .channel('calendar_meetings_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'meetings',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          if (payload.eventType === 'UPDATE' && payload.new) {
            // Update the specific meeting in the local state
            const updatedMeeting = payload.new as Meeting;
            
            // Update selected meeting if it's the one that changed
            setSelectedMeeting(prev => 
              prev && prev.id === updatedMeeting.id ? updatedMeeting : prev
            );
            
            // Update meeting for config if it's the one that changed
            setMeetingForConfig(prev => 
              prev && prev.id === updatedMeeting.id ? updatedMeeting : prev
            );
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [user?.id]);

  const getEventStatusBadge = (eventStatus: Meeting['event_status']) => {
    switch (eventStatus) {
      case 'accepted':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 hover:bg-green-100 text-xs">Attending</Badge>;
      case 'declined':
        return <Badge variant="secondary" className="bg-red-100 text-red-800 hover:bg-red-100 text-xs">Declined</Badge>;
      case 'tentative':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 text-xs">Tentative</Badge>;
      case 'needsAction':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800 hover:bg-gray-100 text-xs">Invited</Badge>;
      default:
        return <Badge variant="secondary" className="hover:bg-secondary text-xs">Unknown</Badge>;
    }
  };

  const getBotStatusBadge = (meeting: Meeting) => {
    if (!meeting) return null;
    const { bot_status, bot_deployment_method, auto_scheduled_via_email } = meeting;
    
    // Don't show any badge if there's no bot (bot_status is null/undefined or 'pending' without auto_scheduled_via_email)
    if (!bot_status || bot_status === 'pending') {
      if (auto_scheduled_via_email) {
        return <Button size="sm" variant="outline" className="font-mono bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100">Auto-Scheduled</Button>;
      } else {
        return null; // No badge for meetings without bots
      }
    }
    
    let badge;
    switch (bot_status) {
      case 'bot_scheduled':
        if (bot_deployment_method === 'automatic') {
          badge = <Button size="sm" variant="outline" className="font-mono bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100">Auto Bot Scheduled</Button>;
        } else {
          badge = <Button size="sm" variant="outline" className="font-mono bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100">Bot Scheduled</Button>;
        }
        break;
      case 'bot_joined':
        badge = <Button size="sm" variant="outline" className="font-mono bg-green-50 text-green-700 border-green-200 hover:bg-green-100">Bot Joined</Button>;
        break;
      case 'transcribing':
        badge = <Button size="sm" variant="outline" className="font-mono bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100">Transcribing</Button>;
        break;
      case 'completed':
        badge = <Button size="sm" variant="outline" className="font-mono bg-green-50 text-green-700 border-green-200 hover:bg-green-100">Completed</Button>;
        break;
      case 'failed':
        badge = <Button size="sm" variant="outline" className="font-mono bg-red-50 text-red-700 border-red-200 hover:bg-red-100">Failed</Button>;
        break;
      default:
        badge = <Button size="sm" variant="outline" className="font-mono">Unknown</Button>;
    }
    
    return badge;
  };

  const sendBotToMeeting = async (meeting: Meeting, configuration?: BotConfiguration) => {
    if (!meeting.meeting_url) return;
    try {
      setSendingBot(meeting.id);
      
      const result = await attendeeService.sendBotToMeeting({
        meeting_url: meeting.meeting_url,
        bot_name: configuration?.transcription_settings?.language || meeting.bot_name || 'AI Assistant',
        bot_chat_message: configuration?.transcription_settings?.enable_speaker_diarization ? 'Hi, I\'m here to transcribe this meeting!' : 'Hi, I\'m here to transcribe this meeting!'
      });
      
      await supabase
        .from('meetings')
        .update({
          attendee_bot_id: result.botId,
          bot_status: 'bot_scheduled',
          updated_at: new Date().toISOString()
        })
        .eq('id', meeting.id);

      onMeetingUpdate();
      
      toast({
        title: "Bot deployed successfully!",
        description: `Bot will join the meeting 2 minutes before it starts.`,
      });
    } catch (error) {
      toast({
        title: "Failed to deploy bot",
        description: "Please try again.",
        variant: "destructive",
      });
    } finally {
      setSendingBot(null);
    }
  };

  const handleConfigureAndDeploy = (meeting: Meeting) => {
    setMeetingForConfig(meeting);
    setConfigModalOpen(true);
  };

  const handleDeployWithConfiguration = async (configuration: BotConfiguration) => {
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
      await supabase
        .from('meetings')
        .update({ project_id: projectId === 'none' ? null : projectId })
        .eq('id', meetingId);
      if (selectedMeeting && selectedMeeting.id === meetingId) {
        setSelectedMeeting({
          ...selectedMeeting,
          project_id: projectId === 'none' ? undefined : projectId
        });
      }
      onMeetingUpdate();
    } catch (error) {
      toast({
        title: "Failed to assign meeting",
        description: "Please try again.",
        variant: "destructive",
      });
    } finally {
      setUpdatingProject(null);
    }
  };

  // Update selected meeting when meetings change
  useEffect(() => {
    if (selectedMeeting) {
      const updatedMeeting = meetings.find(m => m.id === selectedMeeting.id);
      if (updatedMeeting && updatedMeeting !== selectedMeeting) {
        setSelectedMeeting(updatedMeeting);
      }
    }
  }, [meetings, selectedMeeting?.id]);

  const formatTime = (dateTime: string) => {
    const date = new Date(dateTime);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (dateTime: string) => {
    const date = new Date(dateTime);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Sort all meetings by start time
  const sortedMeetings = [...meetings].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

  return (
    <div className="h-full flex flex-col">
      <h1 className="text-2xl font-bold font-mono uppercase tracking-wide text-[#2d3748] dark:text-zinc-50 mb-6">Meetings</h1>
      <div className="flex-1 overflow-y-auto scrollbar-hide space-y-6 pr-2">
        {sortedMeetings.length === 0 && (
          <div className="text-center text-gray-400 py-12 font-mono">No meetings scheduled.</div>
        )}
        {sortedMeetings.map(meeting => {
          const project = projects.find(p => p.id === meeting.project_id);
          return (
            <Card key={meeting.id} className="cursor-pointer font-mono" onClick={() => setSelectedMeeting(meeting)}>
              <CardHeader className="flex flex-row items-center justify-between pb-2 font-mono">
                <div>
                  <CardTitle className="text-base font-bold font-mono text-[#2d3748] dark:text-zinc-50">
                    {meeting.title}
                  </CardTitle>
                  <CardDescription className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                    <span>{formatDate(meeting.start_time)}</span>
                    <span className="mx-1">|</span>
                    <span>{formatTime(meeting.start_time)} - {formatTime(meeting.end_time)}</span>
                  </CardDescription>
                </div>
                <div className="flex flex-col items-end space-y-1 font-mono">
                  {getEventStatusBadge(meeting.event_status)}
                  {project && (
                    <Badge variant="outline" className="text-xs mt-1 font-mono">{project.name}</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-0 font-mono">
                {meeting.description && (
                  <div className="text-sm text-gray-600 dark:text-gray-300 mb-2 font-mono">
                    {stripHtml(meeting.description)}
                  </div>
                )}
                <div className="flex items-center space-x-2 mt-2 font-mono">
                  {meeting.meeting_url && canSendBot(meeting) ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={e => {
                        e.stopPropagation();
                        handleConfigureAndDeploy(meeting);
                      }}
                      disabled={sendingBot === meeting.id}
                      className="font-mono"
                    >
                      {sendingBot === meeting.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                      <span className="ml-1">Deploy Bot</span>
                    </Button>
                  ) : meeting.bot_status && meeting.bot_status !== 'pending' ? (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled
                      className="font-mono bg-green-50 text-green-700 border-green-200 hover:bg-green-50 cursor-not-allowed"
                    >
                      <Bot className="w-4 h-4" />
                      <span className="ml-1">Bot Deployed</span>
                    </Button>
                  ) : (
                    getBotStatusBadge(meeting)
                  )}
                  {meeting.meeting_url && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={e => {
                        e.stopPropagation();
                        window.open(meeting.meeting_url, '_blank');
                      }}
                      className="font-mono"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span className="ml-1">Join Meeting</span>
                    </Button>
                  )}
                  {meeting.transcript && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={e => {
                        e.stopPropagation();
                        window.open(meeting.transcript, '_blank');
                      }}
                      className="font-mono"
                    >
                      Transcript
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      {/* Meeting Detail Dialog (unchanged) */}
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
          <div className="space-y-4 font-mono">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-[#4a5565] dark:text-zinc-50 font-mono">
                {selectedMeeting && `${formatTime(selectedMeeting.start_time)} - ${formatTime(selectedMeeting.end_time)}`}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              {selectedMeeting && getEventStatusBadge(selectedMeeting.event_status)}
              {selectedMeeting && getBotStatusBadge(selectedMeeting)}
            </div>
            {selectedMeeting?.description && (
              <div>
                <h4 className="font-medium text-sm mb-2 text-[#4a5565] dark:text-zinc-50 font-mono">Description</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                  {stripHtml(selectedMeeting.description)}
                </p>
              </div>
            )}
            {selectedMeeting?.meeting_url && (
              <div>
                <h4 className="font-medium text-sm mb-2 text-[#4a5565] dark:text-zinc-50 font-mono">Meeting URL</h4>
                <div className="flex items-center space-x-2">
                  <ExternalLink className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-blue-600 dark:text-blue-400 truncate font-mono">
                    {selectedMeeting.meeting_url}
                  </span>
                </div>
              </div>
            )}
            {selectedMeeting?.transcript && (
              <div>
                <h4 className="font-medium text-sm mb-2 text-[#4a5565] dark:text-zinc-50 font-mono">Transcript</h4>
                <div className="flex items-center space-x-2">
                  <ExternalLink className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-blue-600 dark:text-blue-400 truncate font-mono">
                    {selectedMeeting.transcript}
                  </span>
                </div>
              </div>
            )}
            {/* Project Selection (unchanged) */}
            <div>
              <h4 className="font-medium text-sm mb-2 text-[#4a5565] dark:text-zinc-50 font-mono">ASSOCIATED PROJECT</h4>
              <Select
                value={selectedMeeting?.project_id ? selectedMeeting.project_id : 'none'}
                onValueChange={projectId => selectedMeeting && handleProjectChange(selectedMeeting.id, projectId === 'none' ? '' : projectId)}
                disabled={updatingProject === selectedMeeting?.id}
              >
                <SelectTrigger className="w-full bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-700 text-xs font-mono">
                  <SelectValue placeholder="Select a project..." />
                </SelectTrigger>
                <SelectContent className="bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
                  <SelectItem
                    value="none"
                    className="text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 font-mono"
                  >
                    No Project
                  </SelectItem>
                  {projects.map(project => (
                    <SelectItem
                      key={project.id}
                      value={project.id}
                      className="text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 font-mono"
                    >
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {updatingProject === selectedMeeting?.id && (
                <div className="flex items-center space-x-2 mt-2 text-xs text-gray-500 font-mono">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Updating project...</span>
                </div>
              )}
            </div>
            <div className="flex space-x-2 pt-4">
              {selectedMeeting && canSendBot(selectedMeeting) && (
                <Button
                  onClick={() => selectedMeeting && sendBotToMeeting(selectedMeeting)}
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
                      <Send className="mr-2 h-4 w-4" />
                      SEND BOT
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
                  <ExternalLink className="w-4 h-4 mr-1" />
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

export default CalendarView; 