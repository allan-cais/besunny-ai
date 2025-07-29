import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageSquare, Clock, Calendar, ExternalLink, Copy, Download, X, Play } from 'lucide-react';
import ParticipantAnalytics from './ParticipantAnalytics';

interface TranscriptModalProps {
  transcript: {
    id: string;
    title: string;
    transcript: string;
    transcript_summary?: string;
    transcript_metadata?: any;
    transcript_duration_seconds?: number;
    transcript_retrieved_at?: string;
    meeting_url?: string;
    start_time?: string;
    end_time?: string;
    transcript_audio_url?: string;
    transcript_segments?: any[];
    transcript_participants?: string[];
  } | null;
  isOpen: boolean;
  onClose: () => void;
}

const TranscriptModal: React.FC<TranscriptModalProps> = ({ transcript, isOpen, onClose }) => {
  if (!transcript) return null;

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
      await navigator.clipboard.writeText(transcript.transcript);
      // You could add a toast notification here
    } catch (error) {
      // Handle copy error silently
    }
  };

  const downloadTranscript = () => {
    const blob = new Blob([transcript.transcript], { type: 'text/plain' });
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
                <Button
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
                </Button>
              </div>
            </div>
            
            {/* Speaker Segments */}
            {transcript.transcript_segments && transcript.transcript_segments.length > 0 ? (
              <div className="bg-white dark:bg-zinc-900 rounded-lg p-4 max-h-96 overflow-y-auto scrollbar-hide border border-[#4a5565] dark:border-zinc-700">
                <div className="space-y-3">
                  {transcript.transcript_segments.map((segment: any, index: number) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/20 flex items-center justify-center">
                          <span className="text-xs font-bold text-purple-600 dark:text-purple-400">
                            {segment.speaker ? segment.speaker.charAt(0).toUpperCase() : '?'}
                          </span>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                            {segment.speaker || 'Unknown Speaker'}
                          </span>
                          <span className="text-xs text-gray-500 font-mono">
                            {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                          {segment.text}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-zinc-900 rounded-lg p-4 max-h-96 overflow-y-auto scrollbar-hide border border-[#4a5565] dark:border-zinc-700">
                <pre className="text-sm text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">
                  {transcript.transcript}
                </pre>
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
                Extract Action Items
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
                Find Key Decisions
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Create Follow-ups
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TranscriptModal; 