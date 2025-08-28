import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { useSupabase } from '@/hooks/use-supabase';
import { CalendarIcon, FileTextIcon, MailIcon, MessageSquareIcon } from 'lucide-react';

interface UnclassifiedDocument {
  id: string;
  title: string;
  content: string;
  source: string;
  project_id: string | null;
  author: string | null;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: string;
  name: string;
  overview: string;
}

export function UnclassifiedDocuments() {
  const [documents, setDocuments] = useState<UnclassifiedDocument[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const { supabase } = useSupabase();
  const { toast } = useToast();

  useEffect(() => {
    loadUnclassifiedDocuments();
    loadProjects();
  }, []);

  const loadUnclassifiedDocuments = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('documents')
        .select('*')
        .is('project_id', null)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setDocuments(data || []);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load unclassified documents",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const { data, error } = await supabase
        .from('projects')
        .select('id, name, overview')
        .order('name');

      if (error) throw error;
      setProjects(data || []);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load projects",
        variant: "destructive",
      });
    }
  };

  const assignToProject = async (documentId: string) => {
    if (!selectedProject) {
      toast({
        title: "Error",
        description: "Please select a project",
        variant: "destructive",
      });
      return;
    }

    try {
      setAssigning(documentId);
      
      const { error } = await supabase
        .from('documents')
        .update({ 
          project_id: selectedProject,
          updated_at: new Date().toISOString()
        })
        .eq('id', documentId);

      if (error) throw error;

      toast({
        title: "Success",
        description: "Document assigned to project successfully",
      });

      // Remove the document from the list
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      setSelectedProject('');
      setAssigning(null);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to assign document to project",
        variant: "destructive",
      });
      setAssigning(null);
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'email':
        return <MailIcon className="h-4 w-4" />;
      case 'google_drive':
        return <FileTextIcon className="h-4 w-4" />;
      case 'attendee_bot':
        return <MessageSquareIcon className="h-4 w-4" />;
      default:
        return <FileTextIcon className="h-4 w-4" />;
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'email':
        return 'bg-blue-100 text-blue-800';
      case 'google_drive':
        return 'bg-green-100 text-green-800';
      case 'attendee_bot':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Unclassified Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (documents.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Unclassified Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <FileTextIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No unclassified documents found.</p>
            <p className="text-sm">All your documents have been automatically classified!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileTextIcon className="h-5 w-5" />
          Unclassified Documents ({documents.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96">
          <div className="space-y-4">
            {documents.map((doc) => (
              <div key={doc.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getSourceIcon(doc.source)}
                      <Badge variant="secondary" className={getSourceColor(doc.source)}>
                        {doc.source.replace('_', ' ')}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {formatDate(doc.created_at)}
                      </span>
                    </div>
                    
                    <h3 className="font-medium text-lg mb-1">
                      {doc.title || 'Untitled Document'}
                    </h3>
                    
                    {doc.author && (
                      <p className="text-sm text-muted-foreground mb-2">
                        From: {doc.author}
                      </p>
                    )}
                    
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {doc.content || 'No content available'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t">
                  <Select
                    value={selectedProject}
                    onValueChange={setSelectedProject}
                    disabled={assigning === doc.id}
                  >
                    <SelectTrigger className="w-64">
                      <SelectValue placeholder="Select a project..." />
                    </SelectTrigger>
                    <SelectContent>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          <div className="flex flex-col">
                            <span className="font-medium">{project.name}</span>
                            <span className="text-xs text-muted-foreground line-clamp-1">
                              {project.overview}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Button
                    onClick={() => assignToProject(doc.id)}
                    disabled={!selectedProject || assigning === doc.id}
                    size="sm"
                  >
                    {assigning === doc.id ? 'Assigning...' : 'Assign to Project'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
