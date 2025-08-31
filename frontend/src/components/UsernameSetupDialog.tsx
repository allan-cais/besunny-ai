import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Copy, CheckCircle, AlertCircle, Mail, FileText, Users } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';
import { config } from '@/config';

interface UsernameSetupDialogProps {
  open: boolean;
  onClose: () => void;
}

const UsernameSetupDialog: React.FC<UsernameSetupDialogProps> = ({ open, onClose }) => {
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');
  const [isValid, setIsValid] = useState(false);
  const [copied, setCopied] = useState(false);
  const [setupStep, setSetupStep] = useState<'username' | 'gmail-watch' | 'complete'>('username');
  const { user, clearUsernameStatus } = useAuth();
  const { toast } = useToast();

  const virtualEmailAddress = username ? `ai+${username}@besunny.ai` : '';

  // Validate username format
  const validateUsername = (value: string) => {
    if (!value) {
      setValidationMessage('');
      setIsValid(false);
      return;
    }

    if (value.length < 3) {
      setValidationMessage('Username must be at least 3 characters long');
      setIsValid(false);
      return;
    }

    if (value.length > 30) {
      setValidationMessage('Username must be no more than 30 characters long');
      setIsValid(false);
      return;
    }

    if (!/^[a-zA-Z0-9]+$/.test(value)) {
      setValidationMessage('Username can only contain letters and numbers');
      setIsValid(false);
      return;
    }

    if (/^[0-9]/.test(value)) {
      setValidationMessage('Username cannot start with a number');
      setIsValid(false);
      return;
    }

    setValidationMessage('');
    setIsValid(true);
  };

  // Debounced validation
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      validateUsername(username);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [username]);

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toLowerCase();
    setUsername(value);
    setCopied(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isValid || !user) return;

    setIsLoading(true);
    setSetupStep('username');
    
    try {
      // Get the current session for authentication
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) {
        throw new Error('No valid session found');
      }
      


      // Use Python backend instead of Supabase edge function
      const response = await fetch(`${config.pythonBackend.url}/api/v1/user/username/set`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ username }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || result.error_message || `Failed to set username (${response.status})`);
      }

      // Show Gmail watch setup progress
      setSetupStep('gmail-watch');
      
      // Check if Gmail watch was set up successfully
      if (result.gmail_watch_setup?.success) {
        setSetupStep('complete');
        toast({
          title: 'Username set successfully!',
          description: `Your virtual email address is ready: ${result.virtual_email}. Gmail monitoring is now active!`,
        });
      } else {
        setSetupStep('complete');
        toast({
          title: 'Username set successfully!',
          description: `Your virtual email address is: ${result.virtual_email}. Gmail monitoring will be set up shortly.`,
        });
      }

      // Clear the username status cache so it will be refreshed
      clearUsernameStatus();
      
      // Close dialog after a short delay to show completion
      setTimeout(() => {
        onClose();
      }, 1500);
      
    } catch (error) {
      // Error setting username
      toast({
        title: 'Error',
        description: error.message || 'Failed to set username',
        variant: 'destructive',
      });
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
    }
  };

  return (
          <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-[600px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono">
          <DialogHeader>
            <DialogTitle className="text-base font-bold text-[#4a5565] dark:text-zinc-300">
              SET UP YOUR PERSONAL PROJECT INBOX
            </DialogTitle>
            <DialogDescription className="text-sm text-gray-600 dark:text-gray-400">
              Choose a username to create your personal virtual email address for project organization.
            </DialogDescription>
          </DialogHeader>

        <div className="space-y-6">
          {/* Feature Description */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-[#4a5565] dark:text-zinc-300" />
              <h3 className="text-sm font-bold text-[#4a5565] dark:text-zinc-300">YOUR PERSONAL PROJECT INBOX</h3>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Your account comes with a unique email address you can use to keep everything organized automatically.
            </p>
            
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-bold text-[#4a5565] dark:text-zinc-300">AUTOMATIC ORGANIZATION</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Simply CC this address on any emails about your project, or share Google Drive files with it.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-bold text-[#4a5565] dark:text-zinc-300">INSTANT CAPTURE</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Our system will instantly capture, tag, and attach the content to your project workspace.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Users className="h-4 w-4 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-bold text-[#4a5565] dark:text-zinc-300">SEARCHABLE CONTENT</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Everything will be saved and searchable—no extra steps required.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Username Setup Form */}
          {setupStep !== 'complete' && (
            <form id="username-form" onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-xs font-bold text-[#4a5565] dark:text-zinc-300">CHOOSE YOUR USERNAME</Label>
              <div className="flex gap-2">
                <Badge variant="secondary" className="px-3 py-2 text-xs font-mono bg-stone-200 dark:bg-zinc-700 text-[#4a5565] dark:text-zinc-300 border border-[#4a5565] dark:border-zinc-700">
                  ai+
                </Badge>
                <Input
                  id="username"
                  type="text"
                  placeholder="yourusername"
                  value={username}
                  onChange={handleUsernameChange}
                  className="flex-1 bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 text-xs font-mono"
                  disabled={isLoading || setupStep === 'complete'}
                />
                <Badge variant="secondary" className="px-3 py-2 text-xs font-mono bg-stone-200 dark:bg-zinc-700 text-[#4a5565] dark:text-zinc-300 border border-[#4a5565] dark:border-zinc-700">
                  @besunny.ai
                </Badge>
              </div>
              {validationMessage && (
                <p className="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {validationMessage}
                </p>
              )}
              <div className="bg-amber-50 dark:bg-amber-950/20 p-3 rounded border border-amber-200 dark:border-amber-800">
                <p className="text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2">
                  <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>IMPORTANT:</strong> Your username is permanent and cannot be changed once set. 
                    Choose carefully as this will be part of your virtual email address.
                  </span>
                </p>
              </div>
            </div>

            {/* Setup Progress */}
            {isLoading && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    setupStep === 'username' ? 'border-blue-500 bg-blue-500' : 
                    setupStep === 'gmail-watch' ? 'border-green-500 bg-green-500' : 
                    setupStep === 'complete' ? 'border-green-500 bg-green-500' : 
                    'border-gray-300 bg-gray-300'
                  }`} />
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {setupStep === 'username' ? 'Setting up username...' : 
                     setupStep === 'gmail-watch' ? 'Setting up Gmail monitoring...' : 
                     setupStep === 'complete' ? 'Setup complete!' : 
                     'Preparing...'}
                  </span>
                </div>
                {setupStep === 'gmail-watch' && (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full border-2 border-green-500 bg-green-500" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      Username set successfully
                    </span>
                  </div>
                )}
                {setupStep === 'complete' && (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full border-2 border-green-500 bg-green-500" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      Gmail monitoring setup complete
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Success Message */}
            {setupStep === 'complete' && (
              <div className="bg-green-50 dark:bg-green-950/20 p-4 rounded border border-green-200 dark:border-green-800">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <div>
                    <h4 className="text-sm font-bold text-green-800 dark:text-green-200">
                      Setup Complete!
                    </h4>
                    <p className="text-xs text-green-700 dark:text-green-300">
                      Your virtual email address is ready and Gmail monitoring is now active. 
                      You'll receive notifications for emails sent to {virtualEmailAddress}.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Preview */}
            {username && isValid && setupStep !== 'complete' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Your Virtual Email Address</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                    <code className="flex-1 text-sm">{virtualEmailAddress}</code>
                    <Button
                      type="button"
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
                </CardContent>
              </Card>
            )}

            {/* Usage Instructions */}
            {username && isValid && setupStep !== 'complete' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">How to Use</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p>• CC <code className="bg-muted px-1 rounded">{virtualEmailAddress}</code> on project emails</p>
                  <p>• Share Google Drive files with this address</p>
                  <p>• Content will automatically appear in your project workspace</p>
                </CardContent>
              </Card>
            )}

            </form>
          )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading || setupStep === 'complete'}
                className="flex-1 font-mono text-xs px-3 py-2 h-auto hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-300"
              >
                {setupStep === 'complete' ? 'CLOSE' : 'SKIP FOR NOW'}
              </Button>
              {setupStep !== 'complete' && (
                <Button
                  type="submit"
                  form="username-form"
                  disabled={!isValid || isLoading}
                  className="flex-1 font-mono text-xs px-3 py-2 h-auto bg-[#4a5565] dark:bg-zinc-700 hover:bg-[#3a4555] dark:hover:bg-zinc-600 focus:bg-[#3a4555] dark:focus:bg-zinc-600 text-white border border-[#4a5565] dark:border-zinc-700"
                >
                  {isLoading ? 'SETTING UP...' : 'SET USERNAME'}
                </Button>
              )}
            </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UsernameSetupDialog; 