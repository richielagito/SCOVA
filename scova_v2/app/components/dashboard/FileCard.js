import React, { useState, useRef, useEffect } from "react";
import { FileText, Download, Eye, Loader2, FileCode, FileImage, MoreVertical, Trash2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

const getFileIcon = (filename) => {
    if (!filename) return <FileText size={20} />;
    const ext = filename.split(".").pop().toLowerCase();
    switch (ext) {
        case "pdf":
            return <FileText size={20} className="text-red-500" />;
        case "docx":
        case "doc":
            return <FileText size={20} className="text-primary" />;
        case "txt":
            return <FileText size={20} className="text-slate-500" />;
        case "jpg":
        case "jpeg":
        case "png":
            return <FileImage size={20} className="text-primary" />;
        default:
            return <FileCode size={20} className="text-slate-500" />;
    }
};

export default function FileCard({ filename, fileUrl, isLoading = false, onPreview, onDownload, onRemove, onChangeFile, className }) {
    const [showMenu, setShowMenu] = useState(false);
    const menuRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowMenu(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleCardClick = () => {
        if (!isLoading && onPreview) {
            onPreview();
        }
    };

    return (
        <div
            onClick={handleCardClick}
            className={cn(
                "group relative flex items-center p-3.5 bg-white border-2 border-slate-100 rounded-2xl shadow-sm hover:shadow-xl hover:shadow-primary/5 hover:border-primary/20 transition-all duration-300 cursor-pointer",
                isLoading && "opacity-75 cursor-not-allowed",
                className,
            )}
        >
            {/* File Icon Container */}
            <div className="shrink-0 w-10 h-10 bg-surface-low rounded-xl flex items-center justify-center mr-3">{isLoading ? <Loader2 size={20} className="text-primary animate-spin" /> : <div>{getFileIcon(filename)}</div>}</div>

            {/* File Info */}
            <div className="flex-1 min-w-0 mr-4">
                <p className="text-sm font-extrabold text-foreground truncate font-headline transition-colors">{filename || "Unnamed File"}</p>

                {!isLoading && onChangeFile && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onChangeFile();
                        }}
                        className="mt-1.5 text-[10px] font-extrabold text-primary hover:text-primary-container flex items-center gap-1.5 uppercase tracking-widest transition-colors font-sans"
                    >
                        <RefreshCw size={10} /> Change File
                    </button>
                )}

                {isLoading && <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mt-1.5 font-sans">Processing...</p>}

                {!isLoading && !onChangeFile && <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mt-1.5 font-sans">Ready to view</p>}
            </div>

            {/* Actions Menu */}
            {!isLoading && (
                <div className="relative" ref={menuRef}>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowMenu(!showMenu);
                        }}
                        className="w-8 h-8 flex items-center justify-center hover:bg-surface-low text-slate-400 hover:text-primary rounded-lg transition-all"
                    >
                        <MoreVertical size={18} />
                    </button>

                    {showMenu && (
                        <div className="absolute right-0 mt-3 w-44 bg-white border border-slate-100 rounded-2xl shadow-2xl z-20 overflow-hidden py-1.5 animate-in fade-in zoom-in-95 duration-200">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowMenu(false);
                                    if (onDownload) onDownload();
                                    else if (fileUrl) window.open(fileUrl, "_blank");
                                }}
                                className="w-full px-4 py-2.5 text-left text-sm text-slate-600 hover:bg-primary/5 hover:text-primary flex items-center gap-2.5 transition-colors font-bold font-sans"
                            >
                                <Download size={16} /> Download
                            </button>

                            {onRemove && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setShowMenu(false);
                                        onRemove();
                                    }}
                                    className="w-full px-4 py-2.5 text-left text-sm text-red-500 hover:bg-red-50 flex items-center gap-2.5 transition-colors font-bold font-sans"
                                >
                                    <Trash2 size={16} /> Remove
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Loading Progress Bar - Animated Underline */}
            {isLoading && (
                <div className="absolute bottom-0 left-0 h-1 bg-surface-low w-full overflow-hidden rounded-b-2xl">
                    <div className="h-full bg-primary animate-loading-bar"></div>
                </div>
            )}
        </div>
    );
}
