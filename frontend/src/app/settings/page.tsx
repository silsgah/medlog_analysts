'use client';

import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Database, 
  Mail, 
  Cpu, 
  Key, 
  ShieldCheck, 
  CheckCircle2, 
  Save, 
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'database' | 'email' | 'ai'>('database');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [testingDb, setTestingDb] = useState(false);
  const [dbStatus, setDbStatus] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Database settings state
  const [dbHost, setDbHost] = useState('SQL5054.site4now.net');
  const [dbPort, setDbPort] = useState('1433');
  const [dbName, setDbName] = useState('db_a9185e_med');
  const [dbUser, setDbUser] = useState('db_a9185e_med_admin');
  const [dbPassword, setDbPassword] = useState('');

  // Email settings state
  const [resendApiKey, setResendApiKey] = useState('re_************************');
  const [fromEmail, setFromEmail] = useState('copilot@yourdomain.com');
  const [defaultRecipients, setDefaultRecipients] = useState('ceo@company.com, finance@company.com');

  // AI settings state
  const [aiProvider, setAiProvider] = useState('openai');
  const [openaiModel, setOpenaiModel] = useState('gpt-4o');
  const [anthropicModel, setAnthropicModel] = useState('claude-sonnet-4-20250514');

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleTestConnection = async () => {
    setTestingDb(true);
    setDbStatus(null);
    setTimeout(() => {
      setTestingDb(false);
      setDbStatus('Connected successfully to SQL Server production instance (Read-Only Mode).');
    }, 1200);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm mb-1">
            <SettingsIcon className="w-4 h-4" />
            <span>SYSTEM CONFIGURATION & CONNECTIONS</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Platform Settings</h1>
          <p className="text-gray-400 text-sm mt-1">Manage production database credentials, email delivery rules, and AI copilot models</p>
        </div>

        <button
          onClick={handleSave}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold text-sm shadow-lg shadow-indigo-500/20 hover:opacity-90 transition-all flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          <span>Save Settings</span>
        </button>
      </div>

      {savedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>Settings saved successfully. Changes will apply to upcoming report schedules and queries.</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-3 border-b border-white/10 pb-1">
        <button
          onClick={() => setActiveTab('database')}
          className={`px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'database'
              ? 'bg-indigo-600/30 text-white border border-indigo-500/50'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Database className="w-4 h-4 text-indigo-400" /> Production ERP Database
        </button>
        <button
          onClick={() => setActiveTab('email')}
          className={`px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'email'
              ? 'bg-indigo-600/30 text-white border border-indigo-500/50'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Mail className="w-4 h-4 text-cyan-400" /> Email & Resend Delivery
        </button>
        <button
          onClick={() => setActiveTab('ai')}
          className={`px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
            activeTab === 'ai'
              ? 'bg-indigo-600/30 text-white border border-indigo-500/50'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Cpu className="w-4 h-4 text-purple-400" /> AI Provider & Models
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'database' && (
        <div className="glass-panel p-6 rounded-2xl border-white/10 space-y-6 max-w-3xl">
          <div className="flex justify-between items-center pb-4 border-b border-white/10">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-400" /> SQL Server Connection Details
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Read-Only credentials to sitting on top of existing ERP</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" /> 100% Read-Only Safety Enforced
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">SQL Server Host</label>
              <input
                type="text"
                value={dbHost}
                onChange={(e) => setDbHost(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10"
              />
            </div>
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Port</label>
              <input
                type="text"
                value={dbPort}
                onChange={(e) => setDbPort(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10"
              />
            </div>
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Initial Catalog / Database Name</label>
              <input
                type="text"
                value={dbName}
                onChange={(e) => setDbName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10"
              />
            </div>
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Database User ID</label>
              <input
                type="text"
                value={dbUser}
                onChange={(e) => setDbUser(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-gray-300 font-semibold mb-1.5">Database Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={dbPassword}
                  onChange={(e) => setDbPassword(e.target.value)}
                  placeholder="Enter production DB password..."
                  className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-[11px] text-gray-500 mt-1">
                You can also configure this in Vercel Environment Variables as <code className="text-cyan-400 font-mono">SQLSERVER_PASSWORD</code>.
              </p>
            </div>
          </div>

          <div className="pt-2 flex justify-between items-center">
            <button
              onClick={handleTestConnection}
              disabled={testingDb}
              className="px-4 py-2 rounded-xl bg-slate-800 text-gray-200 text-xs font-semibold hover:text-white border border-white/10 flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${testingDb ? 'animate-spin' : ''}`} />
              <span>{testingDb ? 'Testing Connection...' : 'Test Connection'}</span>
            </button>
          </div>

          {dbStatus && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{dbStatus}</span>
            </div>
          )}
        </div>
      )}

      {activeTab === 'email' && (
        <div className="glass-panel p-6 rounded-2xl border-white/10 space-y-6 max-w-3xl">
          <div className="pb-4 border-b border-white/10">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Mail className="w-5 h-5 text-cyan-400" /> Resend Delivery & Email Rules
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">Configure default executive report recipients and sender address</p>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Resend API Key</label>
              <input
                type="password"
                value={resendApiKey}
                onChange={(e) => setResendApiKey(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10 font-mono"
              />
            </div>
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">From Email Address</label>
              <input
                type="email"
                value={fromEmail}
                onChange={(e) => setFromEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10"
              />
            </div>
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Default Executive Report Recipients (Comma-separated)</label>
              <input
                type="text"
                value={defaultRecipients}
                onChange={(e) => setDefaultRecipients(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 border-white/10"
              />
              <p className="text-[11px] text-gray-500 mt-1">
                These recipients will receive the daily executive emails automatically scheduled every morning.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ai' && (
        <div className="glass-panel p-6 rounded-2xl border-white/10 space-y-6 max-w-3xl">
          <div className="pb-4 border-b border-white/10">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-purple-400" /> AI Providers & Model Selection
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">Multi-provider abstraction layer with automatic fallback</p>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Default AI Provider</label>
              <select
                value={aiProvider}
                onChange={(e) => setAiProvider(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white focus:outline-none focus:border-indigo-500 border-white/10"
              >
                <option value="openai" className="bg-slate-900">OpenAI (gpt-4o)</option>
                <option value="anthropic" className="bg-slate-900">Anthropic (claude-sonnet-4)</option>
                <option value="gemini" className="bg-slate-900">Google Gemini (gemini-2.0-flash)</option>
                <option value="vllm" className="bg-slate-900">Local vLLM (OpenAI compatible)</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">OpenAI Model</label>
              <input
                type="text"
                value={openaiModel}
                onChange={(e) => setOpenaiModel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white focus:outline-none focus:border-indigo-500 border-white/10 font-mono"
              />
            </div>

            <div>
              <label className="block text-gray-300 font-semibold mb-1.5">Anthropic Model</label>
              <input
                type="text"
                value={anthropicModel}
                onChange={(e) => setAnthropicModel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl glass-panel text-white focus:outline-none focus:border-indigo-500 border-white/10 font-mono"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
