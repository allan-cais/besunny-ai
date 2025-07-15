import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Copy, CheckCircle, AlertCircle, Mail, FileText, Users } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';

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
  const { user } = useAuth();
  const { toast } = useToast();

  const virtualEmailAddress = username ? `inbound+${username}@sunny.ai` : '';

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
    try {
      // Get the current session for authentication
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) {
        throw new Error('No valid session found');
      }

      const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/set-username`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ username }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Failed to set username');
      }

      toast({
        title: 'Username set successfully!',
        description: `Your virtual email address is: ${result.email_address}`,
      });

      onClose();
    } catch (error) {
      console.error('Error setting username:', error);
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
      console.error('Failed to copy:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center">
            Set Up Your Personal Project Inbox
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Feature Description */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Your Personal Project Inbox
              </CardTitle>
              <CardDescription>
                Every project you create comes with a unique email address you can use to keep everything organized automatically.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium">Automatic Organization</p>
                  <p className="text-sm text-muted-foreground">
                    Simply CC this address on any emails about your project, or share Google Drive files with it.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">Instant Capture</p>
                  <p className="text-sm text-muted-foreground">
                    Our system will instantly capture, tag, and attach the content to your project workspace.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Users className="h-5 w-5 text-purple-500 mt-0.5" />
                <div>
                  <p className="font-medium">Searchable Content</p>
                  <p className="text-sm text-muted-foreground">
                    Everything will be saved and searchable—no extra steps required.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Username Setup Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Choose Your Username</Label>
              <div className="flex gap-2">
                <Input
                  id="username"
                  type="text"
                  placeholder="yourusername"
                  value={username}
                  onChange={handleUsernameChange}
                  className="flex-1"
                  disabled={isLoading}
                />
                <Badge variant="secondary" className="px-3 py-2">
                  @sunny.ai
                </Badge>
              </div>
              {validationMessage && (
                <p className="text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-4 w-4" />
                  {validationMessage}
                </p>
              )}
              <div className="bg-amber-50 dark:bg-amber-950 p-3 rounded-lg border border-amber-200 dark:border-amber-800">
                <p className="text-sm text-amber-800 dark:text-amber-200 flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>Important:</strong> Your username is permanent and cannot be changed once set. 
                    Choose carefully as this will be part of your virtual email address.
                  </span>
                </p>
              </div>
            </div>

            {/* Preview */}
            {username && isValid && (
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
            {username && isValid && (
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

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1"
              >
                Skip for Now
              </Button>
              <Button
                type="submit"
                disabled={!isValid || isLoading}
                className="flex-1"
              >
                {isLoading ? 'Setting up...' : 'Set Username'}
              </Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UsernameSetupDialog; 