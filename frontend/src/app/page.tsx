'use client';

import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowUpRight, 
  ArrowDownRight, 
  Calendar,
  Layers,
  Sparkles
} from 'lucide-react';

export default function ExecutiveDashboard() {
  const [healthScore, setHealthScore] = useState(84);
  const [loading, setLoading] = useState(false);

  // Mock initial dashboard state for instant demonstration
  const kpiData = [
    { name: 'Revenue', value: 'GHS 2,450,000', change: '+8.4%', trend: 'up', icon: DollarSign, color: 'emerald' },
    { name: 'Cash Position', value: 'GHS 820,000', change: '-6.2%', trend: 'down', icon: TrendingUp, color: 'rose' },
    { name: 'Outstanding Receivables', value: 'GHS 1,120,000', change: '+2.1%', trend: 'up', icon: Calendar, color: 'amber' },
    { name: 'Collection Rate', value: '71.5%', change: '+4.0%', trend: 'up', icon: Layers, color: 'cyan' },
  ];

  const topAlerts = [
    { id: '1', title: 'Cash withdrawals unusually high', severity: 'critical', detail: 'Withdrawals up 32% this month without matching customer posting' },
    { id: '2', title: 'Customer ABC overdue by 94 days', severity: 'high', detail: 'Balance due: GHS 145,000. Risk threshold exceeded' },
    { id: '3', title: 'Takoradi Branch negative cash flow', severity: 'high', detail: 'Expenses exceeded receipts by GHS 42,000 over past 14 days' },
    { id: '4', title: 'Fuel expenses spiked +19%', severity: 'medium', detail: 'Unusual mileage to fuel consumption ratio flagged in Branch Kumasi' },
  ];

  const recommendedActions = [
    { priority: 1, action: 'Review cash withdrawals above GHS 10,000 threshold', reason: 'Prevent cash leakage and audit branch authorization' },
    { priority: 2, action: 'Escalate top 5 overdue customer receivables', reason: 'Improve collection rate from 71.5% to target 85%' },
    { priority: 3, action: 'Investigate Branch Takoradi operational costs', reason: 'Address negative cash flow trend before month-end' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm mb-1">
            <Sparkles className="w-4 h-4" />
            <span>AI EXECUTIVE INTELLIGENCE</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Executive Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Real-time operational & financial overview sitting on SQL Server ERP</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 rounded-xl glass-card text-xs text-gray-300 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-indigo-400" />
            <span>Period: Current Month (Aug 2026)</span>
          </div>
        </div>
      </div>

      {/* Top Banner Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Score Card */}
        <div className="glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between border-indigo-500/20">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold tracking-wider text-indigo-400">Composite Score</span>
              <h2 className="text-xl font-bold text-white mt-1">Business Health Score</h2>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Good Performance
            </span>
          </div>

          <div className="flex items-center gap-6 my-4">
            <div className="relative w-28 h-28 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-slate-800"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-indigo-500"
                  strokeDasharray={`${healthScore}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute text-center">
                <span className="text-3xl font-black text-white">{healthScore}</span>
                <span className="text-xs text-gray-400 block font-medium">/ 100</span>
              </div>
            </div>

            <div className="flex-1 space-y-2 text-xs">
              <div className="flex justify-between text-gray-300">
                <span>Revenue Health</span>
                <span className="font-semibold text-emerald-400">88/100</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '88%' }}></div>
              </div>

              <div className="flex justify-between text-gray-300">
                <span>Cash Flow Stability</span>
                <span className="font-semibold text-amber-400">72/100</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: '72%' }}></div>
              </div>

              <div className="flex justify-between text-gray-300">
                <span>Collection Efficiency</span>
                <span className="font-semibold text-indigo-400">81/100</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: '81%' }}></div>
              </div>
            </div>
          </div>

          <p className="text-xs text-gray-400 border-t border-white/5 pt-3">
            Calculated across 14 financial indicators. Highest risk branch: <strong className="text-amber-400">Takoradi</strong>
          </p>
        </div>

        {/* Top Priority Recommended Actions */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                Recommended Executive Actions
              </h2>
              <span className="text-xs text-indigo-300 font-medium">Traceable to business data</span>
            </div>

            <div className="space-y-3">
              {recommendedActions.map((item) => (
                <div key={item.priority} className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 flex items-start gap-3.5 hover:border-indigo-500/30 transition-all">
                  <div className="w-6 h-6 rounded-lg bg-indigo-600/30 text-indigo-400 font-bold text-xs flex items-center justify-center border border-indigo-500/40 shrink-0">
                    {item.priority}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-white">{item.action}</h3>
                    <p className="text-xs text-gray-400 mt-0.5">{item.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex justify-end">
            <a href="/chat" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              Ask Copilot for detailed reasoning <ArrowUpRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpiData.map((kpi) => {
          const Icon = kpi.icon;
          const isUp = kpi.trend === 'up';
          return (
            <div key={kpi.name} className="glass-card rounded-2xl p-5 relative overflow-hidden">
              <div className="flex justify-between items-start">
                <span className="text-xs text-gray-400 font-medium">{kpi.name}</span>
                <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-2xl font-bold text-white tracking-tight">{kpi.value}</h3>
                <div className="flex items-center gap-1.5 mt-2 text-xs font-semibold">
                  {isUp ? (
                    <span className="text-emerald-400 flex items-center gap-0.5">
                      <ArrowUpRight className="w-4 h-4" /> {kpi.change}
                    </span>
                  ) : (
                    <span className="text-rose-400 flex items-center gap-0.5">
                      <ArrowDownRight className="w-4 h-4" /> {kpi.change}
                    </span>
                  )}
                  <span className="text-gray-500 font-normal">vs previous month</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Executive Alerts */}
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Active Executive Alerts
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">Detected by Isolation Forest & Z-score anomaly engines</p>
          </div>
          <a href="/alerts" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold">
            View All Alerts →
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topAlerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`p-4 rounded-xl border transition-all ${
                alert.severity === 'critical' 
                  ? 'bg-rose-950/20 border-rose-500/30' 
                  : alert.severity === 'high'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-indigo-950/20 border-indigo-500/30'
              }`}
            >
              <div className="flex justify-between items-start">
                <h3 className="text-sm font-semibold text-white">{alert.title}</h3>
                <span className={`text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-md ${
                  alert.severity === 'critical' 
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' 
                    : alert.severity === 'high'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                }`}>
                  {alert.severity}
                </span>
              </div>
              <p className="text-xs text-gray-300 mt-2 leading-relaxed">{alert.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
