import React from 'react';
import { Card } from '@/components/ui/card';

const StatsGrid = () => {
  const stats = [
    { value: "24", label: "ACTIVE PROJECTS" },
    { value: "156", label: "FILES PROCESSED" },
    { value: "98%", label: "UPTIME" }
  ];

  return (
    <div className="grid grid-cols-3 gap-4 mt-12">
      {stats.map((stat, index) => (
        <Card key={index} className="p-6">
          <div className="text-lg font-bold font-mono">{stat.value}</div>
          <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">{stat.label}</div>
        </Card>
      ))}
    </div>
  );
};

export default StatsGrid; 