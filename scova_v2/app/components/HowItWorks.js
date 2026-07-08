"use client";
import React from 'react';
import { UserPlus, Upload, ArrowRight, Zap, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const steps = [
  {
    id: 1,
    icon: <UserPlus size={28} />,
    title: "Setup Class",
    description: "Define your rubric with a reference answer."
  },
  {
    id: 2,
    icon: <ArrowRight size={28} />,
    title: "Join Code",
    description: "Students join via a secure 6-digit access code."
  },
  {
    id: 3,
    icon: <Upload size={28} />,
    title: "Upload Essay",
    description: "Students upload their work in PDF or DOCX."
  },
  {
    id: 4,
    icon: <Zap size={28} />,
    title: "Get Results",
    description: "AI Audit provides deep semantic evaluation."
  }
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-32 bg-[#fafbfd] overflow-hidden relative">
      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-3xl mx-auto text-center mb-28">
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-6xl font-black text-foreground mb-6 font-headline tracking-tighter"
          >
            How Scova Works
          </motion.h2>
          <p className="text-slate-500 text-lg font-sans font-medium">
            Seamless automated grading in four simple steps.
          </p>
        </div>

        <div className="relative">
          {/* Centered Dashed Line */}
          <div className="hidden lg:block absolute top-[110px] left-[10%] right-[10%] h-[1px] z-0">
            <svg width="100%" height="2" fill="none" className="opacity-10">
              <line x1="0" y1="1" x2="100%" y2="1" stroke="currentColor" strokeWidth="2" strokeDasharray="8 8" className="text-primary" />
            </svg>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 relative z-10">
            {steps.map((step, index) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                whileHover={{ y: -5 }}
                className="group relative"
              >
                <div className="flex flex-col items-center">

                  {/* Google Photos Style Number & Icon Integration */}
                  <div className="relative w-40 h-52 mb-8 flex items-center justify-center">
                    {/* Massive Number with Gradient Masking */}
                    <span className="absolute inset-0 flex items-center justify-center text-[14rem] font-black leading-none select-none pointer-events-none opacity-[0.08] lg:opacity-[0.12] transition-opacity duration-200 group-hover:opacity-[0.18] font-headline">
                      {step.id}
                    </span>

                    {/* The Masked Number Overlay (Google Photos Style) */}
                    <span className="absolute inset-0 flex items-center justify-center text-[14rem] font-black leading-none text-transparent bg-clip-text bg-gradient-to-br from-primary via-primary-container to-secondary opacity-0 group-hover:opacity-100 transition-all duration-300 transform scale-95 group-hover:scale-100 font-headline">
                      {step.id}
                    </span>

                    {/* Icon Node */}
                    <div className="relative z-10 w-20 h-20 rounded-[1.5rem] bg-white shadow-xl shadow-primary/10 flex items-center justify-center text-primary group-hover:scale-110 group-hover:bg-gradient-to-br group-hover:from-primary group-hover:to-primary-container group-hover:text-white transition-all duration-200 border border-slate-100">
                      {step.icon}
                    </div>

                    {/* Floating Decorative Elements */}
                    <div className="absolute -top-4 -right-4 w-12 h-12 bg-primary/10 rounded-full blur-xl opacity-0 group-hover:opacity-60 transition-opacity duration-300 pointer-events-none" />
                  </div>

                  <div className="text-center max-w-[240px] px-2">
                    <h3 className="text-2xl font-black text-foreground mb-3 font-headline tracking-tight group-hover:text-primary transition-colors duration-300">
                      {step.title}
                    </h3>
                    <p className="text-slate-500 text-sm leading-relaxed font-sans font-medium">
                      {step.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
