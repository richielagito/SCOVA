"use client";
import React, { useState } from 'react';
import { X, ArrowLeft, ArrowRight, ChevronDown, Check, Info, FileText, BookOpen, Clock, Download, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn, renderHighlightedEssay } from '@/lib/utils';

export default function ManualReview({ result, assignment, onClose, onSave }) {
    const [viewMode, setViewMode] = useState('highlight'); // 'highlight' or 'plain'
    const [isPublished, setIsPublished] = useState(result?.status === 'published');
    const [reviewForm, setReviewForm] = useState({
        grade: result?.nilai || result?.grade || 0,
        feedback: result?.feedback || '',
        sub_criteria_scores: result?.sub_criteria_scores || []
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSave = async (status) => {
        setIsSubmitting(true);
        // Ensure grade is a number before saving
        const finalForm = {
            ...reviewForm,
            grade: parseInt(reviewForm.grade) || 0,
            sub_criteria_scores: reviewForm.sub_criteria_scores.map(s => ({
                ...s,
                grade: parseInt(s.grade) || 0
            })),
            is_published: status === 'published' ? true : (status === 'draft' ? false : isPublished)
        };
        await onSave(finalForm, status);
        setIsSubmitting(false);
    };

    const similarity = result?.similarity ? (result.similarity * 100).toFixed(1) : "0";
    const strengthsCount = result?.highlights?.filter(h => h.category === 'strong' || h.type === 'strength')?.length || 0;
    const improvementsCount = result?.highlights?.filter(h => h.category === 'weak' || h.type === 'improvement')?.length || 0;

    const getFilenameFromUrl = (url) => {
        if (!url) return "";
        return url.split('/').pop().split('?')[0];
    };

    const getFileExtension = (url) => {
        if (!url) return "";
        const filename = getFilenameFromUrl(url);
        return filename.split('.').pop().toUpperCase();
    };

    const formatDate = (dateValue) => {
        if (!dateValue) return "-";
        try {
            // Jika sudah diformat manual sebelumnya, jangan diproses lagi
            if (typeof dateValue === 'string' && dateValue.includes(" | ")) return dateValue;

            // Coba parsing langsung dulu (paling aman untuk format GMT/ISO standar)
            let dateObj = new Date(dateValue);

            // Jika gagal parsing langsung, coba bersihkan spasi (khusus format "YYYY-MM-DD HH:MM:SS")
            if (isNaN(dateObj.getTime()) && typeof dateValue === 'string') {
                const safeDateStr = dateValue.trim().replace(" ", "T");
                dateObj = new Date(safeDateStr);
            }

            // Jika tetap Invalid Date setelah semua upaya
            if (isNaN(dateObj.getTime())) {
                return String(dateValue);
            }

            const d = dateObj.toLocaleDateString('id-ID', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
            const t = dateObj.toLocaleTimeString('id-ID', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            }).replace('.', ':');

            return `${d} | ${t}`;
        } catch (e) {
            return String(dateValue);
        }
    };

    return (
        <div className="fixed inset-0 bg-white z-[150] flex flex-col font-sans text-slate-900 animate-in fade-in duration-300">
            {/* Topbar */}
            <div className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm relative z-20">
                <div className="flex items-center gap-6">
                    <button onClick={onClose} className="group flex items-center gap-2 text-slate-500 hover:text-primary transition-colors font-bold font-headline">
                        <ArrowLeft size={20} />
                        <span>Exit Review</span>
                    </button>
                    <div className="h-8 w-px bg-slate-200" />
                    <div>
                        <h2 className="text-lg font-extrabold text-foreground font-headline tracking-tight">{assignment?.judul}</h2>
                        <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5 flex items-center gap-2">
                            <span className="text-primary">{assignment?.class_name}</span>
                            <span className="text-slate-300">&bull;</span>
                            <span>{result?.nama_murid || result?.name}</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3 bg-slate-100 p-1 rounded-xl">
                        <button
                            onClick={() => setIsPublished(false)}
                            className={cn(
                                "px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all",
                                !isPublished ? "bg-white text-slate-700 shadow-sm" : "text-slate-400 hover:text-slate-600"
                            )}
                        >
                            Draft
                        </button>
                        <button
                            onClick={() => setIsPublished(true)}
                            className={cn(
                                "px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all",
                                isPublished ? "bg-emerald-500 text-white shadow-sm" : "text-slate-400 hover:text-slate-600"
                            )}
                        >
                            Published
                        </button>
                    </div>
                    <div className="h-8 w-px bg-slate-200" />
                    <button
                        disabled={isSubmitting}
                        onClick={() => handleSave(isPublished ? 'published' : 'draft')}
                        className="px-6 py-2.5 bg-primary text-white text-sm font-bold rounded-2xl hover:bg-primary-container transition-all shadow-lg shadow-primary/20 flex items-center gap-2 disabled:opacity-50 font-headline"
                    >
                        {isSubmitting ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <Check size={18} />
                        )}
                        Save Changes
                    </button>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Main Essay Panel */}
                <div className="flex-1 bg-white overflow-y-auto relative z-10 border-r border-slate-100">
                    <div className="max-w-4xl mx-auto p-10 lg:p-16 space-y-12">
                        {/* Header Info */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-5">
                                <div className="w-16 h-16 rounded-3xl bg-primary/5 text-primary flex items-center justify-center font-black text-2xl border-2 border-primary/10 shadow-sm">
                                    {result?.nama_murid?.charAt(0) || result?.name?.charAt(0) || 'S'}
                                </div>
                                <div>
                                    <div className="text-xl font-extrabold text-foreground font-headline tracking-tight">{result?.nama_murid || result?.name}</div>
                                    <div className="text-xs text-slate-400 font-bold uppercase tracking-widest flex items-center gap-2 mt-1.5">
                                        <Clock size={14} className="text-primary/60" />
                                        Submitted {formatDate(result?.created_at)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Simplified Assignment Description */}
                        <div className="space-y-4">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                                Assignment Description
                            </div>
                            <p className="text-slate-600 leading-relaxed font-sans font-medium text-base">
                                {assignment?.deskripsi}
                            </p>

                            {/* Simplified Assignment Files */}
                            {assignment?.file_path && (
                                <div className="space-y-4">
                                    <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest font-sans">Reference Material</p>
                                    <div className="max-w-md">
                                        <div
                                            className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 hover:bg-slate-100 transition-colors group cursor-pointer"
                                            onClick={() => window.open(assignment.file_path, '_blank')}
                                        >
                                            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm text-primary group-hover:scale-110 transition-transform">
                                                <FileText size={20} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold text-slate-700 truncate">{getFilenameFromUrl(assignment.file_path)}</p>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Click to view &bull; {getFileExtension(assignment.file_path)}</p>
                                            </div>
                                            <ExternalLink size={16} className="text-slate-300 group-hover:text-primary transition-colors mr-1" />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* View Controls & Content */}
                        <div className="space-y-8 pt-4">
                            <div className="flex items-center justify-between border-b border-slate-100 pb-6">
                                <div className="flex bg-slate-100 p-1 rounded-2xl w-fit">
                                    <button
                                        onClick={() => setViewMode('highlight')}
                                        className={cn(
                                            "px-6 py-2.5 text-xs font-bold rounded-xl font-headline",
                                            viewMode === 'highlight' ? "bg-white text-primary shadow-sm" : "text-slate-500"
                                        )}
                                    >
                                        AI Highlights
                                    </button>
                                    <button
                                        onClick={() => setViewMode('plain')}
                                        className={cn(
                                            "px-6 py-2.5 text-xs font-bold rounded-xl font-headline",
                                            viewMode === 'plain' ? "bg-white text-primary shadow-sm" : "text-slate-500"
                                        )}
                                    >
                                        Original Text
                                    </button>
                                </div>

                                {viewMode === 'highlight' && (
                                    <div className="flex items-center gap-6">
                                        <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-wider">
                                            <div className="w-3 h-3 rounded-full bg-green-500/30 border border-green-500/50"></div>
                                            Strengths
                                        </div>
                                        <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-wider">
                                            <div className="w-3 h-3 rounded-full bg-red-500/30 border border-red-500/50"></div>
                                            Improvements
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="relative overflow-visible">
                                <div className="prose prose-slate max-w-none overflow-visible">
                                    <div className="text-slate-800 leading-[2.2] font-serif text-[19px] whitespace-pre-wrap antialiased overflow-visible">
                                        {viewMode === 'plain' ? (
                                            result?.essay_text || "No essay text available."
                                        ) : (
                                            renderHighlightedEssay(result?.essay_text, result?.highlights)
                                        )}
                                    </div>
                                </div>
                                <div className="mt-8 pt-8 border-t border-slate-50 flex justify-end">
                                    <span className="text-xs text-slate-400 font-medium italic flex items-center gap-2">
                                        <Info size={14} />
                                        Hover over highlights to see detailed feedback from Gemini
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Sidebar Panel */}
                <div className="w-full lg:w-[420px] bg-slate-50/50 overflow-y-auto relative z-10 flex flex-col shadow-[inset_1px_0_0_0_rgba(0,0,0,0.05)]">
                    <div className="p-8 lg:p-10 space-y-5 flex-1">
                        {/* Score Section */}
                        <div className="bg-white border-2 border-slate-100 rounded-[2.5rem] p-10 shadow-sm group hover:border-primary/20 transition-all text-center relative overflow-hidden">
                            <div className="text-lg font-black uppercase tracking-[0.1em] mb-6 font-sans relative z-10">Score</div>
                            <div className="relative z-10 flex items-center justify-center gap-4">
                                <input
                                    type="number"
                                    inputMode="numeric"
                                    min="0" max="100"
                                    value={reviewForm.grade}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        setReviewForm({ ...reviewForm, grade: val === '' ? '' : parseInt(val) });
                                    }}
                                    onBlur={() => {
                                        if (reviewForm.grade === '') {
                                            setReviewForm({ ...reviewForm, grade: 0 });
                                        }
                                    }}
                                    className="w-32 bg-surface-low border-2 border-slate-100 rounded-3xl px-6 py-5 text-4xl font-black text-slate-900 focus:border-primary focus:ring-8 focus:ring-primary/10 outline-none transition-all shadow-inner text-center"
                                />
                                <span className="text-slate-300 text-3xl font-black font-headline ml-1">/ 100</span>
                            </div>
                        </div>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white border-2 border-slate-100 rounded-3xl p-6 shadow-sm group hover:border-primary/20 transition-all text-center">
                                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 font-sans">Similarity</div>
                                <div className="text-2xl font-mono font-black text-slate-700 tracking-tighter">{similarity}%</div>
                            </div>
                            <div className="bg-white border-2 border-slate-100 rounded-3xl p-6 shadow-sm group hover:border-primary/20 transition-all text-center flex flex-col items-center justify-center">
                                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 font-sans">Highlights</div>
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center gap-1 text-green-600 font-bold">
                                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                        {strengthsCount}
                                    </div>
                                    <div className="flex items-center gap-1 text-red-600 font-bold">
                                        <span className="w-2 h-2 rounded-full bg-red-500"></span>
                                        {improvementsCount}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Feedback Section */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between px-1">
                                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-sans">Feedback & Guidance</div>
                                <div className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border border-blue-100">AI Generated</div>
                            </div>
                            <div className="bg-white border-2 border-slate-100 rounded-[2rem] p-6 shadow-sm relative group focus-within:border-primary/30 focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                                <textarea
                                    value={reviewForm.feedback}
                                    onChange={(e) => setReviewForm({ ...reviewForm, feedback: e.target.value })}
                                    className="w-full min-h-[200px] text-[15px] text-slate-700 leading-relaxed font-medium bg-transparent outline-none resize-y"
                                    placeholder="Provide your feedback here..."
                                />
                            </div>
                        </div>

                        {/* Aspects Breakdown */}
                        <div className="space-y-6 pb-20">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-1 font-sans">Detailed Breakdown</div>
                            <div className="space-y-4">
                                {reviewForm.sub_criteria_scores && reviewForm.sub_criteria_scores.length > 0 ? (
                                    reviewForm.sub_criteria_scores.map((sub, idx) => (
                                        <div key={idx} className="bg-white border-2 border-slate-50 rounded-3xl p-6 shadow-sm group hover:border-primary/20 transition-all">
                                            <div className="flex justify-between items-center mb-4">
                                                <span className="text-sm font-extrabold text-foreground font-headline group-hover:text-primary transition-colors">Question {sub.question}</span>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-[10px] font-mono font-bold text-slate-400">{(sub.similarity * 100).toFixed(0)}% Match</span>
                                                    <input
                                                        type="number"
                                                        value={sub.grade}
                                                        onChange={e => {
                                                            const val = e.target.value;
                                                            const newScores = [...reviewForm.sub_criteria_scores];
                                                            newScores[idx].grade = val === '' ? '' : parseInt(val);
                                                            setReviewForm({ ...reviewForm, sub_criteria_scores: newScores });
                                                        }}
                                                        onBlur={() => {
                                                            if (reviewForm.sub_criteria_scores[idx].grade === '') {
                                                                const newScores = [...reviewForm.sub_criteria_scores];
                                                                newScores[idx].grade = 0;
                                                                setReviewForm({ ...reviewForm, sub_criteria_scores: newScores });
                                                            }
                                                        }}
                                                        className="w-16 text-center bg-surface-low border border-slate-100 rounded-xl px-3 py-2 text-sm font-black text-primary focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all shadow-inner"
                                                    />
                                                </div>
                                            </div>
                                            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary transition-all duration-700"
                                                    style={{ width: `${(sub.similarity * 100) || 0}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    ['Content Accuracy', 'Grammar & Style', 'Structure'].map(aspect => (
                                        <div key={aspect} className="bg-white border-2 border-slate-50 rounded-3xl p-6 shadow-sm text-center lg:text-left">
                                            <div className="flex justify-between items-center mb-3">
                                                <span className="text-sm font-extrabold text-foreground font-headline">{aspect}</span>
                                                <span className="text-sm font-black text-primary">{reviewForm.grade > 0 ? Math.floor(reviewForm.grade * 0.9) : '-'}/100</span>
                                            </div>
                                            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-primary" style={{ width: `${reviewForm.grade || 0}%` }}></div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
