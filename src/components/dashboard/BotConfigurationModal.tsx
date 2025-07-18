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
  // Basic settings only
  bot_name: string;
  bot_chat_message: string;
  chat_message_recipient: 'everyone' | 'specific_user' | 'everyone_but_host';
  to_user_uuid?: string;
  
  // Basic features
  auto_join: boolean;
  recording_enabled: boolean;
  transcription_language: string;
  
  // Advanced features - commented out, will use defaults
  /*
  transcription_settings?: {
    deepgram?: {
      language?: string;
      model?: string;
      smart_format?: boolean;
    };
  };
  
  recording_settings?: {
    format?: 'mp4' | 'webm';
    view?: 'speaker_view' | 'gallery_view';
    resolution?: '720p' | '1080p' | '1440p';
  };
  
  teams_settings?: {
    use_login?: boolean;
  };
  
  debug_settings?: {
    create_debug_recording?: boolean;
  };
  
  automatic_leave_settings?: {
    leave_after_minutes?: number;
    leave_when_empty?: boolean;
  };
  
  webhooks?: Array<{
    url: string;
    triggers: string[];
  }>;
  
  metadata?: Record<string, any>;
  
  deduplication_key?: string;
  
  custom_settings?: Record<string, any>;
  */
}

interface BotConfigurationModalProps {
  meeting: Meeting | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeploy: (configuration: BotConfiguration) => Promise<void>;
  deploying: boolean;
}

const DEFAULT_CONFIGURATION: BotConfiguration = {
  bot_name: 'Sunny AI Assistant',
  bot_chat_message: 'Hi, I\'m here to transcribe this meeting!',
  chat_message_recipient: 'everyone',
  auto_join: true,
  recording_enabled: true,
  transcription_language: 'en-US',
  // Advanced settings commented out - will use Attendee API defaults
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
      <DialogContent className="sm:max-w-[500px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono">
        <DialogHeader>
          <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-lg font-bold flex items-center">
            <Bot className="w-5 h-5 mr-2" />
            Configure Meeting Bot
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-sm">
            Configure your transcription bot for: <span className="font-semibold">{meeting.title}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Basic Bot Configuration */}
          <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                <Bot className="w-4 h-4 mr-2" />
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
                    <SelectItem value="specific_user">Specific user</SelectItem>
                    <SelectItem value="everyone_but_host">Everyone except host</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Specific User UUID (if needed) */}
              {configuration.chat_message_recipient === 'specific_user' && (
                <div className="space-y-2">
                  <Label htmlFor="user-uuid" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    USER UUID
                  </Label>
                  <Input
                    id="user-uuid"
                    value={configuration.to_user_uuid || ''}
                    onChange={(e) => updateConfiguration('to_user_uuid', e.target.value)}
                    placeholder="Enter user UUID"
                    className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600"
                  />
                </div>
              )}

              {/* Transcription Language */}
              <div className="space-y-2">
                <Label htmlFor="transcription-language" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                  TRANSCRIPTION LANGUAGE
                </Label>
                <Select
                  value={configuration.transcription_language}
                  onValueChange={(value) => updateConfiguration('transcription_language', value)}
                >
                  <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                    {LANGUAGE_OPTIONS.map(lang => (
                      <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Basic Bot Features */}
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
          <Card className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <CardContent className="pt-4">
              <div className="flex items-start space-x-2">
                <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-blue-800 dark:text-blue-200">
                  <p className="font-medium mb-1">Basic Bot Configuration</p>
                  <p>This configuration uses essential Attendee API features. Advanced options like transcription models, recording settings, webhooks, and automatic leave settings will use Attendee API defaults.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-2 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="text-sm"
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleDeploy}
            disabled={deploying}
            className="text-sm bg-blue-600 hover:bg-blue-700 text-white"
          >
            {deploying ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Deploying...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Deploy Bot
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default BotConfigurationModal; 