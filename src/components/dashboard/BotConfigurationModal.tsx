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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bot, 
  MessageSquare, 
  Settings, 
  Send, 
  Loader2,
  Info,
  CheckCircle,
  Mic,
  Video,
  Webhook,
  Database,
  Shield,
  Clock,
  FileText,
  Users,
  Volume2
} from 'lucide-react';
import { Meeting } from '@/lib/calendar';

interface BotConfiguration {
  // Basic settings
  bot_name: string;
  bot_chat_message: string;
  chat_message_recipient: 'everyone' | 'specific_user' | 'everyone_but_host';
  to_user_uuid?: string;
  
  // Advanced features
  auto_join: boolean;
  recording_enabled: boolean;
  transcription_language: string;
  
  // Transcription settings
  transcription_settings?: {
    deepgram?: {
      language?: string;
      model?: string;
      smart_format?: boolean;
    };
  };
  
  // Recording settings
  recording_settings?: {
    format?: 'mp4' | 'webm';
    view?: 'speaker_view' | 'gallery_view';
    resolution?: '720p' | '1080p' | '1440p';
  };
  
  // Teams settings
  teams_settings?: {
    use_login?: boolean;
  };
  
  // Debug settings
  debug_settings?: {
    create_debug_recording?: boolean;
  };
  
  // Automatic leave settings
  automatic_leave_settings?: {
    leave_after_minutes?: number;
    leave_when_empty?: boolean;
  };
  
  // Webhooks
  webhooks?: Array<{
    url: string;
    triggers: string[];
  }>;
  
  // Metadata
  metadata?: Record<string, any>;
  
  // Deduplication
  deduplication_key?: string;
  
