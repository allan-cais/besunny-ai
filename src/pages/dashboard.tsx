import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { useSupabase } from '@/hooks/use-supabase';
import {
  MainWorkspace,
} from '@/components/dashboard';
import PageHeader from '@/components/dashboard/PageHeader';
import UsernameSetupManager from '@/components/UsernameSetupManager';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, Clock, Database, Calendar, Video, Bot, Send, ExternalLink, Mail, FileText, Image, Folder, MessageSquare, File } from 'lucide-react';
import { calendarService, Meeting } from '@/lib/calendar';
import { supabase, Document } from '@/lib/supabase';
import { useAttendeePolling } from '@/hooks/use-attendee-polling';
import { useEnhancedAdaptiveSync } from '@/hooks/use-enhanced-adaptive-sync';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import BotConfigurationModal from '@/components/dashboard/BotConfigurationModal';
import { apiKeyService } from '@/lib/api-keys';
import { attendeeService } from '../lib/attendee-service';
import { useToast } from '@/components/ui/use-toast';
import TranscriptModal from '@/components/dashboard/TranscriptModal';
import EmailModal from '@/components/dashboard/EmailModal';
import DocumentModal from '@/components/dashboard/DocumentModal';
import ClassificationModal from '@/components/dashboard/ClassificationModal';


interface VirtualEmailActivity {
  id: string;
  type: 'email' | 'document' | 'spreadsheet' | 'presentation' | 'image' | 'folder' | 'meeting_transcript';
  title: string;
  summary: string;
  source: string;
  sender?: string;
  file_size?: string;
  created_at: string;
  processed: boolean;
  project_id?: string;
  transcript_duration_seconds?: number;
  transcript_metadata?: any;
  rawTranscript?: any;
}

