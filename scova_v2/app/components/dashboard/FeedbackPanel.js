import React from "react";
import { X, FileText, UploadCloud, CheckCircle, Clock, AlertCircle, Loader2, BookOpen } from "lucide-react";
import { cn, renderHighlightedEssay } from "@/lib/utils";
import FileCard from "./FileCard";

export default function FeedbackPanel({ assignment, result, stagedFile, isStaging, isEditing, isUploading, onClose, onStage, isDeadlineOpen }) {
    if (!assignment) return null;

    const score = result?.nilai || result?.grade || "-";
    const similarity = result?.similarity || "0%";
    const feedback = result?.feedback || "No feedback provided yet.";

    // Use real sub-criteria scores if available, otherwise fallback to mock
    const criteria =
        result?.sub_criteria_scores && Array.isArray(result.sub_criteria_scores)
            ? result.sub_criteria_scores.map((s) => ({
                  name: `Question ${s.question}`,
                  score: s.grade,
                  weight: "Score",
              }))
            : [
                  { name: "Content Accuracy", score: score > 0 ? Math.min(100, parseInt(score) + 5) : "-", weight: "40%" },
                  { name: "Grammar & Structure", score: score > 0 ? Math.max(0, parseInt(score) - 5) : "-", weight: "30%" },
                  { name: "Relevance to Prompt", score: score || "-", weight: "30%" },
              ];

    const getFilenameFromUrl = (url) => {
        if (!url) return "";
        return url.split("/").pop().split("?")[0];
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return "";
        try {
            const parts = dateStr.includes(" ") ? dateStr.split(" ") : [dateStr];
            const dateParts = parts[0].split("-");
            let formattedDate = "";

            if (dateParts.length === 3) {
                if (dateParts[0].length === 4) formattedDate = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
                else formattedDate = `${dateParts[0]}/${dateParts[1]}/${dateParts[2]}`;
            } else {
                formattedDate = dateStr;
            }

            if (parts.length > 1) {
                const timeParts = parts[1].split(":");
                formattedDate += ` ${timeParts[0]}:${timeParts[1]}`;
            }

            return formattedDate;
        } catch (e) {
            return dateStr;
        }
    };

    return (
        <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col">
                {/* Content */}
                <div className="p-6 space-y-8">
                    {/* Top Section: Assignment File & Grade Summary */}
                    <div className="flex flex-col lg:flex-row gap-8">
                        {/* Left: Assignment Info & File */}
                        <div className="flex flex-col justify-between flex-1 space-y-5">
                            <div>
                                {assignment.deadline && (
                                    <div className="flex items-center gap-2 text-[10px] font-bold text-primary uppercase tracking-widest mb-2.5 bg-primary/5 w-fit px-3 py-1 rounded-lg border border-primary/10">
                                        <Clock size={12} />
                                        Due {formatDate(assignment.deadline)}
                                    </div>
                                )}
                                <h3 className="text-xl font-extrabold text-foreground mb-2.5 font-headline">Assignment Overview</h3>
                                <p className="text-slate-600 leading-relaxed font-sans font-medium text-sm">{assignment.deskripsi}</p>
                            </div>

                            {assignment.file_path && (
                                <div className="space-y-3">
                                    <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest font-sans ml-1">Reference Material</p>
                                    <div className="max-w-md">
                                        <FileCard filename={getFilenameFromUrl(assignment.file_path)} fileUrl={assignment.file_path} onPreview={() => window.open(assignment.file_path, "_blank")} />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Right: Grade Overview - 1 Column Stack */}
                        <div className="w-full lg:w-64 flex flex-col gap-3.5">
                            <div className="bg-primary/5 border-2 border-primary/10 rounded-3xl p-5 text-center shadow-sm relative overflow-hidden group">
                                <div className="absolute top-0 right-0 w-16 h-16 bg-primary/5 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-150 duration-700"></div>
                                <p className="text-primary text-[10px] font-extrabold uppercase tracking-[0.2em] mb-1.5 font-sans">Final Score</p>
                                <p className="text-4xl font-black text-primary font-headline tracking-tighter">{score}</p>
                            </div>

                            <div className="bg-surface-low/50 border border-slate-100 rounded-2xl p-3.5 text-center flex items-center justify-between shadow-sm px-5">
                                <p className="text-slate-400 text-[10px] font-extrabold uppercase tracking-widest font-sans">Grade</p>
                                <span
                                    className={cn(
                                        "px-3 py-1 rounded-xl text-xs font-black shadow-sm",
                                        parseFloat(score) >= 80
                                            ? "bg-green-100 text-green-700 border border-green-200"
                                            : parseFloat(score) >= 60
                                              ? "bg-yellow-100 text-yellow-700 border border-yellow-200"
                                              : "bg-red-100 text-red-700 border border-red-200",
                                    )}
                                >
                                    {parseFloat(score) >= 80 ? "A" : parseFloat(score) >= 60 ? "B/C" : parseFloat(score) < 60 ? "D/E" : "-"}
                                </span>
                            </div>

                            <div className="bg-surface-low/50 border border-slate-100 rounded-2xl p-3.5 text-center flex items-center justify-between shadow-sm px-5">
                                <p className="text-slate-400 text-[10px] font-extrabold uppercase tracking-widest font-sans">Similarity</p>
                                <p className="text-lg font-black text-slate-700 font-mono tracking-tighter">{similarity}</p>
                            </div>
                        </div>
                    </div>

                    {/* Teacher Feedback - Full Width Row */}
                    <div className="flex flex-col space-y-3.5">
                        <h3 className="text-lg font-extrabold text-foreground flex items-center gap-2.5 font-headline">
                            <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                                <FileText size={18} />
                            </div>
                            Teacher&apos;s Feedback
                        </h3>
                        <div
                            className={cn(
                                "w-full rounded-3xl p-6 border-2 leading-relaxed text-base shadow-sm transition-all font-sans font-medium",
                                result ? "bg-primary/5 border-primary/10 text-slate-700" : "bg-surface-low border-slate-100 text-slate-400",
                            )}
                        >
                            &quot;{feedback}&quot;
                        </div>
                    </div>

                    {/* Essay Analysis - Highlighted Text */}
                    {result?.essay_text && (
                        <div className="flex flex-col space-y-3.5">
                            <h3 className="text-lg font-extrabold text-foreground flex items-center gap-2.5 font-headline">
                                <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
                                    <BookOpen size={18} />
                                </div>
                                Essay Analysis
                            </h3>
                            <div className="w-full rounded-3xl p-6 bg-white border-2 border-slate-100 shadow-sm font-sans text-base leading-relaxed text-slate-700 whitespace-pre-wrap">
                                {renderHighlightedEssay(result.essay_text, result.highlights)}
                            </div>
                            <div className="flex gap-4 px-2">
                                <div className="flex items-center gap-2">
                                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/30 border border-green-500/50"></div>
                                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Strengths</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/30 border border-red-500/50"></div>
                                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Improvements</span>
                                </div>
                                <span className="text-[9px] text-slate-400 font-medium italic ml-auto">* Hover over highlights to see detailed feedback</span>
                            </div>
                        </div>
                    )}

                    {/* Criteria Breakdown - Full Width Row */}
                    <div className="flex flex-col space-y-3.5">
                        <h3 className="text-lg font-extrabold text-foreground flex items-center gap-2.5 font-headline">
                            <div className="w-9 h-9 rounded-xl bg-green-50 flex items-center justify-center text-green-600">
                                <CheckCircle size={18} />
                            </div>
                            Criteria Breakdown
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 w-full">
                            {criteria.map((c, i) => (
                                <div
                                    key={i}
                                    className="flex items-center justify-between p-5 bg-white border-2 border-slate-50 rounded-3xl shadow-sm hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 transition-all duration-300 group"
                                >
                                    <div>
                                        <p className="font-extrabold text-foreground text-base font-headline group-hover:text-primary transition-colors">{c.name}</p>
                                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest font-sans mt-0.5">{c.weight}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-2xl font-black text-foreground font-headline tracking-tighter group-hover:text-primary transition-colors">{c.score}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Student Submission Section - Simplified as it is now in AssignmentCard */}
                    <div className="space-y-3.5 pt-4 border-t border-slate-100">
                        <h3 className="text-lg font-extrabold text-foreground flex items-center gap-2.5 font-headline">
                            <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400">
                                <Clock size={18} />
                            </div>
                            Submission History
                        </h3>
                        <div className="flex flex-wrap gap-5">
                            {result?.file_path && (
                                <div className="space-y-2.5 w-full md:w-[calc(50%-10px)] lg:w-[calc(33.333%-14px)]">
                                    <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest font-sans ml-1">Evaluated Version</p>
                                    <FileCard filename={getFilenameFromUrl(result.file_path)} fileUrl={result.file_path} onPreview={() => window.open(result.file_path, "_blank")} />
                                    {result.version && <p className="text-[9px] font-bold text-primary uppercase tracking-tight ml-1 italic">Version {result.version}</p>}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
