"use client";
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    ArrowLeft, Plus, Edit, Trash2, Download, FileText, Calendar, Clock, UploadCloud, X, ArrowRight, RotateCcw
} from 'lucide-react';
import { createClient } from '@/lib/supabase';
import DashboardShell from '@/app/components/dashboard/DashboardShell';
import ManualReview from '@/app/components/dashboard/ManualReview';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import Swal from 'sweetalert2';
import { toast } from 'sonner';

export default function ClassDetailsTeacher() {
    const { kode_kelas } = useParams();
    const router = useRouter();
    const supabase = createClient();
    const [user, setUser] = useState(null);

    const [classInfo, setClassInfo] = useState(null);
    const [assignments, setAssignments] = useState([]);
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedAssignmentId, setSelectedAssignmentId] = useState(null);
    const [gradingId, setGradingId] = useState(null); // submission id or 'bulk'

    // Modals
    const [isAddAssignmentOpen, setIsAddAssignmentOpen] = useState(false);
    const [isEditClassOpen, setIsEditClassOpen] = useState(false);
    const [editClassName, setEditClassName] = useState('');

    // Review Modal State
    const [isReviewOpen, setIsReviewOpen] = useState(false);
    const [reviewingResult, setReviewingResult] = useState(null);
    const [reviewForm, setReviewReviewForm] = useState({
        grade: 0,
        feedback: '',
        sub_criteria_scores: []
    });

    const selectedAssignment = useMemo(() => {
        if (!selectedAssignmentId) return null;
        return assignments.find(a => a.id === selectedAssignmentId);
    }, [assignments, selectedAssignmentId]);

    const isDeadlinePassed = (deadlineStr) => {
        if (!deadlineStr) return true;
        try {
            const deadline = new Date(deadlineStr.replace(" ", "T"));
            return new Date() > deadline;
        } catch (e) { return true; }
    };

    const handleGradeNow = async (submissionId) => {
        setGradingId(submissionId);
        try {
            const res = await fetch(`/api/submissions/grade/${submissionId}`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                toast.success('AI Grading completed!');
                fetchResults(selectedAssignmentId);
            } else {
                toast.error(data.error || 'Grading failed');
            }
        } catch (e) {
            console.error(e);
            toast.error('Error during AI grading');
        } finally {
            setGradingId(null);
        }
    };

    const handleBulkGrade = async (assignmentId) => {
        setGradingId('bulk');
        try {
            const res = await fetch(`/api/assignments/grade-bulk/${assignmentId}`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                toast.success(`Processed ${data.processed_count} submissions!`);
                fetchResults(assignmentId);
            } else {
                toast.error(data.error || 'Bulk grading failed');
            }
        } catch (e) {
            console.error(e);
            toast.error('Error during bulk grading');
        } finally {
            setGradingId(null);
        }
    };

    const handleOpenReview = (res) => {
        setReviewingResult(res);
        setReviewReviewForm({
            grade: res.nilai || res.grade || 0,
            feedback: res.feedback || '',
            sub_criteria_scores: res.sub_criteria_scores || []
        });
        setIsReviewOpen(true);
    };

    const handleSaveReview = async (formData, status = 'published') => {
        setSubmitting(true);
        try {
            const res = await fetch('/api/results/override', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: reviewingResult.id,
                    grade: formData.grade,
                    feedback: formData.feedback,
                    sub_criteria_scores: formData.sub_criteria_scores,
                    status: status
                })
            });

            if (res.ok) {
                toast.success(status === 'published' ? 'Result published!' : 'Draft saved!');
                setIsReviewOpen(false);
                fetchResults(selectedAssignmentId);
            } else {
                toast.error('Failed to save changes');
            }
        } catch (e) {
            console.error(e);
            toast.error('Error saving review');
        } finally {
            setSubmitting(false);
        }
    };

    // Form State
    const [newAssignment, setNewAssignment] = useState({
        judul: '',
        deskripsi: '',
        deadlineDate: '',
        deadlineTime: '',
        file: null,
        jawabanGuru: null
    });
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const init = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                router.push('/login-register');
                return;
            }
            setUser(session.user);
            await Promise.all([fetchClassInfo(), fetchAssignments()]);
            setLoading(false);
        };
        init();
    }, [kode_kelas]);

    const fetchClassInfo = async () => {
        try {
            const res = await fetch('/api/classes');
            if (res.ok) {
                const data = await res.json();
                const cls = data.find(c => c.kode_kelas === kode_kelas);
                if (cls) {
                    setClassInfo(cls);
                    setEditClassName(cls.nama_kelas);
                } else {
                    router.push('/dashboard'); // Class not found or not authorized
                }
            }
        } catch (e) {
            console.error(e);
        }
    };

    const fetchAssignments = async () => {
        try {
            const res = await fetch(`/api/assignments/${kode_kelas}`);
            if (res.ok) {
                const data = await res.json();
                setAssignments(data);
            }
        } catch (e) { console.error(e); }
    };

    const fetchResults = async (assignmentId) => {
        setResults([]); // Clear previous
        setSelectedAssignmentId(assignmentId);
        try {
            const res = await fetch(`/api/results/assignment/${assignmentId}`);
            if (res.ok) {
                const data = await res.json();
                setResults(data);
            }
        } catch (e) { console.error(e); }
    };

    const handleDeleteClass = async () => {
        const result = await Swal.fire({
            title: 'Are you sure?',
            text: "You won't be able to revert this!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc2626',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Yes, delete it!'
        });

        if (result.isConfirmed) {
            try {
                const res = await fetch(`/api/class/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ kode_kelas })
                });
                if (res.ok) {
                    toast.success('Class has been deleted.');
                    router.push('/dashboard');
                } else {
                    toast.error('Failed to delete class');
                }
            } catch (e) { console.error(e); }
        }
    };

    const handleEditClass = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch('/api/class/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kode_kelas, nama_kelas: editClassName })
            });
            if (res.ok) {
                toast.success('Class updated successfully');
                setIsEditClassOpen(false);
                fetchClassInfo();
            } else {
                toast.error('Failed to update class');
            }
        } catch (e) { console.error(e); }
    };

    const handleAddAssignment = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        const formData = new FormData();
        formData.append('judulAssignment', newAssignment.judul);
        formData.append('deskripsiAssignment', newAssignment.deskripsi);

        // Gabungkan tanggal dan jam menjadi format YYYY-MM-DD HH:MM:SS
        const deadlineStr = `${newAssignment.deadlineDate} ${newAssignment.deadlineTime}:00`;
        formData.append('deadlineAssignment', deadlineStr);

        formData.append('fileAssignment', newAssignment.file);
        formData.append('jawabanGuru', newAssignment.jawabanGuru);
        formData.append('kelas_id', classInfo.id);

        try {
            const res = await fetch('/api/assignments', {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                toast.success('Assignment created!');
                setIsAddAssignmentOpen(false);
                fetchAssignments();
                setNewAssignment({ judul: '', deskripsi: '', deadlineDate: '', deadlineTime: '', file: null, jawabanGuru: null });
            } else {
                const err = await res.json();
                toast.error(err.error || "Failed to create assignment");
            }
        } catch (e) {
            console.error(e);
            toast.error('An unexpected error occurred');
        }
        finally { setSubmitting(false); }
    };

    const handleDeleteAssignment = async (id) => {
        const result = await Swal.fire({
            title: 'Are you sure?',
            text: "Delete this assignment?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc2626',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Yes, delete it!'
        });
        if (!result.isConfirmed) return;

        try {
            const res = await fetch(`/api/assignments/${id}`, { method: 'DELETE' });
            if (res.ok) {
                toast.success('Assignment deleted');
                fetchAssignments();
                if (selectedAssignmentId === id) {
                    setSelectedAssignmentId(null);
                    setResults([]);
                }
            } else {
                const err = await res.json();
                toast.error(err.message || "Failed");
            }
        } catch (e) { console.error(e); }
    };

    const handleDeleteResult = async (id) => {
        const result = await Swal.fire({
            title: 'Are you sure?',
            text: "Delete this submission?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc2626',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Yes, delete it!'
        });
        if (!result.isConfirmed) return;

        try {
            const res = await fetch(`/api/upload/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            if (res.ok) {
                toast.success('Submission deleted');
                fetchResults(selectedAssignmentId);
            } else {
                toast.error('Failed to delete submission');
            }
        } catch (e) { console.error(e); }
    };

    const downloadCSV = async (assignmentId) => {
        window.open(`/api/assignments/${assignmentId}/download-csv`, '_blank');
    };

    const togglePublish = async (assignmentId, currentStatus) => {
        try {
            const res = await fetch(`/api/assignments/publish/${assignmentId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_published: !currentStatus })
            });
            const data = await res.json();
            if (res.ok) {
                toast.success(data.message);
                // Update local assignments state
                setAssignments(prev => prev.map(a =>
                    a.id === assignmentId ? { ...a, is_published: !currentStatus } : a
                ));
            } else {
                toast.error(data.error || "Failed to update publication status");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error updating publication status");
        }
    };

    if (loading) return <div className="min-h-screen bg-slate-50 flex items-center justify-center">Loading...</div>;

    return (
        <DashboardShell role="Teacher" username={user?.user_metadata?.username}>
            <div className="mb-8">
                <Link href="/dashboard" className="text-slate-500 hover:text-primary flex items-center gap-2 mb-6 text-sm font-bold font-sans transition-colors group">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                        <ArrowLeft size={16} />
                    </div>
                    Back to Dashboard
                </Link>
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 bg-white p-8 rounded-3xl border border-slate-200 shadow-sm shadow-primary/5">
                    <div>
                        <h1 className="text-3xl font-extrabold text-foreground mb-2 font-headline tracking-tight">{classInfo?.nama_kelas}</h1>
                        <div className="flex items-center gap-3">
                            <span className="text-primary font-mono text-sm font-bold bg-primary/10 px-3 py-1 rounded-lg border border-primary/10 tracking-wider">
                                CODE: {classInfo?.kode_kelas}
                            </span>
                            <span className="text-slate-400 text-xs font-bold uppercase tracking-widest font-sans flex items-center gap-1">
                                <Calendar size={12} />
                                Teacher Class
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={() => setIsEditClassOpen(true)} className="px-6 py-3 bg-yellow-50 text-yellow-600 border-2 cursor-pointer border-yellow-100 rounded-2xl hover:bg-yellow-100 hover:border-yellow-200 flex items-center gap-2 font-bold font-headline transition-all">
                            <Edit size={18} /> Edit Class
                        </button>
                        <button onClick={handleDeleteClass} className="px-6 py-3 bg-red-50 text-red-600 border-2 cursor-pointer border-red-100 rounded-2xl hover:bg-red-100 hover:border-red-200 flex items-center gap-2 font-bold font-headline transition-all">
                            <Trash2 size={18} /> Delete Class
                        </button>
                    </div>
                </div>
            </div>

            {isReviewOpen ? (
                <ManualReview
                    result={reviewingResult}
                    assignment={{
                        ...selectedAssignment,
                        class_name: classInfo?.nama_kelas
                    }}
                    onClose={() => setIsReviewOpen(false)}
                    onSave={handleSaveReview}
                />
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in duration-500">
                    {/* Assignments List */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="flex items-center justify-between px-2">
                            <h3 className="text-xl font-extrabold text-foreground font-headline">Assignments</h3>
                            <button
                                onClick={() => setIsAddAssignmentOpen(true)}
                                className="w-10 h-10 bg-primary text-white cursor-pointer rounded-xl hover:bg-primary-container transition-all shadow-lg shadow-primary/20 flex items-center justify-center"
                                title="Add New Assignment"
                            >
                                <Plus size={24} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {assignments.length === 0 && (
                                <div className="p-8 text-center bg-surface-low/50 rounded-2xl border-2 border-dashed border-slate-200">
                                    <p className="text-slate-500 text-sm font-bold italic font-sans">No assignments yet.</p>
                                </div>
                            )}
                            {assignments.map(ass => (
                                <div
                                    key={ass.id}
                                    onClick={() => fetchResults(ass.id)}
                                    className={cn(
                                        "p-6 rounded-3xl border-2 cursor-pointer transition-all hover:shadow-xl hover:shadow-primary/5",
                                        selectedAssignmentId === ass.id
                                            ? "bg-white border-primary shadow-xl shadow-primary/5"
                                            : "bg-white border-slate-100 hover:border-primary/30"
                                    )}
                                >
                                    <h4 className={cn(
                                        "font-extrabold text-lg mb-2 font-headline transition-colors",
                                        selectedAssignmentId === ass.id ? "text-slate-900" : "text-slate-900"
                                    )}>{ass.judul}</h4>
                                    <p className="text-sm text-slate-500 line-clamp-2 mb-4 font-sans font-medium">{ass.deskripsi}</p>
                                    <div className="flex items-center gap-2 text-xs text-slate-400 font-bold uppercase tracking-wider mb-5">
                                        <Calendar size={14} className="text-primary" />
                                        {new Date(ass.deadline.replace(" ", "T")).toLocaleDateString('id-ID', {
                                            day: 'numeric',
                                            month: 'long',
                                            year: 'numeric'
                                        })} | {new Date(ass.deadline.replace(" ", "T")).toLocaleTimeString('id-ID', {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                            hour12: false
                                        }).replace('.', ':')}
                                    </div>
                                    <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); togglePublish(ass.id, ass.is_published); }}
                                            className={cn(
                                                "text-[10px] font-black cursor-pointer px-3 py-1.5 rounded-lg border transition-all uppercase tracking-widest font-headline flex items-center gap-1.5",
                                                ass.is_published
                                                    ? "bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-emerald-100"
                                                    : "bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100"
                                            )}
                                        >
                                            <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", ass.is_published ? "bg-emerald-500" : "bg-slate-400")} />
                                            {ass.is_published ? "Published" : "Draft (Hidden)"}
                                        </button>
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); downloadCSV(ass.id); }}
                                                className="text-xs font-extrabold cursor-pointer text-primary hover:text-primary-container flex items-center gap-1.5 transition-colors font-headline uppercase tracking-wider"
                                            >
                                                <Download size={14} /> CSV
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDeleteAssignment(ass.id); }}
                                                className="text-xs font-extrabold cursor-pointer text-red-500 hover:text-red-700 flex items-center gap-1.5 transition-colors font-headline uppercase tracking-wider"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Results Area */}
                    <div className="lg:col-span-2 sticky top-6 self-start">
                        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm shadow-primary/5 min-h-[500px] flex flex-col overflow-hidden">
                            <div className="p-6 border-b border-slate-100 bg-surface-low/30 flex items-center justify-between">
                                <h3 className="text-lg font-extrabold text-foreground font-headline">
                                    {selectedAssignmentId ? "Submission Results" : "Select an Assignment"}
                                </h3>
                                {selectedAssignmentId && (
                                    <div className="flex items-center gap-3">
                                        <button
                                            disabled={gradingId === 'bulk' || !isDeadlinePassed(selectedAssignment?.deadline)}
                                            onClick={() => handleBulkGrade(selectedAssignmentId)}
                                            className={cn(
                                                "px-4 py-2 text-[10px] font-bold rounded-xl uppercase tracking-widest transition-all flex items-center gap-2",
                                                gradingId === 'bulk' ? "bg-slate-100 text-slate-400 cursor-not-allowed" :
                                                !isDeadlinePassed(selectedAssignment?.deadline) ? "bg-slate-50 text-slate-300 cursor-not-allowed border border-slate-100" :
                                                "bg-primary text-white hover:bg-primary-container shadow-md shadow-primary/20"
                                            )}
                                            title={!isDeadlinePassed(selectedAssignment?.deadline) ? "Deadline must pass before bulk grading" : "Grade all pending submissions"}
                                        >
                                            {gradingId === 'bulk' ? (
                                                <div className="w-3 h-3 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin" />
                                            ) : (
                                                <RotateCcw size={14} />
                                            )}
                                            Bulk Grade
                                        </button>
                                        <span className="px-3 py-1 bg-primary text-white text-[10px] font-bold rounded-full uppercase tracking-widest">
                                            {results.length} Submissions
                                        </span>
                                    </div>
                                )}
                            </div>

                            {!selectedAssignmentId ? (
                                <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-12 text-center">
                                    <div className="w-20 h-20 bg-primary/5 rounded-3xl flex items-center justify-center mb-6">
                                        <FileText size={40} className="text-primary opacity-40" />
                                    </div>
                                    <p className="max-w-xs font-sans font-medium">Select an assignment from the list to view detailed grades and student submissions.</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    {results.length === 0 ? (
                                        <div className="p-12 text-center text-slate-500 flex flex-col items-center">
                                            <div className="w-16 h-16 bg-surface-low rounded-full flex items-center justify-center mb-4">
                                                <UploadCloud size={32} className="text-slate-300" />
                                            </div>
                                            <p className="font-bold font-headline">No submissions yet.</p>
                                            <p className="text-sm font-sans">Wait for students to turn in their work.</p>
                                        </div>
                                    ) : (
                                        <table className="w-full text-left">
                                            <thead className="bg-surface-low/50 border-b border-slate-100">
                                                <tr>
                                                    <th className="px-6 py-5 text-xs font-bold text-slate-400 uppercase tracking-widest font-sans">Student</th>
                                                    <th className="px-6 py-5 text-xs font-bold text-slate-400 uppercase tracking-widest font-sans">Grade</th>
                                                    <th className="px-6 py-5 text-xs font-bold text-slate-400 uppercase tracking-widest font-sans">Similarity</th>
                                                    <th className="px-6 py-5 text-xs font-bold text-slate-400 uppercase tracking-widest font-sans text-right">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-50">
                                                {results.map((res, idx) => (
                                                    <tr key={res.id || idx} className="hover:bg-primary/5 transition-colors group">
                                                        <td className="px-6 py-5 font-bold text-foreground font-headline">{res.nama_murid || res.name}</td>
                                                        <td className="px-6 py-5">
                                                            <div className="flex flex-col gap-1.5">
                                                                <span className={cn(
                                                                    "px-3 py-1 rounded-lg text-xs font-extrabold w-fit shadow-sm",
                                                                    parseFloat(res.nilai) >= 80 ? "bg-green-100 text-green-700 border border-green-200" :
                                                                        parseFloat(res.nilai) >= 60 ? "bg-yellow-100 text-yellow-700 border border-yellow-200" : "bg-red-100 text-red-700 border border-red-200"
                                                                )}>
                                                                    {res.nilai || res.grade}
                                                                </span>
                                                                <span className={cn(
                                                                    "text-[10px] uppercase tracking-widest font-extrabold px-1",
                                                                    res.status === 'published' ? "text-green-500" : "text-amber-500"
                                                                )}>
                                                                    {res.status || 'draft'}
                                                                </span>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-5">
                                                            <div className="flex items-center gap-2">
                                                                <div className="w-full max-w-[60px] h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                                                    <div
                                                                        className="h-full bg-primary transition-all duration-500"
                                                                        style={{ width: `${(res.similarity * 100) || 0}%` }}
                                                                    />
                                                                </div>
                                                                <span className="text-slate-600 text-xs font-mono font-bold">{(res.similarity * 100).toFixed(0)}%</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-5 text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                {res.status === 'pending' && (
                                                                    <button
                                                                        disabled={gradingId === res.id || !isDeadlinePassed(selectedAssignment?.deadline)}
                                                                        onClick={() => handleGradeNow(res.id)}
                                                                        className={cn(
                                                                            "w-9 h-9 flex items-center justify-center rounded-xl transition-all border",
                                                                            gradingId === res.id ? "bg-slate-50 text-slate-300 border-slate-100" :
                                                                            !isDeadlinePassed(selectedAssignment?.deadline) ? "text-slate-200 border-slate-100 cursor-not-allowed" :
                                                                            "text-primary border-primary/20 bg-primary/5 hover:bg-primary/10 hover:border-primary/40 cursor-pointer"
                                                                        )}
                                                                        title={!isDeadlinePassed(selectedAssignment?.deadline) ? "Deadline not yet passed" : "Grade Now with AI"}
                                                                    >
                                                                        {gradingId === res.id ? (
                                                                            <div className="w-4 h-4 border-2 border-slate-300/30 border-t-slate-400 rounded-full animate-spin" />
                                                                        ) : (
                                                                            <RotateCcw size={18} />
                                                                        )}
                                                                    </button>
                                                                )}
                                                                <button
                                                                    onClick={() => handleOpenReview(res)}
                                                                    className="w-9 h-9 flex items-center justify-center text-slate-400 cursor-pointer hover:text-yellow-500 hover:bg-yellow-50 rounded-xl transition-all border border-transparent hover:border-yellow-100"
                                                                    title="Review & Override"
                                                                >
                                                                    <Edit size={18} />
                                                                </button>
                                                                <button
                                                                    onClick={() => handleDeleteResult(res.id)}
                                                                    className="w-9 h-9 flex items-center justify-center text-slate-400 cursor-pointer hover:text-red-500 hover:bg-red-50 rounded-xl transition-all border border-transparent hover:border-red-100"
                                                                    title="Delete Submission"
                                                                >
                                                                    <Trash2 size={18} />
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Add Assignment Modal */}
            {isAddAssignmentOpen && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                    <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col border border-slate-100">
                        <div className="flex justify-between items-center p-8 border-b border-slate-100 bg-surface-low/30">
                            <h3 className="text-2xl text-foreground font-extrabold font-headline">New Assignment</h3>
                            <button onClick={() => setIsAddAssignmentOpen(false)} className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all">
                                <X size={24} className="cursor-pointer" />
                            </button>
                        </div>
                        <form onSubmit={handleAddAssignment} className="p-8 space-y-6 overflow-y-auto">
                            <div>
                                <label className="block text-slate-900 text-sm font-bold mb-2 font-sans">Assignment Title</label>
                                <input
                                    type="text"
                                    required
                                    value={newAssignment.judul}
                                    onChange={e => setNewAssignment({ ...newAssignment, judul: e.target.value })}
                                    placeholder="e.g. Analisis Puisi Kontemporer"
                                    className="w-full border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none rounded-2xl px-5 py-4 text-slate-900 font-bold transition-all placeholder-slate-400"
                                />
                            </div>
                            <div>
                                <label className="block text-slate-900 text-sm font-bold mb-2 font-sans">Description & Instructions</label>
                                <textarea
                                    required
                                    value={newAssignment.deskripsi}
                                    onChange={e => setNewAssignment({ ...newAssignment, deskripsi: e.target.value })}
                                    placeholder="Provide clear instructions for your students..."
                                    className="w-full border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none rounded-2xl px-5 py-4 text-slate-900 font-medium transition-all placeholder-slate-400"
                                    rows="4"
                                ></textarea>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-slate-900 text-sm font-bold mb-2 font-sans">Deadline Date</label>
                                    <input
                                        type="date"
                                        required
                                        value={newAssignment.deadlineDate}
                                        onChange={e => setNewAssignment({ ...newAssignment, deadlineDate: e.target.value })}
                                        className="w-full border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none rounded-2xl px-5 py-4 text-slate-900 font-bold transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-slate-900 text-sm font-bold mb-2 font-sans">Deadline Time</label>
                                    <input
                                        type="time"
                                        required
                                        value={newAssignment.deadlineTime}
                                        onChange={e => setNewAssignment({ ...newAssignment, deadlineTime: e.target.value })}
                                        className="w-full border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none rounded-2xl px-5 py-4 text-slate-900 font-bold transition-all"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-slate-900 text-sm font-bold mb-2 font-sans">Assignment Materials (Optional PDF/DOCX)</label>
                                <div className="relative group">
                                    <div className="border-3 border-dashed border-slate-200 rounded-3xl p-8 flex flex-col items-center justify-center text-center transition-all group-hover:bg-primary/5 group-hover:border-primary/30 bg-surface-low/50">
                                        <input
                                            type="file"
                                            onChange={e => setNewAssignment({ ...newAssignment, file: e.target.files[0] })}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                        />
                                        <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all", newAssignment.file ? "bg-primary text-white" : "bg-white text-slate-400 group-hover:text-primary shadow-sm")}>
                                            <UploadCloud size={32} />
                                        </div>

                                        {newAssignment.file ? (
                                            <div className="animate-in fade-in slide-in-from-bottom-2">
                                                <p className="text-sm font-extrabold text-primary break-all">{newAssignment.file.name}</p>
                                                <p className="text-[10px] font-bold text-primary/60 mt-1 uppercase tracking-widest">Click to change file</p>
                                            </div>
                                        ) : (
                                            <div>
                                                <p className="text-sm font-bold text-slate-900 font-headline">
                                                    <span className="text-primary underline">Click to upload</span> or drag and drop
                                                </p>
                                                <p className="text-xs text-slate-400 mt-2 font-sans font-medium">PDF or DOCX materials for the assignment</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div>
                                <label className="block text-slate-900 text-sm font-bold mb-2 font-sans">Teacher Answer Key (Required for AI Grading)</label>
                                <div className="relative group">
                                    <div className="border-3 border-dashed border-slate-200 rounded-3xl p-8 flex flex-col items-center justify-center text-center transition-all group-hover:bg-primary/5 group-hover:border-primary/30 bg-surface-low/50">
                                        <input
                                            type="file"
                                            required
                                            onChange={e => setNewAssignment({ ...newAssignment, jawabanGuru: e.target.files[0] })}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                        />
                                        <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all", newAssignment.jawabanGuru ? "bg-primary text-white" : "bg-white text-slate-400 group-hover:text-primary shadow-sm")}>
                                            <UploadCloud size={32} />
                                        </div>

                                        {newAssignment.jawabanGuru ? (
                                            <div className="animate-in fade-in slide-in-from-bottom-2">
                                                <p className="text-sm font-extrabold text-primary break-all">{newAssignment.jawabanGuru.name}</p>
                                                <p className="text-[10px] font-bold text-primary/60 mt-1 uppercase tracking-widest">Click to change file</p>
                                            </div>
                                        ) : (
                                            <div>
                                                <p className="text-sm font-bold text-slate-900 font-headline">
                                                    <span className="text-primary underline">Upload answer key</span>
                                                </p>
                                                <p className="text-xs text-slate-400 mt-2 font-sans font-medium">This will be used as the gold standard for grading</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <button disabled={submitting} type="submit" className="w-full cursor-pointer py-5 bg-linear-to-r from-primary to-primary-container text-white rounded-2xl font-extrabold text-lg hover:shadow-xl hover:shadow-primary/30 transition-all font-headline flex items-center justify-center gap-3">
                                {submitting ? (
                                    <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>Create Assignment <ArrowRight size={22} /></>
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit Class Modal */}
            {isEditClassOpen && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md text-center">
                    <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 border border-slate-100">
                        <h3 className="text-2xl text-foreground font-extrabold font-headline mb-2">Edit Class Name</h3>
                        <p className="text-slate-500 text-sm font-sans font-medium mb-8">Update the name of your classroom.</p>
                        <form onSubmit={handleEditClass}>
                            <input type="text" value={editClassName} onChange={e => setEditClassName(e.target.value)} className="w-full text-primary text-xl font-bold border-2 border-slate-100 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none rounded-2xl px-6 py-4 mb-8 transition-all" />
                            <div className="flex gap-4">
                                <button type="button" onClick={() => setIsEditClassOpen(false)} className="flex-1 py-4 text-slate-600 font-bold hover:bg-slate-50 rounded-2xl transition-all font-headline">Cancel</button>
                                <button type="submit" className="flex-1 py-4 bg-primary text-white font-bold hover:bg-primary-container rounded-2xl shadow-lg shadow-primary/20 transition-all font-headline">Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

        </DashboardShell>
    );
}
