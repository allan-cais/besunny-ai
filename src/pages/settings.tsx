import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import VirtualEmailSettings from '@/components/VirtualEmailSettings';

const SettingsPage: React.FC = () => {
  return (
    <div className="px-4 pt-12 pb-8 font-sans h-full flex flex-col">
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        <div className="space-y-8">
          <Tabs defaultValue="virtual-email" className="space-y-6">
            {/* <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
              <TabsTrigger value="virtual-email">Virtual Email</TabsTrigger>
              <TabsTrigger value="account">Account</TabsTrigger>
            </TabsList> */}

            <TabsContent value="virtual-email" className="space-y-6">
              <VirtualEmailSettings />
            </TabsContent>

            {/* <TabsContent value="account" className="space-y-6">
              <div className="text-center py-12 text-muted-foreground">
                <p>Account settings coming soon...</p>
              </div>
            </TabsContent> */}
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage; 