import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageSquare, Clock, Calendar, ExternalLink, Copy, Download } from 'lucide-react';
import type { TranscriptMetadata } from '@/types';

interface TranscriptDetailProps {
  transcript: {
    id: string;
    title: string;
    transcript: string;
    transcript_summary: string;
    transcript_metadata: TranscriptMetadata;
    transcript_duration_seconds: number;
    transcript_retrieved_at: string;
    meeting_url?: string;
    start_time: string;
    end_time: string;
  };
  onBack: () => void;
}

const TranscriptDetail: React.FC<TranscriptDetailProps> = ({ transcript, onBack }) => {
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

  const copyTranscript = async () => {
    try {
      await navigator.clipboard.writeText(transcript.transcript);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy transcript:', error);
      // Failed to copy transcript
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
    <div className="flex-1 flex flex-col overflow-y-auto scrollbar-hide">
      <div className="p-8 pb-2">
        <button onClick={onBack} className="mb-4 text-xs text-gray-500 hover:underline font-mono">
          &lt; Data Feed
        </button>
        
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-mono">{transcript.title}</h1>
            <div className="text-xs text-gray-500 font-mono">Data Feed &gt; Meeting Transcript</div>
          </div>
        </div>

        {/* Meeting Info */}
        <Card className="mb-6 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono">MEETING DETAILS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  {formatDateTime(transcript.start_time)} - {formatDateTime(transcript.end_time)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  Duration: {formatDuration(transcript.transcript_duration_seconds)}
                </span>
              </div>
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
              <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                Retrieved: {formatDateTime(transcript.transcript_retrieved_at)}
              </Badge>
              {transcript.transcript_metadata?.word_count && (
                <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono">
                  {transcript.transcript_metadata.word_count} words
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Transcript Summary */}
        <Card className="mb-6 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono">SUMMARY</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400 font-mono leading-relaxed">
              {transcript.transcript_summary}
            </p>
          </CardContent>
        </Card>

        {/* Full Transcript */}
        <Card className="mb-6 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-mono">FULL TRANSCRIPT</CardTitle>
              <div className="flex items-center gap-2">
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
          </CardHeader>
          <CardContent>
            <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4 max-h-96 overflow-y-auto scrollbar-hide">
              <pre className="text-sm text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">
                {transcript.transcript}
              </pre>
            </div>
          </CardContent>
        </Card>

        {/* AI Actions */}
        <Card className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono">AI ACTIONS</CardTitle>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TranscriptDetail; 