const Dashboard = () => {
  const { user } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [projects, setProjects] = useState<any[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeCenterPanel, setActiveCenterPanel] = useState('');
  const [activeFeedItemId, setActiveFeedItemId] = useState<string | null>(null);
  const location = useLocation();

  // Dashboard-specific state
  const [currentWeekMeetings, setCurrentWeekMeetings] = useState<Meeting[]>([]);
  const [unclassifiedData, setUnclassifiedData] = useState<VirtualEmailActivity[]>([]);
  const [meetingsLoading, setMeetingsLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(true);
  
  // Modal states for meetings
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [meetingForConfig, setMeetingForConfig] = useState<Meeting | null>(null);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const [updatingProject, setUpdatingProject] = useState<string | null>(null);

  // Modal states for data
  const [selectedTranscript, setSelectedTranscript] = useState<any>(null);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [classificationActivity, setClassificationActivity] = useState<VirtualEmailActivity | null>(null);

  const { toast } = useToast();

  // Set up enhanced adaptive sync
  const { recordActivity, recordVirtualEmailDetection, virtualEmailActivity, userState } = useEnhancedAdaptiveSync({
    enabled: true,
    trackActivity: true,
    trackVirtualEmailActivity: true,
  });

  // Set up automatic polling
  const { pollNow } = useAttendeePolling({
    enabled: false, // Temporarily disabled due to 401 errors
    intervalMs: 30000, // Poll every 30 seconds
    onPollingComplete: (results) => {
      if (results.length > 0) {
        // Reload meetings to show updated status
        loadCurrentWeekMeetings();
      }
    },
    onError: (error) => {
      console.error('Polling error:', error);
    }
  });

  // Load projects for the current user
  useEffect(() => {
    if (user?.id) {
      loadUserProjects();
    }
  }, [user?.id]);

  // Load dashboard data
  useEffect(() => {
    if (user?.id) {
      console.log('Loading dashboard data for user:', user.id);
      loadCurrentWeekMeetings();
      loadUnclassifiedData();
      
      // Record calendar view activity
      recordActivity('calendar_view');
      
      // Automatically set up calendar sync if needed
      setupCalendarSyncIfNeeded();
    }
  }, [user?.id, recordActivity]);

  const setupCalendarSyncIfNeeded = async () => {
    if (!user?.id) return;
    
    try {
      // Check if user has Google credentials
      const { data: credentials } = await supabase
        .from('google_credentials')
        .select('user_id')
        .eq('user_id', user.id)
        .maybeSingle();

      if (!credentials) {
        return; // User doesn't have Google credentials
      }

      // Check if user has active webhook
      const { data: webhook } = await supabase
        .from('calendar_webhooks')
        .select('user_id')
        .eq('user_id', user.id)
        .eq('is_active', true)
        .maybeSingle();

      // If no active webhook, set up calendar sync automatically
      if (!webhook) {
        console.log('No active webhook found, setting up calendar sync automatically...');
        try {
          const result = await calendarService.initializeCalendarSync(user.id);
          if (result.success) {
            console.log('Automatic calendar sync setup successful');
          } else {
            console.error('Automatic calendar sync setup failed:', result.error);
          }
        } catch (error) {
          console.error('Automatic calendar sync setup error:', error);
        }
      }
    } catch (error) {
      console.error('Error checking calendar sync status:', error);
    }
  };

  const loadUserProjects = async () => {
    if (!user?.id) return;
    
    try {
      const userProjects = await getProjectsForUser(user.id);
      setProjects(userProjects);
    } catch (error) {
      console.error('Error loading user projects:', error);
    }
  };

  const loadCurrentWeekMeetings = async () => {
    try {
      setMeetingsLoading(true);
      const meetings = await calendarService.getCurrentWeekMeetings();
      setCurrentWeekMeetings(meetings);
      
      // Debug: Also load all meetings to see what's happening
      try {
        const allMeetings = await calendarService.getAllCurrentWeekMeetings();
        console.log('All current week meetings:', allMeetings);
        console.log('Unassigned meetings (shown in dashboard):', meetings);
        console.log('Assigned meetings (hidden from dashboard):', allMeetings.filter(m => m.project_id));
      } catch (debugErr) {
        console.error('Debug: Failed to load all meetings:', debugErr);
      }
    } catch (err: any) {
      console.error('Failed to load current week meetings:', err);
    } finally {
      setMeetingsLoading(false);
    }
  };



  const loadUnclassifiedData = async () => {
    if (!user?.id) return;

    try {
      setDataLoading(true);
      
      // Load documents that don't have a project_id (unclassified)
      const { data: documentsData, error: documentsError } = await supabase
        .from('documents')
        .select('*')
        .is('project_id', null) // Only unclassified documents
        .order('created_at', { ascending: false })
        .limit(50);

      if (documentsError) {
        console.error('Error loading unclassified documents:', documentsError);
        setUnclassifiedData([]);
      } else {
        // Transform documents to match our interface
        const documentActivities: VirtualEmailActivity[] = (documentsData || []).map(doc => ({
          id: doc.id,
          type: doc.type || getDocumentType(doc.source, doc),
          title: doc.title || 'Untitled Document',
          summary: doc.summary ? doc.summary.substring(0, 150) + '...' : 'No content available',
          source: doc.source || 'unknown',
          sender: doc.author,
          file_size: doc.file_size,
          created_at: doc.created_at,
          processed: true,
          project_id: doc.project_id,
          transcript_duration_seconds: doc.transcript_duration_seconds,
          transcript_metadata: doc.transcript_metadata,
          rawTranscript: doc.type === 'meeting_transcript' ? {
            id: doc.meeting_id || doc.id,
            title: doc.title,
            transcript: doc.summary,
            transcript_summary: doc.summary,
            transcript_metadata: doc.transcript_metadata,
            transcript_duration_seconds: doc.transcript_duration_seconds,
            transcript_retrieved_at: doc.received_at,
            final_transcript_ready: true
          } : undefined
        }));
        
        setUnclassifiedData(documentActivities);
      }
    } catch (error) {
      console.error('Error loading unclassified data:', error);
      setUnclassifiedData([]);
    } finally {
      setDataLoading(false);
    }
  };

  const getDocumentType = (source: string, document: Document): VirtualEmailActivity['type'] => {
    if (source === 'email' || source === 'gmail') return 'email';
    
    if (document.file_id) {
      if (document.title?.includes('.xlsx') || document.title?.includes('.csv')) return 'spreadsheet';
      if (document.title?.includes('.pptx') || document.title?.includes('.key')) return 'presentation';
      if (document.title?.includes('.jpg') || document.title?.includes('.png') || document.title?.includes('.gif')) return 'image';
    }
    
    return 'document';
  };

  // Check URL parameters for panel
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const panel = searchParams.get('panel');
    if (panel === 'data') {
      setActiveCenterPanel('data');
    }
  }, [location.search]);

  // Meeting functions
  const handleMeetingUpdate = () => {
    loadCurrentWeekMeetings();
  };

  const updateMeetingInState = (meetingId: string, updates: Partial<Meeting>) => {
    setCurrentWeekMeetings(prevMeetings => 
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
    
    if (!bot_status || bot_status === 'pending') {
      if (auto_scheduled_via_email) {
        return <Badge className="border border-purple-500 rounded px-2 py-0.5 text-[10px] text-purple-500 bg-purple-50 dark:bg-purple-950 hover:bg-purple-50 dark:hover:bg-purple-950 uppercase font-mono">Auto-Scheduled</Badge>;
      } else {
        return null;
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

  const sendBotToMeeting = async (meeting: Meeting, configuration?: any) => {
    if (!meeting.meeting_url) return;
    try {
      // Record meeting creation activity
      recordActivity('meeting_create');
      
      setSendingBot(meeting.id);
      
      const result = await attendeeService.sendBotToMeeting({
        meeting_url: meeting.meeting_url,
        bot_name: configuration?.bot_name || meeting.bot_name || 'AI Assistant',
        bot_chat_message: configuration?.bot_chat_message || meeting.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!'
      });
      
      await supabase
        .from('meetings')
        .update({
          attendee_bot_id: result.botId,
          bot_status: 'bot_scheduled',
          updated_at: new Date().toISOString()
        })
        .eq('id', meeting.id);

      loadCurrentWeekMeetings();
      
      toast({
        title: "Bot deployed successfully!",
        description: `Bot will join the meeting 2 minutes before it starts.`,
      });
    } catch (error: any) {
      console.error('Error sending bot to meeting:', error);
      toast({
        title: "Failed to deploy bot",
        description: error.message,
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
           !meeting.auto_scheduled_via_email &&
           !sendingBot;
  };

  const handleProjectChange = async (meetingId: string, projectId: string) => {
    try {
      setUpdatingProject(meetingId);
      
      // Use direct Supabase query instead of calendarService to avoid the polling_enabled error
      const { error } = await supabase
        .from('meetings')
        .update({
          project_id: projectId === 'none' ? null : projectId,
          updated_at: new Date().toISOString(),
        })
        .eq('id', meetingId);
      
      if (error) throw error;
      
      if (selectedMeeting && selectedMeeting.id === meetingId) {
        setSelectedMeeting({
          ...selectedMeeting,
          project_id: projectId === 'none' ? undefined : projectId
        });
      }
      
      // Show success message if a project was assigned
      if (projectId !== 'none') {
        const projectName = projects.find(p => p.id === projectId)?.name;
        toast({
          title: "Meeting assigned successfully!",
          description: `Meeting assigned to project: ${projectName}`,
        });
      }
      
      // Don't refresh the meetings list here - let it happen when modal closes
    } catch (error) {
      console.error('Error assigning meeting to project:', error);
      toast({
        title: "Failed to assign meeting",
        description: "Please try again.",
        variant: "destructive",
      });
    } finally {
      setUpdatingProject(null);
    }
  };

  // Data functions
  const getTypeIcon = (type: VirtualEmailActivity['type']) => {
    switch (type) {
      case 'email':
        return <Mail className="h-4 w-4" />;
      case 'document':
        return <FileText className="h-4 w-4" />;
      case 'spreadsheet':
        return <FileText className="h-4 w-4" />;
      case 'presentation':
        return <FileText className="h-4 w-4" />;
      case 'image':
        return <Image className="h-4 w-4" />;
      case 'folder':
        return <Folder className="h-4 w-4" />;
      case 'meeting_transcript':
        return <MessageSquare className="h-4 w-4" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  const getTypeLabel = (type: VirtualEmailActivity['type']) => {
    switch (type) {
      case 'email':
        return 'Email';
      case 'document':
        return 'Document';
      case 'spreadsheet':
        return 'Spreadsheet';
      case 'presentation':
        return 'Presentation';
      case 'image':
        return 'Image';
      case 'folder':
        return 'Folder';
      case 'meeting_transcript':
        return 'Meeting Transcript';
      default:
        return 'File';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    
    const diffInWeeks = Math.floor(diffInDays / 7);
    return `${diffInWeeks} week${diffInWeeks > 1 ? 's' : ''} ago`;
  };

  const handleClassify = async (activityId: string, projectId: string) => {
    try {
      setUnclassifiedData(prevActivities => 
        prevActivities.map(activity => 
          activity.id === activityId 
            ? { ...activity, project_id: projectId }
            : activity
        )
      );

      const { error } = await supabase
        .from('documents')
        .update({ project_id: projectId || null })
        .eq('id', activityId);

      if (error) {
        console.error('Error updating project classification:', error);
        setUnclassifiedData(prevActivities => 
          prevActivities.map(activity => 
            activity.id === activityId 
              ? { ...activity, project_id: activity.project_id }
              : activity
          )
        );
      }
    } catch (error) {
      console.error('Error in handleClassify:', error);
      setUnclassifiedData(prevActivities => 
        prevActivities.map(activity => 
          activity.id === activityId 
            ? { ...activity, project_id: activity.project_id }
            : activity
        )
      );
    }
  };

  const stripHtml = (html: string) => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  return (
    <div className="px-4 pt-12 pb-8 font-sans h-full flex flex-col">


      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {/* Main Workspace (existing functionality) */}
        <MainWorkspace
          activeCenterPanel={activeCenterPanel}
          setActiveCenterPanel={setActiveCenterPanel}
          activeProjectId={activeProjectId}
          activeFeedItemId={activeFeedItemId}
          setActiveFeedItemId={setActiveFeedItemId}
          projects={projects}
        />

        {/* Two Column Layout for Meetings and Data */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Current Week's Meetings */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base font-mono uppercase tracking-wide flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                UNASSIGNED MEETINGS
              </CardTitle>
                                  <span className="text-xs text-gray-500 font-mono">Action Required</span>
            </CardHeader>
            <CardContent className="space-y-2">
              {meetingsLoading ? (
                <div className="text-sm text-gray-500 font-mono text-center py-4">
                  <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
                  Loading meetings...
                </div>
              ) : currentWeekMeetings.length === 0 ? (
                <div className="text-sm text-gray-500 font-mono text-center py-4">
                  All meetings have been assigned to projects
                </div>
              ) : (
                <div className="space-y-3">
                  {currentWeekMeetings.map((meeting) => (
                    <div 
                      key={meeting.id} 
                      className="flex items-start space-x-3 p-2 rounded-md border border-stone-200 dark:border-zinc-700 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                      onClick={() => setSelectedMeeting(meeting)}
                    >
                      <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate">
                          {meeting.title}
                        </div>
                        <div className="text-xs text-gray-500 font-mono mt-1">
                          {new Date(meeting.start_time).toLocaleDateString()} • {new Date(meeting.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          {getEventStatusBadge(meeting.event_status)}
                          {getBotStatusBadge(meeting)}
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-1">
                        {meeting.meeting_url && canSendBot(meeting) && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={e => {
                              e.stopPropagation();
                              handleConfigureAndDeploy(meeting);
                            }}
                            disabled={sendingBot === meeting.id}
                            className="text-xs"
                          >
                            {sendingBot === meeting.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Bot className="w-3 h-3" />
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
                            className="text-xs"
                          >
                            <Video className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Unclassified Data */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base font-mono uppercase tracking-wide flex items-center">
                <Database className="w-4 h-4 mr-2" />
                UNCLASSIFIED DATA
              </CardTitle>
              <span className="text-xs text-gray-500 font-mono">Needs Project</span>
            </CardHeader>
            <CardContent className="space-y-2">
              {dataLoading ? (
                <div className="text-sm text-gray-500 font-mono text-center py-4">
                  <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
                  Loading data...
                </div>
              ) : unclassifiedData.length === 0 ? (
                <div className="text-sm text-gray-500 font-mono text-center py-4">
                  No unclassified data found
                </div>
              ) : (
                <div className="space-y-3">
                  {unclassifiedData.map((activity) => (
                    <div 
                      key={activity.id} 
                      className="flex items-start space-x-3 p-2 rounded-md border border-stone-200 dark:border-zinc-700 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                      onClick={(e) => {
                        const target = e.target as HTMLElement;
                        if (target.closest('.select-project-badge')) {
                          e.stopPropagation();
                          setClassificationActivity(activity);
                          return;
                        }
                        
                        if (activity.type === 'meeting_transcript' && activity.rawTranscript) {
                          // Merge activity data with rawTranscript data for the modal
                          const transcriptData = {
                            ...activity.rawTranscript,
                            project_id: activity.project_id,
                            source: activity.source,
                            bot_name: activity.rawTranscript.transcript_metadata?.bot_id || 'SunnyAI Notetaker'
                          };
                          setSelectedTranscript(transcriptData);
                        } else if (activity.type === 'email') {
                          setSelectedEmail(activity);
                        } else {
                          setSelectedDocument(activity as any);
                        }
                      }}
                    >
                      <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate">
                          {activity.title}
                        </div>
                        <div className="text-xs text-gray-500 font-mono mt-1">
                          {formatTimeAgo(activity.created_at)} • {getTypeLabel(activity.type)}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="select-project-badge px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 uppercase font-mono cursor-pointer">
                            Select Project
                          </Badge>
                          <Badge variant="outline" className="px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                            {getTypeLabel(activity.type)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <UsernameSetupManager />

      {/* Meeting Detail Dialog */}
      <Dialog open={!!selectedMeeting} onOpenChange={(open) => {
        if (!open) {
          // When modal is closed, refresh the meetings list
          // This ensures that meetings assigned to projects disappear from the dashboard
          loadCurrentWeekMeetings();
          setSelectedMeeting(null);
        }
      }}>
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

              <div className="flex items-center gap-2">
                {selectedMeeting && getEventStatusBadge(selectedMeeting.event_status)}
                {selectedMeeting?.bot_status && getBotStatusBadge(selectedMeeting)}
              </div>
            </div>

            <div className="bg-white dark:bg-zinc-700 rounded-lg p-4 space-y-3">
              <h3 className="text-xs font-bold text-[#4a5565] dark:text-zinc-50 font-mono">PROJECT ASSOCIATION</h3>
              <div className="flex items-center gap-2">
                <Select
                  value={selectedMeeting?.project_id || 'none'}
                  onValueChange={(value) => selectedMeeting && handleProjectChange(selectedMeeting.id, value)}
                  disabled={updatingProject === selectedMeeting?.id}
                >
                  <SelectTrigger className="text-xs bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                    <SelectValue>
                      {selectedMeeting?.project_id && selectedMeeting.project_id !== 'none' 
                        ? projects.find(p => p.id === selectedMeeting.project_id)?.name || 'Unknown Project'
                        : 'No Project'
                      }
                    </SelectValue>
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
                {updatingProject === selectedMeeting?.id && (
                  <div className="flex items-center gap-1 text-xs text-gray-500 font-mono">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Updating...</span>
                  </div>
                )}
              </div>
            </div>

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

      {/* Transcript Modal */}
      <TranscriptModal 
        transcript={selectedTranscript} 
        isOpen={!!selectedTranscript}
        onClose={() => setSelectedTranscript(null)}
        projects={projects}
        onProjectChange={handleClassify}
      />

      {/* Email Modal */}
      <EmailModal 
        email={selectedEmail} 
        isOpen={!!selectedEmail}
        onClose={() => setSelectedEmail(null)}
        projects={projects}
        onProjectChange={handleClassify}
      />

      {/* Document Modal */}
      <DocumentModal 
        document={selectedDocument} 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        projects={projects}
        onProjectChange={handleClassify}
      />

              {/* Classification Modal */}
        <ClassificationModal 
          activity={classificationActivity} 
          projects={projects}
          isOpen={!!classificationActivity}
          onClose={() => setClassificationActivity(null)}
          onClassify={handleClassify}
        />


      </div>
    );
};

export default Dashboard; 