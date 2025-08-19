import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { supabaseService, supabase } from '@/lib/supabase';
import { useSupabase } from '@/hooks/use-supabase';
import type { Project, Meeting, Document, PersonData } from '@/types';
import ProjectMeetingsCard from '@/components/dashboard/ProjectMeetingsCard';
import PageHeader from '@/components/dashboard/PageHeader';
import { Loader2, Brain, Tag, Users, MapPin, Calendar, FileText, Building, Clock, Database } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/providers/AuthProvider';
import TranscriptModal from '@/components/dashboard/TranscriptModal';
import EmailModal from '@/components/dashboard/EmailModal';
import DocumentModal from '@/components/dashboard/DocumentModal';

const colorMap = {
  red: 'bg-red-500',
  orange: 'bg-yellow-500',
  yellow: 'bg-yellow-300',
};

// Mock data removed - will be replaced with real data from API

interface ExtendedProject extends Project {
  normalized_tags?: string[];
  categories?: string[];
  reference_keywords?: string[];
  notes?: string;
  // entity_patterns and classification_signals are now properly typed from Project interface
  // pinecone_document_count and last_classification_at are now properly typed from Project interface
  // classification_feedback is now properly typed from Project interface
}

interface ProjectMeeting {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  status: string;
  description?: string;
  attendees?: string[];
  notes?: string;
  meeting_url?: string;
  transcript_url?: string;
  transcript: string;
  transcript_summary?: string;
  transcript_metadata?: Record<string, unknown>;
  transcript_duration_seconds?: number;
  transcript_retrieved_at?: string;
  project_id?: string;
}

interface ProjectData {
  id: string;
  type: string;
  title: string;
  created_at: string;
  status: string;
  size?: string;
  source: string;
  content?: string;
  summary: string;
  sender?: string;
  file_size?: string;
  project_id?: string;
  subject?: string;
  body?: string;
  recipients?: string[];
  cc?: string[];
  bcc?: string[];
  attachments?: Array<{
    name: string;
    size: string;
    type: string;
  }>;
}

