"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [session, setSession] = useState(null);
  const [scrolled, setScrolled] = useState(false);
  const supabase = createClient();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener("scroll", handleScroll);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const handleLogout = async () => {
      await supabase.auth.signOut();
      // Sync logout with Flask backend
      await fetch('/logout');
      window.location.href = "/";
  };

  const navLinks = [
    { name: "How It Works", href: "#how-it-works" },
    { name: "Features", href: "#features" },
  ];

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 w-full z-50 transition-all duration-500",
        scrolled
          ? "bg-surface-lowest/80 backdrop-blur-xl shadow-2xl shadow-primary/5 py-4"
          : "bg-transparent py-8"
      )}
    >
      <div className="container mx-auto px-6 flex items-center justify-between">
        <Link href="/" className="text-2xl font-extrabold text-foreground flex items-center font-headline tracking-tight">
          Scova<span className="text-primary">.ai</span>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-10">
          <div className="flex gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="text-slate-600 hover:text-primary font-bold transition-all font-sans relative group"
              >
                {link.name}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full" />
              </Link>
            ))}
          </div>
          
          {session ? (
              <div className="flex items-center gap-6">
                  <Link href="/dashboard" className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-primary-container text-white font-bold hover:shadow-xl hover:shadow-primary/20 transition-all font-headline">
                      Dashboard
                  </Link>
                   <button onClick={handleLogout} className="text-slate-600 hover:text-red-500 font-bold font-sans transition-colors cursor-pointer">Log out</button>
              </div>

          ) : (
            <Link
              href="/login-register"
              className="px-8 py-3 rounded-xl bg-gradient-to-r from-primary to-primary-container text-white font-bold hover:shadow-xl hover:shadow-primary/20 transition-all font-headline"
            >
              Get Started
            </Link>
          )}
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-slate-800"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden absolute top-full left-0 w-full bg-surface-lowest/95 backdrop-blur-2xl shadow-[0_40px_60px_-15px_rgba(0,0,0,0.1)] p-8 flex flex-col gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-xl text-slate-700 font-bold font-headline"
              onClick={() => setIsOpen(false)}
            >
              {link.name}
            </Link>
          ))}
            <div className="h-[2px] bg-surface-low my-2" />
             {session ? (
                 <>
                    <Link href="/dashboard" className="w-full text-center py-4 rounded-2xl bg-gradient-to-br from-primary to-primary-container text-white font-bold font-headline shadow-lg">Dashboard</Link>
                    <button onClick={handleLogout} className="w-full text-center py-4 text-red-500 font-bold font-headline">Log out</button>
                 </>
             ) : (
                 <Link
                    href="/login-register"
                    className="w-full text-center py-4 rounded-2xl bg-gradient-to-br from-primary to-primary-container text-white font-bold font-headline shadow-lg"
                    onClick={() => setIsOpen(false)}
                  >
                    Get Started
                  </Link>
             )}
        </div>
      )}
    </nav>
  );
}
