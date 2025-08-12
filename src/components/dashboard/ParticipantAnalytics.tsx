import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Users, MessageSquare, Clock, TrendingUp } from 'lucide-react';

interface ParticipantAnalyticsProps {
  participants: string[];
  segments: Record<string, unknown>[];
  duration: number;
}

const ParticipantAnalytics: React.FC<ParticipantAnalyticsProps> = ({
  participants,
  segments,
  duration
}) => {
  // Calculate participant statistics
  const participantStats = participants.map(participant => {
    const participantSegments = segments.filter(segment => segment.speaker === participant);
    const totalWords = participantSegments.reduce((sum, segment) => 
      sum + (segment.text?.split(' ').length || 0), 0
    );
    const totalDuration = participantSegments.reduce((sum, segment) => 
      sum + ((segment.end || 0) - (segment.start || 0)), 0
    );
    
    return {
      name: participant,
      segments: participantSegments.length,
      words: totalWords,
      duration: totalDuration,
      percentage: (totalDuration / duration) * 100
    };
  }).sort((a, b) => b.percentage - a.percentage);

  const totalWords = segments.reduce((sum, segment) => 
    sum + (segment.text?.split(' ').length || 0), 0
  );

  return (
    <Card className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono flex items-center gap-2">
          <Users className="w-4 h-4" />
          PARTICIPANT ANALYTICS
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {participants.length}
            </div>
            <div className="text-xs text-gray-500 font-mono">Participants</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {segments.length}
            </div>
            <div className="text-xs text-gray-500 font-mono">Segments</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {totalWords}
            </div>
            <div className="text-xs text-gray-500 font-mono">Total Words</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {Math.round(duration / 60)}
            </div>
            <div className="text-xs text-gray-500 font-mono">Minutes</div>
          </div>
        </div>

        {/* Participant Breakdown */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold font-mono text-gray-700 dark:text-gray-300">
            PARTICIPATION BREAKDOWN
          </h4>
          {participantStats.map((participant, index) => (
            <div key={participant.name} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/20 flex items-center justify-center">
                    <span className="text-xs font-bold text-purple-600 dark:text-purple-400">
                      {participant.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {participant.name}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {participant.segments} segments
                  </Badge>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {participant.percentage.toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500 font-mono">
                    {participant.words} words
                  </div>
                </div>
              </div>
              <Progress value={participant.percentage} className="h-2" />
            </div>
          ))}
        </div>

        {/* Engagement Insights */}
        <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-3">
          <h4 className="text-xs font-bold font-mono text-gray-700 dark:text-gray-300 mb-2">
            ENGAGEMENT INSIGHTS
          </h4>
          <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-3 h-3" />
              <span>Most active participant: {participantStats[0]?.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <MessageSquare className="w-3 h-3" />
              <span>Average words per participant: {Math.round(totalWords / participants.length)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-3 h-3" />
              <span>Average speaking time: {Math.round(duration / participants.length / 60)} minutes</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ParticipantAnalytics; 