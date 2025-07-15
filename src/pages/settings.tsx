import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import VirtualEmailSettings from '@/components/VirtualEmailSettings';

const SettingsPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

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
  );
};

export default SettingsPage; 