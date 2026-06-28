import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, Key, AlertCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || '';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [secretKey, setSecretKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: secretKey })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Invalid key');
      }

      const data = await response.json();
      localStorage.setItem('devil_token', data.token);
      localStorage.setItem('devil_user_id', data.user_id);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <Flame className="w-12 h-12 text-[#FF4444]" />
            <h1 className="text-4xl font-bold text-white">Devil Agent</h1>
          </div>
          <p className="text-gray-400">Enter your 40-word secret key to login</p>
        </div>

        <form onSubmit={handleLogin} className="bg-[#1a1a1a] rounded-2xl p-8 border border-[#333]">
          <div className="mb-6">
            <label className="flex items-center gap-2 text-white mb-3">
              <Key className="w-5 h-5 text-[#FF8C00]" />
              <span>Secret Key</span>
            </label>
            <textarea
              value={secretKey}
              onChange={(e) => setSecretKey(e.target.value)}
              placeholder="Enter your 40-word secret key here..."
              rows={6}
              className="w-full bg-[#0a0a0a] border border-[#333] rounded-lg p-4 text-white placeholder-gray-500 focus:border-[#FF4444] focus:outline-none resize-none font-mono text-sm"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <p className="text-red-400">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !secretKey.trim()}
            className="w-full py-4 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <p className="text-center text-gray-500 mt-6">
            Don't have an account?{' '}
            <a href="/signup" className="text-[#FF8C00] hover:underline">Create one</a>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Login;
