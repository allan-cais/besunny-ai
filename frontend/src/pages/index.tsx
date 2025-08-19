import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  const handleLogin = () => {
    navigate('/auth');
  };

  return (
    <div className="min-h-screen bg-white text-black font-mono flex items-center justify-center">
      <div className="max-w-[90rem] mx-auto px-4 py-8 font-sans">
        <div className="text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-6xl font-bold tracking-tight">sunny.ai</h1>
            <div className="w-32 h-px bg-black mx-auto"></div>
          </div>
          <div className="space-y-6">
            <p className="text-lg text-gray-600 max-w-md mx-auto leading-relaxed">
              Intelligent workspace for modern development
            </p>
            <Button 
              onClick={handleLogin}
              className="bg-white text-black border-2 border-black hover:bg-black hover:text-white transition-colors duration-200 px-8 py-3 text-base font-mono font-medium"
              variant="outline"
            >
              [ LOGIN ]
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
