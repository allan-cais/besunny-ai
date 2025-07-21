import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { attendeePollingService } from '@/lib/attendee-polling';
import { RefreshCw, Play, Pause, AlertCircle, CheckCircle } from 'lucide-react';

interface PollingStatus {
  id: string;
  title: string;
  bot_status: string;
  last_polled_at: string | null;
  next_poll_at: string | null;
  polling_enabled: boolean;
  polling_status: string;
}

const PollingDebugPanel: React.FC = () => {
  const { user } = useAuth();
  const [pollingStatus, setPollingStatus] = useState<PollingStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastPollTime, setLastPollTime] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const loadPollingStatus = async () => {
    if (!user?.id) return;

    try {
      const { data, error } = await supabase
        .from('polling_status')
        .select('*')
        .order('next_poll_at', { ascending: true });

      if (error) {
        console.error('Error loading polling status:', error);
        return;
      }

      setPollingStatus(data || []);
    } catch (error) {
      console.error('Error loading polling status:', error);
    }
  };

  const triggerManualPoll = async () => {
    if (!user?.id) return;

    try {
      setIsPolling(true);
      setLoading(true);
      console.log('Triggering manual poll...');
      
      const results = await attendeePollingService.pollAllMeetings();
      console.log('Manual poll results:', results);
      
      setLastPollTime(new Date());
      await loadPollingStatus();
    } catch (error) {
      console.error('Error during manual poll:', error);
    } finally {
      setIsPolling(false);
      setLoading(false);
    }
  };

  const triggerMeetingPoll = async (meetingId: string) => {
    if (!user?.id) return;

    try {
      setLoading(true);
      console.log('Triggering poll for meeting:', meetingId);
      
      const result = await attendeePollingService.pollMeeting(meetingId);
      console.log('Meeting poll result:', result);
      
      setLastPollTime(new Date());
      await loadPollingStatus();
    } catch (error) {
      console.error('Error polling meeting:', error);
    } finally {
      setLoading(false);
    }
  };

  const fixPollingForMeeting = async (meetingId: string) => {
    if (!user?.id) return;

    try {
      setLoading(true);
      
      // Call the database function to fix polling for this meeting
      const { data, error } = await supabase.rpc('trigger_meeting_poll', {
        meeting_id: meetingId
      });

      if (error) {
        console.error('Error fixing polling:', error);
        return;
      }

      console.log('Fixed polling for meeting:', data);
      await loadPollingStatus();
    } catch (error) {
      console.error('Error fixing polling:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPollingStatus();
  }, [user?.id]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready_for_polling':
        return <Badge className="bg-green-100 text-green-800">Ready</Badge>;
      case 'waiting':
        return <Badge className="bg-yellow-100 text-yellow-800">Waiting</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{status}</Badge>;
    }
  };

  const getBotStatusBadge = (status: string) => {
    switch (status) {
      case 'bot_scheduled':
        return <Badge className="bg-blue-100 text-blue-800">Scheduled</Badge>;
      case 'bot_joined':
        return <Badge className="bg-green-100 text-green-800">Joined</Badge>;
      case 'transcribing':
        return <Badge className="bg-yellow-100 text-yellow-800">Transcribing</Badge>;
      case 'completed':
        return <Badge className="bg-purple-100 text-purple-800">Completed</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{status}</Badge>;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5" />
          Bot Polling Debug Panel
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Manual Poll Controls */}
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
          <Button 
            onClick={triggerManualPoll} 
            disabled={loading || isPolling}
            className="flex items-center gap-2"
          >
            {isPolling ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isPolling ? 'Polling...' : 'Trigger Manual Poll'}
          </Button>
          
          <Button 
            onClick={loadPollingStatus} 
            disabled={loading}
            variant="outline"
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh Status
          </Button>

          {lastPollTime && (
            <div className="text-sm text-gray-600">
              Last poll: {lastPollTime.toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Polling Status */}
        <div className="space-y-2">
          <h3 className="font-semibold text-sm">Active Polling Meetings ({pollingStatus.length})</h3>
          
          {pollingStatus.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>No meetings currently being polled</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {pollingStatus.map((meeting) => (
                <div key={meeting.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{meeting.title}</div>
                    <div className="flex items-center gap-2 mt-1">
                      {getBotStatusBadge(meeting.bot_status)}
                      {getStatusBadge(meeting.polling_status)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Last polled: {meeting.last_polled_at ? new Date(meeting.last_polled_at).toLocaleString() : 'Never'}
                      {meeting.next_poll_at && (
                        <span className="ml-4">
                          Next poll: {new Date(meeting.next_poll_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => triggerMeetingPoll(meeting.id)}
                      disabled={loading}
                    >
                      Poll Now
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => fixPollingForMeeting(meeting.id)}
                      disabled={loading}
                    >
                      Fix Polling
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Debug Info */}
        <div className="text-xs text-gray-500 space-y-1">
          <div>User ID: {user?.id}</div>
          <div>Polling enabled meetings: {pollingStatus.filter(m => m.polling_enabled).length}</div>
          <div>Ready for polling: {pollingStatus.filter(m => m.polling_status === 'ready_for_polling').length}</div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PollingDebugPanel; 