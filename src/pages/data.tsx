import React from 'react';
import DataFeed from '@/components/dashboard/DataFeed';
import PageHeader from '@/components/dashboard/PageHeader';

const DataPage = () => (
  <div className="px-4 py-8 font-sans h-full flex flex-col">
    {/* Fixed Header */}
    <div className="flex-shrink-0">
      <div className="mb-6">
        <PageHeader title="DATA" path="~/sunny.ai/data" />
      </div>
    </div>

    {/* Scrollable Content */}
    <div className="flex-1 overflow-y-auto">
      <DataFeed />
    </div>
  </div>
);

export default DataPage; 