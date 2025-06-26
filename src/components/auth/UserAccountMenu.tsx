import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  Settings, 
  LogOut, 
  Key, 
  Mail, 
  Loader2,
  Edit
} from 'lucide-react';

const UserAccountMenu: React.FC = () => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [name, setName] = useState(user?.user_metadata?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleSignOut = async () => {
    if (typeof signOut !== 'function') return;
    await signOut();
    navigate('/auth', { replace: true });
    setDropdownOpen(false);
  };

  const handleUpdateProfile = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Update user metadata in Supabase Auth
      const { error: authError } = await supabase.auth.updateUser({
        data: { name }
      });

      if (authError) {
        setError(authError.message);
        setLoading(false);
        return;
      }

      // Update user record in our users table
      const { error: dbError } = await supabase
        .from('users')
        .update({ name })
        .eq('id', user?.id);

      if (dbError) {
        setError(dbError.message);
        setLoading(false);
        return;
      }

      setSuccess('Profile updated successfully!');
      setTimeout(() => {
        setProfileDialogOpen(false);
        setSuccess(null);
      }, 2000);
    } catch (error) {
      setError('An unexpected error occurred');
    }

    setLoading(false);
  };

  const handleIntegrationsClick = () => {
    navigate('/integrations');
  };

  const getUserInitials = () => {
    if (user?.user_metadata?.name) {
      return user.user_metadata.name
        .split(' ')
        .map((n: string) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return user?.email?.charAt(0).toUpperCase() || 'U';
  };

  const getUserDisplayName = () => {
    return user?.user_metadata?.name || user?.email?.split('@')[0] || 'User';
  };

  return (
    <>
      <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="relative h-8 w-8 rounded-full border border-transparent hover:border-[#4a5565] dark:hover:border-zinc-700 transition-colors"
          >
            <Avatar className="h-8 w-8">
              <AvatarImage src={user?.user_metadata?.avatar_url} alt={getUserDisplayName()} />
              <AvatarFallback className="text-xs font-mono bg-stone-200 dark:bg-zinc-700 text-[#4a5565] dark:text-zinc-300">
                {getUserInitials()}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          className="w-56 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs z-[9999]" 
          align="end"
          sideOffset={8}
          collisionPadding={8}
        >
          <DropdownMenuLabel className="font-mono text-xs px-3 py-2">
            <div className="flex flex-col space-y-1">
              <p className="text-xs font-bold leading-none text-[#4a5565] dark:text-zinc-300">
                {user?.email}
              </p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator className="bg-[#4a5565] dark:bg-zinc-700" />
          <DropdownMenuItem 
            onClick={() => {
              setProfileDialogOpen(true);
              setDropdownOpen(false);
            }}
            className="font-mono text-xs px-3 py-2 h-auto hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 cursor-pointer"
          >
            <User className="mr-3 h-4 w-4" />
            <span>PROFILE</span>
          </DropdownMenuItem>
          <DropdownMenuItem className="font-mono text-xs px-3 py-2 h-auto hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 cursor-pointer">
            <Settings className="mr-3 h-4 w-4" />
            <span>SETTINGS</span>
          </DropdownMenuItem>
          <DropdownMenuItem 
            onClick={() => {
              handleIntegrationsClick();
              setDropdownOpen(false);
            }}
            className="font-mono text-xs px-3 py-2 h-auto hover:bg-stone-300 dark:hover:bg-zinc-700 focus:bg-stone-300 dark:focus:bg-zinc-700 cursor-pointer"
          >
            <Key className="mr-3 h-4 w-4" />
            <span>INTEGRATIONS</span>
          </DropdownMenuItem>
          <DropdownMenuSeparator className="bg-[#4a5565] dark:bg-zinc-700" />
          <DropdownMenuItem 
            onClick={handleSignOut}
            className="font-mono text-xs px-3 py-2 h-auto hover:bg-red-100 dark:hover:bg-red-900/20 focus:bg-red-100 dark:focus:bg-red-900/20 cursor-pointer text-red-600 dark:text-red-400 transition-colors border border-red-200 dark:border-red-800 rounded"
          >
            <LogOut className="mr-3 h-4 w-4" />
            <span>LOG OUT</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Profile Update Dialog */}
      <Dialog open={profileDialogOpen} onOpenChange={setProfileDialogOpen}>
        <DialogContent className="sm:max-w-[425px] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono">
          <DialogHeader>
            <DialogTitle className="text-base font-bold text-[#4a5565] dark:text-zinc-300">
              EDIT PROFILE
            </DialogTitle>
            <DialogDescription className="text-xs text-gray-600 dark:text-gray-400">
              Update your account information and settings.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {error && (
              <Alert variant="destructive" className="border-red-500 bg-red-50 dark:bg-red-900/20">
                <AlertDescription className="text-xs">{error}</AlertDescription>
              </Alert>
            )}
            {success && (
              <Alert className="border-green-500 bg-green-50 dark:bg-green-900/20">
                <AlertDescription className="text-xs">{success}</AlertDescription>
              </Alert>
            )}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right text-xs font-mono text-[#4a5565] dark:text-zinc-300">
                NAME
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="col-span-3 text-xs font-mono bg-white dark:bg-zinc-700 border-[#4a5565] dark:border-zinc-700"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right text-xs font-mono text-[#4a5565] dark:text-zinc-300">
                EMAIL
              </Label>
              <div className="col-span-3 flex items-center space-x-2">
                <Input
                  id="email"
                  value={email}
                  disabled
                  className="col-span-3 text-xs font-mono bg-gray-100 dark:bg-zinc-600 border-[#4a5565] dark:border-zinc-700"
                />
                <Mail className="h-4 w-4 text-gray-500 dark:text-gray-400" />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="submit"
              onClick={handleUpdateProfile}
              disabled={loading}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  UPDATING...
                </>
              ) : (
                <>
                  <Edit className="mr-2 h-4 w-4" />
                  UPDATE PROFILE
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default UserAccountMenu; 