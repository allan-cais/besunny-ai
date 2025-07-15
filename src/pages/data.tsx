import React from 'react';
import DataFeed from '@/components/dashboard/DataFeed';
import PageHeader from '@/components/dashboard/PageHeader';

const DataPage = () => (
  <div className="px-4 py-8 font-sans h-full flex flex-col">
    <PageHeader title="DATA" path="~/sunny.ai/data" />
    <div className="flex-1 min-h-0">
      <DataFeed />
    </div>
  </div>
);

export default DataPage; 