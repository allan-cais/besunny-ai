import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { FileText, Clock, Calendar, Copy, Download, User, ExternalLink, File } from 'lucide-react';
import { Document } from '@/lib/supabase';

interface DocumentModalProps {
  document: Document | null;
  isOpen: boolean;
  onClose: () => void;
}

const DocumentModal: React.FC<DocumentModalProps> = ({ document, isOpen, onClose }) => {
  if (!document) return null;

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getDocumentIcon = (source: string, title?: string) => {
    if (source === 'email' || source === 'gmail') return <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />;
    
    if (title) {
      if (title.includes('.xlsx') || title.includes('.csv')) return <FileText className="w-6 h-6 text-green-600 dark:text-green-400" />;
      if (title.includes('.pptx') || title.includes('.key')) return <FileText className="w-6 h-6 text-orange-600 dark:text-orange-400" />;
      if (title.includes('.jpg') || title.includes('.png') || title.includes('.gif')) return <FileText className="w-6 h-6 text-purple-600 dark:text-purple-400" />;
    }
    
    return <FileText className="w-6 h-6 text-gray-600 dark:text-gray-400" />;
  };

  const getDocumentType = (source: string, title?: string) => {
    if (source === 'email' || source === 'gmail') return 'Email';
    
    if (title) {
      if (title.includes('.xlsx') || title.includes('.csv')) return 'Spreadsheet';
      if (title.includes('.pptx') || title.includes('.key')) return 'Presentation';
      if (title.includes('.jpg') || title.includes('.png') || title.includes('.gif')) return 'Image';
    }
    
    return 'Document';
  };

  const copyDocumentContent = async () => {
    const content = `Title: ${document.title}\n\nAuthor: ${document.author}\nDate: ${formatDateTime(document.created_at)}\n\n${document.summary}`;
    try {
      await navigator.clipboard.writeText(content);
      // You could add a toast notification here
    } catch (error) {
      // Handle copy error silently
    }
  };

  const downloadDocument = () => {
    const content = `Title: ${document.title}\n\nAuthor: ${document.author}\nDate: ${formatDateTime(document.created_at)}\n\n${document.summary}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = `${document.title?.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'document'}_summary.txt`;
    window.document.body.appendChild(a);
    a.click();
    window.document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const openOriginalFile = () => {
    if (document.file_url) {
      window.open(document.file_url, '_blank');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-stone-100 dark:bg-zinc-800 rounded-lg flex items-center justify-center">
              {getDocumentIcon(document.source, document.title)}
            </div>
            <div>
              <DialogTitle className="text-lg font-bold font-mono">{document.title || 'Untitled Document'}</DialogTitle>
              <div className="text-xs text-gray-500 font-mono">{getDocumentType(document.source, document.title)}</div>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-6">
          {/* Document Info */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-bold font-mono">DOCUMENT DETAILS</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  Author: {document.author || 'Unknown Author'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  Created: {formatDateTime(document.created_at)}
                </span>
              </div>
              {document.received_at && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-mono">
                    Received: {formatDateTime(document.received_at)}
                  </span>
                </div>
              )}
              {document.last_synced_at && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-mono">
                    Last Synced: {formatDateTime(document.last_synced_at)}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                Source: {document.source || 'Unknown'}
              </Badge>
              {document.status && (
                <Badge className={`border rounded px-2 py-0.5 text-[10px] uppercase font-mono ${
                  document.status === 'active' ? 'border-green-500 text-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-50 dark:hover:bg-green-950' :
                  document.status === 'updated' ? 'border-blue-500 text-blue-500 bg-blue-50 dark:bg-blue-950 hover:bg-blue-50 dark:hover:bg-blue-950' :
                  document.status === 'deleted' ? 'border-red-500 text-red-500 bg-red-50 dark:bg-red-950 hover:bg-red-50 dark:hover:bg-red-950' :
                  'border-gray-500 text-gray-500 bg-gray-50 dark:bg-gray-950 hover:bg-gray-50 dark:hover:bg-gray-950'
                }`}>
                  {document.status}
                </Badge>
              )}
              {document.project_id && (
                <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                  Project ID: {document.project_id}
                </Badge>
              )}
              {document.file_id && (
                <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                  File ID: {document.file_id}
                </Badge>
              )}
            </div>
          </div>

          {/* Document Content */}
          <div className="bg-white dark:bg-zinc-900 rounded-lg border border-[#4a5565] dark:border-zinc-700">
            {/* Document Header Bar */}
            <div className="border-b border-[#4a5565] dark:border-zinc-700 p-4 bg-stone-50 dark:bg-zinc-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium font-mono">Title:</span>
                    <span className="text-sm font-mono">{document.title || 'Untitled Document'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium font-mono">Author:</span>
                    <span className="text-sm font-mono">{document.author || 'Unknown Author'}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {document.file_url && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={openOriginalFile}
                      className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                    >
                      <ExternalLink className="w-3 h-3 mr-1" />
                      Open Original
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={copyDocumentContent}
                    className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                  >
                    <Copy className="w-3 h-3 mr-1" />
                    Copy
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={downloadDocument}
                    className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Download
                  </Button>
                </div>
              </div>
            </div>

            {/* Document Content */}
            <div className="p-6">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <div className="text-sm text-gray-700 dark:text-gray-300 font-mono leading-relaxed whitespace-pre-wrap">
                  {document.summary || 'No content available for this document.'}
                </div>
              </div>
            </div>

            {/* File Information */}
            {document.file_url && (
              <div className="border-t border-[#4a5565] dark:border-zinc-700 p-4 bg-stone-50 dark:bg-zinc-800">
                <h4 className="text-sm font-bold font-mono mb-3">FILE INFORMATION</h4>
                <div className="flex items-center gap-3 p-2 bg-white dark:bg-zinc-900 rounded border border-[#4a5565] dark:border-zinc-700">
                  <File className="w-4 h-4 text-gray-500" />
                  <div className="flex-1">
                    <div className="text-sm font-mono">{document.title || 'Untitled Document'}</div>
                    <div className="text-xs text-gray-500 font-mono">
                      {document.source} • {document.file_id ? `ID: ${document.file_id}` : 'No file ID'}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={openOriginalFile}
                    className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    Open
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* AI Actions */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4">
            <h3 className="text-sm font-bold font-mono mb-3">AI ACTIONS</h3>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Extract Key Points
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Generate Summary
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Find Related Documents
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Create Notes
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DocumentModal; 