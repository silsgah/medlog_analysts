import './globals.css';
import React from 'react';
import Navigation from '@/components/Navigation';

export const metadata = {
  title: 'AI Freight Operations & Financial Intelligence Copilot',
  description: 'Evidence-backed executive intelligence for freight and logistics operations',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-screen">
        <Navigation />
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
