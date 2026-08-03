'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  MessageSquareCode, 
  FileText, 
  AlertTriangle, 
  Database, 
  Activity, 
  ShieldCheck 
} from 'lucide-react';

const navItems = [
  { href: '/', label: 'Executive Dashboard', icon: LayoutDashboard },
  { href: '/chat', label: 'Conversational Copilot', icon: MessageSquareCode },
  { href: '/reports', label: 'Executive Intelligence', icon: FileText },
  { href: '/alerts', label: 'Alerts & Anomalies', icon: AlertTriangle },
  { href: '/discovery', label: 'Knowledge Graph', icon: Database },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <aside className="w-64 glass-panel border-r border-white/10 flex flex-col justify-between p-4 h-screen sticky top-0">
      <div>
        {/* Brand Logo */}
        <div className="flex items-center gap-3 px-3 py-4 mb-6 border-b border-white/10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide leading-tight">MEDLOG AI</h1>
            <p className="text-xs text-indigo-300 font-medium">Executive Copilot</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/30 text-white border border-indigo-500/40 shadow-inner'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-indigo-400' : 'text-gray-400'}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
        <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
          <ShieldCheck className="w-4 h-4" />
          <span>Connected to SQL Server</span>
        </div>
        <p className="text-[11px] text-gray-500 leading-normal">
          Read-only ERP Intelligence Layer • Multi-Tenant Architecture
        </p>
      </div>
    </aside>
  );
}
