'use client';

import { useState, useEffect, useCallback } from 'react';
import { getDecisions, getProjects, exportDecisions, Decision, Project } from '../../lib/api';
import { toast } from '../../lib/toast';
import AuthGuard from '../../components/AuthGuard';
import DecisionList from '../../components/DecisionList';
import ExportButton from '../../components/ExportButton';
import LoadingSpinner from '../../components/LoadingSpinner';
import Link from 'next/link';

export default function DecisionsPage() {
    const [decisions, setDecisions] = useState<Decision[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const [search, setSearch] = useState('');
    const [projectFilter, setProjectFilter] = useState<string>('');
    const limit = 20;

    useEffect(() => {
        loadProjects();
    }, []);

    useEffect(() => {
        setOffset(0);
        loadDecisions(true);
    }, [search, projectFilter]);

    async function loadProjects() {
        try {
            const data = await getProjects();
            setProjects(data.items || []);
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    async function loadDecisions(reset = false) {
        setLoading(true);
        try {
            const currentOffset = reset ? 0 : offset;
            const data = await getDecisions({
                project_id: projectFilter || undefined,
                search: search || undefined,
                sort_by: 'created_at',
                sort_order: 'desc',
                limit,
                offset: currentOffset,
            });

            if (reset) {
                setDecisions(data.items);
                setOffset(0);
            } else {
                setDecisions(prev => [...prev, ...data.items]);
            }
            setTotal(data.total);
            setHasMore(data.has_more);
        } catch (error) {
            console.error('Failed to load decisions:', error);
            toast.error('決定事項の読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }

    const handleExport = async () => {
        await exportDecisions({
            project_id: projectFilter || undefined,
        });
    };

    const handleDecisionDeleted = useCallback((decisionId: string) => {
        setDecisions(prev => prev.filter(d => d.decision_id !== decisionId));
        setTotal(prev => prev - 1);
    }, []);

    const loadMore = () => {
        const newOffset = offset + limit;
        setOffset(newOffset);
        loadDecisions(false);
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
                                <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
                                    決定事項一覧
                                </h1>
                                <p className="text-gray-400 mt-2">
                                    会議で決定された事項を確認できます
                                </p>
                            </div>
                            <ExportButton onExport={handleExport} label="決定事項をエクスポート" />
                        </div>

                        {/* Statistics */}
                        <div className="glass p-4 rounded-xl mt-6">
                            <div className="text-gray-400 text-sm">総決定事項数</div>
                            <div className="text-3xl font-bold text-green-400">{total}</div>
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="glass p-4 rounded-xl mb-6">
                        <div className="flex flex-wrap gap-4">
                            <input
                                type="text"
                                placeholder="決定事項を検索..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 flex-1 min-w-[200px]"
                            />
                            <select
                                value={projectFilter}
                                onChange={(e) => setProjectFilter(e.target.value)}
                                className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="">すべてのプロジェクト</option>
                                {projects.map(project => (
                                    <option key={project.project_id} value={project.project_id}>
                                        {project.project_name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Content */}
                    {loading && decisions.length === 0 ? (
                        <div className="glass p-12 rounded-xl flex justify-center">
                            <LoadingSpinner size="large" text="決定事項を読み込み中..." />
                        </div>
                    ) : (
                        <>
                            <DecisionList
                                decisions={decisions}
                                search={search}
                                onDecisionDeleted={handleDecisionDeleted}
                            />
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

