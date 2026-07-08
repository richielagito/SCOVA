"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, BookOpen, ArrowRight, X, LogIn } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

export default function StudentDashboard({ user }) {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [joinCode, setJoinCode] = useState('');
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const res = await fetch('/api/joined-classes');
      if (res.ok) {
        const data = await res.json();
        setClasses(data);
      }
    } catch (error) {
      console.error("Error fetching classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinClass = async (e) => {
    e.preventDefault();
    setJoining(true);
    try {
        const res = await fetch('/api/join-class', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kode_kelas: joinCode })
        });
        
        const data = await res.json();

        if (res.ok && data.success) {
            toast.success(`Joined class: ${data.nama_kelas}`);
            setIsModalOpen(false);
            setJoinCode('');
            fetchClasses();
        } else {
            toast.error(data.error || "Failed to join class");
        }
    } catch (error) {
        console.error(error);
        toast.error("Error joining class");
    } finally {
        setJoining(false);
    }
  };

  return (
    <div>
       <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
         <div>
            <h1 className="text-2xl font-bold text-slate-900">Enrolled Classes</h1>
            <p className="text-slate-500">Access your courses and assignments</p>
         </div>
         <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary to-primary-container text-white rounded-xl hover:shadow-xl hover:shadow-primary/20 transition-all font-bold font-headline"
         >
            <LogIn size={20} /> Join Class
         </button>
       </div>

       {loading ? (
           <div className="flex items-center justify-center py-20">
               <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
           </div>
       ) : classes.length === 0 ? (
           <div className="text-center py-20 bg-white rounded-2xl border border-slate-100">
               <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mx-auto mb-4 transition-transform hover:scale-110 duration-300">
                   <BookOpen size={32} />
               </div>
               <h3 className="text-xl font-extrabold text-foreground mb-2 font-headline">No Classes Yet</h3>
               <p className="text-slate-500 mb-6 font-sans">Ask your teacher for a class code to join.</p>
               <button 
                    onClick={() => setIsModalOpen(true)}
                    className="text-primary font-bold hover:text-primary-container transition-colors font-headline"
                >
                    Join Class Now
                </button>
           </div>
       ) : (
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
               {classes.map((cls, index) => (
                   <div key={index} className="bg-white rounded-2xl p-6 border border-slate-200 hover:shadow-xl hover:shadow-primary/5 hover:border-primary/20 transition-all group">
                       <div className="flex items-start justify-between mb-4">
                           <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-primary-container text-white flex items-center justify-center shadow-lg shadow-primary/20 transition-transform group-hover:scale-110">
                               <BookOpen size={24} />
                           </div>
                           <span className="px-3 py-1 rounded-full bg-surface-low text-primary text-xs font-mono font-bold border border-primary/10">
                               {cls.kode_kelas}
                           </span>
                       </div>
                       <h3 className="text-xl font-extrabold text-foreground mb-2 line-clamp-1 font-headline">{cls.nama_kelas}</h3>
                       <p className="text-slate-500 text-sm mb-6 font-sans font-medium uppercase tracking-wider">Student Class</p>
                       
                       <Link 
                            href={`/kelas-murid/${cls.kode_kelas}`}
                            className="w-full py-3 rounded-xl border border-slate-200 text-slate-700 font-bold flex items-center justify-center gap-2 group-hover:bg-primary group-hover:text-white group-hover:border-primary transition-all font-headline"
                        >
                           Enter Class <ArrowRight size={18} />
                       </Link>
                   </div>
               ))}
           </div>
       )}

       {/* Join Class Modal */}
       {isModalOpen && (
           <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
               <motion.div 
                 initial={{ opacity: 0, scale: 0.95 }}
                 animate={{ opacity: 1, scale: 1 }}
                 className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-100"
               >
                   <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-surface-low/30">
                       <h3 className="text-xl font-extrabold text-foreground font-headline">Join a Class</h3>
                       <button onClick={() => setIsModalOpen(false)} className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all">
                           <X size={20} />
                       </button>
                   </div>
                   
                   <form onSubmit={handleJoinClass} className="p-8">
                       <div className="mb-6">
                           <label className="block text-sm font-bold text-slate-700 mb-2 font-sans">Class Code</label>
                           <input 
                                type="text" 
                                value={joinCode}
                                onChange={(e) => setJoinCode(e.target.value)}
                                className="w-full px-4 py-4 text-primary rounded-2xl border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all font-mono text-center tracking-widest text-2xl uppercase font-bold"
                                placeholder="XXXXXX"
                                required
                           />
                           <p className="text-xs text-slate-500 mt-4 text-center font-medium">Ask your teacher for the 6-character code</p>
                       </div>
                       <button 
                            type="submit" 
                            disabled={joining}
                            className="w-full py-4 rounded-2xl bg-gradient-to-r from-primary to-primary-container text-white font-bold hover:shadow-xl hover:shadow-primary/30 transition-all flex items-center justify-center gap-2 font-headline"
                        >
                            {joining ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>Join Class <ArrowRight size={20} /></>
                            )}
                        </button>
                   </form>
               </motion.div>
           </div>
       )}
    </div>
  );
}
