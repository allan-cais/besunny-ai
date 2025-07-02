import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { Project } from '@/lib/supabase';

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated: (project: Project) => void;
  currentUserId: string;
}

const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  open,
  onOpenChange,
  onProjectCreated,
  currentUserId
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);

  const { createProject } = useSupabase();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Project name is required');
      return;
    }
    if (!consent) {
      setError('You must allow Sunny AI to scan and categorize your data.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create the project
      const newProject = await createProject({
        id: crypto.randomUUID(),
        name: name.trim(),
        description: description.trim() || undefined,
        status: 'active',
        created_by: currentUserId
      });

      if (newProject) {
        // Call the callback
        onProjectCreated(newProject);
        
        // Reset form
        setName('');
        setDescription('');
        onOpenChange(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setName('');
    setDescription('');
    setError(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs">
        <DialogHeader>
          <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
            CREATE NEW PROJECT
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
            Create a new project to organize your work and collaborate with your data.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name" className="text-[#4a5565] dark:text-zinc-300 font-mono text-xs font-bold">
                PROJECT NAME
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter project name"
                disabled={loading}
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600"
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description" className="text-[#4a5565] dark:text-zinc-300 font-mono text-xs font-bold">
                DESCRIPTION (OPTIONAL)
              </Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter project description"
                disabled={loading}
                rows={3}
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600 resize-none"
              />
            </div>

            <div className="flex items-start gap-2 mt-2">
              <input
                id="consent"
                type="checkbox"
                checked={consent}
                onChange={e => setConsent(e.target.checked)}
                disabled={loading}
                required
                className="mt-1 accent-[#4a5565] dark:accent-zinc-50"
              />
              <label htmlFor="consent" className="text-xs text-[#4a5565] dark:text-zinc-300 font-mono select-none">
                Allow Sunny AI to scan, analyze, and categorize email and document data from your connected Google account for enhanced project intelligence.
              </label>
            </div>

            {error && (
              <Alert variant="destructive" className="border-red-500 bg-red-50 dark:bg-red-900/20">
                <AlertDescription className="font-mono text-xs text-red-700 dark:text-red-400">
                  {error}
                </AlertDescription>
              </Alert>
            )}
          </div>
          
          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 hover:bg-stone-300 dark:hover:bg-zinc-700"
            >
              CANCEL
            </Button>
            <Button 
              type="submit" 
              disabled={loading || !consent}
              className="font-mono text-xs bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 hover:bg-[#3a4555] dark:hover:bg-zinc-200"
            >
              {loading && <Loader2 className="mr-2 h-3 w-3 animate-spin" />}
              Build Intelligence
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateProjectDialog; 