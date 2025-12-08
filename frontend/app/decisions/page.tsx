'use client';

import { useState, useCallback } from 'react';
import { useDecisions, useProjects } from '../../lib/hooks';
import { exportDecisions } from '../../lib/api';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';
import DecisionList from '../../components/DecisionList';
import ExportButton from '../../components/ExportButton';
import LoadingSpinner from '../../components/LoadingSpinner';

export default function DecisionsPage() {
    const [search, setSearch] = useState('');
    const [projectFilter, setProjectFilter] = useState<string>('');
    const [offset, setOffset] = useState(0);
    const limit = 20;

    const { data: decisionsData, isLoading } = useDecisions({
        project_id: projectFilter || undefined,
        search: search || undefined,
        sort_by: 'created_at',
        sort_order: 'desc',
        limit,
        offset,
    });

    const { data: projectsData } = useProjects();

    const decisions = decisionsData?.items || [];
    const total = decisionsData?.total || 0;
    const hasMore = decisionsData?.has_more || false;
    const projects = projectsData?.items || [];

    const handleExport = async () => {
        await exportDecisions({
            project_id: projectFilter || undefined,
        });
    };

    const handleDecisionDeleted = useCallback(() => {
        // TanStack Query will auto-refetch
    }, []);

    const loadMore = () => {
        setOffset(prev => prev + limit);
    };

    return (
        <AuthGuard>
            <AppLayout>
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
                                決定事項一覧
                            </h1>
                            <p className="text-gray-400 mt-1">
                                会議で決定された事項を確認・管理
                            </p>
                        </div>
                        <ExportButton onExport={handleExport} label="決定事項をエクスポート" />
                    </div>

                    {/* Statistics */}
                    <div className="glass p-4 rounded-xl inline-block">
                        <div className="text-gray-400 text-sm">総決定事項数</div>
                        <div className="text-3xl font-bold text-green-400">{total}</div>
                    </div>

                    {/* Filters */}
                    <div className="glass p-4 rounded-xl">
                        <div className="flex flex-wrap gap-4">
                            <input
                                type="text"
                                placeholder="決定事項を検索..."
                                value={search}
                                onChange={(e) => {
                                    setSearch(e.target.value);
                                    setOffset(0);
                                }}
                                className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 flex-1 min-w-[200px]"
                            />
                            <select
                                value={projectFilter}
                                onChange={(e) => {
                                    setProjectFilter(e.target.value);
                                    setOffset(0);
                                }}
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
                    {isLoading && decisions.length === 0 ? (
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
                                        disabled={isLoading}
                                        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    >
                                        {isLoading ? '読み込み中...' : 'もっと読み込む'}
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
