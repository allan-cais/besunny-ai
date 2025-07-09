import React from 'react';
import ProjectMeetingsCard from '@/components/dashboard/ProjectMeetingsCard';

const MeetingsPage: React.FC = () => {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Meetings</h1>
      {/* Calendar, meeting list, and bot controls will go here */}
      {/* TODO: Update ProjectMeetingsCard to support showing all meetings, not just by project */}
      <ProjectMeetingsCard />
    </div>
  );
};

export default MeetingsPage; 