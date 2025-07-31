import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import VirtualEmailSettings from '@/components/VirtualEmailSettings';
import PageHeader from '@/components/dashboard/PageHeader';

const SettingsPage: React.FC = () => {
  return (
    <div className="px-4 pt-12 pb-8 font-sans">


      <div className="max-w-4xl">
        <Tabs defaultValue="virtual-email" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
            <TabsTrigger value="virtual-email">Virtual Email</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>

          <TabsContent value="virtual-email" className="space-y-6">
            <VirtualEmailSettings />
          </TabsContent>

          <TabsContent value="account" className="space-y-6">
            <div className="text-center py-12 text-muted-foreground">
              <p>Account settings coming soon...</p>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SettingsPage; 