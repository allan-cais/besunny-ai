import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, MessageSquare } from 'lucide-react';
import { apiKeyService } from '@/lib/api-keys';

const DEFAULT_BOT_NAME = 'Kirit Notetaker';
const DEFAULT_BOT_MESSAGE = 'Hi, I’m here to transcribe this meeting!';

const SendBotToMeetingCard: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [meetingUrl, setMeetingUrl] = useState('');
  const [botName, setBotName] = useState(DEFAULT_BOT_NAME);
  const [botMessage, setBotMessage] = useState(DEFAULT_BOT_MESSAGE);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleOpen = () => {
    setOpen(true);
    setSuccess(null);
    setError(null);
  };

  const handleClose = () => {
    setOpen(false);
    setMeetingUrl('');
    setBotName(DEFAULT_BOT_NAME);
    setBotMessage(DEFAULT_BOT_MESSAGE);
    setLoading(false);
    setSuccess(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!meetingUrl.trim()) {
      setError('Meeting URL is required.');
      return;
    }
    if (!botName.trim()) {
      setError('Bot name is required.');
      return;
    }
    setLoading(true);
    try {
      await apiKeyService.sendBotToMeeting(meetingUrl.trim(), {
        bot_name: botName.trim(),
        bot_chat_message: {
          to: 'everyone',
          message: botMessage.trim(),
        },
      });
      setSuccess('Bot has been sent to the meeting!');
      setMeetingUrl('');
      setBotName(DEFAULT_BOT_NAME);
      setBotMessage(DEFAULT_BOT_MESSAGE);
    } catch (err: any) {
      setError(err.message || 'Failed to send bot.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 mb-8">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <CardTitle className="text-base font-bold">Send Bot to Meeting</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Button onClick={handleOpen} className="font-mono text-xs bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-md shadow-md">
          Send Bot to Meeting
        </Button>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Send Bot to Meeting</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert className="mb-2 border-red-500 bg-red-50 dark:bg-red-900/20">
                  <AlertDescription className="text-red-800 dark:text-red-200">{error}</AlertDescription>
                </Alert>
              )}
              {success && (
                <Alert className="mb-2 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <AlertDescription className="text-green-800 dark:text-green-200">{success}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-2">
                <Label htmlFor="meeting-url">Meeting URL</Label>
                <Input
                  id="meeting-url"
                  type="url"
                  value={meetingUrl}
                  onChange={e => setMeetingUrl(e.target.value)}
                  placeholder="https://zoom.us/j/123?pwd=456"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot-name">Bot Name</Label>
                <Input
                  id="bot-name"
                  type="text"
                  value={botName}
                  onChange={e => setBotName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot-message">Bot Chat Message (optional)</Label>
                <Input
                  id="bot-message"
                  type="text"
                  value={botMessage}
                  onChange={e => setBotMessage(e.target.value)}
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleClose} disabled={loading}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading} className="bg-purple-600 hover:bg-purple-700 text-white">
                  {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Send Bot
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default SendBotToMeetingCard; 