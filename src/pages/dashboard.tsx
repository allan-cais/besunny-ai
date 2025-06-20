import { Button } from "@/components/ui/button";

const Dashboard = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md text-center text-gray-900">
        <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
        <p className="mb-6">Welcome to your dashboard!</p>
        <Button>Do Something</Button>
      </div>
    </div>
  );
};

export default Dashboard; 