'use client';

import { useEffect } from 'react';
import { login } from '../../lib/auth';

export default function LoginPage() {
    useEffect(() => {
        // Automatically redirect to OAuth flow
        const params = new URLSearchParams(window.location.search);
        const redirect = params.get('redirect') || '/';
        login(redirect);
    }, []);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900">
            <div className="glass p-12 rounded-2xl text-center max-w-md">
                <h1 className="text-4xl font-bold text-white mb-6">
                    Project Progress DB
                </h1>
                <div className="space-y-4">
                    <div className="animate-spin h-12 w-12 border-4 border-blue-400 border-t-transparent rounded-full mx-auto"></div>
                    <p className="text-gray-300">Googleログインへリダイレクト中...</p>
                </div>
            </div>
        </div>
    );
}
