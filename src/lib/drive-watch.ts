import { supabaseService } from './supabase';
import { useAuth } from '@/providers/AuthProvider';

// Extract Google Drive file ID from various URL formats
export function extractGoogleDriveFileId(url: string): string | null {
  // Handle different Google Drive URL formats
  const patterns = [
    // Standard sharing URL: https://drive.google.com/file/d/{fileId}/view
    /\/file\/d\/([a-zA-Z0-9-_]+)/,
    // Edit URL: https://docs.google.com/document/d/{fileId}/edit
    /\/document\/d\/([a-zA-Z0-9-_]+)/,
    // Spreadsheet URL: https://docs.google.com/spreadsheets/d/{fileId}/edit
    /\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/,
    // Presentation URL: https://docs.google.com/presentation/d/{fileId}/edit
    /\/presentation\/d\/([a-zA-Z0-9-_]+)/,
    // Direct file ID
    /^([a-zA-Z0-9-_]{25,})$/,
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }

  return null;
}

// Subscribe to Google Drive file changes
export async function subscribeToGoogleDriveFile(
  userId: string,
  documentId: string,
  fileId: string
): Promise<{ success: boolean; message: string; watch_id?: string }> {
  try {
    const result = await supabaseService.subscribeToDriveFile(userId, documentId, fileId);
    
    if (result.success) {
      // Update the document to reflect the active watch
      await supabaseService.updateDocument(documentId, {
        file_id: fileId,
        watch_active: true,
        status: 'active',
        last_synced_at: new Date().toISOString(),
      });
    }
    
    return result;
  } catch (error) {
    console.error('Error subscribing to Google Drive file:', error);
    return {
      success: false,
      message: `Failed to subscribe to file: ${error.message}`,
    };
  }
}

// Check if a document has an active Google Drive watch
export function hasActiveDriveWatch(document: any): boolean {
  return document.file_id && document.watch_active === true;
}

// Get the appropriate status badge for a document
export function getDocumentStatusBadge(document: any) {
  if (!document.file_id) {
    return { label: 'No Drive Link', variant: 'secondary' as const };
  }

  switch (document.status) {
    case 'deleted':
      return { label: 'Deleted from Drive', variant: 'destructive' as const };
    case 'updated':
      return { label: 'Recently Updated', variant: 'default' as const };
    case 'error':
      return { label: 'Watch Error', variant: 'destructive' as const };
    case 'active':
      return { label: 'Watch Active', variant: 'default' as const };
    default:
      return { label: 'Watch Inactive', variant: 'secondary' as const };
  }
}

// Hook for managing Google Drive file watches
export function useDriveWatch() {
  const { user } = useAuth();

  const subscribeToFile = async (documentId: string, fileId: string) => {
    if (!user?.id) {
      throw new Error('User not authenticated');
    }

    return await subscribeToGoogleDriveFile(user.id, documentId, fileId);
  };

  const unsubscribeFromFile = async (documentId: string) => {
    try {
      // Update document to reflect inactive watch
      await supabaseService.updateDocument(documentId, {
        watch_active: false,
        status: 'active',
      });
      
      return { success: true, message: 'Unsubscribed from file changes' };
    } catch (error) {
      console.error('Error unsubscribing from file:', error);
      return {
        success: false,
        message: `Failed to unsubscribe: ${error.message}`,
      };
    }
  };

  return {
    subscribeToFile,
    unsubscribeFromFile,
    hasActiveDriveWatch,
    getDocumentStatusBadge,
  };
} 