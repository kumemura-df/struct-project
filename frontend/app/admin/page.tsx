'use client';

import { useState, useEffect, useCallback } from 'react';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';
import LoadingSpinner from '../../components/LoadingSpinner';
import { toast } from '../../lib/toast';

interface User {
    user_id: string;
    email: string;
    name: string;
    role: string;
    is_active: boolean;
    created_at: string;
    last_login_at?: string;
}

interface AuditLog {
    log_id: string;
    entity_type: string;
    entity_id: string;
    action: string;
    user_id: string;
    created_at: string;
    old_value?: string;
    new_value?: string;
}

interface MyRole {
    user_id: string;
    email: string;
    name: string;
    role: string;
    is_admin: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AdminPage() {
    const [myRole, setMyRole] = useState<MyRole | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'users' | 'logs'>('users');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newUser, setNewUser] = useState({ email: '', name: '', role: 'member' });
    const [creating, setCreating] = useState(false);

    const loadMyRole = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/admin/me/role`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error('Failed to load role');
            const data = await res.json();
            setMyRole(data);
            return data.is_admin;
        } catch (error) {
            console.error('Failed to load role:', error);
            return false;
        }
    }, []);

    const loadUsers = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/admin/users`, {
                credentials: 'include'
            });
            if (!res.ok) {
                if (res.status === 403) {
                    toast.error('管理者権限が必要です');
                    return;
                }
                throw new Error('Failed to load users');
            }
            const data = await res.json();
            setUsers(data.items || []);
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    }, []);

    const loadAuditLogs = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/admin/audit-logs?limit=50`, {
                credentials: 'include'
            });
            if (!res.ok) {
                if (res.status === 403) return;
                throw new Error('Failed to load audit logs');
            }
            const data = await res.json();
            setAuditLogs(data.items || []);
        } catch (error) {
            console.error('Failed to load audit logs:', error);
        }
    }, []);

    useEffect(() => {
        const init = async () => {
            setLoading(true);
            const isAdmin = await loadMyRole();
            if (isAdmin) {
                await Promise.all([loadUsers(), loadAuditLogs()]);
            }
            setLoading(false);
        };
        init();
    }, [loadMyRole, loadUsers, loadAuditLogs]);

    const updateUserRole = async (userId: string, newRole: string) => {
        try {
            const res = await fetch(`${API_URL}/admin/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ role: newRole })
            });
            
            if (!res.ok) throw new Error('Failed to update user');
            
            toast.success('ロールを更新しました');
            loadUsers();
            loadAuditLogs();
        } catch (error) {
            console.error('Failed to update user:', error);
            toast.error('更新に失敗しました');
        }
    };

    const toggleUserActive = async (userId: string, currentActive: boolean) => {
        try {
            const res = await fetch(`${API_URL}/admin/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ is_active: !currentActive })
            });
            
            if (!res.ok) throw new Error('Failed to update user');
            
            toast.success(currentActive ? 'ユーザーを無効化しました' : 'ユーザーを有効化しました');
            loadUsers();
            loadAuditLogs();
        } catch (error) {
            console.error('Failed to toggle user:', error);
            toast.error('更新に失敗しました');
        }
    };

    const createUser = async () => {
        if (!newUser.email || !newUser.name) {
            toast.error('メールアドレスと名前は必須です');
            return;
        }
        
        setCreating(true);
        try {
            const res = await fetch(`${API_URL}/admin/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(newUser)
            });
            
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to create user');
            }
            
            toast.success('ユーザーを作成しました');
            setShowCreateModal(false);
            setNewUser({ email: '', name: '', role: 'member' });
            loadUsers();
            loadAuditLogs();
        } catch (error: unknown) {
            console.error('Failed to create user:', error);
            toast.error(error instanceof Error ? error.message : '作成に失敗しました');
        } finally {
            setCreating(false);
        }
    };

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString('ja-JP', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getRoleLabel = (role: string) => {
        switch (role) {
            case 'admin': return '管理者';
            case 'pm': return 'PM';
            case 'member': return 'メンバー';
            default: return role;
        }
    };

    const getRoleColor = (role: string) => {
        switch (role) {
            case 'admin': return 'bg-red-600';
            case 'pm': return 'bg-blue-600';
            case 'member': return 'bg-gray-600';
            default: return 'bg-gray-600';
        }
    };

    if (loading) {
        return (
            <AuthGuard>
                <AppLayout>
                    <div className="flex justify-center items-center min-h-[400px]">
                        <LoadingSpinner size="large" />
                    </div>
                </AppLayout>
            </AuthGuard>
        );
    }

    if (!myRole?.is_admin) {
        return (
            <AuthGuard>
                <AppLayout>
                    <div className="glass p-8 rounded-xl text-center max-w-md mx-auto">
                        <span className="text-6xl mb-4 block">🔒</span>
                        <h1 className="text-2xl font-bold text-white mb-2">アクセス拒否</h1>
                        <p className="text-gray-400">
                            このページを表示するには管理者権限が必要です。
                        </p>
                        <div className="mt-4 p-4 bg-white/5 rounded-lg">
                            <p className="text-sm text-gray-400">
                                現在のロール: <span className="text-white">{getRoleLabel(myRole?.role || 'member')}</span>
                            </p>
                        </div>
                    </div>
                </AppLayout>
            </AuthGuard>
        );
    }

    return (
        <AuthGuard>
            <AppLayout>
                <div className="space-y-6">
                    {/* Header */}
                    <div>
                        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-pink-400">
                            管理者画面
                        </h1>
                        <p className="text-gray-400 mt-1">
                            ユーザー管理と監査ログ
                        </p>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-2 border-b border-white/10 pb-2">
                        <button
                            onClick={() => setActiveTab('users')}
                            className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                                activeTab === 'users'
                                    ? 'bg-white/10 text-white border-b-2 border-red-500'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            👥 ユーザー管理
                        </button>
                        <button
                            onClick={() => setActiveTab('logs')}
                            className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                                activeTab === 'logs'
                                    ? 'bg-white/10 text-white border-b-2 border-red-500'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            📋 監査ログ
                        </button>
                    </div>

                    {/* Users Tab */}
                    {activeTab === 'users' && (
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <h2 className="text-xl font-semibold text-white">ユーザー一覧</h2>
                                <button
                                    onClick={() => setShowCreateModal(true)}
                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                                >
                                    + ユーザー追加
                                </button>
                            </div>

                            <div className="glass rounded-xl overflow-hidden">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-white/10">
                                            <th className="text-left p-4 text-gray-400 font-medium">ユーザー</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">ロール</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">状態</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">最終ログイン</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.map((user) => (
                                            <tr key={user.user_id} className="border-b border-white/5 hover:bg-white/5">
                                                <td className="p-4">
                                                    <div className="text-white font-medium">{user.name || 'N/A'}</div>
                                                    <div className="text-sm text-gray-400">{user.email}</div>
                                                </td>
                                                <td className="p-4">
                                                    <select
                                                        value={user.role}
                                                        onChange={(e) => updateUserRole(user.user_id, e.target.value)}
                                                        className={`px-3 py-1 rounded text-white text-sm ${getRoleColor(user.role)} border-0 focus:ring-2 focus:ring-white/30`}
                                                        disabled={user.email === myRole?.email}
                                                    >
                                                        <option value="admin">管理者</option>
                                                        <option value="pm">PM</option>
                                                        <option value="member">メンバー</option>
                                                    </select>
                                                </td>
                                                <td className="p-4">
                                                    <span className={`px-2 py-1 rounded text-xs ${
                                                        user.is_active
                                                            ? 'bg-green-600 text-white'
                                                            : 'bg-gray-600 text-gray-300'
                                                    }`}>
                                                        {user.is_active ? '有効' : '無効'}
                                                    </span>
                                                </td>
                                                <td className="p-4 text-gray-400 text-sm">
                                                    {formatDate(user.last_login_at || '')}
                                                </td>
                                                <td className="p-4">
                                                    <button
                                                        onClick={() => toggleUserActive(user.user_id, !!user.is_active)}
                                                        disabled={user.email === myRole?.email}
                                                        className={`px-3 py-1 text-sm rounded transition-colors ${
                                                            user.email === myRole?.email
                                                                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                                                : user.is_active
                                                                    ? 'bg-red-600/20 text-red-400 hover:bg-red-600/30'
                                                                    : 'bg-green-600/20 text-green-400 hover:bg-green-600/30'
                                                        }`}
                                                    >
                                                        {user.is_active ? '無効化' : '有効化'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Audit Logs Tab */}
                    {activeTab === 'logs' && (
                        <div className="space-y-4">
                            <h2 className="text-xl font-semibold text-white">監査ログ</h2>
                            <div className="glass rounded-xl overflow-hidden">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-white/10">
                                            <th className="text-left p-4 text-gray-400 font-medium">日時</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">操作者</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">操作</th>
                                            <th className="text-left p-4 text-gray-400 font-medium">対象</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {auditLogs.map((log) => (
                                            <tr key={log.log_id} className="border-b border-white/5 hover:bg-white/5">
                                                <td className="p-4 text-gray-400 text-sm">
                                                    {formatDate(log.created_at)}
                                                </td>
                                                <td className="p-4 text-white text-sm">
                                                    {log.user_id || 'System'}
                                                </td>
                                                <td className="p-4">
                                                    <span className={`px-2 py-1 rounded text-xs ${
                                                        log.action === 'create' ? 'bg-green-600' :
                                                        log.action === 'update' ? 'bg-blue-600' :
                                                        log.action === 'delete' ? 'bg-red-600' :
                                                        'bg-gray-600'
                                                    } text-white`}>
                                                        {log.action}
                                                    </span>
                                                </td>
                                                <td className="p-4 text-sm text-gray-400">
                                                    {log.entity_type} / {log.entity_id.substring(0, 8)}...
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Create User Modal */}
                    {showCreateModal && (
                        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                            <div className="glass p-6 rounded-xl w-full max-w-md mx-4">
                                <h3 className="text-xl font-semibold text-white mb-4">ユーザー追加</h3>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">メールアドレス</label>
                                        <input
                                            type="email"
                                            value={newUser.email}
                                            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                                            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                            placeholder="user@example.com"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">名前</label>
                                        <input
                                            type="text"
                                            value={newUser.name}
                                            onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                                            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                            placeholder="山田 太郎"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">ロール</label>
                                        <select
                                            value={newUser.role}
                                            onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                                            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                        >
                                            <option value="member">メンバー</option>
                                            <option value="pm">PM</option>
                                            <option value="admin">管理者</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="flex gap-2 mt-6">
                                    <button
                                        onClick={() => setShowCreateModal(false)}
                                        className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                                    >
                                        キャンセル
                                    </button>
                                    <button
                                        onClick={createUser}
                                        disabled={creating}
                                        className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        {creating ? '作成中...' : '作成'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
