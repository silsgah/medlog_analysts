'use client';

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  RefreshCw, 
  CheckCircle2, 
  Activity, 
  Sliders,
  Sparkles,
  Filter
} from 'lucide-react';

export default function AlertsPage() {
  const [scanning, setScanning] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  const [alerts, setAlerts] = useState([
    { id: '1', type: 'suspicious_withdrawal', metric: 'Withdrawal Amount', severity: 'critical', current: 'GHS 45,000', expected: 'GHS 12,000', method: 'Z-Score (z=3.8)', status: 'active', detail: 'Cash withdrawal recorded at Takoradi Branch without attached customer invoice receipt.' },
    { id: '2', type: 'duplicate_payment', metric: 'Customer Payment', severity: 'high', current: '2 occurrences', expected: '1 occurrence', method: 'Exact Match', status: 'active', detail: 'Duplicate customer payment receipt of GHS 18,500 recorded within 4 minutes.' },
    { id: '3', type: 'delayed_collection', metric: 'Days Outstanding', severity: 'high', current: '94 days', expected: '30 days', method: 'Threshold Rule', status: 'active', detail: 'Invoice #INV-9042 for Customer ABC severely past due.' },
    { id: '4', type: 'expense_spike', metric: 'Fuel Expense', severity: 'medium', current: 'GHS 28,400', expected: 'GHS 19,200', method: 'Rolling Stats (14d)', status: 'active', detail: 'Unusual fuel consumption spike flagged for Fleet Unit 04.' },
    { id: '5', type: 'revenue_drop', metric: 'Daily Revenue', severity: 'medium', current: 'GHS 32,000', expected: 'GHS 78,000', method: 'Seasonality & Trend', status: 'acknowledged', detail: 'Revenue drop detected on Branch Kumasi vs 4-week historical moving average.' },
  ]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await fetch('/api/v1/alerts/scan', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.alerts_created > 0) {
          // updated
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setScanning(false), 1200);
    }
  };

  const handleAcknowledge = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'acknowledged' } : a))
    );
  };

  const handleResolve = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'resolved' } : a))
    );
  };

  const filteredAlerts = alerts.filter(a => 
    filterSeverity === 'all' ? true : a.severity === filterSeverity
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm mb-1">
            <Activity className="w-4 h-4" />
            <span>AI ANOMALY DETECTION ENGINE</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Alerts & Anomalies</h1>
          <p className="text-gray-400 text-sm mt-1">Multi-algorithmic statistical detection across transactions & operational logs</p>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 text-white font-semibold text-sm shadow-lg shadow-amber-500/20 hover:opacity-90 transition-all flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          <span>{scanning ? 'Running Anomaly Detection...' : 'Run Immediate Scan'}</span>
        </button>
      </div>

      {/* Algorithms Overview Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Primary Model</span>
          <h3 className="text-sm font-bold text-white mt-1">Isolation Forest</h3>
          <span className="text-[11px] text-indigo-400 font-mono mt-0.5 block">Unsupervised Contamination</span>
        </div>
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Statistical Filter</span>
          <h3 className="text-sm font-bold text-white mt-1">Z-Score & Modified MAD</h3>
          <span className="text-[11px] text-cyan-400 font-mono mt-0.5 block">Standard Deviation Threshold</span>
        </div>
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Moving Average</span>
          <h3 className="text-sm font-bold text-white mt-1">Rolling 14d Statistics</h3>
          <span className="text-[11px] text-emerald-400 font-mono mt-0.5 block">Dynamic Deviation Bands</span>
        </div>
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Pattern Drift</span>
          <h3 className="text-sm font-bold text-white mt-1">Seasonality & Autocorr</h3>
          <span className="text-[11px] text-amber-400 font-mono mt-0.5 block">Periodicity Analysis</span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex justify-between items-center glass-panel p-3.5 rounded-xl">
        <div className="flex items-center gap-2 text-xs font-semibold text-gray-300">
          <Filter className="w-4 h-4 text-indigo-400" />
          <span>Filter Severity:</span>
          {['all', 'critical', 'high', 'medium'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1 rounded-lg capitalize transition-all ${
                filterSeverity === sev
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-400">{filteredAlerts.length} active alerts requiring review</span>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`glass-panel p-5 rounded-2xl border transition-all ${
              alert.severity === 'critical'
                ? 'border-rose-500/40 bg-rose-950/10'
                : alert.severity === 'high'
                ? 'border-amber-500/40 bg-amber-950/10'
                : 'border-indigo-500/40 bg-indigo-950/10'
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center gap-3">
                  <span className={`text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-md ${
                    alert.severity === 'critical'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      : alert.severity === 'high'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  }`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">Method: {alert.method}</span>
                </div>

                <h3 className="text-base font-bold text-white mt-2 capitalize">
                  {alert.type.replace('_', ' ')} — {alert.metric}
                </h3>
                <p className="text-xs text-gray-300 mt-1">{alert.detail}</p>
              </div>

              {/* Status Action Buttons */}
              <div className="flex items-center gap-2">
                {alert.status === 'active' && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 text-gray-300 text-xs font-semibold hover:text-white border border-white/10"
                  >
                    Acknowledge
                  </button>
                )}
                {alert.status !== 'resolved' ? (
                  <button
                    onClick={() => handleResolve(alert.id)}
                    className="px-3 py-1.5 rounded-xl bg-emerald-600/30 text-emerald-300 text-xs font-semibold hover:bg-emerald-600/50 border border-emerald-500/40 flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Resolve
                  </button>
                ) : (
                  <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> Resolved
                  </span>
                )}
              </div>
            </div>

            {/* Metrics Breakdown Box */}
            <div className="mt-4 pt-3 border-t border-white/10 flex gap-6 text-xs font-mono">
              <div>
                <span className="text-gray-500 block text-[10px] uppercase">Current Observed Value</span>
                <span className="text-rose-400 font-bold">{alert.current}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px] uppercase">Historical Expected Benchmark</span>
                <span className="text-emerald-400 font-bold">{alert.expected}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
