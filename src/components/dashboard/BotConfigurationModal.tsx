import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Bot, 
  MessageSquare, 
  Settings, 
  Send, 
  Loader2,
  Info,
  CheckCircle
} from 'lucide-react';
import { Meeting } from '@/lib/calendar';

interface BotConfiguration {
  bot_name: string;
  bot_chat_message: string;
  chat_message_recipient: 'everyone' | 'host' | 'none';
  auto_join: boolean;
  recording_enabled: boolean;
  transcription_language: string;
  custom_settings?: Record<string, any>;
}

interface BotConfigurationModalProps {
  meeting: Meeting | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeploy: (configuration: BotConfiguration) => Promise<void>;
  deploying: boolean;
}

const DEFAULT_CONFIGURATION: BotConfiguration = {
  bot_name: 'Kirit Notetaker',
  bot_chat_message: 'Hi, I\'m here to transcribe this meeting!',
  chat_message_recipient: 'everyone',
  auto_join: true,
  recording_enabled: true,
  transcription_language: 'en-US',
};

const LANGUAGE_OPTIONS = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'es-ES', label: 'Spanish' },
  { value: 'fr-FR', label: 'French' },
  { value: 'de-DE', label: 'German' },
  { value: 'it-IT', label: 'Italian' },
  { value: 'pt-BR', label: 'Portuguese (Brazil)' },
  { value: 'ja-JP', label: 'Japanese' },
  { value: 'ko-KR', label: 'Korean' },
  { value: 'zh-CN', label: 'Chinese (Simplified)' },
];

const BotConfigurationModal: React.FC<BotConfigurationModalProps> = ({
  meeting,
  open,
  onOpenChange,
  onDeploy,
  deploying
}) => {
  const [configuration, setConfiguration] = useState<BotConfiguration>(DEFAULT_CONFIGURATION);

  const handleDeploy = async () => {
    await onDeploy(configuration);
  };

  const updateConfiguration = (key: keyof BotConfiguration, value: any) => {
    setConfiguration(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (!meeting) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono">
        <DialogHeader>
          <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-lg font-bold flex items-center">
            <Bot className="w-5 h-5 mr-2" />
            Configure Meeting Bot
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-sm">
            Configure your transcription bot for: <span className="font-semibold">{meeting.title}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 font-mono">
          {/* Meeting Info */}
          <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50">MEETING DETAILS</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-400">Title:</span>
                <span className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">{meeting.title}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-400">Time:</span>
                <span className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                  {new Date(meeting.start_time).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-400">Platform:</span>
                <Badge variant="outline" className="text-xs">
                  {meeting.meeting_url?.includes('zoom') ? 'Zoom' : 
                   meeting.meeting_url?.includes('teams') ? 'Teams' : 
                   meeting.meeting_url?.includes('meet') ? 'Google Meet' : 'Other'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Bot Configuration */}
          <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                <Settings className="w-4 h-4 mr-2" />
                BOT CONFIGURATION
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Bot Name */}
              <div className="space-y-2">
                <Label htmlFor="bot-name" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                  BOT NAME
                </Label>
                <Input
                  id="bot-name"
                  value={configuration.bot_name}
                  onChange={(e) => updateConfiguration('bot_name', e.target.value)}
                  placeholder="Enter bot name"
                  className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600"
                />
              </div>

              {/* Chat Message */}
              <div className="space-y-2">
                <Label htmlFor="chat-message" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                  CHAT MESSAGE
                </Label>
                <Textarea
                  id="chat-message"
                  value={configuration.bot_chat_message}
                  onChange={(e) => updateConfiguration('bot_chat_message', e.target.value)}
                  placeholder="Message to send when bot joins"
                  className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600"
                  rows={3}
                />
              </div>

              {/* Chat Message Recipient */}
              <div className="space-y-2">
                <Label htmlFor="chat-recipient" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                  MESSAGE RECIPIENT
                </Label>
                <Select
                  value={configuration.chat_message_recipient}
                  onValueChange={(value) => updateConfiguration('chat_message_recipient', value)}
                >
                  <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                    <SelectItem value="everyone">Everyone in meeting</SelectItem>
                    <SelectItem value="host">Meeting host only</SelectItem>
                    <SelectItem value="none">Don't send message</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Transcription Language */}
              <div className="space-y-2">
                <Label htmlFor="language" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                  TRANSCRIPTION LANGUAGE
                </Label>
                <Select
                  value={configuration.transcription_language}
                  onValueChange={(value) => updateConfiguration('transcription_language', value)}
                >
                  <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600 max-h-48">
                    {LANGUAGE_OPTIONS.map(lang => (
                      <SelectItem key={lang.value} value={lang.value}>
                        {lang.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Bot Features */}
          <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                <CheckCircle className="w-4 h-4 mr-2" />
                BOT FEATURES
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    AUTO-JOIN MEETING
                  </Label>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Bot will automatically join when meeting starts
                  </p>
                </div>
                <Switch
                  checked={configuration.auto_join}
                  onCheckedChange={(checked) => updateConfiguration('auto_join', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    ENABLE RECORDING
                  </Label>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Record audio for transcription
                  </p>
                </div>
                <Switch
                  checked={configuration.recording_enabled}
                  onCheckedChange={(checked) => updateConfiguration('recording_enabled', checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Info Section */}
          <div className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <p className="text-xs font-medium text-blue-800 dark:text-blue-200">REAL-TIME TRANSCRIPTION</p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                The bot will capture transcription in real-time but only display the final transcript in your data feed once the meeting is complete.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={deploying}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              CANCEL
            </Button>
            <Button
              onClick={handleDeploy}
              disabled={deploying || !configuration.bot_name.trim()}
              className="font-mono text-xs bg-purple-600 hover:bg-purple-700 text-white px-6 py-3"
            >
              {deploying ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  DEPLOYING...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  DEPLOY BOT
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default BotConfigurationModal; 