'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getAuthState, type User } from '../lib/auth';

interface AuthGuardProps {
    children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
    const [loading, setLoading] = useState(true);
    const [authenticated, setAuthenticated] = useState(false);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        checkAuth();
    }, []);

    async function checkAuth() {
        try {
            const authState = await getAuthState();

            if (!authState.authenticated) {
                // Not authenticated, redirect to login
                router.push(`/login?redirect=${encodeURIComponent(pathname || '/')}`);
            } else {
                setAuthenticated(true);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            router.push(`/login?redirect=${encodeURIComponent(pathname || '/')}`);
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900">
                <div className="glass p-12 rounded-2xl text-center">
                    <div className="animate-spin h-12 w-12 border-4 border-blue-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-gray-300">Loading...</p>
                </div>
            </div>
        );
    }

    if (!authenticated) {
        return null; // Will redirect
    }

    return <>{children}</>;
}
