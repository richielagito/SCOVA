"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { 
  Cpu,
  Zap,
  LayoutDashboard,
  CheckCircle 
} from 'lucide-react';

const features = [
  {
    icon: <Cpu size={32} />,
    title: "AI Powered",
    description: "Gemini 2.0 Logic for deep semantic accuracy."
  },
  {
    icon: <Zap size={32} />,
    title: "Full Context",
    description: "Goes beyond keywords to understand meaning."
  },
  {
    icon: <LayoutDashboard size={32} />,
    title: "Class Sync",
    description: "Manage classes and students from one place."
  },
  {
    icon: <CheckCircle size={32} />,
    title: "Rubric Scoring",
    description: "Fair, consistent, and rubric-driven evaluations."
  }
];

export default function Features() {
  return (
    <section id="features" className="py-24 bg-background">
      <div className="container mx-auto px-6">
        <div className="max-w-xl mb-20 text-left">
          <motion.h2 
             initial={{ opacity: 0, y: 10 }}
             whileInView={{ opacity: 1, y: 0 }}
             viewport={{ once: true }}
             className="text-3xl md:text-5xl font-black text-foreground mb-6 font-headline tracking-tighter"
          >
            Core Capabilities
          </motion.h2>
          <p className="text-slate-500 text-lg font-sans font-medium">
             Powerful technology made simple for the modern classroom.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.4 }}
              className="aspect-square h-full p-8 rounded-3xl bg-surface-low border border-surface-low/50 hover:bg-white hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 transition-all duration-150 group flex flex-col justify-center items-center text-center"
            >
              <div className="w-14 h-14 rounded-2xl bg-white shadow-sm flex items-center justify-center text-primary mb-6 group-hover:bg-gradient-to-br group-hover:from-primary group-hover:to-primary-container group-hover:text-white transition-all duration-200 shrink-0">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold text-foreground mb-2 font-headline tracking-tight">{feature.title}</h3>
              <p className="text-slate-500 text-sm font-sans font-medium leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
