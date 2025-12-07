'use client';

import { useState, useEffect, useCallback } from 'react';
import { getMeetings, Meeting } from '../../lib/api';
import { toast } from '../../lib/toast';
import AuthGuard from '../../components/AuthGuard';
import MeetingList from '../../components/MeetingList';
import LoadingSpinner from '../../components/LoadingSpinner';
import Link from 'next/link';

export default function MeetingsPage() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('');
    const limit = 20;

    // 自動更新用（PENDING状態がある場合）
    const [hasPending, setHasPending] = useState(false);

    const loadMeetings = useCallback(async (reset = false) => {
        setLoading(true);
        try {
            const currentOffset = reset ? 0 : offset;
            const data = await getMeetings({
                status: statusFilter || undefined,
                search: search || undefined,
                sort_by: 'created_at',
                sort_order: 'desc',
                limit,
                offset: currentOffset,
            });
            
            if (reset) {
                setMeetings(data.items);
                setOffset(0);
            } else {
                setMeetings(prev => [...prev, ...data.items]);
            }
            setTotal(data.total);
            setHasMore(data.has_more);
            
            // Check if there are pending meetings
            setHasPending(data.items.some(m => m.status === 'PENDING'));
        } catch (error) {
            console.error('Failed to load meetings:', error);
            toast.error('会議の読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }, [statusFilter, search, offset]);

    useEffect(() => {
        loadMeetings(true);
    }, [statusFilter, search]);

    // 自動更新（PENDING状態がある場合、10秒ごとに更新）
    useEffect(() => {
        if (!hasPending) return;

        const interval = setInterval(() => {
            loadMeetings(true);
        }, 10000);

        return () => clearInterval(interval);
    }, [hasPending, loadMeetings]);

    const loadMore = () => {
        const newOffset = offset + limit;
        setOffset(newOffset);
        loadMeetings(false);
    };

    // 統計計算
    const stats = {
        total: meetings.length,
        done: meetings.filter(m => m.status === 'DONE').length,
        pending: meetings.filter(m => m.status === 'PENDING').length,
        error: meetings.filter(m => m.status === 'ERROR').length,
    };

    return (
        <AuthGuard>
            <div className="min-h-screen p-8">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <Link href="/" className="text-blue-400 hover:text-blue-300 text-sm mb-2 inline-block">
                                    ← ダッシュボードに戻る
                                </Link>
                                <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                                    会議一覧
                                </h1>
                                <p className="text-gray-400 mt-2">
                                    アップロードした議事録の処理状況を確認できます
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
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
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
                            <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-center space-x-2">
                                <LoadingSpinner size="small" />
                                <span className="text-yellow-400 text-sm">
                                    処理中の会議があります。10秒ごとに自動更新されます。
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Filters */}
                    <div className="glass p-4 rounded-xl mb-6">
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
                    {loading && meetings.length === 0 ? (
                        <div className="glass p-12 rounded-xl flex justify-center">
                            <LoadingSpinner size="large" text="会議を読み込み中..." />
                        </div>
                    ) : (
                        <>
                            <MeetingList meetings={meetings} search={search} />
                            {hasMore && (
                                <div className="mt-6 text-center">
                                    <button
                                        onClick={loadMore}
                                        disabled={loading}
                                        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        {loading ? '読み込み中...' : 'もっと読み込む'}
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </AuthGuard>
    );
}

