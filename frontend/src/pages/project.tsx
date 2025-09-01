import React from 'react';
import { useParams } from 'react-router-dom';
import ProjectDashboard from '@/components/dashboard/ProjectDashboard';

const ProjectPage = () => {
  const params = useParams<{ id: string }>();
  const projectId = params?.id;
  
  if (!projectId) {
    return <div>Project not found</div>;
  }
  
  return <ProjectDashboard projectId={projectId} />;
};

export default ProjectPage; 