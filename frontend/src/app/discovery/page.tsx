'use client';

import React, { useState } from 'react';
import { 
  Database, 
  Sparkles, 
  RefreshCw, 
  ArrowRight, 
  Layers, 
  ShieldCheck, 
  Table as TableIcon,
  CheckCircle2,
  Share2
} from 'lucide-react';

export default function DiscoveryPage() {
  const [runningDiscovery, setRunningDiscovery] = useState(false);
  const [activeTab, setActiveTab] = useState<'mappings' | 'graph'>('mappings');

  const [discoveredConcepts, setDiscoveredConcepts] = useState([
    { sql: 'tblReceipt', business: 'Customer Payments', category: 'finance', primary: true, desc: 'Customer invoice payment receipts and bank ledger postings' },
    { sql: 'tblWithdrawal', business: 'Bank Withdrawals', category: 'finance', primary: true, desc: 'Cash withdrawals, bank transfers and petty cash disbursements' },
    { sql: 'tblExpense', business: 'Operational Expenses', category: 'finance', primary: true, desc: 'Direct cost of sales, fuel, maintenance and administrative overhead' },
    { sql: 'tblInvoice', business: 'Customer Invoices', category: 'finance', primary: true, desc: 'Freight billing invoices, VAT breakdowns and balance due balances' },
    { sql: 'tblJob', business: 'Shipment Jobs', category: 'operations', primary: true, desc: 'Freight forwarding job files, container tracking and customs manifests' },
    { sql: 'tblCustomer', business: 'Customers & Clients', category: 'master', primary: true, desc: 'Shipper/consignee master records, credit terms and contact details' },
    { sql: 'tblBranch', business: 'Company Branches', category: 'master', primary: false, desc: 'Branch offices (Accra, Kumasi, Takoradi, Tema Port)' },
    { sql: 'tblWithdrawalCategory', business: 'Withdrawal Types', category: 'master', primary: false, desc: 'Lookup categories for bank and cash disbursements' },
  ]);

  const handleRunDiscovery = async () => {
    setRunningDiscovery(true);
    try {
      const res = await fetch('/api/v1/discovery/run', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.knowledge_graph?.concepts) {
          setDiscoveredConcepts(data.knowledge_graph.concepts.map((c: any) => ({
            sql: c.sql_name,
            business: c.business_name,
            category: c.category,
            primary: true,
            desc: c.description,
          })));
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setRunningDiscovery(false), 1500);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm mb-1">
            <Database className="w-4 h-4" />
            <span>AUTOMATIC SCHEMA DISCOVERY</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Business Knowledge Graph</h1>
          <p className="text-gray-400 text-sm mt-1">Converts raw SQL Server tables & views into high-level business domain concepts</p>
        </div>

        <button
          onClick={handleRunDiscovery}
          disabled={runningDiscovery}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 hover:opacity-90 transition-all flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${runningDiscovery ? 'animate-spin' : ''}`} />
          <span>{runningDiscovery ? 'Discovering SQL Server Schema...' : 'Run Auto-Discovery'}</span>
        </button>
      </div>

      {/* Discovery Metrics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Discovered Tables</span>
          <h3 className="text-2xl font-black text-white mt-1">42</h3>
          <span className="text-[11px] text-indigo-400 font-mono mt-0.5 block">SQL Server INFORMATION_SCHEMA</span>
        </div>
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Primary Entities</span>
          <h3 className="text-2xl font-black text-emerald-400 mt-1">12</h3>
          <span className="text-[11px] text-emerald-400 font-mono mt-0.5 block">Core Freight Concepts</span>
        </div>
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Inferred Relationships</span>
          <h3 className="text-2xl font-black text-cyan-400 mt-1">68</h3>
          <span className="text-[11px] text-cyan-400 font-mono mt-0.5 block">FK & Heuristic Mapping</span>
        </div>
        <div className="glass-panel p-4 rounded-xl text-center">
          <span className="text-xs text-gray-400 uppercase font-medium">Stored Procedures</span>
          <h3 className="text-2xl font-black text-purple-400 mt-1">19</h3>
          <span className="text-[11px] text-purple-400 font-mono mt-0.5 block">sys.procedures Introspected</span>
        </div>
      </div>

      {/* Mappings & Concept Table */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-6">
        <div className="flex justify-between items-center pb-4 border-b border-white/10">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            SQL Schema to Business Concept Mappings
          </h2>
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Copilot reasons over Business Concepts, not raw SQL names
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-slate-900/80 text-gray-400 uppercase font-mono border-b border-white/10">
              <tr>
                <th className="py-3 px-4">Raw SQL Table</th>
                <th className="py-3 px-4">→</th>
                <th className="py-3 px-4">Mapped Business Concept</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Entity Type</th>
                <th className="py-3 px-4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans">
              {discoveredConcepts.map((item, idx) => (
                <tr key={idx} className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-cyan-300 font-semibold">{item.sql}</td>
                  <td className="py-3.5 px-4 text-gray-500"><ArrowRight className="w-4 h-4 text-indigo-400" /></td>
                  <td className="py-3.5 px-4 font-bold text-white">{item.business}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] uppercase font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      {item.category}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {item.primary ? (
                      <span className="text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Primary Entity
                      </span>
                    ) : (
                      <span className="text-gray-500">Lookup / Attribute</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-gray-400 leading-normal">{item.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
