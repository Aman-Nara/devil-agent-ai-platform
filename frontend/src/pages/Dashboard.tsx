import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, MessageSquare, Code, Settings, LogOut, Send, Plus, Trash2, Save, X, Menu, ChevronLeft, Wrench, BarChart3, Play, Cpu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const API_URL = process.env.REACT_APP_API_URL || '';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
}

interface Skill {
  id: string;
  name: string;
  description: string;
  code: string;
  is_public: boolean;
  created_at: string;
}

interface UserProfile {
  id: string;
  tier: string;
  has_nvidia_key: boolean;
  nvidia_key_preview: string | null;
  created_at: string;
  last_login: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'chat' | 'skills' | 'tools' | 'analytics' | 'nexus' | 'settings'>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Chat state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [models, setModels] = useState<Array<{ id: string; label: string }>>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [activeSkillId, setActiveSkillId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Skills state
  const [skills, setSkills] = useState<Skill[]>([]);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [newSkill, setNewSkill] = useState({ name: '', description: '', code: '', is_public: false });
  const [showNewSkillForm, setShowNewSkillForm] = useState(false);

  // MCP Tools state
  const [tools, setTools] = useState<any[]>([]);
  const [selectedTool, setSelectedTool] = useState<any>(null);
  const [toolParams, setToolParams] = useState<string>('{}');
  const [toolResult, setToolResult] = useState<any>(null);
  const [toolBusy, setToolBusy] = useState(false);

  // Analytics state
  const [analytics, setAnalytics] = useState<any>(null);

  // NEXUS state
  const [nexusActiveSection, setNexusActiveSection] = useState<'brief' | 'plan' | 'scan' | 'decisions' | 'cognitive'>('brief');
  const [nexusBriefObjective, setNexusBriefObjective] = useState('');
  const [nexusBriefConstraints, setNexusBriefConstraints] = useState('');
  const [nexusBriefResult, setNexusBriefResult] = useState<any>(null);
  const [nexusPlanObjective, setNexusPlanObjective] = useState('');
  const [nexusPlanResult, setNexusPlanResult] = useState<any>(null);
  const [nexusScanText, setNexusScanText] = useState('');
  const [nexusScanResult, setNexusScanResult] = useState<any>(null);
  const [nexusDecisions, setNexusDecisions] = useState<any[]>([]);
  const [nexusDecisionForm, setNexusDecisionForm] = useState({
    title: '', context: '', options: '', decision: '', consequences: ''
  });
  const [nexusCogText, setNexusCogText] = useState('');
  const [nexusCogResult, setNexusCogResult] = useState<any>(null);
  const [nexusLoading, setNexusLoading] = useState(false);

  // Settings state
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [nvidiaKey, setNvidiaKey] = useState('');

  const token = localStorage.getItem('devil_token');

  const authHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };

