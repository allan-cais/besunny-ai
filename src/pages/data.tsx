import React from 'react';
import DataFeed from '@/components/dashboard/DataFeed';
import PageHeader from '@/components/dashboard/PageHeader';

const DataPage = () => (
  <div className="w-[70vw] max-w-[90rem] mx-auto px-4 py-8 font-sans">
    <PageHeader title="DATA" path="~/sunny.ai/data" />
    <DataFeed />
  </div>
);

export default DataPage; 