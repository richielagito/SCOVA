"use client";
import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { useSession } from '../hooks/useSession';

export default function CTA() {
  const { session } = useSession();

  return (
    <section className="bg-gradient-to-br from-[#001E4D] via-foreground to-black text-white overflow-hidden relative">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2 opacity-60" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-primary-container/10 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2 opacity-40" />

      <div className="container mx-auto px-6 py-28 lg:py-40 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <motion.h2 
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-6xl font-black mb-8 font-headline tracking-tighter leading-tight"
          >
            Ready for <span className="text-primary-container italic underline decoration-primary/30 underline-offset-8">Better Feedback?</span>
          </motion.h2>
          
          <motion.p 
             initial={{ opacity: 0, y: 10 }}
             whileInView={{ opacity: 1, y: 0 }}
             viewport={{ once: true }}
             transition={{ delay: 0.1 }}
             className="text-xl text-slate-400 font-sans font-medium mb-12 max-w-xl mx-auto"
          >
            Join educators saving hours every week with AI-powered semantic grading.
          </motion.p>

          <motion.div
             initial={{ opacity: 0, scale: 0.95 }}
             whileInView={{ opacity: 1, scale: 1 }}
             viewport={{ once: true }}
             transition={{ delay: 0.2 }}
          >
            <Link 
              href={session ? "/dashboard" : "/login-register"} 
              className="inline-flex px-10 py-4 rounded-xl bg-gradient-to-r from-primary to-primary-container text-white font-bold text-lg hover:shadow-xl hover:shadow-primary/20 transition-all font-headline group/btn items-center"
            >
              Get Started Now <ArrowRight size={24} className="ml-3 group-hover/btn:translate-x-1 transition-transform" />
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
