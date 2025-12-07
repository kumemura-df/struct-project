'use client';

import { useState, useEffect, useCallback } from 'react';
import { getRisks, getRiskStats, getProjects, exportRisks, Risk, Project } from '../../lib/api';
import { toast } from '../../lib/toast';
import AuthGuard from '../../components/AuthGuard';
import RiskFilters from '../../components/RiskFilters';
import RiskList from '../../components/RiskList';
import ExportButton from '../../components/ExportButton';
import LoadingSpinner from '../../components/LoadingSpinner';
import Link from 'next/link';

export default function RisksPage() {
    const [risks, setRisks] = useState<Risk[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState<any>({});
    const [total, setTotal] = useState(0);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const limit = 20;

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        setOffset(0);
        loadRisks(true);
    }, [filters]);

    async function loadInitialData() {
        try {
            const [projectsData, statsData] = await Promise.all([
                getProjects(),
                getRiskStats()
            ]);
            setProjects(projectsData.items || projectsData);
            setStats(statsData);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            toast.error('Failed to load data');
        }
    }

    async function loadRisks(reset = false) {
        setLoading(true);
        try {
            const { search, ...apiFilters } = filters;
            const currentOffset = reset ? 0 : offset;
            
            // Convert single risk_level to array if needed
            const riskLevelArray = apiFilters.risk_level 
                ? [apiFilters.risk_level] 
                : undefined;
            
            const risksData = await getRisks({
                ...apiFilters,
                risk_level: riskLevelArray,
                search,
                limit,
                offset: currentOffset,
            });
            
            if (reset) {
                setRisks(risksData.items);
            } else {
                setRisks(prev => [...prev, ...risksData.items]);
            }
            setTotal(risksData.total);
            setHasMore(risksData.has_more);
        } catch (error) {
            console.error('Failed to load risks:', error);
            toast.error('Failed to load risks');
        } finally {
            setLoading(false);
        }
    }

    async function handleExport() {
        const { search, ...exportFilters } = filters;
        await exportRisks(exportFilters);
    }

    const handleRiskDeleted = useCallback((riskId: string) => {
        setRisks(prev => prev.filter(r => r.risk_id !== riskId));
        setTotal(prev => prev - 1);
        // Refresh stats
        getRiskStats().then(setStats).catch(console.error);
    }, []);

    const handleRiskUpdated = useCallback((updatedRisk: Risk) => {
        setRisks(prev => prev.map(r => 
            r.risk_id === updatedRisk.risk_id ? updatedRisk : r
        ));
        // Refresh stats
        getRiskStats().then(setStats).catch(console.error);
    }, []);

    const loadMore = () => {
        const newOffset = offset + limit;
        setOffset(newOffset);
        loadRisks(false);
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
                                <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-400">
                                    リスクダッシュボード
                                </h1>
                            </div>
                            <ExportButton onExport={handleExport} label="リスクをエクスポート" />
                        </div>

                        {/* Statistics */}
                        {stats && (
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
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
                    </div>

                    {/* Content */}
                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                        {/* Filters Sidebar */}
                        <div className="lg:col-span-1">
                            <RiskFilters projects={projects} onFilterChange={setFilters} />
                            <div className="mt-4 text-sm text-gray-400">
                                {total} 件のリスク
                            </div>
                        </div>

                        {/* Risks List */}
                        <div className="lg:col-span-3">
                            {loading && risks.length === 0 ? (
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
                </div>
            </div>
        </AuthGuard>
    );
}
