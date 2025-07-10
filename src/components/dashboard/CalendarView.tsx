import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Calendar, 
  Video, 
  Clock, 
  Send, 
  Loader2,
  ExternalLink
} from 'lucide-react';
import { Meeting } from '@/lib/calendar';
import { apiKeyService } from '@/lib/api-keys';
import { calendarService } from '@/lib/calendar';
import { Project } from '@/lib/supabase';

interface CalendarViewProps {
  meetings: Meeting[];
  onMeetingUpdate: () => void;
  projects?: Project[];
}

function stripHtml(html: string): string {
  if (!html) return '';
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const CalendarView: React.FC<CalendarViewProps> = ({ 
  meetings, 
  onMeetingUpdate,
  projects = []
}) => {
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const [updatingProject, setUpdatingProject] = useState<string | null>(null);

  const getEventStatusBadge = (eventStatus: Meeting['event_status']) => {
    switch (eventStatus) {
      case 'accepted':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">Attending</Badge>;
      case 'declined':
        return <Badge variant="secondary" className="bg-red-100 text-red-800 text-xs">Declined</Badge>;
      case 'tentative':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">Tentative</Badge>;
      case 'needsAction':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800 text-xs">Invited</Badge>;
      default:
        return <Badge variant="secondary" className="text-xs">Unknown</Badge>;
    }
  };

  const getBotStatusBadge = (botStatus: Meeting['bot_status']) => {
    switch (botStatus) {
      case 'pending':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800 text-xs">No Bot</Badge>;
      case 'bot_scheduled':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800 text-xs">Bot Scheduled</Badge>;
      case 'bot_joined':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">Bot Joined</Badge>;
      case 'transcribing':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">Transcribing</Badge>;
      case 'completed':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">Completed</Badge>;
      case 'failed':
        return <Badge variant="secondary" className="bg-red-100 text-red-800 text-xs">Failed</Badge>;
      default:
        return <Badge variant="secondary" className="text-xs">Unknown</Badge>;
    }
  };

  const sendBotToMeeting = async (meeting: Meeting) => {
    if (!meeting.meeting_url) return;
    try {
      setSendingBot(meeting.id);
      const result = await apiKeyService.sendBotToMeeting(meeting.meeting_url, {
        bot_name: meeting.bot_name || 'Kirit Notetaker',
        bot_chat_message: {
          to: 'everyone',
          message: meeting.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!',
        },
      });
      await calendarService.updateBotStatus(
        meeting.id, 
        'bot_scheduled', 
        result.id || result.bot_id
      );
      onMeetingUpdate();
    } catch (err: any) {
      // Optionally handle error
    } finally {
      setSendingBot(null);
    }
  };

  const canSendBot = (meeting?: Meeting | null) => {
    if (!meeting) return false;
    return meeting.meeting_url && 
           (meeting.bot_status === 'pending') && 
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
      onMeetingUpdate();
    } catch (error) {
      // console.error('Failed to associate meeting with project:', error);
    } finally {
      setUpdatingProject(null);
    }
  };

  useEffect(() => {
    if (selectedMeeting) {
      const updatedMeeting = meetings.find(m => m.id === selectedMeeting.id);
      if (updatedMeeting && updatedMeeting !== selectedMeeting) {
        setSelectedMeeting(updatedMeeting);
      }
    }
  }, [meetings, selectedMeeting]);

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
    <div>
      <h1 className="text-2xl font-bold font-mono uppercase tracking-wide text-[#2d3748] dark:text-zinc-50 mb-6">Meetings</h1>
      <div className="space-y-6">
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
                  {getBotStatusBadge(meeting.bot_status)}
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
                  {meeting.meeting_url && canSendBot(meeting) && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={e => {
                        e.stopPropagation();
                        sendBotToMeeting(meeting);
                      }}
                      disabled={sendingBot === meeting.id}
                      className="font-mono"
                    >
                      {sendingBot === meeting.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </Button>
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
                      <Video className="w-4 h-4" />
                    </Button>
                  )}
                  {meeting.transcript_url && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={e => {
                        e.stopPropagation();
                        window.open(meeting.transcript_url, '_blank');
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
              {selectedMeeting && getBotStatusBadge(selectedMeeting.bot_status)}
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
                  <Video className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-blue-600 dark:text-blue-400 truncate font-mono">
                    {selectedMeeting.meeting_url}
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
                  <ExternalLink className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CalendarView; 