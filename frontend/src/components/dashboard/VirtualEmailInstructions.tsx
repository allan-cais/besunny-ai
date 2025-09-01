import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Mail, 
  Copy, 
  CheckCircle, 
  Info,
  Bot,
  Calendar
} from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { virtualEmailBotScheduling } from '@/lib/virtual-email-bot-scheduling';

const VirtualEmailInstructions: React.FC = () => {
  const { user } = useAuth();
  const [virtualEmail, setVirtualEmail] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.id) {
      loadVirtualEmail();
    }
  }, [user?.id]);

  const loadVirtualEmail = async () => {
    try {
      setLoading(true);
      const email = await virtualEmailBotScheduling.getUserVirtualEmail(user!.id);
      setVirtualEmail(email);
    } catch (error) {
      // Could add toast notification here for user feedback
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(virtualEmail);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      // Could add toast notification here for user feedback
    }
  };

  if (loading) {
    return (
      <Card className="bg-white dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700">
        <CardContent className="p-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-bold text-[#4a5565] dark:text-zinc-50 flex items-center">
          <Mail className="w-4 h-4 mr-2" />
          AUTO-SCHEDULE WITH VIRTUAL EMAIL
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-xs text-gray-600 dark:text-gray-400 font-mono">
            Add this email address to any meeting invite to automatically schedule a transcription bot:
          </p>
          
          <div className="flex items-center space-x-2">
            <Input
              value={virtualEmail}
              readOnly
              className="text-sm bg-gray-50 dark:bg-zinc-700 border border-[#4a5565] dark:border-zinc-600 font-mono"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={copyToClipboard}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              {copied ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-start space-x-2">
            <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <p className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">HOW IT WORKS</p>
              <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                <p>1. Copy your virtual email address above</p>
                <p>2. Add it as an attendee to any Google Calendar meeting</p>
                <p>3. The bot will be automatically scheduled when the meeting is created</p>
                <p>4. No manual configuration needed!</p>
              </div>
            </div>
          </div>

          <div className="flex items-start space-x-2">
            <Bot className="w-4 h-4 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <p className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">AUTO-SCHEDULED BOTS</p>
              <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                <p>• Use default "Sunny AI Assistant" configuration</p>
                <p>• Can be reconfigured later in the meetings list</p>
                <p>• Show purple "Auto Bot Scheduled" badge</p>
              </div>
            </div>
          </div>

          <div className="flex items-start space-x-2">
            <Info className="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <p className="text-xs font-medium text-[#4a5565] dark:text-zinc-50">BENEFITS</p>
              <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                <p>• Zero friction - works from any calendar client</p>
                <p>• No need to open the app for every meeting</p>
                <p>• Perfect for recurring meetings</p>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <Badge variant="outline" className="text-xs border-purple-500 text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20">
            <Bot className="w-3 h-3 mr-1" />
            Auto-scheduled meetings will show purple badges
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

export default VirtualEmailInstructions; 