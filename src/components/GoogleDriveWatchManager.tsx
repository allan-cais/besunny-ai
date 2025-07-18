import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Eye, EyeOff, Link, AlertCircle, CheckCircle } from 'lucide-react';
import { useDriveWatch, extractGoogleDriveFileId } from '@/lib/drive-watch';
import { Document } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';

interface GoogleDriveWatchManagerProps {
  document: Document;
  onUpdate?: (document: Document) => void;
}

const GoogleDriveWatchManager: React.FC<GoogleDriveWatchManagerProps> = ({ 
  document, 
  onUpdate 
}) => {
  const [driveUrl, setDriveUrl] = useState('');
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [isUnsubscribing, setIsUnsubscribing] = useState(false);
  const { subscribeToFile, unsubscribeFromFile, hasActiveDriveWatch } = useDriveWatch();
  const { toast } = useToast();

  const hasActiveWatch = hasActiveDriveWatch(document);

  const handleSubscribe = async () => {
    if (!driveUrl.trim()) {
      toast({
        title: "Error",
        description: "Please enter a Google Drive URL",
        variant: "destructive",
      });
      return;
    }

    const fileId = extractGoogleDriveFileId(driveUrl);
    if (!fileId) {
      toast({
        title: "Error",
        description: "Invalid Google Drive URL. Please check the format.",
        variant: "destructive",
      });
      return;
    }

    setIsSubscribing(true);
    try {
      const result = await subscribeToFile(document.id, fileId);
      
      if (result.success) {
        toast({
          title: "Success",
          description: "Successfully subscribed to file changes",
        });
        
        // Update the document in the parent component
        if (onUpdate) {
          onUpdate({
            ...document,
            file_id: fileId,
            watch_active: true,
            status: 'active',
            last_synced_at: new Date().toISOString(),
          });
        }
        
        setDriveUrl('');
      } else {
        toast({
          title: "Error",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to subscribe: ${error.message}`,
        variant: "destructive",
      });
    } finally {
      setIsSubscribing(false);
    }
  };

  const handleUnsubscribe = async () => {
    setIsUnsubscribing(true);
    try {
      const result = await unsubscribeFromFile(document.id);
      
      if (result.success) {
        toast({
          title: "Success",
          description: "Successfully unsubscribed from file changes",
        });
        
        // Update the document in the parent component
        if (onUpdate) {
          onUpdate({
            ...document,
            watch_active: false,
            status: 'active',
          });
        }
      } else {
        toast({
          title: "Error",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to unsubscribe: ${error.message}`,
        variant: "destructive",
      });
    } finally {
      setIsUnsubscribing(false);
    }
  };

  const getStatusInfo = () => {
    if (!document.file_id) {
      return {
        icon: EyeOff,
        label: 'No Drive Link',
        description: 'This document is not linked to a Google Drive file',
        color: 'text-muted-foreground',
        variant: 'secondary' as const,
      };
    }

    if (document.status === 'deleted') {
      return {
        icon: AlertCircle,
        label: 'Deleted from Drive',
        description: 'The file has been deleted from Google Drive',
        color: 'text-destructive',
        variant: 'destructive' as const,
      };
    }

    if (document.status === 'updated') {
      return {
        icon: CheckCircle,
        label: 'Recently Updated',
        description: 'The file was recently updated and synced',
        color: 'text-blue-600',
        variant: 'default' as const,
      };
    }

    if (hasActiveWatch) {
      return {
        icon: Eye,
        label: 'Watch Active',
        description: 'Monitoring this file for changes',
        color: 'text-green-600',
        variant: 'default' as const,
      };
    }

    return {
      icon: EyeOff,
      label: 'Watch Inactive',
      description: 'Not monitoring this file for changes',
      color: 'text-muted-foreground',
      variant: 'secondary' as const,
    };
  };

  const statusInfo = getStatusInfo();
  const Icon = statusInfo.icon;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link className="h-5 w-5" />
          Google Drive Integration
        </CardTitle>
        <CardDescription>
          Monitor this document for changes in Google Drive
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Status */}
        <div className="flex items-center gap-2">
          <Badge variant={statusInfo.variant} className="flex items-center gap-1">
            <Icon className={`h-3 w-3 ${statusInfo.color}`} />
            <span>{statusInfo.label}</span>
          </Badge>
          {document.last_synced_at && (
            <span className="text-xs text-muted-foreground">
              Last synced: {new Date(document.last_synced_at).toLocaleDateString()}
            </span>
          )}
        </div>
        
        <p className="text-sm text-muted-foreground">
          {statusInfo.description}
        </p>

        {/* File ID Display */}
        {document.file_id && (
          <div className="p-3 bg-muted rounded-md">
            <Label className="text-xs font-medium">File ID</Label>
            <p className="text-sm font-mono text-muted-foreground break-all">
              {document.file_id}
            </p>
          </div>
        )}

        {/* Subscribe Form */}
        {!hasActiveWatch && document.status !== 'deleted' && (
          <div className="space-y-2">
            <Label htmlFor="drive-url">Google Drive URL</Label>
            <div className="flex gap-2">
              <Input
                id="drive-url"
                placeholder="https://drive.google.com/file/d/..."
                value={driveUrl}
                onChange={(e) => setDriveUrl(e.target.value)}
                className="flex-1"
              />
              <Button
                onClick={handleSubscribe}
                disabled={isSubscribing || !driveUrl.trim()}
                size="sm"
              >
                {isSubscribing ? 'Subscribing...' : 'Subscribe'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Paste a Google Drive sharing URL to monitor this file for changes
            </p>
          </div>
        )}

        {/* Unsubscribe Button */}
        {hasActiveWatch && (
          <Button
            variant="outline"
            onClick={handleUnsubscribe}
            disabled={isUnsubscribing}
            className="w-full"
          >
            {isUnsubscribing ? 'Unsubscribing...' : 'Unsubscribe from Changes'}
          </Button>
        )}

        {/* Help Text */}
        <div className="text-xs text-muted-foreground space-y-1">
          <p>• Supported URL formats:</p>
          <ul className="list-disc list-inside ml-2 space-y-1">
            <li>https://drive.google.com/file/d/[fileId]/view</li>
            <li>https://docs.google.com/document/d/[fileId]/edit</li>
            <li>https://docs.google.com/spreadsheets/d/[fileId]/edit</li>
            <li>https://docs.google.com/presentation/d/[fileId]/edit</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default GoogleDriveWatchManager; 