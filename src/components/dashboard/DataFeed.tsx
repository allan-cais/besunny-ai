import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Mail, FileText, Folder, Image, File, Calendar, Clock, Search, Filter } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { supabase, Document } from '@/lib/supabase';
import FileWatchStatus from '@/components/FileWatchStatus';

interface VirtualEmailActivity {
  id: string;
  type: 'email' | 'document' | 'spreadsheet' | 'presentation' | 'image' | 'folder';
  title: string;
  summary: string;
  source: string;
  sender?: string;
  file_size?: string;
  created_at: string;
  processed: boolean;
  project_id?: string;
}

const DataFeed = () => {
  const { user } = useAuth();
  const [activities, setActivities] = useState<VirtualEmailActivity[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'email' | 'drive'>('all');

  useEffect(() => {
    if (user?.id) {
      loadVirtualEmailActivity();
    }
  }, [user?.id]);

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

      if (documentsError) {
        console.error('Error loading documents:', documentsError);
        setActivities(getMockVirtualEmailActivity());
      } else {
        setDocuments(documentsData || []);
        
        // Transform the data to match our interface
        const transformedData: VirtualEmailActivity[] = (documentsData || []).map(doc => ({
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
        
        setActivities(transformedData);
      }
    } catch (error) {
      console.error('Error loading virtual email activity:', error);
      // Fallback to mock data
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

  const getMockVirtualEmailActivity = (): VirtualEmailActivity[] => [
    {
      id: '1',
      type: 'email',
      title: 'Q1 Budget Review Meeting',
      summary: 'Hi team, please find attached the Q1 budget review document that we\'ll be discussing in tomorrow\'s meeting. I\'ve also included the agenda and previous quarter comparisons.',
      source: 'email',
      sender: 'sarah@company.com',
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      processed: true
    },
    {
      id: '2',
      type: 'spreadsheet',
      title: 'Q1 Budget Review.xlsx',
      summary: 'Comprehensive budget analysis for Q1 2025 including revenue projections, expense tracking, and variance analysis.',
      source: 'google_drive',
      file_size: '2.4 MB',
      created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      processed: true
    },
    {
      id: '3',
      type: 'document',
      title: 'Product Roadmap 2025',
      summary: 'This document outlines our product vision and planned feature releases for the next 12 months, including timelines and resource allocation.',
      source: 'google_drive',
      file_size: '1.8 MB',
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      processed: true
    },
    {
      id: '4',
      type: 'email',
      title: 'Client Feedback on Beta Release',
      summary: 'The client has provided some valuable feedback on the beta release which we should incorporate before the final launch. Key points include UI improvements and performance optimizations.',
      source: 'email',
      sender: 'client@example.com',
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      processed: false
    },
    {
      id: '5',
      type: 'folder',
      title: 'Marketing Campaign Assets',
      summary: 'Collection of images, copy, and design files for our upcoming social media campaign. Please review and provide feedback.',
      source: 'google_drive',
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      processed: true
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

  const filteredActivities = activities.filter(activity => {
    const matchesSearch = activity.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         activity.summary.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterType === 'all' || 
                         (filterType === 'email' && activity.type === 'email') ||
                         (filterType === 'drive' && activity.type !== 'email');
    
    return matchesSearch && matchesFilter;
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
            <Card key={activity.id} className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-stone-50 dark:hover:bg-zinc-800 transition-colors">
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
                      <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                        {getTypeLabel(activity.type)}
                      </Badge>
                      {activity.sender && (
                        <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                          From: {activity.sender}
                        </Badge>
                      )}
                      {activity.file_size && (
                        <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                          {activity.file_size}
                        </Badge>
                      )}
                      {!activity.processed && (
                        <Badge className="border border-red-500 rounded px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 uppercase font-mono">
                          Processing
                        </Badge>
                      )}
                      
                      {/* File Watch Status for Google Drive files */}
                      {activity.type !== 'email' && documents.find(doc => doc.id === activity.id) && (
                        <FileWatchStatus 
                          document={documents.find(doc => doc.id === activity.id)!} 
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
    </div>
  );
};

export default DataFeed; 