  useEffect(() => {
    loadConversations();
    loadSkills();
    loadProfile();
    loadModels();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const res = await fetch(`${API_URL}/api/conversations`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const loadModels = async () => {
    try {
      const res = await fetch(`${API_URL}/api/models`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
        if (data.models && data.models.length > 0) {
          setSelectedModel(data.models[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  };

  const startNewChat = async () => {
    try {
      const res = await fetch(`${API_URL}/api/conversations`, {
        method: 'POST',
        headers: authHeaders,
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentConversationId(data.id);
        setMessages([]);
        loadConversations();
      }
    } catch (err) {
      console.error('Failed to start new chat:', err);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
        headers: authHeaders,
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
        setCurrentConversationId(conversationId);
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  const deleteConversation = async (conversationId: string) => {
    if (!window.confirm('Delete this conversation?')) return;
    try {
      const res = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (res.ok) {
        if (currentConversationId === conversationId) {
          setCurrentConversationId(null);
          setMessages([]);
        }
        loadConversations();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentConversationId) return;
    
    const userMessage: Message = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputMessage;
    setInputMessage('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          conversation_id: currentConversationId,
          message: messageToSend,
          model: selectedModel,
          skill_id: activeSkillId || undefined,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        loadConversations();
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Failed to get response.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const loadSkills = async () => {
    try {
      const res = await fetch(`${API_URL}/api/skills`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setSkills(data.skills || []);
      }
    } catch (err) {
      console.error('Failed to load skills:', err);
    }
  };

  const createSkill = async () => {
    try {
      const res = await fetch(`${API_URL}/api/skills`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(newSkill),
      });
      if (res.ok) {
        setShowNewSkillForm(false);
        setNewSkill({ name: '', description: '', code: '', is_public: false });
        loadSkills();
      }
    } catch (err) {
      console.error('Failed to create skill:', err);
    }
  };

  const updateSkill = async () => {
    if (!editingSkill) return;
    try {
      const res = await fetch(`${API_URL}/api/skills/${editingSkill.id}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(editingSkill),
      });
      if (res.ok) {
        setEditingSkill(null);
        loadSkills();
      }
    } catch (err) {
      console.error('Failed to update skill:', err);
    }
  };

  const deleteSkill = async (skillId: string) => {
    if (!window.confirm('Delete this skill?')) return;
    try {
      const res = await fetch(`${API_URL}/api/skills/${skillId}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (res.ok) loadSkills();
    } catch (err) {
      console.error('Failed to delete skill:', err);
    }
  };

  const loadTools = async () => {
    try {
      const res = await fetch(`${API_URL}/api/mcp/list`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setTools(data.tools || []);
      }
    } catch (err) {
      console.error('Failed to load tools:', err);
    }
  };

  const executeTool = async () => {
    if (!selectedTool) return;
    setToolBusy(true);
    try {
      const parsed = JSON.parse(toolParams || '{}');
      const res = await fetch(`${API_URL}/api/mcp/execute`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ tool: selectedTool.name, params: parsed })
      });
      const data = await res.json();
      setToolResult(data);
    } catch (err: any) {
      setToolResult({ ok: false, error: err?.message || 'execute failed' });
    } finally {
      setToolBusy(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const res = await fetch(`${API_URL}/api/analytics`, { headers: authHeaders });
      if (res.ok) setAnalytics(await res.json());
    } catch (err) { console.error('Failed to load analytics:', err); }
  };

  const loadProfile = async () => {
    try {
      const res = await fetch(`${API_URL}/api/users/profile`, { headers: authHeaders });
      if (res.ok) setProfile(await res.json());
    } catch (err) { console.error('Failed to load profile:', err); }
  };

  const saveNvidiaKey = async () => {
    try {
      const res = await fetch(`${API_URL}/api/users/nvidia-key`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ nvidia_key: nvidiaKey })
      });
      if (res.ok) {
        alert('NVIDIA key saved!');
        setNvidiaKey('');
        loadProfile();
      }
    } catch (err) { console.error('Failed to save key:', err); }
  };

  // NEXUS API calls
  const runNexusBrief = async () => {
    if (!nexusBriefObjective.trim()) return;
    setNexusLoading(true);
    try {
      const constraints = nexusBriefConstraints.trim() 
        ? nexusBriefConstraints.split('\n').filter(c => c.trim())
        : undefined;
      const res = await fetch(`${API_URL}/api/nexus/brief`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ objective: nexusBriefObjective, constraints })
      });
      if (res.ok) {
        const data = await res.json();
        setNexusBriefResult(data);
      }
    } catch (err) {
      console.error('NEXUS Brief error:', err);
    } finally {
      setNexusLoading(false);
    }
  };

  const runNexusPlan = async () => {
    if (!nexusPlanObjective.trim()) return;
    setNexusLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/nexus/plan`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ objective: nexusPlanObjective })
      });
      if (res.ok) {
        const data = await res.json();
        setNexusPlanResult(data);
      }
    } catch (err) {
      console.error('NEXUS Plan error:', err);
    } finally {
      setNexusLoading(false);
    }
  };

  const runNexusScan = async () => {
    if (!nexusScanText.trim()) return;
    setNexusLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/nexus/sentinel/scan`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ text: nexusScanText })
      });
      if (res.ok) {
        const data = await res.json();
        setNexusScanResult(data);
      }
    } catch (err) {
      console.error('NEXUS Scan error:', err);
    } finally {
      setNexusLoading(false);
    }
  };

  const loadNexusDecisions = async () => {
    try {
      const res = await fetch(`${API_URL}/api/nexus/decisions`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setNexusDecisions(data.decisions || []);
      }
    } catch (err) {
      console.error('Failed to load decisions:', err);
    }
  };

  const createNexusDecision = async () => {
    if (!nexusDecisionForm.title.trim() || !nexusDecisionForm.decision.trim()) return;
    setNexusLoading(true);
    try {
      const options = nexusDecisionForm.options.split('\n').filter(o => o.trim());
      const res = await fetch(`${API_URL}/api/nexus/decisions`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          title: nexusDecisionForm.title,
          context: nexusDecisionForm.context,
          options,
          decision: nexusDecisionForm.decision,
          consequences: nexusDecisionForm.consequences
        })
      });
      if (res.ok) {
        setNexusDecisionForm({ title: '', context: '', options: '', decision: '', consequences: '' });
        loadNexusDecisions();
      }
    } catch (err) {
      console.error('NEXUS Decision error:', err);
    } finally {
      setNexusLoading(false);
    }
  };

  const runNexusCognitiveLoad = async () => {
    if (!nexusCogText.trim()) return;
    setNexusLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/nexus/cognitive-load`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ text: nexusCogText })
      });
      if (res.ok) {
        const data = await res.json();
        setNexusCogResult(data);
      }
    } catch (err) {
      console.error('NEXUS Cognitive Load error:', err);
    } finally {
      setNexusLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'tools' && tools.length === 0) loadTools();
    if (activeTab === 'analytics') loadAnalytics();
    if (activeTab === 'nexus' && nexusActiveSection === 'decisions' && nexusDecisions.length === 0) {
      loadNexusDecisions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, nexusActiveSection]);

  const logout = () => {
    localStorage.removeItem('devil_token');
    localStorage.removeItem('devil_user_id');
    navigate('/');
  };

  const tabs = [
    { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
    { id: 'tools' as const, label: 'MCP Tools', icon: Wrench },
    { id: 'skills' as const, label: 'Skills', icon: Code },
    { id: 'nexus' as const, label: 'NEXUS', icon: Cpu },
    { id: 'analytics' as const, label: 'Analytics', icon: BarChart3 },
    { id: 'settings' as const, label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-[#0d0d0d] border-r border-[#1a1a1a] flex flex-col transition-all duration-300`}>
        {/* Logo */}
        <div className="p-4 border-b border-[#1a1a1a] flex items-center justify-between">
          <div className={`flex items-center gap-2 ${!sidebarOpen && 'justify-center'}`}>
            <Flame className="w-8 h-8 text-[#FF4444]" />
            {sidebarOpen && <span className="text-lg font-bold text-white">Devil</span>}
          </div>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-gray-400 hover:text-white">
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                activeTab === tab.id
                  ? 'bg-[#FF4444]/20 text-[#FF4444]'
                  : 'text-gray-400 hover:bg-[#1a1a1a] hover:text-white'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {sidebarOpen && <span>{tab.label}</span>}
            </button>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-2 border-t border-[#1a1a1a]">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <>
            {/* Conversations sidebar */}
            <div className="w-64 bg-[#0d0d0d] border-r border-[#1a1a1a] flex flex-col">
              <div className="p-4 border-b border-[#1a1a1a]">
                <button
                  onClick={startNewChat}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90"
                >
                  <Plus className="w-4 h-4" />
                  New Chat
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                {conversations.map(conv => (
                  <div
                    key={conv.id}
                    className={`group flex items-center justify-between px-3 py-2 rounded-lg mb-1 cursor-pointer transition-colors ${
                      currentConversationId === conv.id
                        ? 'bg-[#1a1a1a] text-white'
                        : 'text-gray-400 hover:bg-[#1a1a1a] hover:text-white'
                    }`}
                    onClick={() => loadMessages(conv.id)}
                  >
                    <div className="flex-1 truncate">
                      <p className="text-sm truncate">{conv.title}</p>
                      <p className="text-xs text-gray-500">{conv.message_count} messages</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Chat area */}
            <div className="flex-1 flex flex-col">
              {/* Model selector */}
              <div className="p-4 border-b border-[#1a1a1a] flex items-center gap-4">
                <label className="text-gray-400 text-sm">Model:</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-1 text-white text-sm focus:border-[#FF4444] focus:outline-none"
                >
                  {models.map(model => (
                    <option key={model.id} value={model.id}>{model.label}</option>
                  ))}
                </select>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6">
                {!currentConversationId ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <Flame className="w-16 h-16 text-[#FF4444] mx-auto mb-4" />
                      <p className="text-gray-400">Select a conversation or start a new chat</p>
                    </div>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-gray-400">Start a conversation...</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-w-4xl mx-auto">
                    {messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-3 ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white'
                              : 'bg-[#1a1a1a] text-gray-200'
                          }`}
                        >
                          {msg.role === 'assistant' ? (
                            <ReactMarkdown
                              components={{
                                code({ node, className, children, ...props }: any) {
                                  const match = /language-(\w+)/.exec(className || '');
                                  const inline = props.inline; return !inline && match ? (
                                    <SyntaxHighlighter
                                      style={vscDarkPlus}
                                      language={match[1]}
                                      PreTag="div"
                                      {...props}
                                    >
                                      {String(children).replace(/\n$/, '')}
                                    </SyntaxHighlighter>
                                  ) : (
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  );
                                },
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                          ) : (
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                          )}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-[#1a1a1a] rounded-lg px-4 py-3">
                          <div className="flex gap-2">
                            <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Input */}
              {currentConversationId && (
                <div className="p-4 border-t border-[#1a1a1a]">
                  <div className="flex gap-2 max-w-4xl mx-auto mb-2 items-center">
                    <label className="text-xs text-gray-400">Personality / Skill:</label>
                    <select
                      data-testid="chat-skill-picker"
                      value={activeSkillId}
                      onChange={(e) => setActiveSkillId(e.target.value)}
                      className="flex-1 bg-[#1a1a1a] border border-[#333] rounded-md px-2 py-1 text-sm text-white focus:border-[#FF4444] focus:outline-none"
                    >
                      <option value="">— Default (no skill) —</option>
                      {skills.map((s: any) => (
                        <option key={s.id} value={s.id}>{s.category ? `[${s.category}] ` : ""}{s.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex gap-2 max-w-4xl mx-auto">
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                      placeholder="Type your message..."
                      className="flex-1 bg-[#1a1a1a] border border-[#333] rounded-lg px-4 py-3 text-white focus:border-[#FF4444] focus:outline-none"
                      disabled={chatLoading}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={chatLoading || !inputMessage.trim()}
                      className="px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-6xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Skills</h2>
                <button
                  onClick={() => setShowNewSkillForm(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90"
                >
                  <Plus className="w-4 h-4" />
                  New Skill
                </button>
              </div>

              {showNewSkillForm && (
                <div className="bg-[#1a1a1a] rounded-lg p-6 mb-6 border border-[#333]">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Create New Skill</h3>
                    <button
                      onClick={() => setShowNewSkillForm(false)}
                      className="text-gray-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="space-y-4">
                    <input
                      type="text"
                      placeholder="Skill name"
                      value={newSkill.name}
                      onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
                      className="w-full bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none"
                    />
                    <textarea
                      placeholder="Description"
                      value={newSkill.description}
                      onChange={(e) => setNewSkill({ ...newSkill, description: e.target.value })}
                      className="w-full h-20 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none resize-none"
                    />
                    <textarea
                      placeholder="Code"
                      value={newSkill.code}
                      onChange={(e) => setNewSkill({ ...newSkill, code: e.target.value })}
                      className="w-full h-40 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white font-mono text-sm focus:border-[#FF4444] focus:outline-none resize-none"
                    />
                    <label className="flex items-center gap-2 text-gray-400">
                      <input
                        type="checkbox"
                        checked={newSkill.is_public}
                        onChange={(e) => setNewSkill({ ...newSkill, is_public: e.target.checked })}
                        className="rounded"
                      />
                      Make public
                    </label>
                    <button
                      onClick={createSkill}
                      disabled={!newSkill.name || !newSkill.code}
                      className="w-full px-4 py-2 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                    >
                      Create
                    </button>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {skills.map(skill => (
                  <div key={skill.id} className="bg-[#1a1a1a] rounded-lg p-5 border border-[#333]">
                    {editingSkill?.id === skill.id ? (
                      <div className="space-y-3">
                        <input
                          type="text"
                          value={editingSkill.name}
                          onChange={(e) => setEditingSkill({ ...editingSkill, name: e.target.value })}
                          className="w-full bg-[#0a0a0a] border border-[#333] rounded px-3 py-1 text-white text-sm"
                        />
                        <textarea
                          value={editingSkill.description}
                          onChange={(e) => setEditingSkill({ ...editingSkill, description: e.target.value })}
                          className="w-full h-16 bg-[#0a0a0a] border border-[#333] rounded px-3 py-1 text-white text-sm resize-none"
                        />
                        <textarea
                          value={editingSkill.code}
                          onChange={(e) => setEditingSkill({ ...editingSkill, code: e.target.value })}
                          className="w-full h-32 bg-[#0a0a0a] border border-[#333] rounded px-3 py-1 text-white font-mono text-xs resize-none"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={updateSkill}
                            className="flex-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingSkill(null)}
                            className="flex-1 px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="text-lg font-semibold text-white">{skill.name}</h3>
                            {skill.is_public && (
                              <span className="text-xs text-[#FF8C00]">Public</span>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => setEditingSkill(skill)}
                              className="text-gray-400 hover:text-white"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteSkill(skill.id)}
                              className="text-gray-400 hover:text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <p className="text-gray-400 text-sm mb-3">{skill.description}</p>
                        <div className="bg-[#0a0a0a] rounded p-3 max-h-32 overflow-y-auto">
                          <code className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                            {skill.code}
                          </code>
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                          Created: {new Date(skill.created_at).toLocaleDateString()}
                        </p>
                      </>
                    )}
                  </div>
                ))}
              </div>

              {skills.length === 0 && !showNewSkillForm && (
                <div className="text-center py-12">
                  <Code className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No skills yet. Create your first skill!</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* MCP Tools Tab */}
        {activeTab === 'tools' && (
          <div className="flex-1 flex">
            <div className="w-80 bg-[#0d0d0d] border-r border-[#1a1a1a] p-4 overflow-y-auto">
              <h3 className="text-lg font-semibold text-white mb-4">Available Tools</h3>
              <div className="space-y-2">
                {tools.map((tool, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setSelectedTool(tool);
                      setToolResult(null);
                      setToolParams('{}');
                    }}
                    className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                      selectedTool?.name === tool.name
                        ? 'bg-[#FF4444]/20 text-[#FF4444] border border-[#FF4444]'
                        : 'bg-[#1a1a1a] text-gray-300 hover:bg-[#252525] border border-[#333]'
                    }`}
                  >
                    <p className="font-semibold text-sm">{tool.name}</p>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{tool.description}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1 p-6 overflow-y-auto">
              {selectedTool ? (
                <div className="max-w-4xl mx-auto">
                  <h2 className="text-2xl font-bold text-white mb-2">{selectedTool.name}</h2>
                  <p className="text-gray-400 mb-6">{selectedTool.description}</p>

                  <div className="bg-[#1a1a1a] rounded-lg p-6 mb-6 border border-[#333]">
                    <h3 className="text-lg font-semibold text-white mb-4">Parameters (JSON)</h3>
                    <textarea
                      value={toolParams}
                      onChange={(e) => setToolParams(e.target.value)}
                      placeholder='{"param1": "value1"}'
                      className="w-full h-40 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-3 text-white font-mono text-sm focus:border-[#FF4444] focus:outline-none resize-none"
                    />
                    <button
                      onClick={executeTool}
                      disabled={toolBusy}
                      className="mt-4 w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                    >
                      <Play className="w-5 h-5" />
                      {toolBusy ? 'Executing...' : 'Execute Tool'}
                    </button>
                  </div>

                  {toolResult && (
                    <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                      <h3 className="text-lg font-semibold text-white mb-4">Result</h3>
                      <div className="bg-[#0a0a0a] rounded-lg p-4 max-h-96 overflow-y-auto">
                        <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                          {JSON.stringify(toolResult, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <Wrench className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">Select a tool to get started</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-6xl mx-auto">
              <h2 className="text-2xl font-bold text-white mb-6">Analytics</h2>

              {analytics ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <StatCard label="Total Conversations" value={analytics.conversations?.total || 0} />
                    <StatCard label="Total Messages" value={analytics.messages?.total || 0} />
                    <StatCard label="Skills Created" value={analytics.skills?.total || 0} />
                  </div>

                  <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333] mb-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
                    <div className="space-y-3">
                      {analytics.recent_messages?.map((msg: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-3 p-3 bg-[#0a0a0a] rounded-lg">
                          <MessageSquare className="w-5 h-5 text-[#FF8C00] mt-0.5" />
                          <div className="flex-1">
                            <p className="text-sm text-gray-300">{msg.content?.substring(0, 100)}...</p>
                            <p className="text-xs text-gray-500 mt-1">{new Date(msg.timestamp).toLocaleString()}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#FF4444]" />
                </div>
              )}
            </div>
          </div>
        )}

        {/* NEXUS Tab */}
        {activeTab === 'nexus' && (
          <div className="flex-1 flex">
            {/* NEXUS Sidebar */}
            <div className="w-64 bg-[#0d0d0d] border-r border-[#1a1a1a] p-4">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[#FF4444]" />
                NEXUS Engine
              </h3>
              <div className="space-y-2">
                {[
                  { id: 'brief', label: 'Strategic Brief', icon: '📋' },
                  { id: 'plan', label: 'Task Graph', icon: '🗺️' },
                  { id: 'scan', label: 'Sentinel Scan', icon: '🛡️' },
                  { id: 'decisions', label: 'Decision Records', icon: '⚖️' },
                  { id: 'cognitive', label: 'Cognitive Load', icon: '🧠' },
                ].map(section => (
                  <button
                    key={section.id}
                    onClick={() => setNexusActiveSection(section.id as any)}
                    className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                      nexusActiveSection === section.id
                        ? 'bg-[#FF4444]/20 text-[#FF4444] border border-[#FF4444]'
                        : 'text-gray-400 hover:bg-[#1a1a1a] hover:text-white'
                    }`}
                  >
                    <span className="mr-2">{section.icon}</span>
                    {section.label}
                  </button>
                ))}
              </div>
            </div>

            {/* NEXUS Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="max-w-4xl mx-auto">
                {/* Strategic Brief */}
                {nexusActiveSection === 'brief' && (
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Strategic Brief</h2>
                    <p className="text-gray-400 mb-6">Generate a comprehensive strategic analysis for any objective</p>

                    <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333] mb-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Objective</label>
                          <input
                            type="text"
                            value={nexusBriefObjective}
                            onChange={(e) => setNexusBriefObjective(e.target.value)}
                            placeholder="Migrate auth to JWT with zero downtime"
                            className="w-full bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Constraints (optional, one per line)</label>
                          <textarea
                            value={nexusBriefConstraints}
                            onChange={(e) => setNexusBriefConstraints(e.target.value)}
                            placeholder="Backwards compatibility&#10;No new infrastructure cost&#10;Production SLO unchanged"
                            className="w-full h-24 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none resize-none"
                          />
                        </div>
                        <button
                          onClick={runNexusBrief}
                          disabled={nexusLoading || !nexusBriefObjective.trim()}
                          className="w-full px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          <Play className="w-5 h-5" />
                          {nexusLoading ? 'Generating...' : 'Generate Brief'}
                        </button>
                      </div>
                    </div>

                    {nexusBriefResult && (
                      <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                        <h3 className="text-lg font-semibold text-white mb-4">Brief Result</h3>
                        <div className="space-y-4">
                          <div>
                            <p className="text-sm font-medium text-gray-400 mb-1">Objective</p>
                            <p className="text-white">{nexusBriefResult.objective}</p>
                          </div>
                          {nexusBriefResult.constraints && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-1">Constraints</p>
                              <ul className="list-disc list-inside text-gray-300 space-y-1">
                                {nexusBriefResult.constraints.map((c: string, i: number) => (
                                  <li key={i}>{c}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {nexusBriefResult.risks && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-1">Risks</p>
                              {nexusBriefResult.risks.map((r: any, i: number) => (
                                <div key={i} className="bg-[#0a0a0a] p-3 rounded mb-2">
                                  <p className="text-red-400 font-medium">{r.risk}</p>
                                  <p className="text-sm text-gray-400 mt-1">Mitigation: {r.mitigation}</p>
                                </div>
                              ))}
                            </div>
                          )}
                          {nexusBriefResult.estimated_effort && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-1">Estimated Effort</p>
                              <p className="text-gray-300">
                                {nexusBriefResult.estimated_effort.hours} hours ({nexusBriefResult.estimated_effort.minutes} minutes)
                              </p>
                            </div>
                          )}
                          <details className="bg-[#0a0a0a] rounded p-3">
                            <summary className="text-[#FF8C00] cursor-pointer">View Full JSON</summary>
                            <pre className="text-xs text-gray-400 mt-2 overflow-x-auto">
                              {JSON.stringify(nexusBriefResult, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Task Graph Plan */}
                {nexusActiveSection === 'plan' && (
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Task Graph</h2>
                    <p className="text-gray-400 mb-6">Decompose objectives into executable task graphs</p>

                    <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333] mb-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Objective</label>
                          <input
                            type="text"
                            value={nexusPlanObjective}
                            onChange={(e) => setNexusPlanObjective(e.target.value)}
                            placeholder="Implement user authentication system"
                            className="w-full bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none"
                          />
                        </div>
                        <button
                          onClick={runNexusPlan}
                          disabled={nexusLoading || !nexusPlanObjective.trim()}
                          className="w-full px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          <Play className="w-5 h-5" />
                          {nexusLoading ? 'Planning...' : 'Generate Plan'}
                        </button>
                      </div>
                    </div>

                    {nexusPlanResult && (
                      <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                        <h3 className="text-lg font-semibold text-white mb-4">Task Graph</h3>
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-[#0a0a0a] p-4 rounded">
                              <p className="text-gray-400 text-sm">Total Nodes</p>
                              <p className="text-2xl font-bold text-[#FF4444]">{nexusPlanResult.nodes?.length || 0}</p>
                            </div>
                            <div className="bg-[#0a0a0a] p-4 rounded">
                              <p className="text-gray-400 text-sm">Critical Path</p>
                              <p className="text-sm text-gray-300 mt-1">{nexusPlanResult.critical_path?.join(' → ')}</p>
                            </div>
                          </div>
                          {nexusPlanResult.nodes && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-2">Nodes</p>
                              <div className="space-y-2">
                                {nexusPlanResult.nodes.map((node: any, i: number) => (
                                  <div key={i} className="bg-[#0a0a0a] p-3 rounded flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-full bg-[#FF4444]/20 text-[#FF4444] flex items-center justify-center text-sm font-bold flex-shrink-0">
                                      {i + 1}
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-white font-medium">{node.id || node.name}</p>
                                      {node.dependencies && (
                                        <p className="text-xs text-gray-500 mt-1">
                                          Depends on: {node.dependencies.join(', ')}
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          <details className="bg-[#0a0a0a] rounded p-3">
                            <summary className="text-[#FF8C00] cursor-pointer">View Full JSON</summary>
                            <pre className="text-xs text-gray-400 mt-2 overflow-x-auto">
                              {JSON.stringify(nexusPlanResult, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Sentinel Scan */}
                {nexusActiveSection === 'scan' && (
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Sentinel Security Scan</h2>
                    <p className="text-gray-400 mb-6">Scan code for security vulnerabilities and bad practices</p>

                    <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333] mb-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Code to Scan</label>
                          <textarea
                            value={nexusScanText}
                            onChange={(e) => setNexusScanText(e.target.value)}
                            placeholder="api_key = &quot;sk-1234567890&quot;&#10;import hashlib&#10;hashlib.md5(b&quot;password&quot;)"
                            className="w-full h-48 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white font-mono text-sm focus:border-[#FF4444] focus:outline-none resize-none"
                          />
                        </div>
                        <button
                          onClick={runNexusScan}
                          disabled={nexusLoading || !nexusScanText.trim()}
                          className="w-full px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          <Play className="w-5 h-5" />
                          {nexusLoading ? 'Scanning...' : 'Scan Code'}
                        </button>
                      </div>
                    </div>

                    {nexusScanResult && (
                      <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                        <h3 className="text-lg font-semibold text-white mb-4">Scan Results</h3>
                        <div className="space-y-4">
                          <div className="flex items-center gap-4">
                            <div className="bg-[#0a0a0a] p-4 rounded flex-1">
                              <p className="text-gray-400 text-sm">Security Score</p>
                              <p className={`text-3xl font-bold ${nexusScanResult.score >= 70 ? 'text-green-400' : nexusScanResult.score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                                {nexusScanResult.score}/100
                              </p>
                            </div>
                            <div className="bg-[#0a0a0a] p-4 rounded flex-1">
                              <p className="text-gray-400 text-sm">Findings</p>
                              <p className="text-2xl font-bold text-[#FF4444]">{nexusScanResult.findings?.length || 0}</p>
                            </div>
                          </div>
                          {nexusScanResult.findings && nexusScanResult.findings.length > 0 && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-2">Issues Found</p>
                              <div className="space-y-2">
                                {nexusScanResult.findings.map((finding: any, i: number) => (
                                  <div key={i} className={`bg-[#0a0a0a] p-4 rounded border-l-4 ${
                                    finding.severity === 'high' ? 'border-red-500' :
                                    finding.severity === 'medium' ? 'border-yellow-500' :
                                    'border-blue-500'
                                  }`}>
                                    <div className="flex items-start justify-between">
                                      <div>
                                        <p className="text-white font-medium">{finding.rule}</p>
                                        <p className="text-sm text-gray-400 mt-1">{finding.message || finding.description}</p>
                                        {finding.line && (
                                          <p className="text-xs text-gray-500 mt-1">Line {finding.line}</p>
                                        )}
                                      </div>
                                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                                        finding.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                                        finding.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-blue-500/20 text-blue-400'
                                      }`}>
                                        {finding.severity}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          <details className="bg-[#0a0a0a] rounded p-3">
                            <summary className="text-[#FF8C00] cursor-pointer">View Full JSON</summary>
                            <pre className="text-xs text-gray-400 mt-2 overflow-x-auto">
                              {JSON.stringify(nexusScanResult, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Decision Records */}
                {nexusActiveSection === 'decisions' && (
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Decision Records</h2>
                    <p className="text-gray-400 mb-6">Document and track architectural decisions</p>

                    <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333] mb-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Create New Decision</h3>
                      <div className="space-y-4">
                        <input
                          type="text"
                          value={nexusDecisionForm.title}
                          onChange={(e) => setNexusDecisionForm({ ...nexusDecisionForm, title: e.target.value })}
                          placeholder="Decision title"
                          className="w-full bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none"
                        />
                        <textarea
                          value={nexusDecisionForm.context}
                          onChange={(e) => setNexusDecisionForm({ ...nexusDecisionForm, context: e.target.value })}
                          placeholder="Context: Why does this decision need to be made?"
                          className="w-full h-20 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none resize-none"
                        />
                        <textarea
                          value={nexusDecisionForm.options}
                          onChange={(e) => setNexusDecisionForm({ ...nexusDecisionForm, options: e.target.value })}
                          placeholder="Options (one per line)&#10;Option A: Use PostgreSQL&#10;Option B: Use MongoDB"
                          className="w-full h-24 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none resize-none"
                        />
                        <input
                          type="text"
                          value={nexusDecisionForm.decision}
                          onChange={(e) => setNexusDecisionForm({ ...nexusDecisionForm, decision: e.target.value })}
                          placeholder="Decision made"
                          className="w-full bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none"
                        />
                        <textarea
                          value={nexusDecisionForm.consequences}
                          onChange={(e) => setNexusDecisionForm({ ...nexusDecisionForm, consequences: e.target.value })}
                          placeholder="Consequences of this decision"
                          className="w-full h-20 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none resize-none"
                        />
                        <button
                          onClick={createNexusDecision}
                          disabled={nexusLoading || !nexusDecisionForm.title.trim()}
                          className="w-full px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          <Plus className="w-5 h-5" />
                          {nexusLoading ? 'Creating...' : 'Create Decision'}
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-white">Past Decisions</h3>
                      {nexusDecisions.length > 0 ? (
                        nexusDecisions.map((decision: any, i: number) => (
                          <div key={i} className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                            <div className="flex items-start justify-between mb-3">
                              <div>
                                <h4 className="text-lg font-semibold text-white">{decision.title}</h4>
                                <p className="text-xs text-gray-500">{decision.id} • {new Date(decision.created_at).toLocaleDateString()}</p>
                              </div>
                              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-xs font-bold">
                                {decision.status}
                              </span>
                            </div>
                            <p className="text-gray-400 text-sm mb-3">{decision.context}</p>
                            <div className="space-y-2">
                              <div>
                                <p className="text-xs font-medium text-gray-500">Options Considered:</p>
                                <ul className="list-disc list-inside text-sm text-gray-300 mt-1">
                                  {decision.options?.map((opt: string, j: number) => (
                                    <li key={j}>{opt}</li>
                                  ))}
                                </ul>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-gray-500">Decision:</p>
                                <p className="text-white font-medium mt-1">{decision.decision}</p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-gray-500">Consequences:</p>
                                <p className="text-gray-300 text-sm mt-1">{decision.consequences}</p>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8 bg-[#1a1a1a] rounded-lg border border-[#333]">
                          <p className="text-gray-400">No decisions recorded yet</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Cognitive Load */}
                {nexusActiveSection === 'cognitive' && (
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Cognitive Load Analysis</h2>
                    <p className="text-gray-400 mb-6">Measure code complexity and cognitive load</p>

                    <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333] mb-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Code to Analyze</label>
                          <textarea
                            value={nexusCogText}
                            onChange={(e) => setNexusCogText(e.target.value)}
                            placeholder="def complex_function(x):&#10;    if x:&#10;        for i in range(10):&#10;            if i % 2:&#10;                print(i)"
                            className="w-full h-48 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white font-mono text-sm focus:border-[#FF4444] focus:outline-none resize-none"
                          />
                        </div>
                        <button
                          onClick={runNexusCognitiveLoad}
                          disabled={nexusLoading || !nexusCogText.trim()}
                          className="w-full px-6 py-3 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          <Play className="w-5 h-5" />
                          {nexusLoading ? 'Analyzing...' : 'Analyze Code'}
                        </button>
                      </div>
                    </div>

                    {nexusCogResult && (
                      <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                        <h3 className="text-lg font-semibold text-white mb-4">Analysis Results</h3>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div className="bg-[#0a0a0a] p-4 rounded">
                            <p className="text-gray-400 text-sm">Cognitive Load Score</p>
                            <p className={`text-3xl font-bold ${
                              nexusCogResult.cognitive_load_score < 20 ? 'text-green-400' :
                              nexusCogResult.cognitive_load_score < 40 ? 'text-yellow-400' :
                              'text-red-400'
                            }`}>
                              {nexusCogResult.cognitive_load_score?.toFixed(1)}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">Band: {nexusCogResult.band}</p>
                          </div>
                          <div className="bg-[#0a0a0a] p-4 rounded">
                            <p className="text-gray-400 text-sm">Cyclomatic Complexity</p>
                            <p className="text-3xl font-bold text-[#FF8C00]">{nexusCogResult.cyclomatic_complexity}</p>
                          </div>
                          <div className="bg-[#0a0a0a] p-4 rounded">
                            <p className="text-gray-400 text-sm">Max Nesting Depth</p>
                            <p className="text-2xl font-bold text-white">{nexusCogResult.max_nesting}</p>
                          </div>
                          <div className="bg-[#0a0a0a] p-4 rounded">
                            <p className="text-gray-400 text-sm">Lines of Code</p>
                            <p className="text-2xl font-bold text-white">{nexusCogResult.lloc}</p>
                          </div>
                        </div>
                        {nexusCogResult.recommendation && (
                          <div className="bg-blue-500/10 border border-blue-500/30 rounded p-4">
                            <p className="text-blue-400 font-medium">Recommendation</p>
                            <p className="text-gray-300 text-sm mt-1">{nexusCogResult.recommendation}</p>
                          </div>
                        )}
                        <details className="bg-[#0a0a0a] rounded p-3 mt-4">
                          <summary className="text-[#FF8C00] cursor-pointer">View Full JSON</summary>
                          <pre className="text-xs text-gray-400 mt-2 overflow-x-auto">
                            {JSON.stringify(nexusCogResult, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-2xl mx-auto">
              <h2 className="text-2xl font-bold text-white mb-6">Settings</h2>

              {/* Profile Section */}
              {profile && (
                <div className="bg-[#1a1a1a] rounded-lg p-6 mb-6 border border-[#333]">
                  <h3 className="text-lg font-semibold text-white mb-4">Profile</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">User ID</span>
                      <span className="text-white font-mono">{profile.id.substring(0, 12)}...</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tier</span>
                      <span className="text-[#FF8C00] font-semibold uppercase">{profile.tier}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Created</span>
                      <span className="text-white">{new Date(profile.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Last Login</span>
                      <span className="text-white">{new Date(profile.last_login).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* NVIDIA API Key */}
              <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#333]">
                <h3 className="text-lg font-semibold text-white mb-4">NVIDIA API Key</h3>
                <p className="text-gray-400 text-sm mb-4">
                  Add your personal NVIDIA API key for custom model access.
                </p>
                {profile?.has_nvidia_key && (
                  <p className="text-green-400 text-sm mb-4">
                    Current key: {profile.nvidia_key_preview}
                  </p>
                )}
                <div className="flex gap-4">
                  <input
                    type="password"
                    value={nvidiaKey}
                    onChange={(e) => setNvidiaKey(e.target.value)}
                    placeholder="Enter NVIDIA API key (nvapi-...)"
                    className="flex-1 bg-[#0a0a0a] border border-[#333] rounded-lg px-4 py-2 text-white focus:border-[#FF4444] focus:outline-none"
                  />
                  <button
                    onClick={saveNvidiaKey}
                    disabled={!nvidiaKey}
                    className="px-6 py-2 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

const StatCard: React.FC<{ label: string; value: number | string }> = ({ label, value }) => (
  <div className="bg-[#1a1a1a] rounded-lg p-5 border border-[#333]">
    <p className="text-gray-400 text-sm">{label}</p>
    <p className="text-3xl font-bold mt-2 bg-gradient-to-r from-[#FF4444] to-[#FF8C00] text-transparent bg-clip-text">
      {value}
    </p>
  </div>
);
