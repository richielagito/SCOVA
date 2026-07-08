"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight, Play } from "lucide-react";
import { motion } from "framer-motion";
import { useSession } from "../hooks/useSession";

function AnimatedScore() {
    const [score, setScore] = useState(95);
    const [blink, setBlink] = useState(true);

    useEffect(() => {
        let timeout;

        const interval = setInterval(() => {
            const nextScore = Math.floor(Math.random() * (100 - 80 + 1)) + 80;
            setScore(nextScore);
            setBlink(false);

            clearTimeout(timeout);
            timeout = setTimeout(() => setBlink(true), 100);
        }, 3000);

        return () => {
            clearInterval(interval);
            clearTimeout(timeout);
        };
    }, []);

    return (
        <motion.tspan 
            animate={{ opacity: blink ? 1 : 0 }} 
            transition={{ duration: 0.1 }}
        >
            {score}
        </motion.tspan>
    );
}

export default function Hero() {
    const { session } = useSession();

    return (
        <section className="relative pt-24 pb-16 lg:pt-36 lg:pb-20 overflow-hidden bg-background">
            <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2" />

            <div className="container mx-auto px-6 relative z-10">
                <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
                    <div className="flex-[1.2] text-left">
                        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }}>
                            <h1 className="text-5xl lg:text-7xl font-extrabold text-foreground leading-tight mb-6 font-headline tracking-tighter max-w-2xl">
                                Smarter Essay <br /> <span className="text-primary italic pr-2">Grading</span>{" "}with Scova
                            </h1>
                        </motion.div>

                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }} className="max-w-xl mb-10">
                            <p className="text-lg text-slate-500 leading-relaxed font-sans font-medium">
                                Fast, objective, and rubric-based evaluations powered by Gemini 2.0. Scale your feedback without losing the human touch.
                            </p>
                        </motion.div>

                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }} className="flex items-center gap-4">
                            <Link href={session ? "/dashboard" : "/login-register"} className="px-8 py-4 rounded-xl bg-gradient-to-r from-primary to-primary-container text-white font-bold transition-all duration-200 hover:shadow-xl hover:shadow-primary/20 hover:-translate-y-0.5 flex items-center gap-2">
                                Start Now <ArrowRight size={20} />
                            </Link>
                            <Link href="#how-it-works" className="px-8 py-4 rounded-xl bg-white text-slate-700 font-bold border border-slate-200 transition-all duration-200 hover:bg-slate-50 hover:shadow-lg hover:-translate-y-0.5 flex items-center gap-2">
                                <Play size={20} className="fill-current text-primary" /> How It Works
                            </Link>
                        </motion.div>
                    </div>

                    <div className="flex-1 w-full max-w-[500px] lg:max-w-none relative">
                        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8 }} className="relative">
                            <div className="absolute inset-0 bg-primary/10 rounded-full blur-[80px] opacity-40 translate-y-8" />

                            <svg viewBox="0 0 480 420" className="w-full h-auto drop-shadow-2xl relative z-10" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <defs>
                                    <clipPath id="paper-clip">
                                        <rect x="60" y="30" width="320" height="360" rx="32" />
                                    </clipPath>
                                    <filter id="shadow-box" x="220" y="10" width="230" height="110" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                                        <feDropShadow dx="0" dy="8" stdDeviation="8" floodOpacity="0.1" />
                                    </filter>
                                    <filter id="shadow-circle" x="245" y="235" width="150" height="150" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                                        <feDropShadow dx="0" dy="16" stdDeviation="16" floodColor="#0052CC" floodOpacity="0.3" />
                                    </filter>
                                    <linearGradient id="gradient-line" x1="0" y1="0" x2="1" y2="0">
                                        <stop offset="0%" stopColor="#0052CC" stopOpacity="0" />
                                        <stop offset="50%" stopColor="#0052CC" stopOpacity="1" />
                                        <stop offset="100%" stopColor="#0052CC" stopOpacity="0" />
                                    </linearGradient>
                                </defs>

                                <rect x="60" y="30" width="320" height="360" rx="32" fill="white" />
                                <rect x="60" y="30" width="320" height="360" rx="32" stroke="#E2E8F0" strokeWidth="1.5" />

                                <motion.rect initial={{ width: 0 }} animate={{ width: 200 }} transition={{ duration: 1, delay: 0.1 }} x="100" y="80" height="8" rx="4" fill="#F1F5F9" />
                                <motion.rect initial={{ width: 0 }} animate={{ width: 140 }} transition={{ duration: 1, delay: 0.2 }} x="100" y="108" height="8" rx="4" fill="#F1F5F9" />
                                <motion.rect initial={{ width: 0 }} animate={{ width: 240 }} transition={{ duration: 1, delay: 0.3 }} x="100" y="170" height="5" rx="2.5" fill="#F8FAFC" />
                                <motion.rect initial={{ width: 0 }} animate={{ width: 220 }} transition={{ duration: 1, delay: 0.4 }} x="100" y="192" height="5" rx="2.5" fill="#F8FAFC" />
                                <motion.rect initial={{ width: 0 }} animate={{ width: 240 }} transition={{ duration: 1, delay: 0.5 }} x="100" y="214" height="5" rx="2.5" fill="#F8FAFC" />

                                <motion.rect
                                    clipPath="url(#paper-clip)"
                                    animate={{ y: [40, 340, 40] }}
                                    transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                                    x="70" y="40" width="300" height="4" fill="url(#gradient-line)"
                                />

                                <motion.g animate={{ y: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}>
                                    <rect x="240" y="20" width="190" height="70" rx="16" fill="white" filter="url(#shadow-box)" />
                                    <circle cx="272" cy="55" r="17" fill="#0052CC" />
                                    <path d="M266 55L270 59L279 50" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                    <text x="298" y="50" fontFamily="Inter, sans-serif" fontSize="13" fontWeight="900" fill="#1E293B">AI Scoring</text>
                                    <text x="298" y="66" fontFamily="Inter, sans-serif" fontSize="10" fontStyle="italic" fill="#64748B">Gemini 2.0 Enabled</text>
                                </motion.g>

                                <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ scale: { type: "spring" } }}>
                                    <circle cx="320" cy="310" r="55" fill="#0052CC" />
                                    <text x="320" y="325" fontFamily="Inter, sans-serif" fontSize="48" fontWeight="900" textAnchor="middle" fill="white">
                                        <AnimatedScore />
                                    </text>
                                </motion.g>
                            </svg>
                        </motion.div>
                    </div>
                </div>
            </div>
        </section>
    );
}