  // Custom settings
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
  bot_name: 'Sunny AI Assistant',
  bot_chat_message: 'Hi, I\'m here to transcribe this meeting!',
  chat_message_recipient: 'everyone',
  auto_join: true,
  recording_enabled: true,
  transcription_language: 'en-US',
  transcription_settings: {
    deepgram: {
      language: 'en-US',
      model: 'nova-2',
      smart_format: true
    }
  },
  recording_settings: {
    format: 'mp4',
    view: 'speaker_view',
    resolution: '1080p'
  },
  teams_settings: {
    use_login: false
  },
  debug_settings: {
    create_debug_recording: false
  },
  automatic_leave_settings: {
    leave_after_minutes: 0, // 0 = don't auto-leave
    leave_when_empty: false
  },
  metadata: {
    meeting_title: '',
    project: '',
    tags: []
  }
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

const TRANSCRIPTION_MODELS = [
  { value: 'nova-2', label: 'Nova 2 (Latest)' },
  { value: 'nova', label: 'Nova' },
  { value: 'enhanced', label: 'Enhanced' },
  { value: 'base', label: 'Base' }
];

const RECORDING_VIEWS = [
  { value: 'speaker_view', label: 'Speaker View' },
  { value: 'gallery_view', label: 'Gallery View' }
];

const RECORDING_RESOLUTIONS = [
  { value: '720p', label: '720p' },
  { value: '1080p', label: '1080p' },
  { value: '1440p', label: '1440p' }
];

const WEBHOOK_TRIGGERS = [
  'bot_created',
  'bot_joined',
  'bot_left',
  'transcription_started',
  'transcription_completed',
  'recording_started',
  'recording_completed',
  'chat_message_sent',
  'participant_joined',
  'participant_left'
];

const BotConfigurationModal: React.FC<BotConfigurationModalProps> = ({
  meeting,
  open,
  onOpenChange,
  onDeploy,
  deploying
}) => {
  const [configuration, setConfiguration] = useState<BotConfiguration>(DEFAULT_CONFIGURATION);
  const [activeTab, setActiveTab] = useState('basic');

  const handleDeploy = async () => {
    await onDeploy(configuration);
  };

  const updateConfiguration = (key: keyof BotConfiguration, value: any) => {
    setConfiguration(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const updateNestedConfiguration = (path: string[], value: any) => {
    setConfiguration(prev => {
      const newConfig = { ...prev };
      let current: any = newConfig;
      
      for (let i = 0; i < path.length - 1; i++) {
        if (!current[path[i]]) {
          current[path[i]] = {};
        }
        current = current[path[i]];
      }
      
      current[path[path.length - 1]] = value;
      return newConfig;
    });
  };

  const addWebhook = () => {
    const newWebhook = {
      url: '',
      triggers: ['bot_joined']
    };
    setConfiguration(prev => ({
      ...prev,
      webhooks: [...(prev.webhooks || []), newWebhook]
    }));
  };

  const updateWebhook = (index: number, field: 'url' | 'triggers', value: any) => {
    setConfiguration(prev => ({
      ...prev,
      webhooks: prev.webhooks?.map((webhook, i) => 
        i === index ? { ...webhook, [field]: value } : webhook
      ) || []
    }));
  };

  const removeWebhook = (index: number) => {
    setConfiguration(prev => ({
      ...prev,
      webhooks: prev.webhooks?.filter((_, i) => i !== index) || []
    }));
  };

  if (!meeting) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono">
        <DialogHeader>
          <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-lg font-bold flex items-center">
            <Bot className="w-5 h-5 mr-2" />
            Configure Advanced Meeting Bot
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-sm">
            Configure your transcription bot for: <span className="font-semibold">{meeting.title}</span>
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
            <TabsTrigger value="basic" className="text-xs">Basic</TabsTrigger>
            <TabsTrigger value="transcription" className="text-xs">Transcription</TabsTrigger>
            <TabsTrigger value="recording" className="text-xs">Recording</TabsTrigger>
            <TabsTrigger value="advanced" className="text-xs">Advanced</TabsTrigger>
            <TabsTrigger value="webhooks" className="text-xs">Webhooks</TabsTrigger>
          </TabsList>

          {/* Basic Settings Tab */}
          <TabsContent value="basic" className="space-y-4 mt-4">
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

                {/* Deduplication Key */}
                <div className="space-y-2">
                  <Label htmlFor="deduplication-key" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    DEDUPLICATION KEY (Optional)
                  </Label>
                  <Input
                    id="deduplication-key"
                    value={configuration.deduplication_key || ''}
                    onChange={(e) => updateConfiguration('deduplication_key', e.target.value)}
                    placeholder="Prevent duplicate bots"
                    className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600"
                  />
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    If a bot with this key already exists, no new bot will be created
                  </p>
                </div>
              </CardContent>
            </Card>

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
          </TabsContent>

          {/* Transcription Settings Tab */}
          <TabsContent value="transcription" className="space-y-4 mt-4">
            <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                  <Mic className="w-4 h-4 mr-2" />
                  TRANSCRIPTION SETTINGS
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Transcription Language */}
                <div className="space-y-2">
                  <Label htmlFor="transcription-language" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    LANGUAGE
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

                {/* Deepgram Model */}
                <div className="space-y-2">
                  <Label htmlFor="transcription-model" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    TRANSCRIPTION MODEL
                  </Label>
                  <Select
                    value={configuration.transcription_settings?.deepgram?.model || 'nova-2'}
                    onValueChange={(value) => updateNestedConfiguration(['transcription_settings', 'deepgram', 'model'], value)}
                  >
                    <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                      {TRANSCRIPTION_MODELS.map(model => (
                        <SelectItem key={model.value} value={model.value}>{model.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Smart Format */}
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                      SMART FORMAT
                    </Label>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Automatically format numbers, dates, and punctuation
                    </p>
                  </div>
                  <Switch
                    checked={configuration.transcription_settings?.deepgram?.smart_format || false}
                    onCheckedChange={(checked) => updateNestedConfiguration(['transcription_settings', 'deepgram', 'smart_format'], checked)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recording Settings Tab */}
          <TabsContent value="recording" className="space-y-4 mt-4">
            <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                  <Video className="w-4 h-4 mr-2" />
                  RECORDING SETTINGS
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Recording Format */}
                <div className="space-y-2">
                  <Label htmlFor="recording-format" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    FORMAT
                  </Label>
                  <Select
                    value={configuration.recording_settings?.format || 'mp4'}
                    onValueChange={(value) => updateNestedConfiguration(['recording_settings', 'format'], value)}
                  >
                    <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                      <SelectItem value="mp4">MP4</SelectItem>
                      <SelectItem value="webm">WebM</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Recording View */}
                <div className="space-y-2">
                  <Label htmlFor="recording-view" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    VIEW
                  </Label>
                  <Select
                    value={configuration.recording_settings?.view || 'speaker_view'}
                    onValueChange={(value) => updateNestedConfiguration(['recording_settings', 'view'], value)}
                  >
                    <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                      {RECORDING_VIEWS.map(view => (
                        <SelectItem key={view.value} value={view.value}>{view.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Recording Resolution */}
                <div className="space-y-2">
                  <Label htmlFor="recording-resolution" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                    RESOLUTION
                  </Label>
                  <Select
                    value={configuration.recording_settings?.resolution || '1080p'}
                    onValueChange={(value) => updateNestedConfiguration(['recording_settings', 'resolution'], value)}
                  >
                    <SelectTrigger className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
                      {RECORDING_RESOLUTIONS.map(res => (
                        <SelectItem key={res.value} value={res.value}>{res.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Advanced Settings Tab */}
          <TabsContent value="advanced" className="space-y-4 mt-4">
            <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                  <Settings className="w-4 h-4 mr-2" />
                  ADVANCED SETTINGS
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Teams Settings */}
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                      USE TEAMS LOGIN
                    </Label>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Use Microsoft Teams login for authentication
                    </p>
                  </div>
                  <Switch
                    checked={configuration.teams_settings?.use_login || false}
                    onCheckedChange={(checked) => updateNestedConfiguration(['teams_settings', 'use_login'], checked)}
                  />
                </div>

                {/* Debug Recording */}
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                      CREATE DEBUG RECORDING
                    </Label>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Create additional debug recording for troubleshooting
                    </p>
                  </div>
                  <Switch
                    checked={configuration.debug_settings?.create_debug_recording || false}
                    onCheckedChange={(checked) => updateNestedConfiguration(['debug_settings', 'create_debug_recording'], checked)}
                  />
                </div>

                {/* Auto Leave Settings */}
                <div className="space-y-4 border-t pt-4">
                  <h4 className="text-xs font-bold text-[#4a5565] dark:text-zinc-50">AUTOMATIC LEAVE SETTINGS</h4>
                  
                  <div className="space-y-2">
                    <Label htmlFor="leave-after" className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                      LEAVE AFTER MINUTES (0 = don't auto-leave)
                    </Label>
                    <Input
                      id="leave-after"
                      type="number"
                      min="0"
                      value={configuration.automatic_leave_settings?.leave_after_minutes || 0}
                      onChange={(e) => updateNestedConfiguration(['automatic_leave_settings', 'leave_after_minutes'], parseInt(e.target.value) || 0)}
                      className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                        LEAVE WHEN EMPTY
                      </Label>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        Leave meeting when no other participants remain
                      </p>
                    </div>
                    <Switch
                      checked={configuration.automatic_leave_settings?.leave_when_empty || false}
                      onCheckedChange={(checked) => updateNestedConfiguration(['automatic_leave_settings', 'leave_when_empty'], checked)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Webhooks Tab */}
          <TabsContent value="webhooks" className="space-y-4 mt-4">
            <Card className="bg-white dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
                  <Webhook className="w-4 h-4 mr-2" />
                  WEBHOOK SETTINGS
                </CardTitle>
                <CardDescription className="text-xs text-gray-600 dark:text-gray-400">
                  Configure webhooks to receive real-time updates about bot events
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {configuration.webhooks?.map((webhook, index) => (
                  <div key={index} className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="text-sm font-medium text-[#4a5565] dark:text-zinc-50">Webhook {index + 1}</h4>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeWebhook(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Remove
                      </Button>
                    </div>
                    
                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                        WEBHOOK URL
                      </Label>
                      <Input
                        value={webhook.url}
                        onChange={(e) => updateWebhook(index, 'url', e.target.value)}
                        placeholder="https://your-webhook-url.com/endpoint"
                        className="text-sm bg-white dark:bg-zinc-600 border border-[#4a5565] dark:border-zinc-600"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">
                        TRIGGERS
                      </Label>
                      <div className="grid grid-cols-2 gap-2">
                        {WEBHOOK_TRIGGERS.map(trigger => (
                          <label key={trigger} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={webhook.triggers.includes(trigger)}
                              onChange={(e) => {
                                const newTriggers = e.target.checked
                                  ? [...webhook.triggers, trigger]
                                  : webhook.triggers.filter(t => t !== trigger);
                                updateWebhook(index, 'triggers', newTriggers);
                              }}
                              className="rounded"
                            />
                            <span className="text-xs text-[#4a5565] dark:text-zinc-50">{trigger}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}

                <Button
                  type="button"
                  variant="outline"
                  onClick={addWebhook}
                  className="w-full text-sm"
                >
                  Add Webhook
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Info Section */}
        <Card className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <CardContent className="pt-4">
            <div className="flex items-start space-x-2">
              <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">Advanced Bot Configuration</p>
                <p>This configuration uses all available Attendee API features including transcription settings, recording options, webhooks, and automatic leave settings. The bot will be scheduled to join 2 minutes before your meeting starts.</p>
              </div>
            </div>
          </CardContent>
        </Card>

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