'use client';

import { useState, useEffect, useCallback } from 'react';
import AuthGuard from '../../components/AuthGuard';
import LoadingSpinner from '../../components/LoadingSpinner';
import { toast } from '../../lib/toast';
import Link from 'next/link';

interface Meeting {
    meeting_id: string;
    title: string;
    meeting_date: string;
}

interface NewTask {
    task_id: string;
    task_title: string;
    owner: string;
    project_name: string;
    created_at: string;
    status: string;
    priority: string;
}

interface StatusChange {
    task_id: string;
    task_title: string;
    owner: string;
    project_name: string;
    old_value: string;
    new_value: string;
    changed_at: string;
}

interface EscalatedRisk {
    risk_id: string;
    risk_description: string;
    project_name: string;
    old_level: string;
    new_level: string;
    changed_at: string;
}

interface DiffSummary {
    new_tasks: { count: number; items: NewTask[] };
    status_changes: { count: number; items: StatusChange[] };
    escalated_risks: { count: number; items: EscalatedRisk[] };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchWithAuth(url: string) {
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
}

export default function DiffPage() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [selectedMeetingId, setSelectedMeetingId] = useState<string>('');
    const [diff, setDiff] = useState<DiffSummary | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingMeetings, setLoadingMeetings] = useState(true);

    // Load meetings for selector
    useEffect(() => {
        const loadMeetings = async () => {
            try {
                const data = await fetchWithAuth(`${API_URL}/meetings/?limit=20&sort_by=meeting_date&sort_order=desc`);
                setMeetings(data.items || []);
                if (data.items?.length > 0) {
                    setSelectedMeetingId(data.items[0].meeting_id);
                }
            } catch (error) {
                console.error('Failed to load meetings:', error);
                toast.error('会議一覧の読み込みに失敗しました');
            } finally {
                setLoadingMeetings(false);
            }
        };
        loadMeetings();
    }, []);

    // Load diff when meeting selected
    const loadDiff = useCallback(async () => {
        if (!selectedMeetingId) return;
        
        setLoading(true);
        try {
            const data = await fetchWithAuth(`${API_URL}/diff/meetings/${selectedMeetingId}`);
            setDiff(data);
        } catch (error) {
            console.error('Failed to load diff:', error);
            toast.error('差分データの読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }, [selectedMeetingId]);

    useEffect(() => {
        if (selectedMeetingId) {
            loadDiff();
        }
    }, [selectedMeetingId, loadDiff]);

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    const formatDateTime = (dateStr: string) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString('ja-JP', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'NOT_STARTED': return '未着手';
            case 'IN_PROGRESS': return '進行中';
            case 'DONE': return '完了';
            default: return status;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'NOT_STARTED': return 'text-gray-400';
            case 'IN_PROGRESS': return 'text-blue-400';
            case 'DONE': return 'text-green-400';
            default: return 'text-gray-400';
        }
    };

    const getRiskLevelColor = (level: string) => {
        switch (level) {
            case 'HIGH': return 'bg-red-500 text-white';
            case 'MEDIUM': return 'bg-yellow-500 text-black';
            case 'LOW': return 'bg-green-500 text-white';
            default: return 'bg-gray-500 text-white';
        }
    };

    return (
        <AuthGuard>
            <main className="min-h-screen p-8">
                <div className="max-w-6xl mx-auto space-y-8">
                    {/* Header */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <Link
                                href="/"
                                className="text-blue-400 hover:text-blue-300 text-sm mb-2 inline-block"
                            >
                                ← ダッシュボードに戻る
                            </Link>
                            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-cyan-400">
                                🔄 会議間差分
                            </h1>
                            <p className="text-gray-400 mt-1">
                                前回会議からの変更を確認
                            </p>
                        </div>
                    </div>

                    {/* Meeting Selector */}
                    <div className="glass p-4 rounded-xl">
                        <label className="block text-sm text-gray-400 mb-2">
                            基準会議を選択
                        </label>
                        {loadingMeetings ? (
                            <div className="flex items-center gap-2 text-gray-400">
                                <LoadingSpinner size="small" />
                                読み込み中...
                            </div>
                        ) : (
                            <select
                                value={selectedMeetingId}
                                onChange={(e) => setSelectedMeetingId(e.target.value)}
                                className="w-full md:w-auto px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                            >
                                {meetings.map((meeting) => (
                                    <option key={meeting.meeting_id} value={meeting.meeting_id}>
                                        {formatDate(meeting.meeting_date)} - {meeting.title || meeting.meeting_id}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    {/* Diff Content */}
                    {loading ? (
                        <div className="flex justify-center py-20">
                            <LoadingSpinner size="large" />
                        </div>
                    ) : diff ? (
                        <div className="space-y-8">
                            {/* Summary Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="glass p-4 rounded-xl text-center border-l-4 border-blue-500">
                                    <div className="text-3xl font-bold text-blue-400">
                                        {diff.new_tasks.count}
                                    </div>
                                    <div className="text-sm text-gray-400">新規タスク</div>
                                </div>
                                <div className="glass p-4 rounded-xl text-center border-l-4 border-purple-500">
                                    <div className="text-3xl font-bold text-purple-400">
                                        {diff.status_changes.count}
                                    </div>
                                    <div className="text-sm text-gray-400">ステータス変更</div>
                                </div>
                                <div className="glass p-4 rounded-xl text-center border-l-4 border-red-500">
                                    <div className="text-3xl font-bold text-red-400">
                                        {diff.escalated_risks.count}
                                    </div>
                                    <div className="text-sm text-gray-400">リスクエスカレーション</div>
                                </div>
                            </div>

                            {/* New Tasks */}
                            <div className="glass p-6 rounded-xl">
                                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                    ✨ 新規タスク
                                    <span className="text-sm font-normal text-gray-400">
                                        ({diff.new_tasks.count}件)
                                    </span>
                                </h2>
                                {diff.new_tasks.items.length === 0 ? (
                                    <div className="text-center py-8 text-gray-400">
                                        新規タスクはありません
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {diff.new_tasks.items.map((task) => (
                                            <div
                                                key={task.task_id}
                                                className="p-4 bg-blue-500/10 rounded-lg border-l-4 border-blue-500"
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <div className="text-white font-medium">
                                                            {task.task_title}
                                                        </div>
                                                        <div className="text-sm text-gray-400 mt-1">
                                                            担当: {task.owner || '未割当'} / {task.project_name || 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className={`text-sm ${getStatusColor(task.status)}`}>
                                                            {getStatusLabel(task.status)}
                                                        </span>
                                                        <div className="text-xs text-gray-500 mt-1">
                                                            {formatDateTime(task.created_at)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Status Changes */}
                            <div className="glass p-6 rounded-xl">
                                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                    🔄 ステータス変更
                                    <span className="text-sm font-normal text-gray-400">
                                        ({diff.status_changes.count}件)
                                    </span>
                                </h2>
                                {diff.status_changes.items.length === 0 ? (
                                    <div className="text-center py-8 text-gray-400">
                                        ステータス変更はありません
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {diff.status_changes.items.map((change, idx) => (
                                            <div
                                                key={`${change.task_id}-${idx}`}
                                                className="p-4 bg-purple-500/10 rounded-lg border-l-4 border-purple-500"
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <div className="text-white font-medium">
                                                            {change.task_title}
                                                        </div>
                                                        <div className="text-sm text-gray-400 mt-1">
                                                            担当: {change.owner || '未割当'} / {change.project_name || 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="flex items-center gap-2">
                                                            <span className={`text-sm ${getStatusColor(change.old_value)}`}>
                                                                {getStatusLabel(change.old_value)}
                                                            </span>
                                                            <span className="text-gray-500">→</span>
                                                            <span className={`text-sm font-semibold ${getStatusColor(change.new_value)}`}>
                                                                {getStatusLabel(change.new_value)}
                                                            </span>
                                                        </div>
                                                        <div className="text-xs text-gray-500 mt-1">
                                                            {formatDateTime(change.changed_at)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Escalated Risks */}
                            <div className="glass p-6 rounded-xl">
                                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                    ⚠️ リスクエスカレーション
                                    <span className="text-sm font-normal text-gray-400">
                                        ({diff.escalated_risks.count}件)
                                    </span>
                                </h2>
                                {diff.escalated_risks.items.length === 0 ? (
                                    <div className="text-center py-8 text-gray-400">
                                        エスカレーションしたリスクはありません
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {diff.escalated_risks.items.map((risk, idx) => (
                                            <div
                                                key={`${risk.risk_id}-${idx}`}
                                                className="p-4 bg-red-500/10 rounded-lg border-l-4 border-red-500"
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <div className="text-white">
                                                            {risk.risk_description}
                                                        </div>
                                                        <div className="text-sm text-gray-400 mt-1">
                                                            {risk.project_name || 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div className="text-right ml-4">
                                                        <div className="flex items-center gap-2">
                                                            <span className={`px-2 py-0.5 text-xs font-bold rounded ${getRiskLevelColor(risk.old_level)}`}>
                                                                {risk.old_level}
                                                            </span>
                                                            <span className="text-gray-500">→</span>
                                                            <span className={`px-2 py-0.5 text-xs font-bold rounded ${getRiskLevelColor(risk.new_level)}`}>
                                                                {risk.new_level}
                                                            </span>
                                                        </div>
                                                        <div className="text-xs text-gray-500 mt-1">
                                                            {formatDateTime(risk.changed_at)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-20 text-gray-400">
                            会議を選択してください
                        </div>
                    )}
                </div>
            </main>
        </AuthGuard>
    );
}

