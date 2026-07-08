"use client";
import React from 'react';
import Link from 'next/link';
import { Facebook, Instagram, Linkedin, Heart } from 'lucide-react';
import { useSession } from '../hooks/useSession';

export default function Footer() {
  const { session } = useSession();
  return (
    <footer className="bg-foreground text-white py-24">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-16 mb-20">
            {/* Brand */}
            <div className="col-span-1 lg:col-span-2">
                 <Link href="/" className="text-4xl font-extrabold flex items-center mb-8 font-headline tracking-tight">
                    Scova<span className="text-primary-container">.ai</span>
                </Link>
                <p className="text-slate-400 max-w-sm leading-relaxed font-sans text-lg">
                    The leading AI-powered essay grading platform designed to empower educators and inspire students through instant, objective feedback.
                </p>
            </div>

            {/* Links */}
            <div>
                <h4 className="font-bold text-xl mb-8 font-headline">Product</h4>
                <ul className="space-y-4 font-sans">
                    <li><Link href="#how-it-works" className="text-slate-400 hover:text-white transition-colors">How It Works</Link></li>
                    <li><Link href="#features" className="text-slate-400 hover:text-white transition-colors">Features</Link></li>
                    <li><Link href={session ? "/dashboard" : "/login-register"} className="text-slate-400 hover:text-white transition-colors">Get Started</Link></li>
                </ul>
            </div>

            {/* Social */}
            <div>
                <h4 className="font-bold text-xl mb-8 font-headline">Connect</h4>
                <div className="flex gap-4">
                    <a href="#" className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary transition-all text-slate-300 hover:text-white shrink-0 shadow-sm">
                        <Facebook size={16} />
                    </a>
                    <a href="#" className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary transition-all text-slate-300 hover:text-white shrink-0 shadow-sm">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231 5.451-6.231zm-1.161 17.52h1.833L7.084 4.126H5.117L17.083 19.77z"/>
                        </svg>
                    </a>
                    <a href="#" className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary transition-all text-slate-300 hover:text-white shrink-0 shadow-sm">
                        <Instagram size={16} />
                    </a>
                    <a href="#" className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary transition-all text-slate-300 hover:text-white shrink-0 shadow-sm">
                        <Linkedin size={16} />
                    </a>
                </div>
            </div>
        </div>

        <div className="bg-white/5 h-[2px] w-full mb-12" />
        <div className="flex flex-col md:flex-row items-center justify-between gap-8 pt-4">
            <p className="text-slate-500 font-sans font-medium italic">© 2026 Scova.ai. All rights reserved.</p>
            <p className="text-slate-500 flex items-center gap-2 font-sans font-medium">
                The future of essay grading <Heart size={18} className="text-primary fill-current" /> by Scova Team
            </p>
        </div>
      </div>
    </footer>
  );
}
