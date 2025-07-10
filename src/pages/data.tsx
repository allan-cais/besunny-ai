import React from 'react';
import DataFeed from '@/components/dashboard/DataFeed';
import PageHeader from '@/components/dashboard/PageHeader';

const DataPage = () => (
  <div className="flex-1 max-w-[90rem] mx-auto px-4 py-8 font-sans">
    <PageHeader title="DATA" path="~/sunny.ai/data" />
    <DataFeed />
  </div>
);

export default DataPage; 