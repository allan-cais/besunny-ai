import React from 'react';
import { Button } from '@/components/ui/button';

const QuickActions = () => {
  const actions = [
    { label: "[ NEW PROJECT ]" },
    { label: "[ OPEN TERMINAL ]" }
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-base font-bold font-mono uppercase tracking-wide">QUICK ACTIONS</h3>
      <div className="grid grid-cols-2 gap-4">
        {actions.map((action, index) => (
          <Button 
            key={index}
            variant="outline"
            className="p-4 h-auto font-mono text-xs"
          >
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions; 