import React, { useState, useEffect } from 'react';
import { useAuth } from '@/providers/AuthProvider';
import UsernameSetupDialog from './UsernameSetupDialog';

const UsernameSetupManager: React.FC = () => {
  const [showDialog, setShowDialog] = useState(false);
  const { user, usernameStatus, checkUsernameStatus } = useAuth();

  useEffect(() => {
    if (user && usernameStatus === undefined) {
      // Only check if we don't have username status yet
      checkUsernameStatusFromAPI();
    } else if (usernameStatus && !usernameStatus.hasUsername) {
      // Show dialog if we know user doesn't have username
      setShowDialog(true);
    }
  }, [user, usernameStatus, checkUsernameStatus]);

  const checkUsernameStatusFromAPI = async () => {
    if (!user) return;

    try {
      const result = await checkUsernameStatus();
      
      if (!result.hasUsername) {
        setShowDialog(true);
      }
    } catch (error) {
      // If there's an error, show the dialog anyway
      setShowDialog(true);
    }
  };

  const handleClose = () => {
    setShowDialog(false);
  };

  // Don't render anything until we have user and username status
  if (!user || usernameStatus === undefined) {
    return null;
  }

  // Don't show dialog if user already has username
  if (usernameStatus.hasUsername) {
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