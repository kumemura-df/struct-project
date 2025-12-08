'use client';

import { useState, useEffect, useCallback } from 'react';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';
import LoadingSpinner from '../../components/LoadingSpinner';
import { toast } from '../../lib/toast';

interface ProjectHealth {
    project_id: string;
    project_name: string;
    score: number;
    overdue_penalty: number;
    risk_penalty: number;
    uncompleted_penalty: number;
    stale_penalty: number;
    status?: string;
    status_label?: string;
    details: {
        total_tasks: number;
        completed_tasks: number;
        overdue_tasks: number;
        high_risks: number;
        overdue_rate: number;
        completion_rate: number;
    };
    recommendations?: Array<{
        type: string;
        priority: string;
        message: string;
    }>;
}

interface HealthSummary {
    total_projects: number;
    average_score: number;
    critical_count: number;
    warning_count: number;
    healthy_count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HealthPage() {
    const [projects, setProjects] = useState<ProjectHealth[]>([]);
    const [summary, setSummary] = useState<HealthSummary | null>(null);
    const [selectedProject, setSelectedProject] = useState<ProjectHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);

    const loadProjects = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/health/projects`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error('Failed to load');
            const data = await res.json();
            setProjects(data.projects || []);
            setSummary(data.summary || null);
        } catch (error) {
            console.error('Failed to load health scores:', error);
            toast.error('ヘルススコアの読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadProjects();
    }, [loadProjects]);

    const loadProjectDetail = async (projectId: string) => {
        setDetailLoading(true);
        try {
            const res = await fetch(`${API_URL}/health/projects/${projectId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error('Failed to load');
            const data = await res.json();
            setSelectedProject(data);
        } catch (error) {
            console.error('Failed to load project health:', error);
            toast.error('詳細の読み込みに失敗しました');
        } finally {
            setDetailLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-green-400';
        if (score >= 60) return 'text-yellow-400';
        if (score >= 40) return 'text-orange-400';
        return 'text-red-400';
    };

    const getScoreBgColor = (score: number) => {
        if (score >= 80) return 'bg-green-500';
        if (score >= 60) return 'bg-yellow-500';
        if (score >= 40) return 'bg-orange-500';
        return 'bg-red-500';
    };

    const getStatusEmoji = (score: number) => {
        if (score >= 80) return '✅';
        if (score >= 60) return '⚠️';
        if (score >= 40) return '🔶';
        return '🚨';
    };

    const ScoreGauge = ({ score }: { score: number }) => {
        const angle = (score / 100) * 180 - 90;
        return (
            <div className="relative w-32 h-16 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-t-full" />
                <div className="absolute inset-1 bg-gray-900 rounded-t-full" />
                <div
                    className="absolute bottom-0 left-1/2 w-1 h-14 bg-white origin-bottom rounded-full"
                    style={{ transform: `translateX(-50%) rotate(${angle}deg)` }}
                />
                <div className="absolute bottom-0 left-1/2 w-4 h-4 bg-white rounded-full transform -translate-x-1/2 translate-y-1/2" />
            </div>
        );
    };

