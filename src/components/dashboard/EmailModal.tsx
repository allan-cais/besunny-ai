import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Mail, Clock, Calendar, Copy, Download, User, FileText } from 'lucide-react';

interface EmailModalProps {
  email: {
    id: string;
    title: string;
    summary: string;
    sender?: string;
    created_at: string;
    source: string;
    project_id?: string;
    // Additional email-specific fields
    subject?: string;
    body?: string;
    recipients?: string[];
    cc?: string[];
    bcc?: string[];
    attachments?: Array<{
      name: string;
      size: string;
      type: string;
    }>;
  } | null;
  isOpen: boolean;
  onClose: () => void;
}

const EmailModal: React.FC<EmailModalProps> = ({ email, isOpen, onClose }) => {
  if (!email) return null;

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

  const copyEmailContent = async () => {
    const content = `Subject: ${email.subject || email.title}\n\nFrom: ${email.sender}\nDate: ${formatDateTime(email.created_at)}\n\n${email.body || email.summary}`;
    try {
      await navigator.clipboard.writeText(content);
      // You could add a toast notification here
    } catch (error) {
      // Handle copy error silently
    }
  };

  const downloadEmail = () => {
    const content = `Subject: ${email.subject || email.title}\n\nFrom: ${email.sender}\nDate: ${formatDateTime(email.created_at)}\n\n${email.body || email.summary}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(email.subject || email.title).replace(/[^a-z0-9]/gi, '_').toLowerCase()}_email.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <Mail className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <DialogTitle className="text-lg font-bold font-mono">{email.subject || email.title}</DialogTitle>
              <div className="text-xs text-gray-500 font-mono">Email Message</div>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-6">
          {/* Email Header */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-bold font-mono">EMAIL DETAILS</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  From: {email.sender || 'Unknown Sender'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  {formatDateTime(email.created_at)}
                </span>
              </div>
            </div>
            
            {email.recipients && email.recipients.length > 0 && (
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  To: {email.recipients.join(', ')}
                </span>
              </div>
            )}

            {email.cc && email.cc.length > 0 && (
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-mono">
                  CC: {email.cc.join(', ')}
                </span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                Source: {email.source}
              </Badge>
              {email.project_id && (
                <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                  Project ID: {email.project_id}
                </Badge>
              )}
            </div>
          </div>

          {/* Email Body */}
          <div className="bg-white dark:bg-zinc-900 rounded-lg border border-[#4a5565] dark:border-zinc-700">
            {/* Email Header Bar */}
            <div className="border-b border-[#4a5565] dark:border-zinc-700 p-4 bg-stone-50 dark:bg-zinc-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium font-mono">From:</span>
                    <span className="text-sm font-mono">{email.sender || 'Unknown Sender'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium font-mono">Subject:</span>
                    <span className="text-sm font-mono">{email.subject || email.title}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={copyEmailContent}
                    className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                  >
                    <Copy className="w-3 h-3 mr-1" />
                    Copy
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={downloadEmail}
                    className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Download
                  </Button>
                </div>
              </div>
            </div>

            {/* Email Content */}
            <div className="p-6">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <div className="text-sm text-gray-700 dark:text-gray-300 font-mono leading-relaxed whitespace-pre-wrap">
                  {email.body || email.summary}
                </div>
              </div>
            </div>

            {/* Attachments */}
            {email.attachments && email.attachments.length > 0 && (
              <div className="border-t border-[#4a5565] dark:border-zinc-700 p-4 bg-stone-50 dark:bg-zinc-800">
                <h4 className="text-sm font-bold font-mono mb-3">ATTACHMENTS</h4>
                <div className="space-y-2">
                  {email.attachments.map((attachment, index) => (
                    <div key={index} className="flex items-center gap-3 p-2 bg-white dark:bg-zinc-900 rounded border border-[#4a5565] dark:border-zinc-700">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <div className="flex-1">
                        <div className="text-sm font-mono">{attachment.name}</div>
                        <div className="text-xs text-gray-500 font-mono">{attachment.size} • {attachment.type}</div>
                      </div>
                    </div>
                  ))}
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
                Extract Action Items
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
                Find Key Information
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="font-mono text-xs border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800"
              >
                Create Follow-up
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EmailModal; 