'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getAuthState, logout, type User } from '../lib/auth';

export default function UserMenu() {
    const [user, setUser] = useState<User | null>(null);
    const [showMenu, setShowMenu] = useState(false);

    useEffect(() => {
        loadUser();
    }, []);

    async function loadUser() {
        const authState = await getAuthState();
        if (authState.authenticated && authState.user) {
            setUser(authState.user);
        }
    }

    if (!user) {
        return null;
    }

    return (
        <div className="relative">
            <button
                onClick={() => setShowMenu(!showMenu)}
                className="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
                {user.picture && (
                    <img
                        src={user.picture}
                        alt={user.name || user.email}
                        className="w-8 h-8 rounded-full"
                    />
                )}
                <div className="text-left">
                    <p className="text-sm font-semibold text-white">{user.name || 'ユーザー'}</p>
                    <p className="text-xs text-gray-400">{user.email}</p>
                </div>
            </button>

            {showMenu && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setShowMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 glass rounded-lg shadow-lg z-20 p-2">
                        <Link
                            href="/settings"
                            onClick={() => setShowMenu(false)}
                            className="block w-full text-left px-4 py-2 rounded-lg text-white hover:bg-white/10 transition-colors"
                        >
                            Settings
                        </Link>
                        <button
                            onClick={() => {
                                setShowMenu(false);
                                logout();
                            }}
                            className="w-full text-left px-4 py-2 rounded-lg text-white hover:bg-white/10 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
