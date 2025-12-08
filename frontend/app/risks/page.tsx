'use client';

import { useState, useCallback } from 'react';
import { useRisks, useRiskStats, useProjects } from '../../lib/hooks';
import { exportRisks, Risk } from '../../lib/api';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';
import RiskFilters from '../../components/RiskFilters';
import RiskList from '../../components/RiskList';
import ExportButton from '../../components/ExportButton';
import LoadingSpinner from '../../components/LoadingSpinner';

export default function RisksPage() {
    const [filters, setFilters] = useState<{
        project_id?: string;
        risk_level?: string;
        search?: string;
    }>({});
    const [offset, setOffset] = useState(0);
    const limit = 20;

    // Convert single risk_level to array if needed
    const riskLevelArray = filters.risk_level ? [filters.risk_level] : undefined;

    const { data: risksData, isLoading: risksLoading } = useRisks({
        project_id: filters.project_id,
        risk_level: riskLevelArray,
        search: filters.search,
        limit,
        offset,
    });

    const { data: stats } = useRiskStats();
    const { data: projectsData } = useProjects();

    const risks = risksData?.items || [];
    const total = risksData?.total || 0;
    const hasMore = risksData?.has_more || false;
    const projects = projectsData?.items || [];

    const handleFilterChange = useCallback((newFilters: typeof filters) => {
        setFilters(newFilters);
        setOffset(0);
    }, []);

    async function handleExport() {
        const { search, ...exportFilters } = filters;
        await exportRisks(exportFilters);
    }

    const handleRiskDeleted = useCallback(() => {
        // TanStack Query will automatically refetch due to cache invalidation
    }, []);

    const handleRiskUpdated = useCallback(() => {
        // TanStack Query will automatically refetch due to cache invalidation
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
                            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-400">
                                リスクダッシュボード
                            </h1>
                            <p className="text-gray-400 mt-1">プロジェクトのリスクを管理・追跡</p>
                        </div>
                        <ExportButton onExport={handleExport} label="リスクをエクスポート" />
                    </div>

                    {/* Statistics */}
                    {stats && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="glass p-4 rounded-xl">
                                <div className="text-gray-400 text-sm">総リスク数</div>
                                <div className="text-3xl font-bold text-white">{stats.total}</div>
                            </div>
                            <div className="glass p-4 rounded-xl">
                                <div className="text-gray-400 text-sm">高優先度</div>
                                <div className="text-3xl font-bold text-red-400">{stats.by_level?.HIGH || 0}</div>
                            </div>
                            <div className="glass p-4 rounded-xl">
                                <div className="text-gray-400 text-sm">中優先度</div>
                                <div className="text-3xl font-bold text-yellow-400">{stats.by_level?.MEDIUM || 0}</div>
                            </div>
                            <div className="glass p-4 rounded-xl">
                                <div className="text-gray-400 text-sm">低優先度</div>
                                <div className="text-3xl font-bold text-green-400">{stats.by_level?.LOW || 0}</div>
                            </div>
                        </div>
                    )}

                    {/* Content */}
                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                        {/* Filters Sidebar */}
                        <div className="lg:col-span-1">
                            <RiskFilters projects={projects} onFilterChange={handleFilterChange} />
                            <div className="mt-4 text-sm text-gray-400">
                                {total} 件のリスク
                            </div>
                        </div>

                        {/* Risks List */}
                        <div className="lg:col-span-3">
                            {risksLoading && risks.length === 0 ? (
                                <div className="glass p-12 rounded-xl flex justify-center">
                                    <LoadingSpinner size="large" text="リスクを読み込み中..." />
                                </div>
                            ) : (
                                <>
                                    <RiskList 
                                        risks={risks} 
                                        search={filters.search}
                                        onRiskDeleted={handleRiskDeleted}
                                        onRiskUpdated={handleRiskUpdated}
                                    />
                                    {hasMore && (
                                        <div className="mt-6 text-center">
                                            <button
                                                onClick={loadMore}
                                                disabled={risksLoading}
                                                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                            >
                                                {risksLoading ? '読み込み中...' : 'もっと読み込む'}
                                            </button>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
