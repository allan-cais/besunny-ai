import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Copy, CheckCircle, Mail, FileText, Users, ExternalLink, AlertCircle } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';
import UsernameSetupDialog from './UsernameSetupDialog';

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
  const { user } = useAuth();
  const { toast } = useToast();

  const virtualEmailAddress = userData?.username ? `inbound+${userData.username}@sunny.ai` : null;

  useEffect(() => {
    loadUserData();
  }, [user]);

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
        console.error('Error loading user data:', error);
        // Fallback to auth user data
        setUserData({
          email: user.email || '',
          name: user.user_metadata?.name || user.user_metadata?.full_name
        });
      } else {
        setUserData(data);
      }
    } catch (error) {
      console.error('Error loading user data:', error);
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
      console.error('Failed to copy:', error);
      toast({
        title: 'Error',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  };

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
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Virtual Email Address</h2>
        <p className="text-muted-foreground">
          Your personal email address for automatic content organization
        </p>
      </div>

      {!userData?.username ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-500" />
              Username Not Set
            </CardTitle>
            <CardDescription>
              Set up your username to get your personal virtual email address
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setShowUsernameDialog(true)}>
              Set Up Username
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Virtual Email Address Display */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Your Virtual Email Address
              </CardTitle>
              <CardDescription>
                Use this address to automatically capture emails and files for your workspace
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 p-4 bg-muted rounded-lg">
                <code className="flex-1 text-lg font-mono">{virtualEmailAddress}</code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                  disabled={copied}
                >
                  {copied ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Badge variant="secondary">Username: {userData.username}</Badge>
                <Badge variant="outline">Active</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Usage Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>How to Use Your Virtual Email</CardTitle>
              <CardDescription>
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
                      <h4 className="font-medium">Email Capture</h4>
                                        <p className="text-sm text-muted-foreground">
                    CC <code className="bg-muted px-1 rounded text-xs">{virtualEmailAddress}</code> on any emails you want to capture
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
                      <h4 className="font-medium">File Sharing</h4>
                      <p className="text-sm text-muted-foreground">
                        Share Google Drive files with this address to automatically capture them
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                  What Happens Next?
                </h4>
                <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                  <li>• Content is automatically captured and tagged</li>
                  <li>• Files and emails appear in your workspace</li>
                  <li>• AI determines the best project association</li>
                  <li>• Everything becomes searchable and organized</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Track your virtual email usage and captured content
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Mail className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No recent activity yet</p>
                <p className="text-sm">Start using your virtual email address to see captured content here</p>
              </div>
            </CardContent>
          </Card>
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