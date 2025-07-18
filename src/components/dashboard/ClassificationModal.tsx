import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Mail, FileText, MessageSquare, X } from 'lucide-react';

interface ClassificationModalProps {
  activity: {
    id: string;
    type: 'email' | 'document' | 'spreadsheet' | 'presentation' | 'image' | 'folder' | 'meeting_transcript';
    title: string;
    summary: string;
    source: string;
    sender?: string;
    created_at: string;
  } | null;
  projects: Array<{ id: string; name: string }>;
  isOpen: boolean;
  onClose: () => void;
  onClassify: (activityId: string, projectId: string) => void;
}

const ClassificationModal: React.FC<ClassificationModalProps> = ({ 
  activity, 
  projects, 
  isOpen, 
  onClose, 
  onClassify 
}) => {
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  if (!activity) return null;

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email':
        return <Mail className="w-6 h-6 text-blue-600 dark:text-blue-400" />;
      case 'meeting_transcript':
        return <MessageSquare className="w-6 h-6 text-purple-600 dark:text-purple-400" />;
      default:
        return <FileText className="w-6 h-6 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'email':
        return 'Email';
      case 'document':
        return 'Document';
      case 'spreadsheet':
        return 'Spreadsheet';
      case 'presentation':
        return 'Presentation';
      case 'image':
        return 'Image';
      case 'folder':
        return 'Folder';
      case 'meeting_transcript':
        return 'Transcript';
      default:
        return 'File';
    }
  };

  const handleClassify = () => {
    if (selectedProjectId) {
      onClassify(activity.id, selectedProjectId);
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
              {getTypeIcon(activity.type)}
            </div>
            <div>
              <DialogTitle className="text-lg font-bold font-mono">Classify Item</DialogTitle>
              <div className="text-xs text-gray-500 font-mono">Select project for this item</div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          {/* Item Details */}
          <div className="bg-stone-50 dark:bg-zinc-800 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                {getTypeLabel(activity.type)}
              </Badge>
              {activity.sender && (
                <Badge className="border border-[#4a5565] dark:border-zinc-700 rounded px-2 py-0.5 text-[10px] text-[#4a5565] dark:text-zinc-200 bg-stone-50 dark:bg-zinc-800 hover:bg-stone-50 dark:hover:bg-zinc-800 uppercase font-mono">
                  From: {activity.sender}
                </Badge>
              )}
            </div>
            <h3 className="font-medium text-[#4a5565] dark:text-zinc-200 font-mono">{activity.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 font-mono line-clamp-2">
              {activity.summary}
            </p>
          </div>

          {/* Project Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-[#4a5565] dark:text-zinc-200 font-mono">
              ASSOCIATE WITH PROJECT
            </label>
            <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
              <SelectTrigger className="w-full bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 text-sm font-mono">
                <SelectValue placeholder="Select a project..." />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 font-mono">
                {projects.map(project => (
                  <SelectItem
                    key={project.id}
                    value={project.id}
                    className="text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 focus:bg-stone-50 dark:focus:bg-zinc-800 font-mono"
                  >
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 border-[#4a5565] dark:border-zinc-700 bg-white dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-200 hover:bg-stone-50 dark:hover:bg-zinc-800 font-mono"
            >
              Cancel
            </Button>
            <Button
              onClick={handleClassify}
              disabled={!selectedProjectId}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-mono"
            >
              Classify
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ClassificationModal; 