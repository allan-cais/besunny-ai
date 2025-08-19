import React from 'react';

interface PageHeaderProps {
  title: React.ReactNode;
  path: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, path }) => (
  <div className="mb-6 flex items-center">
    <div>
      <span className="text-xs font-medium font-mono uppercase tracking-wide">{title}</span>
      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 font-mono">{path}</div>
    </div>
  </div>
);

export default PageHeader; 