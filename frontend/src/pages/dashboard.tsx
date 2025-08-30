import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { useSupabase } from '@/hooks/use-supabase';
import { useEnhancedAdaptiveSync } from '@/hooks/use-enhanced-adaptive-sync';
import { useAttendeePolling } from '@/hooks/use-attendee-polling';
import { calendarService } from '@/lib/calendar';
import { attendeeService } from '@/lib/attendee-service';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';
import { MainWorkspace } from '@/components/dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Clock, Database, Bot, Video, Loader2 } from 'lucide-react';
import type { Project, VirtualEmailActivity, TranscriptMetadata, BotConfiguration, Document, Meeting } from '@/types';
import BotConfigurationModal from '@/components/dashboard/BotConfigurationModal';
import ClassificationModal from '@/components/dashboard/ClassificationModal';
import TranscriptModal from '@/components/dashboard/TranscriptModal';
import EmailModal from '@/components/dashboard/EmailModal';
import DocumentModal from '@/components/dashboard/DocumentModal';

// VirtualEmailActivity interface is now imported from types

const Dashboard = () => {
  const { user, session, loading: authLoading } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeCenterPanel, setActiveCenterPanel] = useState('');
  const [activeFeedItemId, setActiveFeedItemId] = useState<string | null>(null);
  const location = useLocation();

  // Dashboard-specific state
  const [currentWeekMeetings, setCurrentWeekMeetings] = useState<Meeting[]>([]);
  const [unclassifiedData, setUnclassifiedData] = useState<VirtualEmailActivity[]>([]);
  const [meetingsLoading, setMeetingsLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  
  // Modal states for meetings
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [meetingForConfig, setMeetingForConfig] = useState<Meeting | null>(null);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const [updatingProject, setUpdatingProject] = useState<string | null>(null);

  // Modal states for data
  const [selectedTranscript, setSelectedTranscript] = useState<Meeting | null>(null);
  const [selectedEmail, setSelectedEmail] = useState<Document | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [classificationActivity, setClassificationActivity] = useState<VirtualEmailActivity | null>(null);

  const { toast } = useToast();

  // Set up enhanced adaptive sync with safer initialization
  const { recordActivity, recordVirtualEmailDetection, virtualEmailActivity, userState, isInitialized: enhancedSyncInitialized } = useEnhancedAdaptiveSync({
    enabled: true,
    trackActivity: true,
    trackVirtualEmailActivity: true,
    initializeAfterSession: true, // Wait for session to be fully established
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
      // Polling error handled silently
    }
  });

  // Data loading functions
  const loadUserProjects = useCallback(async () => {
    if (!user?.id || !session) {
      return;
    }
    
    try {
      const userProjects = await getProjectsForUser(user.id);
      setProjects(userProjects);
    } catch (error) {
      // Silent error handling
    }
  }, [user?.id, session, getProjectsForUser]);

  const loadCurrentWeekMeetings = useCallback(async () => {
    if (!session) {
      return;
    }

    try {
      setMeetingsLoading(true);
      const meetings = await calendarService.getCurrentWeekMeetings(session);
      setCurrentWeekMeetings(meetings);
    } catch (err: unknown) {
      setCurrentWeekMeetings([]);
    } finally {
      setMeetingsLoading(false);
    }
  }, [session]);

  const loadUnclassifiedData = useCallback(async () => {
    if (!user?.id || !session) {
      return;
    }

    try {
      setDataLoading(true);
      
      // Load documents that don't have a project_id (unclassified) AND belong to the current user
      const { data: documentsData, error: documentsError } = await supabase
        .from('documents')
        .select('*')
        .eq('created_by', user.id) // First filter: documents created by current user
        .is('project_id', null) // Second filter: only unclassified documents
        .order('created_at', { ascending: false })
        .limit(50);

      if (documentsError) {
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
      setUnclassifiedData([]);
    } finally {
      setDataLoading(false);
    }
  }, [user?.id, session]);

  const setupCalendarSyncIfNeeded = useCallback(async () => {
    if (!user?.id || !session) {
      return;
    }
    
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
        try {
          await calendarService.initializeCalendarSync(user.id);
        } catch (error) {
          // Log calendar sync errors for debugging
          console.error('Calendar sync setup failed:', error);
          // Optionally show a toast notification
          if (error instanceof Error) {
            toast({
              title: "Calendar Sync Warning",
              description: `Failed to set up automatic calendar sync: ${error.message}`,
              variant: "destructive",
            });
          }
        }
      }
    } catch (error) {
      // Log credential check errors
      console.error('Failed to check Google credentials:', error);
    }
  }, [user?.id, session, toast]);

  // Load data when session is ready
  useEffect(() => {
    if (!authLoading && user?.id && session) {
      // First, validate and refresh the session if needed
      const validateAndLoadData = async () => {
        try {
          const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession();
          
          if (sessionError || !currentSession) {
            console.error('Session validation failed in main effect:', sessionError);
            // Try to refresh the session
            const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
            
            if (refreshError || !refreshData.session) {
              console.error('Session refresh failed:', refreshError);
              // Session refresh failed, redirect to login
              window.location.href = '/auth';
              return;
            }
            
            console.log('Session refreshed successfully');
          }
          
          // Load projects
          loadUserProjects();
          
          // Load dashboard data
          loadCurrentWeekMeetings();
          loadUnclassifiedData();
          
          // Setup calendar sync
          setupCalendarSyncIfNeeded();
          
          // Record activity
          recordActivity('calendar_view');
        } catch (error) {
          console.error('Error in validateAndLoadData:', error);
          // If there's an error, redirect to login
          window.location.href = '/auth';
        }
      };
      
      validateAndLoadData();
    }
  }, [authLoading, user?.id, session, loadUserProjects, loadCurrentWeekMeetings, loadUnclassifiedData, setupCalendarSyncIfNeeded, recordActivity]);

  // Check URL parameters for panel
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const panel = searchParams.get('panel');
    if (panel === 'data') {
      setActiveCenterPanel('data');
    }
  }, [location.search]);

  // Helper functions
  const getDocumentType = (source: string, document: Document): VirtualEmailActivity['type'] => {
    if (source === 'email' || source === 'gmail') return 'email';
    
    if (document.file_id) {
      if (document.title?.includes('.xlsx') || document.title?.includes('.csv')) return 'spreadsheet';
      if (document.title?.includes('.pptx') || document.title?.includes('.key')) return 'presentation';
      if (document.title?.includes('.jpg') || document.title?.includes('.png') || document.title?.includes('.gif')) return 'image';
    }
    
    return 'document';
  };

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

  const sendBotToMeeting = async (meeting: Meeting, configuration?: BotConfiguration) => {
    if (!meeting.meeting_url) return;
    try {
      // Record meeting creation activity
      recordActivity('meeting_create');
      
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

      loadCurrentWeekMeetings();
      
      toast({
        title: "Bot deployed successfully!",
        description: `Bot will join the meeting 2 minutes before it starts.`,
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      toast({
        title: "Failed to deploy bot",
        description: errorMessage,
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
    }
    setConfigModalOpen(false);
    setMeetingForConfig(null);
  };

  const canSendBot = (meeting?: Meeting | null) => {
    if (!meeting) return false;
    return !meeting.attendee_bot_id && meeting.meeting_url && meeting.event_status === 'accepted';
  };

  const handleProjectChange = async (meetingId: string, projectId: string) => {
    try {
      setUpdatingProject(meetingId);
      
      await supabase
        .from('meetings')
        .update({ 
          project_id: projectId,
          updated_at: new Date().toISOString()
        })
        .eq('id', meetingId);

      // Update local state
      updateMeetingInState(meetingId, { project_id: projectId });
      
      toast({
        title: "Meeting assigned successfully!",
        description: "The meeting has been assigned to the selected project.",
      });
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

  const getTypeIcon = (type: VirtualEmailActivity['type']) => {
    switch (type) {
      case 'email':
        return <Database className="w-4 h-4" />;
      case 'document':
        return <Database className="w-4 h-4" />;
      case 'spreadsheet':
        return <Database className="w-4 h-4" />;
      case 'presentation':
        return <Database className="w-4 h-4" />;
      case 'image':
        return <Database className="w-4 h-4" />;
      case 'folder':
        return <Database className="w-4 h-4" />;
      case 'meeting_transcript':
        return <Database className="w-4 h-4" />;
      default:
        return <Database className="w-4 h-4" />;
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
        return 'Transcript';
      default:
        return 'Unknown';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const handleClassify = async (activityId: string, projectId: string) => {
    try {
      // Find the activity
      const activity = unclassifiedData.find(a => a.id === activityId);
      if (!activity) return;

      // Update the document with the project ID
      await supabase
        .from('documents')
        .update({ 
          project_id: projectId,
          updated_at: new Date().toISOString()
        })
        .eq('id', activityId);

      // Remove from unclassified data
      setUnclassifiedData(prev => prev.filter(a => a.id !== activityId));
      
      toast({
        title: "Item classified successfully!",
        description: "The item has been assigned to the selected project.",
      });
    } catch (error) {
      toast({
        title: "Failed to classify item",
        description: "Please try again.",
        variant: "destructive",
      });
    }
  };

  const stripHtml = (html: string) => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };



  // Simple test render to see if component works at all
  // Show loading state while data is being fetched
  if (meetingsLoading || dataLoading) {
    return null; // Return null for seamless loading
  }

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
                <div className="max-h-[450px] overflow-y-auto scrollbar-hide space-y-3">
                  {currentWeekMeetings.map((meeting) => (
                    <div 
                      key={meeting.id} 
                      className="flex items-start space-x-3 p-3 rounded-md border border-stone-200 dark:border-zinc-700 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                      onClick={() => setSelectedMeeting(meeting)}
                    >
                      <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate">
                            {meeting.title}
                          </div>
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
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
                  All data has been classified
                </div>
              ) : (
                <div className="max-h-[450px] overflow-y-auto scrollbar-hide space-y-3">
                  {unclassifiedData.map((activity) => (
                    <div 
                      key={activity.id} 
                      className="flex items-start space-x-3 p-3 rounded-md border border-stone-200 dark:border-zinc-700 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                      onClick={() => {
                        if (activity.type === 'meeting_transcript') {
                          // Transform RawTranscript to Meeting format for TranscriptModal
                          const meetingData: Meeting = {
                            id: activity.rawTranscript?.id || activity.id,
                            title: activity.title,
                            description: activity.summary,
                            start_time: new Date().toISOString(), // Default value
                            end_time: new Date().toISOString(), // Default value
                            meeting_url: '',
                            user_id: user?.id || '',
                            project_id: activity.project_id,
                            bot_status: 'completed',
                            transcript: activity.rawTranscript?.transcript || '',
                            transcript_retrieved_at: activity.rawTranscript?.transcript_retrieved_at || activity.created_at,
                            transcript_duration_seconds: activity.rawTranscript?.transcript_duration_seconds || activity.transcript_duration_seconds,
                            transcript_metadata: activity.rawTranscript?.transcript_metadata || activity.transcript_metadata,
                            created_at: activity.created_at,
                            updated_at: activity.created_at,
                            event_status: 'accepted'
                          };
                          setSelectedTranscript(meetingData);
                        } else if (activity.type === 'email') {
                          // Transform VirtualEmailActivity to Document format for EmailModal
                          const documentData: Document = {
                            id: activity.id,
                            title: activity.title,
                            summary: activity.summary,
                            source: activity.source,
                            type: activity.type,
                            author: activity.sender,
                            file_size: activity.file_size,
                            project_id: activity.project_id,
                            created_at: activity.created_at,
                            updated_at: activity.created_at, // Use created_at as fallback
                            received_at: activity.created_at
                          };
                          setSelectedEmail(documentData);
                        } else {
                          // Transform VirtualEmailActivity to Document format for DocumentModal
                          const documentData: Document = {
                            id: activity.id,
                            title: activity.title,
                            summary: activity.summary,
                            source: activity.source,
                            type: activity.type,
                            author: activity.sender,
                            file_size: activity.file_size,
                            project_id: activity.project_id,
                            created_at: activity.created_at,
                            updated_at: activity.created_at, // Use created_at as fallback
                            received_at: activity.created_at
                          };
                          setSelectedDocument(documentData);
                        }
                      }}
                    >
                      <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate mb-1">
                          {activity.title}
                        </div>
                        <div className="text-xs text-gray-500 font-mono mb-1">
                          {formatTimeAgo(activity.created_at)} • {activity.type}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                          {activity.source}
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={e => {
                            e.stopPropagation();
                            setClassificationActivity(activity);
                          }}
                          className="text-xs font-mono"
                        >
                          Classify
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modals */}
      <BotConfigurationModal
        open={configModalOpen}
        onOpenChange={setConfigModalOpen}
        onDeploy={handleDeployWithConfiguration}
        meeting={meetingForConfig}
        deploying={sendingBot === meetingForConfig?.id}
      />

      <ClassificationModal
        isOpen={!!classificationActivity}
        onClose={() => setClassificationActivity(null)}
        activity={classificationActivity}
        projects={projects}
        onClassify={handleClassify}
      />

      <TranscriptModal
        transcript={selectedTranscript}
        isOpen={!!selectedTranscript}
        onClose={() => setSelectedTranscript(null)}
        projects={projects}
        onProjectChange={handleClassify}
      />

      <EmailModal
        email={selectedEmail}
        isOpen={!!selectedEmail}
        onClose={() => setSelectedEmail(null)}
        projects={projects}
        onProjectChange={handleClassify}
      />

      <DocumentModal
        document={selectedDocument}
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        projects={projects}
        onProjectChange={handleClassify}
      />
    </div>
  );
};

export default Dashboard; 