    return (
        <AuthGuard>
            <AppLayout>
                <div className="space-y-6">
                    {/* Header */}
                    <div>
                        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">
                            プロジェクトヘルススコア
                        </h1>
                        <p className="text-gray-400 mt-1">
                            プロジェクトの健全性を可視化
                        </p>
                    </div>

                    {loading ? (
                        <div className="flex justify-center py-20">
                            <LoadingSpinner size="large" />
                        </div>
                    ) : (
                        <>
                            {/* Summary Cards */}
                            {summary && (
                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    <div className="glass p-4 rounded-xl text-center">
                                        <div className="text-3xl font-bold text-white">
                                            {summary.total_projects}
                                        </div>
                                        <div className="text-sm text-gray-400">プロジェクト数</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center">
                                        <div className={`text-3xl font-bold ${getScoreColor(summary.average_score)}`}>
                                            {summary.average_score}
                                        </div>
                                        <div className="text-sm text-gray-400">平均スコア</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center border-l-4 border-green-500">
                                        <div className="text-3xl font-bold text-green-400">
                                            {summary.healthy_count}
                                        </div>
                                        <div className="text-sm text-gray-400">良好 (≥70)</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center border-l-4 border-yellow-500">
                                        <div className="text-3xl font-bold text-yellow-400">
                                            {summary.warning_count}
                                        </div>
                                        <div className="text-sm text-gray-400">注意 (50-69)</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center border-l-4 border-red-500">
                                        <div className="text-3xl font-bold text-red-400">
                                            {summary.critical_count}
                                        </div>
                                        <div className="text-sm text-gray-400">危険 (&lt;50)</div>
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                {/* Project List */}
                                <div className="lg:col-span-2 space-y-4">
                                    <h2 className="text-xl font-semibold text-white">プロジェクト一覧</h2>
                                    <div className="space-y-3">
                                        {projects.map((project) => (
                                            <button
                                                key={project.project_id}
                                                onClick={() => loadProjectDetail(project.project_id)}
                                                className={`w-full text-left glass p-4 rounded-xl hover:bg-white/10 transition-colors ${
                                                    selectedProject?.project_id === project.project_id
                                                        ? 'ring-2 ring-blue-500'
                                                        : ''
                                                }`}
                                            >
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-4">
                                                        <span className="text-2xl">
                                                            {getStatusEmoji(project.score)}
                                                        </span>
                                                        <div>
                                                            <div className="text-white font-medium">
                                                                {project.project_name || project.project_id}
                                                            </div>
                                                            <div className="flex gap-4 text-xs text-gray-400 mt-1">
                                                                <span>タスク: {project.details.total_tasks}</span>
                                                                <span>完了率: {project.details.completion_rate}%</span>
                                                                <span>超過: {project.details.overdue_tasks}</span>
                                                                <span>高リスク: {project.details.high_risks}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className={`text-3xl font-bold ${getScoreColor(project.score)}`}>
                                                            {project.score}
                                                        </div>
                                                        <div className="w-24 h-2 bg-gray-700 rounded-full mt-2 overflow-hidden">
                                                            <div
                                                                className={`h-full ${getScoreBgColor(project.score)} transition-all`}
                                                                style={{ width: `${project.score}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Detail Panel */}
                                <div className="lg:col-span-1">
                                    <h2 className="text-xl font-semibold text-white mb-4">詳細</h2>
                                    {detailLoading ? (
                                        <div className="glass p-8 rounded-xl flex justify-center">
                                            <LoadingSpinner />
                                        </div>
                                    ) : selectedProject ? (
                                        <div className="glass p-6 rounded-xl space-y-6">
                                            {/* Score Display */}
                                            <div className="text-center">
                                                <div className="text-lg text-gray-400 mb-2">
                                                    {selectedProject.project_name}
                                                </div>
                                                <ScoreGauge score={selectedProject.score} />
                                                <div className={`text-4xl font-bold mt-2 ${getScoreColor(selectedProject.score)}`}>
                                                    {selectedProject.score}
                                                </div>
                                                <div className="text-sm text-gray-400">/ 100</div>
                                            </div>

                                            {/* Penalty Breakdown */}
                                            <div className="space-y-3">
                                                <h3 className="text-sm font-medium text-gray-400">減点内訳</h3>
                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center">
                                                        <span className="text-gray-300">期限超過</span>
                                                        <span className="text-red-400">-{selectedProject.overdue_penalty}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center">
                                                        <span className="text-gray-300">高リスク</span>
                                                        <span className="text-red-400">-{selectedProject.risk_penalty}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center">
                                                        <span className="text-gray-300">未完了率</span>
                                                        <span className="text-red-400">-{selectedProject.uncompleted_penalty}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center">
                                                        <span className="text-gray-300">更新停滞</span>
                                                        <span className="text-red-400">-{selectedProject.stale_penalty}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Recommendations */}
                                            {selectedProject.recommendations && selectedProject.recommendations.length > 0 && (
                                                <div className="space-y-3">
                                                    <h3 className="text-sm font-medium text-gray-400">改善提案</h3>
                                                    <div className="space-y-2">
                                                        {selectedProject.recommendations.map((rec, i) => (
                                                            <div
                                                                key={i}
                                                                className={`p-3 rounded-lg text-sm ${
                                                                    rec.priority === 'high'
                                                                        ? 'bg-red-500/20 border-l-4 border-red-500'
                                                                        : 'bg-yellow-500/20 border-l-4 border-yellow-500'
                                                                }`}
                                                            >
                                                                {rec.message}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Stats */}
                                            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10">
                                                <div className="text-center p-3 bg-white/5 rounded-lg">
                                                    <div className="text-2xl font-bold text-white">
                                                        {selectedProject.details.completion_rate}%
                                                    </div>
                                                    <div className="text-xs text-gray-400">完了率</div>
                                                </div>
                                                <div className="text-center p-3 bg-white/5 rounded-lg">
                                                    <div className="text-2xl font-bold text-red-400">
                                                        {selectedProject.details.overdue_tasks}
                                                    </div>
                                                    <div className="text-xs text-gray-400">期限超過</div>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="glass p-8 rounded-xl text-center text-gray-400">
                                            プロジェクトを選択してください
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
