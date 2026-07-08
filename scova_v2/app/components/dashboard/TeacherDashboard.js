"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, BookOpen, ArrowRight, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

export default function TeacherDashboard({ user }) {
    const [classes, setClasses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newClassName, setNewClassName] = useState('');
    const [createdClassCode, setCreatedClassCode] = useState(null);
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        fetchClasses();
    }, []);

    const fetchClasses = async () => {
        try {
            const res = await fetch('/api/classes');
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

    const handleCreateClass = async (e) => {
        e.preventDefault();
        setCreating(true);
        try {
            const formData = new FormData();
            formData.append('class_name', newClassName);

            const res = await fetch('/create-class', {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                setCreatedClassCode(data.class_code);
                fetchClasses(); // Refresh list
                toast.success("Class created successfully!");
            } else {
                toast.error("Failed to create class");
            }
        } catch (error) {
            console.error(error);
            toast.error("Error creating class");
        } finally {
            setCreating(false);
        }
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setNewClassName('');
        setCreatedClassCode(null);
    }

    return (
        <div>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">My Classes</h1>
                    <p className="text-slate-500">Manage your classes and assignments</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary to-primary-container text-white rounded-xl hover:shadow-xl hover:shadow-primary/20 transition-all font-bold font-headline"
                >
                    <Plus size={20} /> Create Class
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
                    <p className="text-slate-500 mb-6 font-sans">Create your first class to get started.</p>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="text-primary font-bold hover:text-primary-container transition-colors font-headline"
                    >
                        Create Class Now
                    </button>
                </div>
            ) : (
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-surface-low border-b border-slate-200">
                                <tr>
                                    <th className="px-6 py-4 font-bold text-slate-600 text-sm font-sans uppercase tracking-wider">Class Name</th>
                                    <th className="px-6 py-4 font-bold text-slate-600 text-sm font-sans uppercase tracking-wider">Class Code</th>
                                    <th className="px-6 py-4 font-bold text-slate-600 text-sm font-sans uppercase tracking-wider">Created At</th>
                                    <th className="px-6 py-4 font-bold text-slate-600 text-sm font-sans uppercase tracking-wider text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {classes.map((cls) => (
                                    <tr key={cls.id} className="hover:bg-primary/5 transition-colors group">
                                        <td className="px-6 py-4 font-bold text-foreground font-headline">{cls.nama_kelas}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-3 py-1 text-primary font-mono font-bold bg-primary/10 rounded-lg border border-primary/10">
                                                {cls.kode_kelas}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 text-sm font-sans font-medium">
                                            {new Date(cls.created_at).toLocaleDateString('id-ID', {
                                                day: 'numeric',
                                                month: 'long',
                                                year: 'numeric'
                                            })} | {new Date(cls.created_at).toLocaleTimeString('id-ID', {
                                                hour: '2-digit',
                                                minute: '2-digit',
                                                hour12: false
                                            }).replace('.', ':')}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <Link href={`/kelas/${cls.kode_kelas}`} className="inline-flex items-center gap-1 text-primary hover:text-primary-container font-bold text-sm font-headline transition-colors">
                                                View Details <ArrowRight size={16} />
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Create Class Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-100"
                    >
                        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-surface-low/30">
                            <h3 className="text-xl font-extrabold text-foreground font-headline">Create New Class</h3>
                            <button onClick={closeModal} className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-8">
                            {!createdClassCode ? (
                                <form onSubmit={handleCreateClass} className="space-y-6">
                                    <div>
                                        <label className="block text-sm font-bold text-slate-700 mb-2 font-sans">Class Name</label>
                                        <input
                                            type="text"
                                            value={newClassName}
                                            onChange={(e) => setNewClassName(e.target.value)}
                                            className="w-full px-4 py-4 text-primary rounded-2xl border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all font-bold"
                                            placeholder="e.g. Bahasa Indonesia X-A"
                                            required
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={creating}
                                        className="w-full py-4 rounded-2xl bg-gradient-to-r from-primary to-primary-container text-white font-bold hover:shadow-xl hover:shadow-primary/30 transition-all flex items-center justify-center gap-2 font-headline"
                                    >
                                        {creating ? (
                                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        ) : (
                                            <>Create Class <ArrowRight size={20} /></>
                                        )}
                                    </button>
                                </form>
                            ) : (
                                <div className="text-center py-4">
                                    <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <BookOpen size={32} />
                                    </div>
                                    <h4 className="text-2xl font-extrabold text-foreground mb-2 font-headline">Class Created!</h4>
                                    <p className="text-slate-500 mb-6 font-sans font-medium">Share this code with your students:</p>
                                    <div className="bg-surface-low p-6 rounded-2xl font-mono text-3xl font-bold text-primary border-2 border-primary/10 tracking-widest mb-8 select-all shadow-inner text-center">
                                        {createdClassCode}
                                    </div>
                                    <button
                                        onClick={closeModal}
                                        className="w-full py-4 rounded-2xl bg-surface-low text-slate-700 font-bold hover:bg-slate-200 transition-all font-headline"
                                    >
                                        Close
                                    </button>
                                </div>
                            )}
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
