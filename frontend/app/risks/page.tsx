'use client';

import { useState, useEffect } from 'react';
import { getRisks, getRiskStats, getProjects, exportRisks } from '../../lib/api';
import { toast } from '../../lib/toast';
import AuthGuard from '../../components/AuthGuard';
import RiskFilters from '../../components/RiskFilters';
import RiskList from '../../components/RiskList';
import ExportButton from '../../components/ExportButton';
import LoadingSpinner from '../../components/LoadingSpinner';
import Link from 'next/link';

export default function RisksPage() {
    const [risks, setRisks] = useState<any[]>([]);
    const [projects, setProjects] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState<any>({});

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        loadRisks();
    }, [filters]);

    async function loadInitialData() {
        try {
            const [projectsData, statsData] = await Promise.all([
                getProjects(),
                getRiskStats()
            ]);
            setProjects(projectsData);
            setStats(statsData);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            toast.error('Failed to load data');
        }
    }

    async function loadRisks() {
        setLoading(true);
        try {
            const { search, ...apiFilters } = filters;
            const risksData = await getRisks(apiFilters);
            setRisks(risksData);
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
                        </div>

                        {/* Risks List */}
                        <div className="lg:col-span-3">
                            {loading ? (
                                <div className="glass p-12 rounded-xl flex justify-center">
                                    <LoadingSpinner size="large" text="リスクを読み込み中..." />
                                </div>
                            ) : (
                                <RiskList risks={risks} search={filters.search} />
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </AuthGuard>
    );
}
