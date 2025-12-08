'use client';

import { useState, useEffect, useCallback } from 'react';
import AuthGuard from '../../components/AuthGuard';
import AppLayout from '../../components/AppLayout';
import LoadingSpinner from '../../components/LoadingSpinner';
import { toast } from '../../lib/toast';

interface WeeklySummary {
    week_start: string;
    week_end: string;
    week_offset: number;
    total_tasks: number;
    incomplete_tasks: number;
    overdue_tasks: number;
    high_risks: number;
    weekly_decisions: number;
}

interface OverdueTask {
    task_id: string;
    task_title: string;
    owner: string;
    due_date: string;
    project_name: string;
    days_overdue: number;
}

interface HighRisk {
    risk_id: string;
    risk_description: string;
    risk_level: string;
    project_name: string;
}

interface EmailDraft {
    week_start: string;
    week_end: string;
    email_text: string;
    summary: WeeklySummary;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchWithAuth(url: string) {
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
}

export default function ReportsPage() {
    const [weekOffset, setWeekOffset] = useState(0);
    const [summary, setSummary] = useState<WeeklySummary | null>(null);
    const [overdueTasks, setOverdueTasks] = useState<OverdueTask[]>([]);
    const [highRisks, setHighRisks] = useState<HighRisk[]>([]);
    const [emailDraft, setEmailDraft] = useState<EmailDraft | null>(null);
    const [loading, setLoading] = useState(true);
    const [generatingEmail, setGeneratingEmail] = useState(false);
    const [copied, setCopied] = useState(false);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [summaryData, overdueData, risksData] = await Promise.all([
                fetchWithAuth(`${API_URL}/reports/weekly/summary?week_offset=${weekOffset}`),
                fetchWithAuth(`${API_URL}/reports/weekly/overdue-tasks?limit=10`),
                fetchWithAuth(`${API_URL}/reports/weekly/high-risks?limit=10`),
            ]);
            setSummary(summaryData);
            setOverdueTasks(overdueData.items);
            setHighRisks(risksData.items);
        } catch (error) {
            console.error('Failed to load report data:', error);
            toast.error('レポートデータの読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }, [weekOffset]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const generateEmailDraft = async () => {
        setGeneratingEmail(true);
        try {
            const data = await fetchWithAuth(
                `${API_URL}/reports/email-draft?week_offset=${weekOffset}`
            );
            setEmailDraft(data);
        } catch (error) {
            console.error('Failed to generate email:', error);
            toast.error('メール生成に失敗しました');
        } finally {
            setGeneratingEmail(false);
        }
    };

    const copyToClipboard = async () => {
        if (!emailDraft) return;
        try {
            await navigator.clipboard.writeText(emailDraft.email_text);
            setCopied(true);
            toast.success('クリップボードにコピーしました');
            setTimeout(() => setCopied(false), 2000);
        } catch {
            toast.error('コピーに失敗しました');
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    const getWeekLabel = (offset: number) => {
        if (offset === 0) return '今週';
        if (offset === -1) return '先週';
        return `${Math.abs(offset)}週前`;
    };

    return (
        <AuthGuard>
            <AppLayout>
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-pink-400">
                                週次レポート
                            </h1>
                            <p className="text-gray-400 mt-1">プロジェクト進捗の週次サマリー</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setWeekOffset(prev => prev - 1)}
                                className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                            >
                                ←
                            </button>
                            <span className="px-4 py-2 bg-white/5 rounded-lg text-white min-w-[100px] text-center">
                                {getWeekLabel(weekOffset)}
                            </span>
                            <button
                                onClick={() => setWeekOffset(prev => Math.min(prev + 1, 0))}
                                disabled={weekOffset >= 0}
                                className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors disabled:opacity-50"
                            >
                                →
                            </button>
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex justify-center py-20">
                            <LoadingSpinner size="large" />
                        </div>
                    ) : (
                        <>
                            {/* Week Range */}
                            {summary && (
                                <div className="text-center text-gray-400">
                                    {formatDate(summary.week_start)} 〜 {formatDate(summary.week_end)}
                                </div>
                            )}

                            {/* Summary Cards */}
                            {summary && (
                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    <div className="glass p-4 rounded-xl text-center">
                                        <div className="text-3xl font-bold text-white">
                                            {summary.total_tasks}
                                        </div>
                                        <div className="text-sm text-gray-400">全タスク</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center">
                                        <div className="text-3xl font-bold text-blue-400">
                                            {summary.incomplete_tasks}
                                        </div>
                                        <div className="text-sm text-gray-400">未完了</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center border-2 border-red-500/50">
                                        <div className="text-3xl font-bold text-red-400">
                                            {summary.overdue_tasks}
                                        </div>
                                        <div className="text-sm text-gray-400">期限超過</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center border-2 border-yellow-500/50">
                                        <div className="text-3xl font-bold text-yellow-400">
                                            {summary.high_risks}
                                        </div>
                                        <div className="text-sm text-gray-400">高リスク</div>
                                    </div>
                                    <div className="glass p-4 rounded-xl text-center">
                                        <div className="text-3xl font-bold text-green-400">
                                            {summary.weekly_decisions}
                                        </div>
                                        <div className="text-sm text-gray-400">決定事項</div>
                                    </div>
                                </div>
                            )}

                            {/* Main Content Grid */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Overdue Tasks */}
                                <div className="glass p-6 rounded-xl">
                                    <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                        🔴 期限超過タスク TOP10
                                    </h2>
                                    {overdueTasks.length === 0 ? (
                                        <div className="text-center py-8 text-gray-400">
                                            <div className="text-4xl mb-2">✅</div>
                                            期限超過タスクはありません
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            {overdueTasks.map((task, idx) => (
                                                <div
                                                    key={task.task_id}
                                                    className="p-3 bg-red-500/10 rounded-lg border-l-4 border-red-500"
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-gray-500 text-sm">
                                                                    {idx + 1}.
                                                                </span>
                                                                <span className="text-white font-medium">
                                                                    {task.task_title}
                                                                </span>
                                                            </div>
                                                            <div className="text-sm text-gray-400 mt-1">
                                                                担当: {task.owner || '未割り当て'} / {task.project_name || 'N/A'}
                                                            </div>
                                                        </div>
                                                        <span className="px-2 py-1 bg-red-500 text-white text-xs font-bold rounded">
                                                            {Math.round(task.days_overdue)}日超過
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* High Risks */}
                                <div className="glass p-6 rounded-xl">
                                    <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                        ⚠️ 高リスク項目 TOP10
                                    </h2>
                                    {highRisks.length === 0 ? (
                                        <div className="text-center py-8 text-gray-400">
                                            <div className="text-4xl mb-2">🛡️</div>
                                            高リスク項目はありません
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            {highRisks.map((risk, idx) => (
                                                <div
                                                    key={risk.risk_id}
                                                    className={`p-3 rounded-lg border-l-4 ${
                                                        risk.risk_level === 'HIGH'
                                                            ? 'bg-red-500/10 border-red-500'
                                                            : 'bg-yellow-500/10 border-yellow-500'
                                                    }`}
                                                >
                                                    <div className="flex items-start gap-2">
                                                        <span className="text-gray-500 text-sm">
                                                            {idx + 1}.
                                                        </span>
                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-2">
                                                                <span
                                                                    className={`px-2 py-0.5 text-xs font-bold rounded ${
                                                                        risk.risk_level === 'HIGH'
                                                                            ? 'bg-red-500 text-white'
                                                                            : 'bg-yellow-500 text-black'
                                                                    }`}
                                                                >
                                                                    {risk.risk_level}
                                                                </span>
                                                            </div>
                                                            <div className="text-white mt-1">
                                                                {risk.risk_description}
                                                            </div>
                                                            <div className="text-sm text-gray-400 mt-1">
                                                                {risk.project_name || 'N/A'}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Email Draft Generator */}
                            <div className="glass p-6 rounded-xl">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                        ✉️ メールドラフト生成
                                    </h2>
                                    <button
                                        onClick={generateEmailDraft}
                                        disabled={generatingEmail}
                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                                    >
                                        {generatingEmail ? (
                                            <>
                                                <LoadingSpinner size="small" />
                                                生成中...
                                            </>
                                        ) : (
                                            '📝 レポートを生成'
                                        )}
                                    </button>
                                </div>

                                {emailDraft && (
                                    <div className="mt-4">
                                        <div className="flex justify-end mb-2">
                                            <button
                                                onClick={copyToClipboard}
                                                className={`px-3 py-1 rounded text-sm transition-colors ${
                                                    copied
                                                        ? 'bg-green-600 text-white'
                                                        : 'bg-white/10 hover:bg-white/20 text-white'
                                                }`}
                                            >
                                                {copied ? '✓ コピー済み' : '📋 コピー'}
                                            </button>
                                        </div>
                                        <pre className="bg-black/30 p-4 rounded-lg text-gray-300 text-sm whitespace-pre-wrap overflow-x-auto font-mono">
                                            {emailDraft.email_text}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