const ProjectDashboard = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { user, session } = useAuth();
  const [project, setProject] = useState<ExtendedProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiProcessing, setAiProcessing] = useState(false);
  const [projectMeetings, setProjectMeetings] = useState<ProjectMeeting[]>([]);
  const [projectData, setProjectData] = useState<ProjectData[]>([]);
  const [meetingsLoading, setMeetingsLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(true);
  const [selectedTranscript, setSelectedTranscript] = useState<ProjectMeeting | null>(null);
  const [selectedEmail, setSelectedEmail] = useState<ProjectData | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<ProjectData | null>(null);
  const [selectedMeeting, setSelectedMeeting] = useState<ProjectMeeting | null>(null);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>([]);
  const { toast } = useToast();

  // Load project-specific meetings
  const loadProjectMeetings = async () => {
    if (!projectId) return;
    
    setMeetingsLoading(true);
    try {
      // Load meetings (transcript data is stored directly in meetings table)
      const { data: meetings, error } = await supabase
        .from('meetings')
        .select('*')
        .eq('project_id', projectId)
        .order('start_time', { ascending: true });

      if (error) {
        // Error loading project meetings
        setProjectMeetings([]);
      } else {
        // Transform meetings (transcript data is already in the meeting object)
        const transformedMeetings = (meetings || []).map(meeting => {
  
          return {
            ...meeting,
            // Transcript fields are already available directly from the meeting
            transcript: meeting.transcript,
            transcript_summary: meeting.transcript_summary,
            transcript_metadata: meeting.transcript_metadata,
            transcript_duration_seconds: meeting.transcript_duration_seconds,
            transcript_retrieved_at: meeting.transcript_retrieved_at,
          };
        });
        setProjectMeetings(transformedMeetings);
      }
    } catch (error) {
      // Error loading project meetings
      setProjectMeetings([]);
    } finally {
      setMeetingsLoading(false);
    }
  };

  // Load projects for modal dropdowns
  const loadProjects = async () => {
    if (!user?.id) return;
    
    try {
      const { data: projectsData, error: projectsError } = await supabase
        .from('projects')
        .select('id, name')
        .eq('created_by', user.id)
        .order('created_at', { ascending: false });

      if (projectsError) {
        // Error loading projects
        setProjects([]);
      } else {
        setProjects(projectsData || []);
      }
    } catch (error) {
      // Error in loadProjects
      setProjects([]);
    }
  };

  // Load project-specific data
  const loadProjectData = async () => {
    if (!projectId) return;
    
    setDataLoading(true);
    try {
      const { data: documents, error } = await supabase
        .from('documents')
        .select('*')
        .eq('project_id', projectId)
        .order('created_at', { ascending: false });

      if (error) {
        // Error loading project data
        setProjectData([]);
      } else {
        // Transform documents to ProjectData format with additional fields
        const transformedData: ProjectData[] = (documents || []).map(doc => ({
          id: doc.id,
          type: doc.type || 'document',
          title: doc.title || 'Untitled Document',
          created_at: doc.created_at,
          status: doc.status || 'active',
          size: doc.file_size ? `${Math.round(doc.file_size / 1024)}KB` : undefined,
          source: doc.source || 'upload',
          content: doc.content,
          summary: doc.summary || 'No summary available',
          sender: doc.sender,
          file_size: doc.file_size ? `${Math.round(doc.file_size / 1024)}KB` : undefined,
          project_id: doc.project_id,
          subject: doc.title,
          body: doc.content || doc.summary || 'No content available',
          recipients: [],
          cc: [],
          bcc: [],
          attachments: []
        }));
        setProjectData(transformedData);
      }
    } catch (error) {
      // Error loading project data
      setProjectData([]);
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    const fetchProject = async () => {
      setLoading(true);
      try {
        // Fetch project with all metadata fields
        const { data: projectData, error } = await supabase
          .from('projects')
          .select('*')
          .eq('id', projectId)
          .single();

        if (error) {
          // Error fetching project
          setProject(null);
        } else {
          setProject(projectData);
          
          // Check if AI processing is needed (no metadata yet)
          if (projectData && !projectData.normalized_tags && !projectData.categories) {
            setAiProcessing(true);
            
            // Show AI processing started toast
            toast({
              title: "AI Processing Started",
              description: "Your project is being analyzed. This will take a moment...",
              variant: "default",
            });
          }
        }
      } catch (e) {
        // Error fetching project
        setProject(null);
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchProject();
      
      // Load project-specific meetings and data
      loadProjectMeetings();
      loadProjectData();
      loadProjects();
      
      // Set up real-time subscription for project updates
      const subscription = supabase
        .channel(`project-${projectId}`)
        .on(
          'postgres_changes',
          {
            event: 'UPDATE',
            schema: 'public',
            table: 'projects',
            filter: `id=eq.${projectId}`
          },
          (payload) => {
            const updatedProject = payload.new as ExtendedProject;
            setProject(updatedProject);
            
            // Check if AI processing is complete
            if (aiProcessing && updatedProject.normalized_tags && updatedProject.categories) {
              setAiProcessing(false);
              
              // Show success toast
              toast({
                title: "AI Processing Complete",
                description: "Project metadata has been generated successfully!",
                variant: "default",
              });
            }
          }
        )
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'meetings',
            filter: `project_id=eq.${projectId}`
          },
          () => {
            // Reload meetings when they change
            loadProjectMeetings();
          }
        )
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'documents',
            filter: `project_id=eq.${projectId}`
          },
          () => {
            // Reload data when documents change
            loadProjectData();
          }
        )
        .subscribe();

      return () => {
        subscription.unsubscribe();
      };
    }
  }, [projectId]);

  if (loading) {
    return <div className="flex-1 flex items-center justify-center text-lg">Loading...</div>;
  }

  if (!project) {
    return <div className="flex-1 flex items-center justify-center text-lg">Project not found.</div>;
  }

  return (
    <div className="px-4 pt-12 pb-8 font-sans h-full flex flex-col">


      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        <div className="space-y-8">
          <div className="text-center space-y-4 mb-8">
            <h1 className="text-2xl font-bold font-mono uppercase tracking-wide mb-6">PROJECT {project.name?.toUpperCase()}: DIGEST</h1>
            <div className="w-24 h-px bg-[#4a5565] dark:bg-zinc-700 mx-auto"></div>
          </div>
          {/* AI Processing Status */}
          {aiProcessing && (
            <Card className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-mono uppercase tracking-wide flex items-center text-blue-700 dark:text-blue-300">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  AI PROCESSING PROJECT METADATA
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-blue-600 dark:text-blue-400 font-mono">
                  Our AI is analyzing your project details and generating comprehensive metadata. This will help with document classification and project organization.
                </p>
                <div className="mt-3 flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-blue-600 dark:text-blue-400 font-mono">Processing...</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* AI-Generated Project Summary */}
          {project && (project.normalized_tags || project.categories || project.notes) && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base font-mono uppercase tracking-wide flex items-center">
                  <Brain className="w-4 h-4 mr-2" />
                  AI PROJECT SUMMARY
                </CardTitle>
                <Badge variant="outline" className="text-xs font-mono">AI Generated</Badge>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Project Overview */}
                {project.notes && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200">
                      PROJECT OVERVIEW
                    </h4>
                    <p className="text-sm text-gray-700 dark:text-gray-300 font-mono leading-relaxed">
                      {project.notes}
                    </p>
                  </div>
                )}

                {/* Shoot Dates */}
                {/* {project.classification_signals?.temporal_relevance?.active_period && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200 flex items-center">
                      <Calendar className="w-3 h-3 mr-2" />
                      SHOOT DATES
                    </h4>
                    <div className="text-sm font-mono">
                      <span className="text-gray-600 dark:text-gray-400">Shoot Period: </span>
                      <span className="text-gray-700 dark:text-gray-300 font-medium">
                        {project.classification_signals.temporal_relevance.active_period[0]} - {project.classification_signals.temporal_relevance.active_period[1]}
                      </span>
                    </div>
                  </div>
                )} */}

                {/* Companies/Agencies */}
                {project.entity_patterns?.domains && project.entity_patterns.domains.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200 flex items-center">
                      <Building className="w-3 h-3 mr-2" />
                      COMPANIES & AGENCIES
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {project.entity_patterns.domains.map((domain: string, index: number) => (
                        <Badge key={index} variant="outline" className="text-xs font-mono border-indigo-200 text-indigo-700 dark:border-indigo-700 dark:text-indigo-300">
                          {domain}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Categories */}
                {project.categories && project.categories.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200 flex items-center">
                      <Tag className="w-3 h-3 mr-2" />
                      PROJECT CATEGORIES
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {project.categories.map((category, index) => (
                        <Badge key={index} variant="secondary" className="text-xs font-mono bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                          {category}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reference Keywords */}
                {/* {project.reference_keywords && project.reference_keywords.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200">
                      KEY DELIVERABLES & TERMS
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {project.reference_keywords.map((keyword, index) => (
                        <Badge key={index} variant="outline" className="text-xs font-mono border-green-200 text-green-700 dark:border-green-700 dark:text-green-300">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )} */}



                {/* People */}
                {/* {project.entity_patterns?.people && Object.keys(project.entity_patterns.people).length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200 flex items-center">
                      <Users className="w-3 h-3 mr-2" />
                      PROJECT TEAM
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(project.entity_patterns.people || {}).some(([name, data]) => (data as Record<string, unknown>).role === 'internal_lead') && (
                        <div className="text-sm font-mono">
                          <span className="text-gray-600 dark:text-gray-400">Internal Lead: </span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {Object.entries(project.entity_patterns.people || {}).find(([name, data]) => (data as Record<string, unknown>).role === 'internal_lead')?.[0]}
                          </span>
                        </div>
                      )}
                      {Object.entries(project.entity_patterns.people || {}).some(([name, data]) => (data as Record<string, unknown>).role === 'agency_lead') && (
                        <div className="text-sm font-mono">
                          <span className="text-gray-600 dark:text-gray-400">Agency Lead: </span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {Object.entries(project.entity_patterns.people || {}).find(([name, data]) => (data as Record<string, unknown>).role === 'agency_lead')?.[0]}
                          </span>
                        </div>
                      )}
                      {Object.entries(project.entity_patterns.people || {}).some(([name, data]) => (data as Record<string, unknown>).role === 'client_lead') && (
                        <div className="text-sm font-mono">
                          <span className="text-gray-400">Client Lead: </span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {Object.entries(project.entity_patterns.people || {}).find(([name, data]) => (data as Record<string, unknown>).role === 'client_lead')?.[0]}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )} */}

                {/* Locations */}
                {/* {project.entity_patterns?.locations && project.entity_patterns.locations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold font-mono mb-3 text-[#4a5565] dark:text-zinc-200 flex items-center">
                      <MapPin className="w-3 h-3 mr-2" />
                      LOCATIONS
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {project.entity_patterns.locations.map((location: string, index: number) => (
                        <Badge key={index} variant="outline" className="text-xs font-mono border-purple-200 text-purple-700 dark:border-purple-700 dark:text-purple-300">
                          {location}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )} */}




              </CardContent>
            </Card>
          )}

          {/* Project-specific Meetings and Data Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base font-mono uppercase tracking-wide flex items-center">
                  <Clock className="w-4 h-4 mr-2" />
                  MEETINGS
                </CardTitle>
                <span className="text-xs text-gray-500 font-mono">Project</span>
              </CardHeader>
              <CardContent className="space-y-2">
                {meetingsLoading ? (
                  <div className="text-sm text-gray-500 font-mono text-center py-4">
                    <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
                    Loading meetings...
                  </div>
                ) : projectMeetings.length === 0 ? (
                  <div className="text-sm text-gray-500 font-mono text-center py-4">
                    No meetings scheduled for this project
                  </div>
                ) : (
                  <div className="max-h-[350px] overflow-y-auto scrollbar-hide space-y-3">
                    {projectMeetings.map((meeting) => (
                      <div 
                        key={meeting.id} 
                        className="flex items-start space-x-3 p-3 rounded-md border border-stone-200 dark:border-zinc-700 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                        onClick={() => {
                          if (meeting.transcript) {
                            // Transform ProjectMeeting to TranscriptModal format
                            const transcriptData: ProjectMeeting = {
                              id: meeting.id,
                              title: meeting.title,
                              start_time: meeting.start_time,
                              end_time: meeting.end_time,
                              status: meeting.status,
                              meeting_url: meeting.meeting_url,
                              transcript: meeting.transcript,
                              transcript_summary: meeting.transcript_summary,
                              transcript_metadata: meeting.transcript_metadata,
                              transcript_duration_seconds: meeting.transcript_duration_seconds,
                              transcript_retrieved_at: meeting.transcript_retrieved_at,
                              project_id: meeting.project_id,
                            };
                            setSelectedTranscript(transcriptData);
                          } else {
                            // For meetings without transcripts, show a simple meeting detail modal
                            setSelectedMeeting(meeting);
                          }
                        }}
                      >
                        <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate">
                              {meeting.title}
                            </div>
                            {/* <Badge 
                              variant="outline"
                              className="text-xs px-3 py-1 uppercase font-mono ml-2 flex-shrink-0 bg-white dark:bg-zinc-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600"
                            >
                              {meeting.event_status || meeting.status || 'pending'}
                            </Badge> */}
                          </div>
                          <div className="text-xs text-gray-500 font-mono">
                            {new Date(meeting.start_time).toLocaleDateString()} • {new Date(meeting.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          </div>
                          {meeting.attendees && meeting.attendees.length > 0 && (
                            <div className="text-xs text-gray-400 font-mono mt-1">
                              {meeting.attendees.length} attendee{meeting.attendees.length !== 1 ? 's' : ''}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base font-mono uppercase tracking-wide flex items-center">
                  <Database className="w-4 h-4 mr-2" />
                  DATA
                </CardTitle>
                <span className="text-xs text-gray-500 font-mono">Project</span>
              </CardHeader>
              <CardContent className="space-y-2">
                {dataLoading ? (
                  <div className="text-sm text-gray-500 font-mono text-center py-4">
                    <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
                    Loading data...
                  </div>
                ) : projectData.length === 0 ? (
                  <div className="text-sm text-gray-500 font-mono text-center py-4">
                    No data files for this project
                  </div>
                ) : (
                  <div className="max-h-[350px] overflow-y-auto scrollbar-hide space-y-3">
                    {projectData.map((item) => (
                      <div 
                        key={item.id} 
                        className="flex items-start space-x-3 p-2 rounded-md border border-stone-200 dark:border-zinc-700 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                        onClick={() => {
                          // Determine the type and open appropriate modal
                          if (item.type === 'email' || item.sender) {
                            setSelectedEmail(item);
                          } else {
                            // For documents, spreadsheets, presentations, etc.
                            setSelectedDocument(item);
                          }
                        }}
                      >
                        <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate">
                            {item.title}
                          </div>
                          <div className="text-xs text-gray-500 font-mono mt-1">
                            {new Date(item.created_at).toLocaleDateString()} • {item.type}
                            {item.size && ` • ${item.size}`}
                          </div>
                          {item.source && (
                            <div className="text-xs text-gray-400 font-mono mt-1">
                              Source: {item.source}
                            </div>
                          )}
                        </div>
                        {/* <Badge 
                          variant={item.status === 'active' ? 'default' : 'secondary'} 
                          className="text-[10px] px-1.5 py-0.5 uppercase font-mono"
                        >
                          {item.status}
                        </Badge> */}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Project Meetings Card */}
          {/* <ProjectChat 
            projectId={projectId} 
            userId={user?.id} 
            projectName={project?.name}
          /> */}
        </div>
      </div>

      {/* Transcript Modal */}
      <TranscriptModal 
        transcript={selectedTranscript} 
        isOpen={!!selectedTranscript}
        onClose={() => setSelectedTranscript(null)} 
      />

      {/* Email Modal */}
      <EmailModal 
        email={selectedEmail} 
        isOpen={!!selectedEmail}
        onClose={() => setSelectedEmail(null)}
        projects={projects}
        onProjectChange={() => {}} // No-op since we're already in a project context
      />

      {/* Document Modal */}
      <DocumentModal 
        document={selectedDocument} 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        projects={projects}
        onProjectChange={() => {}} // No-op since we're already in a project context
      />

      {/* Meeting Modal */}
      <Dialog open={!!selectedMeeting} onOpenChange={() => setSelectedMeeting(null)}>
        <DialogContent className="sm:max-w-[480px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
          <DialogHeader>
            <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
              {selectedMeeting?.title}
            </DialogTitle>
            <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
              Meeting details and actions
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-white dark:bg-zinc-700 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-xs font-mono">
                  {selectedMeeting?.start_time && new Date(selectedMeeting.start_time).toLocaleDateString()} - {selectedMeeting?.end_time && new Date(selectedMeeting.end_time).toLocaleDateString()}
                </span>
              </div>
              
              {selectedMeeting?.description && (
                <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                  {selectedMeeting.description}
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
            </div>

            <div className="flex space-x-2 pt-4">
              {selectedMeeting && selectedMeeting.meeting_url && (
                <Button
                  onClick={() => {
                    // Deploy bot logic would go here
              
                  }}
                  size="sm"
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-mono text-xs"
                >
                  <Calendar className="mr-2 h-4 w-4" />
                  DEPLOY BOT
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
    </div>
  );
};

export default ProjectDashboard; 