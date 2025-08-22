import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Copy, CheckCircle, Mail, FileText, Users, ExternalLink, AlertCircle, RefreshCw, Activity } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';
import UsernameSetupDialog from './UsernameSetupDialog';
import AutoScheduleInstructions from '@/components/dashboard/AutoScheduleInstructions';
// Gmail watch functionality disabled for OAuth debugging

interface UserData {
  username?: string;
  email: string;
  name?: string;
}

const VirtualEmailSettings: React.FC = () => {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showUsernameDialog, setShowUsernameDialog] = useState(false);
  const [copied, setCopied] = useState(false);
  // Gmail watch functionality disabled for OAuth debugging
  const { user } = useAuth();
  const { toast } = useToast();

  const virtualEmailAddress = userData?.username ? `ai+${userData.username}@besunny.ai` : null;

  useEffect(() => {
    loadUserData();
    // Gmail watch functionality disabled for OAuth debugging
  }, [user, userData?.email]);

  const loadUserData = async () => {
    if (!user) return;

    try {
      setIsLoading(true);
      
      // Get user data from the users table
      const { data, error } = await supabase
        .from('users')
        .select('username, email, name')
        .eq('id', user.id)
        .single();

      if (error) {
        // Error loading user data
        // Fallback to auth user data
        setUserData({
          email: user.email || '',
          name: user.user_metadata?.name || user.user_metadata?.full_name
        });
      } else {
        setUserData(data);
      }
    } catch (error) {
      // Error loading user data
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!virtualEmailAddress) return;
    
    try {
      await navigator.clipboard.writeText(virtualEmailAddress);
      setCopied(true);
      toast({
        title: 'Copied!',
        description: 'Virtual email address copied to clipboard',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      // Failed to copy
      toast({
        title: 'Error',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  };

  // Gmail watch functionality disabled for OAuth debugging



  // Gmail watch functionality disabled for OAuth debugging

  // Gmail watch functionality disabled for OAuth debugging

  const handleUsernameSet = () => {
    setShowUsernameDialog(false);
    loadUserData(); // Reload user data to get the new username
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="h-32 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {!userData?.username ? (
        <Card className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-[#4a5565] dark:text-zinc-200 font-mono">
              <AlertCircle className="h-5 w-5 text-orange-500" />
              Username Not Set
            </CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400 font-mono">
              Set up your username to get your personal virtual email address
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => setShowUsernameDialog(true)}
              className="bg-[#4a5565] dark:bg-zinc-700 text-white font-mono"
            >
              Set Up Username
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Virtual Email Address Display */}
          <Card className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-[#4a5565] dark:text-zinc-200 font-mono">
                <Mail className="h-5 w-5" />
                Your Virtual Email Address
              </CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400 font-mono">
                Use this address to automatically capture emails and files for your workspace
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 p-4 bg-stone-50 dark:bg-zinc-800 rounded-lg border border-[#4a5565] dark:border-zinc-700">
                <code className="flex-1 text-lg font-mono text-[#4a5565] dark:text-zinc-200">{virtualEmailAddress}</code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                  disabled={copied}
                  className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 font-mono"
                >
                  {copied ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 font-mono">
                <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 uppercase font-mono hover:bg-stone-50 dark:hover:bg-zinc-800">
                  Username: {userData.username}
                </Badge>
                <Badge className="border border-green-500 rounded px-2 py-0.5 text-[10px] text-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-50 dark:hover:bg-green-950 uppercase font-mono">
                  Active
                </Badge>
                {/* Gmail Watch functionality disabled for OAuth debugging */}
              </div>
            </CardContent>
          </Card>

          {/* Usage Instructions */}
          <Card className="border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900">
            <CardHeader>
              <CardTitle className="text-[#4a5565] dark:text-zinc-200 font-mono">How to Use Your Virtual Email</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400 font-mono">
                Follow these steps to automatically capture content for your projects
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <Mail className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h4 className="font-medium text-[#4a5565] dark:text-zinc-200 font-mono">Email Capture</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                        CC <code className="bg-stone-50 dark:bg-zinc-800 px-1 rounded text-xs font-mono">{virtualEmailAddress}</code> on any emails you want to capture
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                      <FileText className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <h4 className="font-medium text-[#4a5565] dark:text-zinc-200 font-mono">File Sharing</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                        Share Google Drive files with this address to automatically capture them
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <Separator className="bg-[#4a5565] dark:bg-zinc-700" />

              <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2 font-mono">
                  What Happens Next?
                </h4>
                <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1 font-mono">
                  <li>• Content is automatically captured and tagged</li>
                  <li>• Files and emails appear in your workspace</li>
                  <li>• AI determines the best project association</li>
                  <li>• Everything becomes searchable and organized</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Auto-Schedule Instructions */}
          <AutoScheduleInstructions />
          
          {/* Gmail Watch functionality disabled for OAuth debugging */}
        </>
      )}

      {/* Username Setup Dialog */}
      <UsernameSetupDialog
        open={showUsernameDialog}
        onClose={handleUsernameSet}
      />
    </div>
  );
};

export default VirtualEmailSettings; 