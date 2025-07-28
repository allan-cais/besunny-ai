import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { supabaseService, Project, supabase } from '@/lib/supabase';
import { useSupabase } from '@/hooks/use-supabase';
import ProjectMeetingsCard from '@/components/dashboard/ProjectMeetingsCard';
import PageHeader from '@/components/dashboard/PageHeader';
import { Loader2, Brain, Tag, Users, MapPin, Calendar, FileText, Building, Clock, Database } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/providers/AuthProvider';

const colorMap = {
  red: 'bg-red-500',
  orange: 'bg-yellow-500',
  yellow: 'bg-yellow-300',
};

const mockData = {
  decisionQueue: [
    { role: 'EP', label: 'approve permit (blocks call sheet)', time: '17:00', tag: 'PRE' },
    { role: 'Client', label: 'countersign SOW', time: '18:00', tag: 'ADM' },
    { role: 'Director', label: 'lock storyboard', time: '09:00 tomorrow', tag: 'CRE' },
    { role: 'AP', label: 'raise invoice #146', time: '12:00 tomorrow', tag: 'ADM' },
  ],
  adminAlerts: [
    { text: 'W-9 missing', detail: '1st AC  due today' },
    { text: 'Invoice #145', detail: '$25 000  overdue today' },
  ],
  riskLog: [
    { color: 'red', text: 'Weather 70% rain 12 May' },
    { color: 'orange', text: 'Budget trending +12%' },
    { color: 'yellow', text: 'Talent clash 12 May' },
  ],
  commStream: [
    { role: 'Client', item: 'Rough Cut V4', time: '10:42', note: 'Logo must hold 3s' },
    { role: 'Director', item: 'Shot 17B', time: '09:15', note: 'Additional camera setup requested for Shot 17B to provide better coverage' },
  ],
};

interface ExtendedProject extends Project {
  normalized_tags?: string[];
  categories?: string[];
  reference_keywords?: string[];
  notes?: string;
  entity_patterns?: any;
  classification_signals?: any;
  pinecone_document_count?: number;
  last_classification_at?: string | null;
  classification_feedback?: any;
}

interface ProjectMeeting {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  status: string;
  attendees?: string[];
  notes?: string;
}

interface ProjectData {
  id: string;
  type: string;
  title: string;
  created_at: string;
  status: string;
  size?: string;
  source?: string;
}

