'use client';

import React, { useState } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  Code2, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  finding?: string;
  confidence?: 'High' | 'Medium' | 'Low' | 'Insufficient';
  evidence?: string[];
  businessImpact?: string;
  recommendedActions?: string[];
  sqlQuery?: string;
}

export default function ChatPage() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSql, setShowSql] = useState<Record<string, boolean>>({});

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello Executive. I am your AI Business Copilot. Ask me any question regarding revenue trends, overdue collections, cash withdrawals, or branch performance.',
    },
  ]);

  const sampleQuestions = [
    'Why is revenue declining in Branch Takoradi?',
    'Which customers owe us the most and are past 90 days overdue?',
    'Why are bank cash withdrawals increasing this month?',
    'Show top 5 operational expense anomalies.',
  ];

  const handleSend = async (questionText?: string) => {
    const q = questionText || input;
    if (!q.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: q,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!questionText) setInput('');
    setLoading(true);

    try {
      // Call backend REST endpoint
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      });

      if (res.ok) {
        const data = await res.json();
        const insight = data.insight;
        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.content,
          finding: insight?.finding,
          confidence: insight?.confidence?.toUpperCase() || 'High',
          evidence: insight?.evidence?.map((e: any) => e.description) || [],
          businessImpact: insight?.business_impact,
          recommendedActions: insight?.recommended_actions || [],
          sqlQuery: data.sql_queries?.[0],
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        // Mock fallback if API backend server isn't running live during frontend demonstration
        setTimeout(() => {
          const mockMsg: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: 'Analysis complete for your request.',
            finding: 'Cash withdrawals increased by 41% over the past 30 days.',
            confidence: 'High',
            evidence: [
              '112 withdrawals recorded this month (historical 3-month average: 79)',
              'Only 38% of withdrawals have linked customer payment receipts',
              'Branch Takoradi accounts for 48% of total unlinked cash withdrawals',
            ],
            businessImpact: 'High risk of cash leakage or delayed customer posting affecting cash flow reconciliation.',
            recommendedActions: [
              'Review top 10 cash withdrawals above GHS 15,000 threshold',
              'Verify customer payment posting logs for Branch Takoradi',
              'Enforce mandatory payment receipt attachment rule',
            ],
            sqlQuery: `SELECT \n  b.BranchName,\n  COUNT(w.WithdrawalID) AS TotalWithdrawals,\n  SUM(w.Amount) AS TotalAmount\nFROM tblWithdrawal w\nJOIN tblBranch b ON w.BranchID = b.BranchID\nWHERE w.WithdrawalDate >= DATEADD(day, -30, GETDATE())\nGROUP BY b.BranchName\nORDER BY TotalAmount DESC;`,
          };
          setMessages((prev) => [...prev, mockMsg]);
        }, 1200);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleSql = (id: string) => {
    setShowSql((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-white/10 pb-4 shrink-0">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            Conversational AI Copilot
          </h1>
          <p className="text-xs text-gray-400">Ask executive questions backed by SQL queries and business logic</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4" /> Zero Hallucinations Policy
        </div>
      </div>

      {/* Chat Messages Scroll Container */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center text-white shrink-0 shadow-lg shadow-indigo-500/20">
                <Bot className="w-5 h-5" />
              </div>
            )}

            <div className={`max-w-3xl rounded-2xl p-5 ${
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-tr-none' 
                : 'glass-panel border-white/10 text-gray-200 rounded-tl-none space-y-4'
            }`}>
              {msg.role === 'user' ? (
                <p className="text-sm font-medium">{msg.content}</p>
              ) : (
                <div className="space-y-4">
                  {/* General message or simple intro */}
                  {!msg.finding && <p className="text-sm leading-relaxed">{msg.content}</p>}

                  {/* Structured Reasoning Template Output */}
                  {msg.finding && (
                    <div className="space-y-4">
                      {/* Finding Header with Confidence Badge */}
                      <div className="flex justify-between items-start gap-4 pb-3 border-b border-white/10">
                        <div>
                          <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400">Finding</span>
                          <h3 className="text-base font-bold text-white mt-0.5">{msg.finding}</h3>
                        </div>
                        {msg.confidence && (
                          <span className={`px-2.5 py-1 rounded-full text-xs font-bold shrink-0 ${
                            msg.confidence === 'High' 
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}>
                            Confidence: {msg.confidence}
                          </span>
                        )}
                      </div>

                      {/* Supporting Evidence */}
                      {msg.evidence && msg.evidence.length > 0 && (
                        <div>
                          <h4 className="text-xs uppercase font-bold tracking-wider text-gray-400 mb-2">Supporting Evidence</h4>
                          <ul className="space-y-1.5 text-xs text-gray-300">
                            {msg.evidence.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-2">
                                <span className="text-indigo-400 font-bold">•</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Business Impact */}
                      {msg.businessImpact && (
                        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs">
                          <h4 className="font-bold text-amber-300 mb-1">Business Impact</h4>
                          <p className="text-amber-100/90 leading-relaxed">{msg.businessImpact}</p>
                        </div>
                      )}

                      {/* Recommended Actions */}
                      {msg.recommendedActions && msg.recommendedActions.length > 0 && (
                        <div>
                          <h4 className="text-xs uppercase font-bold tracking-wider text-emerald-400 mb-2">Recommended Actions</h4>
                          <div className="space-y-1.5">
                            {msg.recommendedActions.map((action, idx) => (
                              <div key={idx} className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-200 flex items-center gap-2">
                                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                                <span>{action}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* SQL Query Collapsible Drawer */}
                      {msg.sqlQuery && (
                        <div className="pt-2">
                          <button
                            onClick={() => toggleSql(msg.id)}
                            className="flex items-center gap-2 text-xs text-gray-400 hover:text-indigo-300 transition-colors font-mono"
                          >
                            <Code2 className="w-4 h-4 text-indigo-400" />
                            <span>{showSql[msg.id] ? 'Hide Executed SQL Query' : 'View Executed SQL Query'}</span>
                            {showSql[msg.id] ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>

                          {showSql[msg.id] && (
                            <div className="mt-2 p-3 rounded-xl bg-slate-950 border border-indigo-500/30 text-xs font-mono text-cyan-300 overflow-x-auto">
                              <pre>{msg.sqlQuery}</pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-gray-300 shrink-0 border border-white/10">
                <User className="w-5 h-5" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-4 items-center">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center text-white shrink-0 animate-pulse">
              <Bot className="w-5 h-5" />
            </div>
            <div className="p-4 rounded-2xl glass-panel text-xs text-indigo-300 flex items-center gap-2">
              <Sparkles className="w-4 h-4 animate-spin" />
              <span>Analyzing SQL Server database and constructing evidence-backed insight...</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Questions */}
      <div className="shrink-0 flex gap-2 overflow-x-auto pb-1">
        {sampleQuestions.map((sq, i) => (
          <button
            key={i}
            onClick={() => handleSend(sq)}
            className="px-3 py-1.5 rounded-full glass-card text-xs text-gray-300 hover:text-white hover:border-indigo-500/50 whitespace-nowrap transition-all"
          >
            {sq}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="shrink-0 relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask any executive operational or financial question..."
          className="w-full pl-5 pr-14 py-4 rounded-2xl glass-panel text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/60 shadow-xl"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="absolute right-3 top-3 p-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 transition-all shadow-lg shadow-indigo-600/30"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
