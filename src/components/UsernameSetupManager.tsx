import React, { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/providers/AuthProvider';
import UsernameSetupDialog from './UsernameSetupDialog';

const UsernameSetupManager: React.FC = () => {
  const [showDialog, setShowDialog] = useState(false);
  const [hasChecked, setHasChecked] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (user && !hasChecked) {
      checkUsernameStatus();
    }
  }, [user, hasChecked]);

  const checkUsernameStatus = async () => {
    if (!user) return;

    try {
      // Check if user has a username set
      const { data, error } = await supabase
        .from('users')
        .select('username')
        .eq('id', user.id)
        .single();

      if (error) {
        console.error('Error checking username status:', error);
        // If there's an error, we'll show the dialog anyway
        setShowDialog(true);
      } else if (!data?.username) {
        // User doesn't have a username, show the dialog
        setShowDialog(true);
      }

      setHasChecked(true);
    } catch (error) {
      console.error('Error checking username status:', error);
      setHasChecked(true);
    }
  };

  const handleClose = () => {
    setShowDialog(false);
  };

  if (!user || !hasChecked) {
    return null;
  }

  return (
    <UsernameSetupDialog
      open={showDialog}
      onClose={handleClose}
    />
  );
};

export default UsernameSetupManager; 