import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, Terminal, Zap, Shield, Copy, Check, AlertTriangle, Download } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || '';

const Signup: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<'initial' | 'show-key' | 'confirm'>('initial');
  const [secretKey, setSecretKey] = useState('');
  const [copied, setCopied] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const createAccount = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error('Failed to create account');
      }
      
      const data = await response.json();
      setSecretKey(data.key);
      localStorage.setItem('devil_token', data.token);
      localStorage.setItem('devil_user_id', data.user_id);
      setStep('show-key');
    } catch (err: any) {
      setError(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const copyKey = () => {
    navigator.clipboard.writeText(secretKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadKey = () => {
    const content =
      `Devil Agent - Account Recovery Key\n` +
      `=====================================\n\n` +
      `Generated: ${new Date().toISOString()}\n\n` +
      `WARNING: This is the ONLY copy of your key.\n` +
      `Anyone with this key can access your account.\n` +
      `Store it in a password manager or encrypted file.\n\n` +
      `KEY:\n${secretKey}\n\n` +
      `Login at: https://your-domain.com/login\n`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `devil-agent-key-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const confirmAndContinue = () => {
    if (confirmed) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <Flame className="w-12 h-12 text-[#FF4444]" />
            <h1 className="text-4xl font-bold text-white">Devil Agent</h1>
          </div>
        </div>

        {step === 'initial' && (
          <div className="bg-[#1a1a1a] rounded-2xl p-8 border border-[#333]">
            <h2 className="text-2xl font-bold text-white mb-6 text-center">Create Your Account</h2>
            
            <div className="bg-[#0a0a0a] rounded-lg p-4 mb-6 border border-[#FF4444]/30">
              <div className="flex items-start gap-3">
                <Shield className="w-6 h-6 text-[#FF8C00] flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-[#FF8C00] font-semibold mb-2">Key-Based Authentication</h3>
                  <p className="text-gray-400 text-sm">
                    Instead of username/password, you'll receive a unique 40-word secret key.
                    This key is your only way to access your account - no email, no recovery options.
                  </p>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
                <p className="text-red-400">{error}</p>
              </div>
            )}

            <button
              onClick={createAccount}
              disabled={loading}
              className="w-full py-4 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Generate My Secret Key'}
            </button>

            <p className="text-center text-gray-500 mt-6">
              Already have a key?{' '}
              <a href="/login" className="text-[#FF8C00] hover:underline">Login</a>
            </p>
          </div>
        )}

        {step === 'show-key' && (
          <div className="bg-[#1a1a1a] rounded-2xl p-8 border border-[#333]">
            <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0" />
                <div>
                  <h3 className="text-red-500 font-bold mb-2">CRITICAL - SAVE THIS KEY NOW!</h3>
                  <p className="text-red-400 text-sm">
                    This key will NEVER be shown again. If you lose it, you lose access to your account forever.
                    There is NO recovery option. Copy and store it safely!
                  </p>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="key-display bg-[#0a0a0a] rounded-lg p-6 border-2 border-[#FF4444] mb-6">
                <p className="text-white font-mono text-sm leading-relaxed break-all" data-testid="signup-secret-key">
                  {secretKey}
                </p>
              </div>
              
              <button
                onClick={copyKey}
                className="absolute top-4 right-16 p-2 bg-[#333] rounded-lg hover:bg-[#444] transition-colors"
                data-testid="signup-copy-btn"
                title="Copy key"
              >
                {copied ? (
                  <Check className="w-5 h-5 text-green-400" />
                ) : (
                  <Copy className="w-5 h-5 text-gray-400" />
                )}
              </button>
              <button
                onClick={downloadKey}
                className="absolute top-4 right-4 p-2 bg-[#333] rounded-lg hover:bg-[#444] transition-colors"
                data-testid="signup-download-btn"
                title="Download key as .txt"
              >
                <Download className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <label className="flex items-center gap-3 mb-6 cursor-pointer">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="w-5 h-5 rounded border-[#333] bg-[#0a0a0a] text-[#FF4444] focus:ring-[#FF4444]"
              />
              <span className="text-white">I have saved my secret key in a safe place</span>
            </label>

            <button
              onClick={confirmAndContinue}
              disabled={!confirmed}
              className="w-full py-4 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Signup;
