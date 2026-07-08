"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  BarChart, 
  Settings, 
  LogOut, 
  HelpCircle, 
  Menu, 
  X, 
  ChevronDown,
  User,
  Plus,
  ArrowRight
} from 'lucide-react';
import { createClient } from '@/lib/supabase';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export default function DashboardShell({ children, role, username, onLogout }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const supabase = createClient();

  // Auto-sync session with Flask backend to ensure it doesn't expire/desync
  React.useEffect(() => {
    const syncSession = async () => {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
            try {
                // Call set_session to ensure Flask knows who we are
                await fetch('/set_session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ access_token: session.access_token }),
                });
            } catch (e) {
                console.error("Session sync failed", e);
            }
        }
    };
    syncSession();
  }, [pathname]); // Re-sync on route change just to be super safe, or just []
    
  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 transform transition-transform duration-300 ease-in-out flex flex-col",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="h-16 flex items-center px-6 border-b border-slate-100">
           <Link href="/dashboard" className="text-2xl font-extrabold text-foreground flex items-center font-headline tracking-tight">
            Scova<span className="text-primary">.ai</span>
          </Link>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
            
             {/* Main Navigation */}
            <div className="space-y-1">
                <p className="px-4 text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 mt-4 font-sans">Menu</p>
                <Link 
                    href="/dashboard" 
                    className={cn(
                        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-bold font-sans",
                        pathname === '/dashboard' ? "bg-primary/10 text-primary" : "text-slate-600 hover:bg-primary/5 hover:text-primary"
                    )}
                >
                    <BarChart size={20} />
                    Dashboard
                </Link>
            </div>

            <div className="space-y-1 mt-auto">
                <p className="px-4 text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 mt-8 font-sans">Support</p>
                <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 hover:bg-primary/5 hover:text-primary transition-all font-bold font-sans">
                    <HelpCircle size={20} />
                    Help & Support
                </a>
                <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 hover:bg-primary/5 hover:text-primary transition-all font-bold font-sans">
                    <Settings size={20} />
                    Settings
                </a>
            </div>
        </div>

        <div className="p-4 border-t border-slate-100">
            <button 
                onClick={async () => {
                    await supabase.auth.signOut();
                    await fetch('/logout');
                    window.location.href = '/login-register';
                }}
                className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-red-500 hover:bg-red-50 transition-all font-bold font-sans"
            >
                <LogOut size={20} />
                Sign Out
            </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Topbar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-8">
            <button 
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 text-slate-600 hover:bg-primary/5 rounded-lg transition-all"
            >
                <Menu size={24} />
            </button>

            <div className="flex items-center gap-4 ml-auto">
                <div className="text-right hidden md:block">
                    <div className="text-sm font-extrabold text-foreground font-headline tracking-tight">{username || 'User'}</div>
                    <div className="text-xs text-primary font-bold font-sans uppercase tracking-wider">{role || 'Student'}</div>
                </div>
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary border border-primary/20 transition-all shadow-sm">
                    <User size={20} />
                </div>
            </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
            {children}
        </main>
      </div>
    </div>
  );
}
