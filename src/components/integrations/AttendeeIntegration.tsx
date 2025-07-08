import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  CheckCircle, 
  XCircle, 
  ExternalLink,
  Loader2,
  AlertCircle,
  Trash2,
  RefreshCw,
  MessageSquare,
  Eye,
  EyeOff
} from 'lucide-react';
import { apiKeyService, ApiKeyStatus } from '@/lib/api-keys';
import { useAuth } from '@/providers/AuthProvider';

interface AttendeeIntegrationProps {
  onStatusChange?: (status: ApiKeyStatus) => void;
}

const AttendeeIntegration: React.FC<AttendeeIntegrationProps> = ({ onStatusChange }) => {
  const { user } = useAuth();
  const [status, setStatus] = useState<ApiKeyStatus | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load status on component mount
  useEffect(() => {
    if (user?.id) {
      loadStatus();
    }
  }, [user?.id]);

  const loadStatus = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      setError(null);
      const statuses = await apiKeyService.getApiKeyStatus(user.id);
      const attendeeStatus = statuses.find(s => s.service === 'attendee');
      if (attendeeStatus) {
        setStatus(attendeeStatus);
        onStatusChange?.(attendeeStatus);
      } else {
        setStatus({ connected: false, service: 'attendee' });
        onStatusChange?.({ connected: false, service: 'attendee' });
      }
    } catch (error) {
      setError('Failed to load Attendee integration status');
      setStatus({ connected: false, service: 'attendee' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) {
      setError('Please enter a valid API key');
      return;
    }
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      setTesting(true);
      const isValid = await apiKeyService.testApiKey(apiKey.trim());
      setTesting(false);
      if (!isValid) {
        setError('Invalid API key. Please check your Attendee API key and try again.');
        return;
      }
      await apiKeyService.storeApiKey(apiKey.trim());
      setSuccess('Attendee API key saved successfully!');
      setApiKey('');
      await loadStatus();
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      setError('Failed to save API key. Please try again.');
    } finally {
      setSaving(false);
      setTesting(false);
    }
  };

  const handleDeleteApiKey = async () => {
    if (!user?.id) return;
    try {
      setDeleting(true);
      setError(null);
      await apiKeyService.deleteApiKey(user.id, 'attendee');
      setStatus({ connected: false, service: 'attendee' });
      onStatusChange?.({ connected: false, service: 'attendee' });
      setSuccess('Attendee integration disconnected successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      setError('Failed to disconnect Attendee integration');
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 mb-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
              <img src="https://attendee.dev/assets/img/logo.svg" alt="Attendee Logo" className="w-7 h-7" />
            </div>
            <div>
              <CardTitle className="text-base font-bold">ATTENDEE</CardTitle>
              <CardDescription className="text-xs text-gray-600 dark:text-gray-400">
                Meeting bot transcription platform for automated meeting capture
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {status?.connected ? (
              <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                <CheckCircle className="w-3 h-3 mr-1" />
                CONNECTED
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400">
                <XCircle className="w-3 h-3 mr-1" />
                NOT CONNECTED
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Error Alert */}
        {error && (
          <Alert className="mb-4 border-red-500 bg-red-50 dark:bg-red-900/20">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-red-800 dark:text-red-200">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Success Alert */}
        {success && (
          <Alert className="mb-4 border-green-500 bg-green-50 dark:bg-green-900/20">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription className="text-green-800 dark:text-green-200">
              {success}
            </AlertDescription>
          </Alert>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span className="text-sm">Loading status...</span>
          </div>
        ) : status?.connected ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {status.last_updated && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-600 dark:text-gray-400">LAST UPDATED</p>
                  <p className="text-sm font-mono">{formatDate(status.last_updated)}</p>
                </div>
              )}
            </div>
            
            <Separator className="bg-[#4a5565] dark:bg-zinc-700" />
            
            <div className="space-y-3">
              <h4 className="text-sm font-bold">CAPABILITIES</h4>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-xs">Automated meeting transcription</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-xs">Bot deployment to meetings</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-xs">Real-time transcript capture</span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 pt-4">
              <Button
                variant="outline"
                onClick={handleDeleteApiKey}
                disabled={deleting}
                className="font-mono text-xs border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                {deleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    DISCONNECTING...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-2 h-4 w-4" />
                    DISCONNECT
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={loadStatus}
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                REFRESH STATUS
              </Button>
              <Button
                variant="outline"
                onClick={() => window.open('https://attendee.dev', '_blank')}
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                VISIT ATTENDEE.DEV
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-3">
              <h4 className="text-sm font-bold">SETUP INSTRUCTIONS</h4>
              <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                <p>1. Visit <a href="https://attendee.dev" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 underline">attendee.dev</a> to create an account</p>
                <p>2. Navigate to your API settings to generate an API key</p>
                <p>3. Copy your API key and paste it below</p>
                <p>4. Click "SAVE & TEST" to validate and store your key</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="attendee-api-key" className="text-xs font-medium">
                  ATTENDEE API KEY
                </Label>
                <div className="relative">
                  <Input
                    id="attendee-api-key"
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your Attendee API key"
                    className="font-mono text-sm"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Button
                onClick={handleSaveApiKey}
                disabled={saving || !apiKey.trim()}
                className="font-mono text-xs bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-md shadow-md"
              >
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {testing ? 'TESTING...' : 'SAVING...'}
                  </>
                ) : (
                  <>
                    <MessageSquare className="mr-2 h-4 w-4" />
                    SAVE & TEST
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => window.open('https://attendee.dev', '_blank')}
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                GET API KEY
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AttendeeIntegration; 