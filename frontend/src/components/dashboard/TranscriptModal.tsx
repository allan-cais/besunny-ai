import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageSquare, Clock, Calendar, ExternalLink, Copy, Download, X, Play, Edit3 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import ParticipantAnalytics from './ParticipantAnalytics';

interface TranscriptModalProps {
  transcript: {
    id: string;
    title: string;
    transcript?: string; // Make optional to match Meeting type
    transcript_summary?: string;
    transcript_metadata?: Record<string, unknown>;
    transcript_duration_seconds?: number;
    transcript_retrieved_at?: string;
    meeting_url?: string;
    start_time?: string;
    end_time?: string;
    transcript_audio_url?: string;
    transcript_segments?: Record<string, unknown>[];
    transcript_participants?: string[];
    project_id?: string;
    source?: string;
    bot_name?: string;
  } | null;
  isOpen: boolean;
  onClose: () => void;
  projects?: Array<{ id: string; name: string }>;
  onProjectChange?: (transcriptId: string, projectId: string) => void;
}

const TranscriptModal: React.FC<TranscriptModalProps> = ({ 
  transcript, 
  isOpen, 
  onClose, 
  projects = [], 
  onProjectChange 
}) => {
  const [isEditingProject, setIsEditingProject] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  // Reset state when modal opens/closes or transcript changes
  useEffect(() => {
    if (transcript) {
      setSelectedProjectId(transcript.project_id || '');
      setIsEditingProject(false);
    }
  }, [transcript, isOpen]);

  if (!transcript) return null;

  // Handle case where transcript might be undefined
  const transcriptText = transcript.transcript || 'No transcript available';

  const getCurrentProjectName = () => {
    if (!transcript.project_id) return null;
    const project = projects.find(p => p.id === transcript.project_id);
    return project?.name || 'Unknown Project';
  };

  const handleProjectChange = () => {
    if (selectedProjectId && onProjectChange) {
      onProjectChange(transcript.id, selectedProjectId);
      setIsEditingProject(false);
    }
  };

  const handleRemoveProject = () => {
    if (onProjectChange) {
      onProjectChange(transcript.id, '');
      setIsEditingProject(false);
    }
  };

  const getSourceBadge = () => {
    if (transcript.source === 'attendee_bot' || transcript.source === 'ATTENDEE_BOT') {
      const botName = transcript.bot_name || transcript.transcript_metadata?.bot_id || 'SunnyAI Notetaker';
      return `Source: ${botName}`;
    }
    return `Source: ${transcript.source || 'Unknown'}`;
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatTimestamp = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const copyTranscript = async () => {
    try {
      await navigator.clipboard.writeText(transcriptText);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy transcript:', error);
      // Handle copy error silently
    }
  };

  const downloadTranscript = () => {
    const blob = new Blob([transcriptText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${transcript.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_transcript.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <DialogTitle className="text-lg font-bold font-mono">{transcript.title}</DialogTitle>
              <div className="text-xs text-gray-500 font-mono">Meeting Transcript</div>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto scrollbar-hide space-y-6">
          {/* Meeting Info */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-bold font-mono">MEETING DETAILS</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {transcript.start_time && transcript.end_time && (
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-mono">
                    {formatDateTime(transcript.start_time)} - {formatDateTime(transcript.end_time)}
                  </span>
                </div>
              )}
              {transcript.transcript_duration_seconds && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-mono">
                    Duration: {formatDuration(transcript.transcript_duration_seconds)}
                  </span>
                </div>
              )}
            </div>
            
            {transcript.meeting_url && (
              <div className="flex items-center gap-2">
                <ExternalLink className="w-4 h-4 text-gray-500" />
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => window.open(transcript.meeting_url, '_blank')}
                  className="p-0 h-auto text-sm font-mono text-blue-600 dark:text-blue-400"
                >
                  View Meeting Recording
                </Button>
              </div>
            )}

            <div className="flex items-center gap-2">
              {/* Source Badge */}
              <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                {getSourceBadge()}
              </Badge>

              {/* Status Badge - Always show as Active for transcripts */}
              <Badge className="border border-green-500 rounded px-2 py-0.5 text-[10px] text-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-50 dark:hover:bg-green-950 uppercase font-mono">
                ACTIVE
              </Badge>

              {/* Project Assignment Section */}
              <div className="flex items-center gap-2">
                {isEditingProject ? (
                  <div className="flex items-center gap-2">
                    <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                      <SelectTrigger className="w-48 h-6 text-xs bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 font-mono">
                        <SelectValue placeholder="Select project..." />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 font-mono">
                        {projects.map(project => (
                          <SelectItem
                            key={project.id}
                            value={project.id}
                            className="text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 focus:bg-stone-50 dark:focus:bg-zinc-800 font-mono text-xs"
                          >
                            {project.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      size="sm"
                      onClick={handleProjectChange}
                      disabled={!selectedProjectId}
                      className="h-6 px-2 text-xs bg-green-600 hover:bg-green-700 text-white font-mono"
                    >
                      Save
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsEditingProject(false)}
                      className="h-6 px-2 text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
                    >
                      Cancel
                    </Button>
                    {transcript.project_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRemoveProject}
                        className="h-6 px-2 text-xs border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-950 font-mono"
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {transcript.project_id ? (
                      <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                        Project: {getCurrentProjectName()}
                      </Badge>
                    ) : (
                      <Badge className="border border-red-500 rounded px-2 py-0.5 text-[10px] text-red-500 bg-red-50 dark:bg-red-950 hover:bg-red-50 dark:hover:bg-red-950 uppercase font-mono">
                        NO PROJECT
                      </Badge>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsEditingProject(true)}
                      className="h-6 px-2 text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
                    >
                      <Edit3 className="w-3 h-3" />
                    </Button>
                  </div>
                )}
              </div>

              {transcript.transcript_retrieved_at && (
                <Badge variant="outline" className="px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                  Retrieved: {formatDateTime(transcript.transcript_retrieved_at)}
                </Badge>
              )}
              {transcript.transcript_metadata?.word_count && (
                <Badge variant="outline" className="px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                  {transcript.transcript_metadata.word_count} words
                </Badge>
              )}
            </div>
          </div>

          {/* Transcript Summary */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4">
            <h3 className="text-sm font-bold font-mono mb-2">SUMMARY</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 font-mono leading-relaxed">
              {transcript.transcript_summary}
            </p>
          </div>

          {/* Participant Analytics */}
          {transcript.transcript_participants && transcript.transcript_segments && transcript.transcript_duration_seconds && (
            <ParticipantAnalytics
              participants={transcript.transcript_participants}
              segments={transcript.transcript_segments}
              duration={transcript.transcript_duration_seconds}
            />
          )}

          {/* Full Transcript */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold font-mono">FULL TRANSCRIPT</h3>
              <div className="flex items-center gap-2">
                {transcript.transcript_audio_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(transcript.transcript_audio_url, '_blank')}
                    className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                  >
                    <Play className="w-3 h-3 mr-1" />
                    Audio
                  </Button>
                )}
                {/* <Button
                  variant="outline"
                  size="sm"
                  onClick={copyTranscript}
                  className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                >
                  <Copy className="w-3 h-3 mr-1" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={downloadTranscript}
                  className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                >
                  <Download className="w-3 h-3 mr-1" />
                  Download
                </Button> */}
              </div>
            </div>
            
            {/* Speaker Segments */}
            {transcript.transcript_segments && transcript.transcript_segments.length > 0 ? (
              <div className="bg-white dark:bg-zinc-900 rounded-lg p-4 max-h-96 overflow-y-auto scrollbar-hide border border-[#4a5565] dark:border-zinc-700">
                <div className="space-y-3">
                                          {transcript.transcript_segments.map((segment: Record<string, unknown>, index: number) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <Badge variant="outline" className="text-xs font-mono">
                          {segment.speaker || 'Unknown'}
                        </Badge>
                      </div>
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 font-mono mb-1">
                          {formatTimestamp(segment.start_time || 0)}
                        </div>
                        <div className="text-sm font-mono leading-relaxed">
                          {segment.text}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-zinc-900 rounded-lg p-4 border border-[#4a5565] dark:border-zinc-700">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <div className="text-sm text-gray-700 dark:text-gray-300 font-mono leading-relaxed whitespace-pre-wrap">
                    {transcriptText}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* AI Actions */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4">
            <h3 className="text-sm font-bold font-mono mb-3">AI ACTIONS</h3>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Extract Key Points
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Generate Summary
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Find Related Documents
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Create Notes
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TranscriptModal; 