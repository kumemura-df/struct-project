'use client';

import { useState } from 'react';
import { useMeetings } from '../../lib/hooks';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';
import MeetingList from '../../components/MeetingList';
import LoadingSpinner from '../../components/LoadingSpinner';
import Link from 'next/link';

export default function MeetingsPage() {
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('');

    const { data, isLoading, error } = useMeetings({
        status: statusFilter || undefined,
        search: search || undefined,
        sort_by: 'created_at',
        sort_order: 'desc',
        limit: 100,
    });

    const meetings = data?.items || [];
    const total = data?.total || 0;
    const hasPending = meetings.some(m => m.status === 'PENDING');

    // 統計計算
    const stats = {
        total: meetings.length,
        done: meetings.filter(m => m.status === 'DONE').length,
        pending: meetings.filter(m => m.status === 'PENDING').length,
        error: meetings.filter(m => m.status === 'ERROR').length,
    };

    return (
        <AuthGuard>
            <AppLayout>
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                                会議一覧
                            </h1>
                            <p className="text-gray-400 mt-1">
                                アップロードした議事録の処理状況を確認
                            </p>
                        </div>
                        <Link
                            href="/upload"
                            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors shadow-lg shadow-blue-500/30"
                        >
                            📤 議事録アップロード
                        </Link>
                    </div>

                    {/* Statistics */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="glass p-4 rounded-xl">
                            <div className="text-gray-400 text-sm">総会議数</div>
                            <div className="text-3xl font-bold text-white">{total}</div>
                        </div>
                        <div className="glass p-4 rounded-xl">
                            <div className="text-gray-400 text-sm">処理完了</div>
                            <div className="text-3xl font-bold text-green-400">{stats.done}</div>
                        </div>
                        <div className="glass p-4 rounded-xl">
                            <div className="text-gray-400 text-sm">処理中</div>
                            <div className="text-3xl font-bold text-yellow-400 animate-pulse">{stats.pending}</div>
                        </div>
                        <div className="glass p-4 rounded-xl">
                            <div className="text-gray-400 text-sm">エラー</div>
                            <div className="text-3xl font-bold text-red-400">{stats.error}</div>
                        </div>
                    </div>

                    {hasPending && (
                        <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-center space-x-2">
                            <LoadingSpinner size="small" />
                            <span className="text-yellow-400 text-sm">
                                処理中の会議があります。自動的に更新されます。
                            </span>
                        </div>
                    )}

                    {/* Filters */}
                    <div className="glass p-4 rounded-xl">
                        <div className="flex flex-wrap gap-4">
                            <input
                                type="text"
                                placeholder="会議を検索..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 flex-1 min-w-[200px]"
                            />
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="">すべてのステータス</option>
                                <option value="DONE">完了</option>
                                <option value="PENDING">処理中</option>
                                <option value="ERROR">エラー</option>
                            </select>
                        </div>
                    </div>

                    {/* Content */}
                    {isLoading && meetings.length === 0 ? (
                        <div className="glass p-12 rounded-xl flex justify-center">
                            <LoadingSpinner size="large" text="会議を読み込み中..." />
                        </div>
                    ) : error ? (
                        <div className="glass p-12 rounded-xl text-center">
                            <div className="text-6xl mb-4">❌</div>
                            <p className="text-red-400">会議の読み込みに失敗しました</p>
                        </div>
                    ) : (
                        <MeetingList meetings={meetings} search={search} />
                    )}
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
