"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase';
import DashboardShell from '@/app/components/dashboard/DashboardShell';
import TeacherDashboard from '@/app/components/dashboard/TeacherDashboard';
import StudentDashboard from '@/app/components/dashboard/StudentDashboard';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const checkUser = async () => {
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (error || !session) {
        router.push('/login-register');
        return;
      }

      const currentUser = session.user;
      setUser(currentUser);
      
      // Role should be in user_metadata if set during sign up
      // If not found, default to 'Student' or fetch from backend if needed
      const userRole = currentUser.user_metadata?.role || 'Student';
      setRole(userRole);
      setLoading(false);
    };

    checkUser();
  }, [router]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    // Also hit backend logout to clear session
    await fetch('/logout');
    router.push('/login-register');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <DashboardShell 
        role={role} 
        username={user?.user_metadata?.username || user?.email} 
    >
      {role === 'Teacher' ? (
        <TeacherDashboard user={user} />
      ) : (
        <StudentDashboard user={user} />
      )}
    </DashboardShell>
  );
}