const ProjectDashboard = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { user } = useAuth();
  const [project, setProject] = useState<ExtendedProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiProcessing, setAiProcessing] = useState(false);
  const [projectMeetings, setProjectMeetings] = useState<ProjectMeeting[]>([]);
  const [projectData, setProjectData] = useState<ProjectData[]>([]);
  const [meetingsLoading, setMeetingsLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(true);
  const { toast } = useToast();

  // Load project-specific meetings
  const loadProjectMeetings = async () => {
    if (!projectId) return;
    
    setMeetingsLoading(true);
    try {
      const { data: meetings, error } = await supabase
        .from('meetings')
        .select('*')
        .eq('project_id', projectId)
        .order('start_time', { ascending: true });

      if (error) {
        console.error('Error loading project meetings:', error);
        setProjectMeetings([]);
      } else {
        setProjectMeetings(meetings || []);
      }
    } catch (error) {
      console.error('Error loading project meetings:', error);
      setProjectMeetings([]);
    } finally {
      setMeetingsLoading(false);
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
        console.error('Error loading project data:', error);
        setProjectData([]);
      } else {
        // Transform documents to ProjectData format
        const transformedData: ProjectData[] = (documents || []).map(doc => ({
          id: doc.id,
          type: doc.type || 'document',
          title: doc.title || 'Untitled Document',
          created_at: doc.created_at,
          status: doc.status || 'active',
          size: doc.file_size ? `${Math.round(doc.file_size / 1024)}KB` : undefined,
          source: doc.source || 'upload'
        }));
        setProjectData(transformedData);
      }
    } catch (error) {
      console.error('Error loading project data:', error);
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
          console.error('Error fetching project:', error);
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
        console.error('Error fetching project:', e);
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
    <div className="px-4 py-8 font-sans">
      <PageHeader title="PROJECT" path={`~/sunny.ai/project/${project?.name?.toLowerCase().replace(/\s+/g, '-') || projectId || ''}`} />
      <div className="flex-1">
        <div className="space-y-8">
          <div className="text-center space-y-4 mb-8">
            <h1 className="text-2xl font-bold font-mono uppercase tracking-wide mb-6">SUNNY DAILY DIGEST</h1>
            <div className="w-24 h-px bg-[#4a5565] dark:bg-zinc-700 mx-auto"></div>
            <div className="flex justify-center gap-4 text-sm text-gray-600 dark:text-gray-400 font-mono">
              <span><b>Project:</b> {project.name}</span>
              <span>|</span>
              <span><b>Client:</b> {project.created_by || 'Unknown'}</span>
              <span>|</span>
              <span><b>Budget</b> $0 spent</span>
            </div>
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
                      {Object.entries(project.entity_patterns.people).some(([name, data]: [string, any]) => data.role === 'internal_lead') && (
                        <div className="text-sm font-mono">
                          <span className="text-gray-600 dark:text-gray-400">Internal Lead: </span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {Object.entries(project.entity_patterns.people).find(([name, data]: [string, any]) => data.role === 'internal_lead')?.[0]}
                          </span>
                        </div>
                      )}
                      {Object.entries(project.entity_patterns.people).some(([name, data]: [string, any]) => data.role === 'agency_lead') && (
                        <div className="text-sm font-mono">
                          <span className="text-gray-600 dark:text-gray-400">Agency Lead: </span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {Object.entries(project.entity_patterns.people).find(([name, data]: [string, any]) => data.role === 'agency_lead')?.[0]}
                          </span>
                        </div>
                      )}
                      {Object.entries(project.entity_patterns.people).some(([name, data]: [string, any]) => data.role === 'client_lead') && (
                        <div className="text-sm font-mono">
                          <span className="text-gray-600 dark:text-gray-400">Client Lead: </span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {Object.entries(project.entity_patterns.people).find(([name, data]: [string, any]) => data.role === 'client_lead')?.[0]}
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
                  <div className="space-y-3">
                    {projectMeetings.map((meeting) => (
                      <div key={meeting.id} className="flex items-start space-x-3 p-2 rounded-md border border-stone-200 dark:border-zinc-700">
                        <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-semibold font-mono text-[#4a5565] dark:text-zinc-200 truncate">
                            {meeting.title}
                          </div>
                          <div className="text-xs text-gray-500 font-mono mt-1">
                            {new Date(meeting.start_time).toLocaleDateString()} • {new Date(meeting.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          </div>
                          {meeting.attendees && meeting.attendees.length > 0 && (
                            <div className="text-xs text-gray-400 font-mono mt-1">
                              {meeting.attendees.length} attendee{meeting.attendees.length !== 1 ? 's' : ''}
                            </div>
                          )}
                        </div>
                        <Badge 
                          variant={meeting.status === 'completed' ? 'secondary' : 'default'} 
                          className="text-[10px] px-1.5 py-0.5 uppercase font-mono"
                        >
                          {meeting.status}
                        </Badge>
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
                  <div className="space-y-3">
                    {projectData.map((item) => (
                      <div key={item.id} className="flex items-start space-x-3 p-2 rounded-md border border-stone-200 dark:border-zinc-700">
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
                        <Badge 
                          variant={item.status === 'active' ? 'default' : 'secondary'} 
                          className="text-[10px] px-1.5 py-0.5 uppercase font-mono"
                        >
                          {item.status}
                        </Badge>
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
    </div>
  );
};

export default ProjectDashboard; 