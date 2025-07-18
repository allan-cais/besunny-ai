import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Mail, FileText, Folder, Image, File, Calendar, Clock, Search, Filter, MessageSquare, Play } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { supabase, Document } from '@/lib/supabase';
import FileWatchStatus from '@/components/FileWatchStatus';
import { attendeePollingService } from '@/lib/attendee-polling';
import TranscriptModal from './TranscriptModal';
import EmailModal from './EmailModal';
import DocumentModal from './DocumentModal';
import ClassificationModal from './ClassificationModal';

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
  rawTranscript?: any; // Store the full transcript data for detail view
}

const DataFeed = () => {
  const { user } = useAuth();
  const [activities, setActivities] = useState<VirtualEmailActivity[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'email' | 'drive' | 'transcripts'>('all');
  const [selectedTranscript, setSelectedTranscript] = useState<any>(null);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [mockDocuments, setMockDocuments] = useState<Document[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [classificationActivity, setClassificationActivity] = useState<VirtualEmailActivity | null>(null);

  useEffect(() => {
    if (user?.id) {
      loadVirtualEmailActivity();
      loadProjects();
    }
  }, [user?.id]);

  const loadProjects = async () => {
    if (!user?.id) return;
    
    try {
      const { data: projectsData, error: projectsError } = await supabase
        .from('projects')
        .select('id, name')
        .eq('created_by', user.id)
        .order('created_at', { ascending: false });

      if (projectsError) {
        // Use mock project for demo
        setProjects([{ id: 'mock-project-1', name: 'Summer' }]);
      } else {
        setProjects(projectsData || [{ id: 'mock-project-1', name: 'Summer' }]);
      }
    } catch (error) {
      setProjects([{ id: 'mock-project-1', name: 'Summer' }]);
    }
  };

  const loadVirtualEmailActivity = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      
      // Get documents from the documents table that are associated with this user's projects
      const { data: documentsData, error: documentsError } = await supabase
        .from('documents')
        .select(`
          id,
          title,
          summary,
          source,
          source_id,
          author,
          received_at,
          file_url,
          status,
          file_id,
          last_synced_at,
          watch_active,
          created_at,
          project_id
        `)
        .in('project_id', (
          await supabase
            .from('projects')
            .select('id')
            .eq('created_by', user.id)
        ).data?.map(p => p.id) || [])
        .order('created_at', { ascending: false })
        .limit(50);

      // Get meeting transcripts
      const transcriptsData = await attendeePollingService.getMeetingsWithTranscripts();

      if (documentsError) {
        const mockDocs = getMockDocuments();
        const mockActivities = getMockVirtualEmailActivity();
        setDocuments(mockDocs);
        setActivities(mockActivities);
      } else {
        setDocuments(documentsData || []);
        
        // Transform documents to match our interface
        const documentActivities: VirtualEmailActivity[] = (documentsData || []).map(doc => ({
          id: doc.id,
          type: getDocumentType(doc.source, doc),
          title: doc.title || 'Untitled Document',
          summary: doc.summary ? doc.summary.substring(0, 150) + '...' : 'No content available',
          source: doc.source || 'unknown',
          sender: doc.author,
          file_size: doc.file_url ? 'Unknown' : undefined,
          created_at: doc.created_at,
          processed: true, // All documents in DB are processed
          project_id: doc.project_id
        }));

        // Transform transcripts to match our interface
        const transcriptActivities: VirtualEmailActivity[] = (transcriptsData || []).map(transcript => ({
          id: transcript.id,
          type: 'meeting_transcript',
          title: `Meeting Transcript: ${transcript.title}`,
          summary: transcript.transcript_summary || 'No transcript summary available',
          source: 'attendee_bot',
          created_at: transcript.transcript_retrieved_at || transcript.created_at,
          processed: true,
          project_id: transcript.project_id,
          transcript_duration_seconds: transcript.transcript_duration_seconds,
          transcript_metadata: transcript.transcript_metadata,
          rawTranscript: transcript // Store the full transcript data for detail view
        }));
        
        // Combine and sort by creation date
        const allActivities = [...documentActivities, ...transcriptActivities]
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        
        setActivities(allActivities);
      }
    } catch (error) {
      // Fallback to mock data
      setDocuments(getMockDocuments());
      setActivities(getMockVirtualEmailActivity());
    } finally {
      setLoading(false);
    }
  };

  const getDocumentType = (source: string, document: Document): VirtualEmailActivity['type'] => {
    if (source === 'email' || source === 'gmail') return 'email';
    
    // Check if it's a Google Drive file
    if (document.file_id) {
      // You could add more sophisticated type detection based on file_id patterns
      // For now, we'll use a simple heuristic
      if (document.title?.includes('.xlsx') || document.title?.includes('.csv')) return 'spreadsheet';
      if (document.title?.includes('.pptx') || document.title?.includes('.key')) return 'presentation';
      if (document.title?.includes('.jpg') || document.title?.includes('.png') || document.title?.includes('.gif')) return 'image';
    }
    
    return 'document';
  };

  const getMockDocuments = (): Document[] => [
    {
      id: '2',
      project_id: 'mock-project-1',
      title: 'Q1 Budget Review.xlsx',
      summary: 'Comprehensive budget analysis for Q1 2025 including revenue projections, expense tracking, and variance analysis.',
      source: 'google_drive',
      author: 'Finance Team',
      created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      status: 'active',
      file_id: 'mock-file-id-2',
      file_url: 'https://docs.google.com/spreadsheets/d/mock-file-id-2',
      watch_active: true,
      last_synced_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '3',
      project_id: 'mock-project-1',
      title: 'Product Roadmap 2025',
      summary: 'This document outlines our product vision and planned feature releases for the next 12 months, including timelines and resource allocation.',
      source: 'google_drive',
      author: 'Product Team',
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      status: 'active',
      file_id: 'mock-file-id-3',
      file_url: 'https://docs.google.com/document/d/mock-file-id-3',
      watch_active: true,
      last_synced_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '5',
      project_id: 'mock-project-1',
      title: 'Marketing Campaign Assets',
      summary: 'Collection of images, copy, and design files for our upcoming social media campaign. Please review and provide feedback.',
      source: 'google_drive',
      author: 'Marketing Team',
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'active',
      file_id: 'mock-file-id-5',
      file_url: 'https://drive.google.com/drive/folders/mock-file-id-5',
      watch_active: true,
      last_synced_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '6',
      project_id: 'mock-project-1',
      title: 'Board Meeting Presentation',
      summary: 'Quarterly board meeting presentation covering financial results, strategic initiatives, and upcoming milestones.',
      source: 'google_drive',
      author: 'Executive Team',
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'active',
      file_id: 'mock-file-id-6',
      file_url: 'https://docs.google.com/presentation/d/mock-file-id-6',
      watch_active: true,
      last_synced_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString()
    }
  ];

  const getMockVirtualEmailActivity = (): VirtualEmailActivity[] => [
    {
      id: '1',
      type: 'email',
      title: 'Q1 Budget Review Meeting',
      summary: 'Hi team, please find attached the Q1 budget review document that we\'ll be discussing in tomorrow\'s meeting. I\'ve also included the agenda and previous quarter comparisons.',
      source: 'email',
      sender: 'sarah@company.com',
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      processed: true,
      project_id: 'mock-project-1'
    },
    {
      id: '2',
      type: 'spreadsheet',
      title: 'Q1 Budget Review.xlsx',
      summary: 'Comprehensive budget analysis for Q1 2025 including revenue projections, expense tracking, and variance analysis.',
      source: 'google_drive',
      file_size: '2.4 MB',
      created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      processed: true,
      project_id: 'mock-project-1'
    },
    {
      id: '3',
      type: 'document',
      title: 'Product Roadmap 2025',
      summary: 'This document outlines our product vision and planned feature releases for the next 12 months, including timelines and resource allocation.',
      source: 'google_drive',
      file_size: '1.8 MB',
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      processed: true,
      project_id: 'mock-project-1'
    },
    {
      id: '4',
      type: 'email',
      title: 'Client Feedback on Beta Release',
      summary: 'The client has provided some valuable feedback on the beta release which we should incorporate before the final launch. Key points include UI improvements and performance optimizations.',
      source: 'email',
      sender: 'client@example.com',
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      processed: true
      // No project_id - needs classification
    },
    {
      id: '5',
      type: 'folder',
      title: 'Marketing Campaign Assets',
      summary: 'Collection of images, copy, and design files for our upcoming social media campaign. Please review and provide feedback.',
      source: 'google_drive',
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      processed: true,
      project_id: 'mock-project-1'
    },
    {
      id: '6',
      type: 'presentation',
      title: 'Board Meeting Presentation',
      summary: 'Quarterly board meeting presentation covering financial results, strategic initiatives, and upcoming milestones.',
      source: 'google_drive',
      file_size: '5.2 MB',
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      processed: true
      // No project_id - needs classification
    },
    // Demo transcript data
    {
      id: 'demo-transcript-1',
      type: 'meeting_transcript',
      title: 'Meeting Transcript: Q1 Budget Review Meeting',
      summary: 'Discussion covered Q1 budget performance, revenue projections for Q2, and strategic planning for the upcoming quarter. Key decisions made on resource allocation and new project funding.',
      source: 'attendee_bot',
      created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      processed: true,
      project_id: 'mock-project-1',
      transcript_duration_seconds: 3240, // 54 minutes
      transcript_metadata: {
        word_count: 2847,
        character_count: 15689,
        bot_id: 'demo-bot-1'
      },
      rawTranscript: {
        id: 'demo-transcript-1',
        title: 'Q1 Budget Review Meeting',
        transcript: `Sarah Johnson: Good morning everyone, welcome to our Q1 budget review meeting. I've prepared a comprehensive overview of our financial performance for the first quarter.

Michael Chen: Thanks Sarah. I've reviewed the preliminary numbers and I'm seeing some interesting trends in our marketing spend.

Sarah Johnson: Yes, let's dive into that. Our marketing budget was 15% over target, but we're seeing a 23% increase in qualified leads, so the ROI is actually quite positive.

Jennifer Davis: I agree, but we need to be careful about maintaining this level of spend in Q2. What's our projection for the next quarter?

Michael Chen: Based on current trends, I'm projecting we'll need about $125,000 for Q2 marketing initiatives. That's about 8% higher than Q1, but we're expecting 30% more leads.

Sarah Johnson: That sounds reasonable. Let's also discuss the new product development budget. We've allocated $200,000 for the mobile app development project.

Jennifer Davis: I have some concerns about that allocation. The development team is saying they need closer to $250,000 to complete all the features we've planned.

Michael Chen: We could potentially reduce scope or extend the timeline. What are the must-have features versus nice-to-have?

Sarah Johnson: Good point. Let me break down the feature list. Must-haves include user authentication, core functionality, and basic reporting. That would bring us down to about $180,000.

Jennifer Davis: That's much more manageable. What about the timeline impact?

Sarah Johnson: We'd be looking at a 2-week delay, pushing the launch from June 15th to July 1st. I think that's acceptable given the budget constraints.

Michael Chen: I agree. The 2-week delay is better than over-extending our budget. Let's also discuss the sales team expansion.

Jennifer Davis: Yes, we've been talking about adding two new sales representatives. The budget impact would be about $180,000 annually, including salary, benefits, and commission structure.

Sarah Johnson: That's a significant investment. What's our expected ROI on that?

Michael Chen: Based on our current sales metrics, each new rep should generate about $500,000 in additional revenue annually. So we're looking at a 2.8x ROI.

Jennifer Davis: That's compelling. I think we should move forward with the sales team expansion. The numbers make sense.

Sarah Johnson: Great. Let's also review our contingency fund. We currently have $50,000 set aside for unexpected expenses.

Michael Chen: I'd recommend increasing that to $75,000 given our expansion plans and the current economic climate.

Jennifer Davis: Agreed. Better to be safe than sorry. What about our technology infrastructure budget?

Sarah Johnson: We've allocated $60,000 for server upgrades and new software licenses. This includes the new CRM system we've been discussing.

Michael Chen: The CRM implementation is critical for our sales team expansion. We need to make sure that's prioritized.

Jennifer Davis: Absolutely. The new reps will need proper tools from day one. Let's also discuss our travel and entertainment budget.

Sarah Johnson: We've set aside $25,000 for client meetings and industry conferences. This includes the annual sales conference in September.

Michael Chen: That seems reasonable. We should also budget for some team building events. Morale is important, especially with the expansion.

Jennifer Davis: Good point. Let's add $10,000 for team events and recognition programs.

Sarah Johnson: Perfect. Now let's talk about our revenue projections for Q2. Based on current pipeline and the new sales hires, I'm projecting $1.2 million in revenue.

Michael Chen: That's a 20% increase from Q1. I think that's achievable, especially with the new sales team members.

Jennifer Davis: I'm a bit more conservative. I'd suggest we plan for $1.1 million to be safe.

Sarah Johnson: That's fair. Let's use $1.1 million as our target and $1.2 million as our stretch goal.

Michael Chen: Sounds good. What about our profit margin targets?

Sarah Johnson: We're targeting 25% net profit margin for Q2, which is consistent with Q1 performance.

Jennifer Davis: That's reasonable. We should also discuss our cash flow projections.

Sarah Johnson: Yes, with the increased spending on marketing and new hires, we need to be careful about cash flow timing.

Michael Chen: I recommend we implement more aggressive payment terms for new clients and follow up on overdue invoices more aggressively.

Jennifer Davis: Agreed. Let's also consider offering early payment discounts to improve cash flow.

Sarah Johnson: Good ideas. Let me summarize the key decisions we've made today:

1. Marketing budget for Q2: $125,000 (8% increase from Q1)
2. Mobile app development: $180,000 (reduced scope, 2-week delay)
3. Sales team expansion: $180,000 annually for two new reps
4. Contingency fund: Increased to $75,000
5. Technology infrastructure: $60,000 (including new CRM)
6. Team events: $10,000 additional budget
7. Q2 revenue target: $1.1 million (stretch goal: $1.2 million)
8. Profit margin target: 25%

Does everyone agree with these decisions?

Michael Chen: Yes, I'm comfortable with these numbers.

Jennifer Davis: I agree. The budget looks balanced and realistic.

Sarah Johnson: Excellent. I'll prepare the final budget document and circulate it by the end of the week. Any other items we need to discuss?

Michael Chen: I think we've covered everything. Thanks for the comprehensive review, Sarah.

Jennifer Davis: Yes, great meeting everyone. I'll follow up on the CRM implementation timeline.

Sarah Johnson: Perfect. Meeting adjourned. Thanks everyone for your time and input.`,
        transcript_summary: 'Discussion covered Q1 budget performance, revenue projections for Q2, and strategic planning for the upcoming quarter. Key decisions made on resource allocation and new project funding.',
        transcript_metadata: {
          word_count: 2847,
          character_count: 15689,
          bot_id: 'demo-bot-1'
        },
        transcript_duration_seconds: 3240,
        transcript_retrieved_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        start_time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        meeting_url: 'https://zoom.us/rec/share/demo-meeting-url'
      }
    },
    {
      id: 'demo-transcript-2',
      type: 'meeting_transcript',
      title: 'Meeting Transcript: Product Strategy Session',
      summary: 'Deep dive into product roadmap planning, feature prioritization, and technical architecture decisions. Team discussed user feedback integration and development timeline adjustments.',
      source: 'attendee_bot',
      created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      processed: true,
      transcript_duration_seconds: 2700, // 45 minutes
      transcript_metadata: {
        word_count: 2156,
        character_count: 12345,
        bot_id: 'demo-bot-2'
      },
      rawTranscript: {
        id: 'demo-transcript-2',
        title: 'Product Strategy Session',
        transcript: `Alex Rodriguez: Welcome to our product strategy session. Today we're going to dive deep into our roadmap planning and feature prioritization.

Lisa Thompson: Thanks Alex. I've been reviewing the user feedback from our beta release and there are some interesting patterns we should discuss.

David Kim: Yes, I've analyzed the feedback data and I'm seeing strong demand for the mobile app features we've been planning.

Alex Rodriguez: Great. Let's start with the mobile app development. What's our current timeline looking like?

Lisa Thompson: Based on our current development capacity, we're looking at a 6-month timeline for the full feature set. But I think we should consider a phased approach.

David Kim: I agree. We could launch with core features in 3 months and add advanced features in subsequent releases.

Alex Rodriguez: That makes sense. What are the core features we should prioritize?

Lisa Thompson: Based on user feedback, the top priorities are:
1. User authentication and profile management
2. Core functionality that mirrors the web app
3. Offline capability for key features
4. Push notifications for important updates

David Kim: I'd add real-time collaboration features to that list. Users are specifically asking for that.

Alex Rodriguez: Good point. What's the technical complexity of real-time features?

David Kim: It's moderate complexity. We'll need to implement WebSocket connections and handle conflict resolution for simultaneous edits.

Lisa Thompson: That could add 2-3 weeks to our timeline. Is it worth the delay?

Alex Rodriguez: I think so. Real-time collaboration is a key differentiator for us. Let's include it in the core features.

David Kim: Agreed. Now let's talk about the advanced features for phase 2.

Lisa Thompson: Phase 2 should include:
- Advanced analytics and reporting
- Custom integrations with third-party tools
- Advanced search and filtering
- Bulk operations and batch processing

Alex Rodriguez: That sounds good. What about our web app improvements? We shouldn't neglect that while focusing on mobile.

David Kim: You're right. We have several web app improvements planned:
- Performance optimizations
- UI/UX improvements based on user feedback
- Enhanced security features
- Better accessibility compliance

Lisa Thompson: I'd also like to discuss our API development. Third-party integrations are becoming increasingly important.

Alex Rodriguez: Good point. What's our API roadmap looking like?

David Kim: We're planning to release our public API in Q3. This will include:
- RESTful endpoints for core functionality
- Webhook support for real-time updates
- Comprehensive documentation
- Developer portal with examples

Lisa Thompson: That's ambitious. Do we have the resources to support that timeline?

Alex Rodriguez: We might need to adjust our priorities. Let's focus on the mobile app first, then the API.

David Kim: I agree. Mobile app should be our top priority for the next quarter.

Lisa Thompson: What about user research? Should we conduct more user interviews before finalizing the mobile app features?

Alex Rodriguez: That's a good idea. Let's plan for 10-15 user interviews over the next two weeks.

David Kim: I can help coordinate those interviews. We should focus on power users and potential new users.

Lisa Thompson: Perfect. Now let's discuss our development process. Are we going to use agile sprints?

Alex Rodriguez: Yes, I recommend 2-week sprints with regular demos and feedback sessions.

David Kim: That works for me. We should also implement continuous integration and automated testing.

Lisa Thompson: Absolutely. Quality is crucial, especially for the mobile app launch.

Alex Rodriguez: Let's also discuss our success metrics. How will we measure the success of the mobile app?

David Kim: I suggest we track:
- User adoption rate
- Daily active users
- Feature usage patterns
- User satisfaction scores
- App store ratings

Lisa Thompson: Good metrics. We should also track conversion rates from web to mobile.

Alex Rodriguez: Excellent point. Now let's talk about our marketing strategy for the mobile app launch.

David Kim: We should plan for:
- App store optimization
- Press release and media outreach
- Social media campaign
- Email marketing to existing users
- Influencer partnerships

Lisa Thompson: That's comprehensive. What's our budget for the launch campaign?

Alex Rodriguez: I'd recommend $50,000 for the initial launch campaign. We can adjust based on early results.

David Kim: That sounds reasonable. Let's also plan for post-launch support and maintenance.

Lisa Thompson: Yes, we'll need to monitor performance, fix bugs, and respond to user feedback quickly.

Alex Rodriguez: Perfect. Let me summarize our key decisions:

1. Mobile app development: 6-month timeline with phased approach
2. Core features: Authentication, core functionality, offline capability, push notifications, real-time collaboration
3. Phase 2 features: Analytics, integrations, advanced search, bulk operations
4. Web app improvements: Performance, UI/UX, security, accessibility
5. API development: Q3 release with RESTful endpoints and webhooks
6. Development process: 2-week agile sprints with CI/CD
7. Success metrics: Adoption rate, DAU, feature usage, satisfaction, ratings
8. Launch campaign: $50,000 budget with comprehensive marketing strategy

Does everyone agree with this plan?

David Kim: Yes, I'm comfortable with this roadmap.

Lisa Thompson: I agree. It's ambitious but achievable.

Alex Rodriguez: Excellent. I'll prepare the detailed project plan and circulate it by the end of the week. Any other items we need to discuss?

David Kim: I think we've covered everything. Thanks for leading this session, Alex.

Lisa Thompson: Yes, great meeting everyone. I'll start coordinating the user interviews.

Alex Rodriguez: Perfect. Meeting adjourned. Thanks everyone for your input and commitment to this project.`,
        transcript_summary: 'Deep dive into product roadmap planning, feature prioritization, and technical architecture decisions. Team discussed user feedback integration and development timeline adjustments.',
        transcript_metadata: {
          word_count: 2156,
          character_count: 12345,
          bot_id: 'demo-bot-2'
        },
        transcript_duration_seconds: 2700,
        transcript_retrieved_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        start_time: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        meeting_url: 'https://teams.microsoft.com/demo-meeting-url'
      }
    }
  ];

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

  const getProjectName = (projectId?: string) => {
    if (!projectId) return null;
    const project = projects.find(p => p.id === projectId);
    return project?.name || null;
  };

  const handleClassify = async (activityId: string, projectId: string) => {
    try {
      // Update the activity in the local state
      setActivities(prevActivities => 
        prevActivities.map(activity => 
          activity.id === activityId 
            ? { ...activity, project_id: projectId }
            : activity
        )
      );

      // In a real implementation, you would also update the database
      // const { error } = await supabase
      //   .from('virtual_email_activity')
      //   .update({ project_id: projectId })
      //   .eq('id', activityId);

      // if (error) {
      //   console.error('Error updating project classification:', error);
      // }
    } catch (error) {
      // Handle classification error silently
    }
  };

  const filteredActivities = activities.filter(activity => {
    const matchesSearch = activity.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         activity.summary.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterType === 'all' || 
                         (filterType === 'email' && activity.type === 'email') ||
                         (filterType === 'drive' && activity.type !== 'email' && activity.type !== 'meeting_transcript') ||
                         (filterType === 'transcripts' && activity.type === 'meeting_transcript');
    
    // For transcripts, only show final transcripts (not real-time ones)
    const isFinalTranscript = activity.type !== 'meeting_transcript' || 
                             (activity.rawTranscript && activity.rawTranscript.final_transcript_ready !== false);
    
    return matchesSearch && matchesFilter && isFinalTranscript;
  });



  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
            <CardContent className="p-4">
              <div className="h-6 bg-stone-50 dark:bg-zinc-800 animate-pulse rounded mb-2" />
              <div className="h-4 bg-stone-50 dark:bg-zinc-800 animate-pulse rounded mb-2" />
              <div className="h-4 bg-stone-50 dark:bg-zinc-800 animate-pulse rounded w-2/3" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xs font-medium font-mono uppercase tracking-wide">Virtual Email Activity</h2>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 font-mono">
          Stream of emails and files captured via your virtual email address
        </p>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500 dark:text-gray-400" />
          <Input
            placeholder="Search captured content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 font-mono"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={filterType === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterType('all')}
            className={filterType === 'all' 
              ? "bg-[#4a5565] dark:bg-zinc-700 text-white hover:bg-[#3a4555] dark:hover:bg-zinc-600 font-mono"
              : "border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            }
          >
            All
          </Button>
          <Button
            variant={filterType === 'email' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterType('email')}
            className={filterType === 'email' 
              ? "bg-[#4a5565] dark:bg-zinc-700 text-white hover:bg-[#3a4555] dark:hover:bg-zinc-600 font-mono"
              : "border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            }
          >
            <Mail className="h-4 w-4 mr-1" />
            Emails
          </Button>
          <Button
            variant={filterType === 'drive' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterType('drive')}
            className={filterType === 'drive' 
              ? "bg-[#4a5565] dark:bg-zinc-700 text-white hover:bg-[#3a4555] dark:hover:bg-zinc-600 font-mono"
              : "border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            }
          >
            <FileText className="h-4 w-4 mr-1" />
            Drive Files
          </Button>
          <Button
            variant={filterType === 'transcripts' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterType('transcripts')}
            className={filterType === 'transcripts' 
              ? "bg-[#4a5565] dark:bg-zinc-700 text-white hover:bg-[#3a4555] dark:hover:bg-zinc-600 font-mono"
              : "border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            }
          >
            <MessageSquare className="h-4 w-4 mr-1" />
            Transcripts
          </Button>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="space-y-4">
        {filteredActivities.length === 0 ? (
          <Card className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
            <CardContent className="p-8 text-center">
              <Mail className="h-12 w-12 mx-auto mb-4 text-gray-500 dark:text-gray-400 opacity-50" />
              <h3 className="text-lg font-medium text-[#4a5565] dark:text-zinc-200 mb-2 font-mono">No activity yet</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4 font-mono">
                Start using your virtual email address to see captured content here
              </p>
              <Button 
                variant="outline" 
                className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
              >
                View Settings
              </Button>
            </CardContent>
          </Card>
        ) : (
          filteredActivities.map(activity => (
            <Card 
              key={activity.id} 
              className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              onClick={(e) => {
                // Check if the click was on the "Select Project" badge
                const target = e.target as HTMLElement;
                if (target.closest('.select-project-badge')) {
                  e.stopPropagation();
                  setClassificationActivity(activity);
                  return;
                }
                
                if (activity.type === 'meeting_transcript' && activity.rawTranscript) {
                  setSelectedTranscript(activity.rawTranscript);
                } else if (activity.type === 'email') {
                  setSelectedEmail(activity);
                } else if (activity.type === 'document' || activity.type === 'spreadsheet' || activity.type === 'presentation' || activity.type === 'image' || activity.type === 'folder') {
                  // Find the corresponding document (check both real and mock documents)
                  const document = documents.find(doc => doc.id === activity.id) || mockDocuments.find(doc => doc.id === activity.id);
                  if (document) {
                    setSelectedDocument(document);
                  }
                }
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-stone-50 dark:bg-zinc-800 rounded-full flex items-center justify-center">
                    {getTypeIcon(activity.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="font-medium text-[#4a5565] dark:text-zinc-200 truncate font-mono">{activity.title}</h3>
                      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 font-mono">
                        <Clock className="h-3 w-3" />
                        {formatTimeAgo(activity.created_at)}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2 font-mono">
                      {activity.summary}
                    </p>
                    <div className="flex items-center gap-2">
                      {/* Project Badge - First */}
                      {activity.project_id ? (
                        <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                          Project {activity.project_id === 'mock-project-1' ? 'Summer' : getProjectName(activity.project_id)}
                        </Badge>
                      ) : (
                        <Badge className="select-project-badge border border-red-500 rounded px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 hover:bg-red-50 dark:hover:bg-red-950 uppercase font-mono cursor-pointer">
                          Select Project
                        </Badge>
                      )}
                      
                      {/* Processing Badge - Second */}
                      {!activity.processed && (
                        <Badge className="border border-red-500 rounded px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 hover:bg-red-50 dark:hover:bg-red-950 uppercase font-mono">
                          Processing
                        </Badge>
                      )}
                      
                      {/* Type Badge */}
                      <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                        {getTypeLabel(activity.type)}
                      </Badge>
                      
                      {/* Other Badges */}
                      {activity.sender && (
                        <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                          From: {activity.sender}
                        </Badge>
                      )}
                      {activity.file_size && (
                        <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                          {activity.file_size}
                        </Badge>
                      )}
                      {activity.transcript_duration_seconds && (
                        <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                          {Math.round(activity.transcript_duration_seconds / 60)}min
                        </Badge>
                      )}
                      
                      {/* File Watch Status for Google Drive files */}
                      {activity.type !== 'email' && (documents.find(doc => doc.id === activity.id) || mockDocuments.find(doc => doc.id === activity.id)) && (
                        <FileWatchStatus 
                          document={documents.find(doc => doc.id === activity.id) || mockDocuments.find(doc => doc.id === activity.id)!} 
                          className="ml-auto"
                        />
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
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
      />

      {/* Document Modal */}
      <DocumentModal 
        document={selectedDocument} 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)} 
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

export default DataFeed; 