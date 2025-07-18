import React from 'react';
import { Badge } from './ui/badge';
import { Eye, EyeOff, RefreshCw, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { Document } from '../lib/supabase';

interface FileWatchStatusProps {
  document: Document;
  className?: string;
}

const FileWatchStatus: React.FC<FileWatchStatusProps> = ({ document, className = '' }) => {
  const getStatusInfo = () => {
    if (!document.file_id) {
      return {
        icon: EyeOff,
        label: 'No Watch',
        variant: 'secondary' as const,
        color: 'text-muted-foreground',
      };
    }

    if (document.status === 'deleted') {
      return {
        icon: XCircle,
        label: 'Deleted from Drive',
        variant: 'destructive' as const,
        color: 'text-destructive',
      };
    }

    if (document.status === 'updated') {
      return {
        icon: RefreshCw,
        label: 'Recently Updated',
        variant: 'default' as const,
        color: 'text-blue-600',
      };
    }

    if (document.status === 'error') {
      return {
        icon: AlertCircle,
        label: 'Watch Error',
        variant: 'destructive' as const,
        color: 'text-destructive',
      };
    }

    if (document.watch_active) {
      return {
        icon: Eye,
        label: 'Watch Active',
        variant: 'default' as const,
        color: 'text-green-600',
      };
    }

    return {
      icon: EyeOff,
      label: 'Watch Inactive',
      variant: 'secondary' as const,
      color: 'text-muted-foreground',
    };
  };

  const statusInfo = getStatusInfo();
  const Icon = statusInfo.icon;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Badge variant={statusInfo.variant} className="flex items-center gap-1">
        <Icon className={`h-3 w-3 ${statusInfo.color}`} />
        <span className="text-xs">{statusInfo.label}</span>
      </Badge>
      
      {document.last_synced_at && (
        <span className="text-xs text-muted-foreground">
          Last synced: {new Date(document.last_synced_at).toLocaleDateString()}
        </span>
      )}
    </div>
  );
};

export default FileWatchStatus; 