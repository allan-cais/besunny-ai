import React, { useState, useEffect } from 'react';
import { useAuth } from '@/providers/AuthProvider';
import UsernameSetupDialog from './UsernameSetupDialog';

const UsernameSetupManager: React.FC = () => {
  const [showDialog, setShowDialog] = useState(false);
  const [hasChecked, setHasChecked] = useState(false);
  const { user, checkUsernameStatus } = useAuth();

  useEffect(() => {
    if (user && !hasChecked) {
      checkUsernameStatusFromAPI();
    }
  }, [user, hasChecked, checkUsernameStatus]);

  const checkUsernameStatusFromAPI = async () => {
    if (!user) return;

    try {
      // Use the new API endpoint to check username status
      const result = await checkUsernameStatus();
      
      if (!result.hasUsername) {
        // User doesn't have a username, show the dialog immediately
        setShowDialog(true);
      }

      setHasChecked(true);
    } catch (error) {
      console.error('Error checking username status:', error);
      
      // If there's an error, wait a bit and retry once
      if (!hasChecked) {
        setTimeout(() => {
          console.log('Retrying username status check...');
          checkUsernameStatusFromAPI();
        }, 2000);
      } else {
        // If retry also failed, show the dialog anyway
        setShowDialog(true);
        setHasChecked(true);
      }
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