import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, Terminal, Zap, Shield, Code, MessageSquare, ArrowRight } from 'lucide-react';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#FF4444]/10 via-transparent to-[#FF8C00]/10" />
        
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
          backgroundSize: '50px 50px'
        }} />

        <nav className="relative z-10 flex items-center justify-between p-6 max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <Flame className="w-8 h-8 text-[#FF4444]" />
            <span className="text-xl font-bold text-white">Devil Agent</span>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => navigate('/login')}
              className="px-6 py-2 text-white hover:text-[#FF8C00] transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="px-6 py-2 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Get Started
            </button>
          </div>
        </nav>

        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-20 pb-32">
          <div className="text-center">
            {/* Devil Logo */}
            <div className="mb-8">
              <Flame className="w-24 h-24 text-[#FF4444] mx-auto animate-pulse" />
            </div>

            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
              <span className="bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-transparent bg-clip-text">
                Devil Agent
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Your Personal AI Agent with Full System Access. 
              Code, Create, and Automate with No Limits.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/signup')}
                className="group px-8 py-4 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white font-semibold rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-2"
              >
                Create Account
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => navigate('/login')}
                className="px-8 py-4 border border-[#333] text-white font-semibold rounded-lg hover:border-[#FF8C00] hover:text-[#FF8C00] transition-colors"
              >
                Login with Key
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-[#0d0d0d] py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-16">
            Unleash the Power of AI
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<MessageSquare className="w-8 h-8" />}
              title="Intelligent Chat"
              description="Natural conversations with an AI that understands context, writes code, and solves complex problems."
            />
            <FeatureCard
              icon={<Terminal className="w-8 h-8" />}
              title="Full Terminal Access"
              description="Execute commands, manage files, and automate tasks directly from the web interface."
            />
            <FeatureCard
              icon={<Code className="w-8 h-8" />}
              title="Custom Skills"
              description="Create and manage custom skills to extend Devil Agent's capabilities for your specific needs."
            />
            <FeatureCard
              icon={<Shield className="w-8 h-8" />}
              title="Key-Based Auth"
              description="Secure 40-word key authentication. No passwords to remember, no accounts to hack."
            />
            <FeatureCard
              icon={<Zap className="w-8 h-8" />}
              title="Lightning Fast"
              description="Powered by cutting-edge LLMs for instant responses and real-time interactions."
            />
            <FeatureCard
              icon={<Flame className="w-8 h-8" />}
              title="No Limits"
              description="Full agentic capabilities with file system access, code execution, and more."
            />
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-24 bg-gradient-to-b from-[#0d0d0d] to-[#0a0a0a]">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-gray-400 text-lg mb-8">
            Create your account in seconds. No email required.
          </p>
          <button
            onClick={() => navigate('/signup')}
            className="px-12 py-4 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white font-bold text-lg rounded-lg hover:opacity-90 transition-opacity"
          >
            Create Your Account
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 border-t border-[#1a1a1a]">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-500">
          <p>Devil Agent - Your Personal AI</p>
        </div>
      </footer>
    </div>
  );
};

const FeatureCard: React.FC<{ icon: React.ReactNode; title: string; description: string }> = ({
  icon,
  title,
  description
}) => (
  <div className="bg-[#1a1a1a] p-6 rounded-xl border border-[#333] hover:border-[#FF4444]/50 transition-colors group">
    <div className="text-[#FF8C00] mb-4 group-hover:text-[#FF4444] transition-colors">
      {icon}
    </div>
    <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
    <p className="text-gray-400">{description}</p>
  </div>
);

export default Landing;
