'use client';

import { useState, useMemo, useEffect } from 'react';
import { useTasks, useUpdateTask, useDeleteTask } from '../lib/hooks';
import { Task, TaskUpdate } from '../lib/api';
import LoadingSpinner from './LoadingSpinner';
import MobileTaskCard from './MobileTaskCard';

interface TaskListProps {
    projectId?: string;
    showFilters?: boolean;
}

// 日付ヘルパー関数
const getToday = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
};

const isOverdue = (dueDate: string | undefined): boolean => {
    if (!dueDate) return false;
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    return due < getToday();
};

const isDueToday = (dueDate: string | undefined): boolean => {
    if (!dueDate) return false;
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    return due.getTime() === getToday().getTime();
};

const isDueThisWeek = (dueDate: string | undefined): boolean => {
    if (!dueDate) return false;
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    const today = getToday();
    const weekEnd = new Date(today);
    weekEnd.setDate(weekEnd.getDate() + 7);
    return due >= today && due <= weekEnd;
};

export default function TaskList({ projectId, showFilters = true }: TaskListProps) {
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState<string[]>([]);
    const [priorityFilter, setPriorityFilter] = useState<string[]>([]);
    const [ownerFilter, setOwnerFilter] = useState<string>('');
    const [quickFilter, setQuickFilter] = useState<'all' | 'overdue' | 'thisWeek'>('all');
    const [isMobile, setIsMobile] = useState(false);

    // Detect mobile
    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    const { data, isLoading, error } = useTasks({
        project_id: projectId,
        search: search || undefined,
        status: statusFilter.length > 0 ? statusFilter : undefined,
        priority: priorityFilter.length > 0 ? priorityFilter : undefined,
        owner: ownerFilter || undefined,
        limit: 100, // Fetch more for client-side filtering
    });

    const updateTaskMutation = useUpdateTask();
    const deleteTaskMutation = useDeleteTask();

    const tasks = data?.items || [];

    // 担当者のユニークリストを取得
    const uniqueOwners = useMemo(() => {
        const owners = tasks.map(t => t.owner).filter((o): o is string => !!o);
        return [...new Set(owners)].sort();
    }, [tasks]);

    const getNextStatus = (current: string): TaskUpdate['status'] => {
        if (current === 'NOT_STARTED') return 'IN_PROGRESS';
        if (current === 'IN_PROGRESS') return 'DONE';
        return 'NOT_STARTED';
    };

    const getStatusClasses = (status: string): string => {
        if (status === 'DONE') {
            return 'border-green-500 text-green-400';
        }
        if (status === 'IN_PROGRESS') {
            return 'border-blue-500 text-blue-400';
        }
        return 'border-gray-500 text-gray-400';
    };

    const getRowClasses = (task: Task): string => {
        if (task.status === 'DONE') return 'hover:bg-white/5 transition-colors';
        if (isOverdue(task.due_date)) {
            return 'bg-red-500/10 hover:bg-red-500/20 transition-colors border-l-4 border-l-red-500';
        }
        if (isDueToday(task.due_date)) {
            return 'bg-yellow-500/10 hover:bg-yellow-500/20 transition-colors border-l-4 border-l-yellow-500';
        }
        return 'hover:bg-white/5 transition-colors';
    };

    const handleStatusClick = async (task: Task) => {
        const newStatus = getNextStatus(task.status);
        updateTaskMutation.mutate({ taskId: task.task_id, updates: { status: newStatus } });
    };

    const handleDelete = async (taskId: string) => {
        if (!confirm('このタスクを削除してもよろしいですか？')) return;
        deleteTaskMutation.mutate(taskId);
    };

    // フィルタリング（クイックフィルタ含む）
    const visibleTasks = useMemo(() => {
        let filtered = tasks.filter(t => t.status !== 'DONE');
        
        if (quickFilter === 'overdue') {
            filtered = filtered.filter(t => isOverdue(t.due_date));
        } else if (quickFilter === 'thisWeek') {
            filtered = filtered.filter(t => isDueThisWeek(t.due_date));
        }
        
        return filtered;
    }, [tasks, quickFilter]);

    // 統計
    const stats = useMemo(() => {
        const notDone = tasks.filter(t => t.status !== 'DONE');
        return {
            total: notDone.length,
            overdue: notDone.filter(t => isOverdue(t.due_date)).length,
            dueToday: notDone.filter(t => isDueToday(t.due_date)).length,
            thisWeek: notDone.filter(t => isDueThisWeek(t.due_date)).length,
        };
    }, [tasks]);

    if (isLoading) {
        return (
            <div className="glass p-6 rounded-xl flex justify-center">
                <LoadingSpinner size="medium" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass p-6 rounded-xl">
                <div className="text-center py-8">
                    <div className="text-4xl mb-2">❌</div>
                    <p className="text-red-400">タスクの読み込みに失敗しました</p>
                </div>
            </div>
        );
    }

    return (
        <div className="glass p-6 rounded-xl">
            {showFilters && (
                <div className="space-y-4 mb-4">
                    {/* クイックフィルタボタン */}
                    <div className="flex flex-wrap gap-2">
                        <button
                            onClick={() => setQuickFilter('all')}
                            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                                quickFilter === 'all'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                            }`}
                        >
                            すべて ({stats.total})
                        </button>
                        <button
                            onClick={() => setQuickFilter('overdue')}
                            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                                quickFilter === 'overdue'
                                    ? 'bg-red-600 text-white'
                                    : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                            }`}
                        >
                            🔴 期限超過 ({stats.overdue})
                        </button>
                        <button
                            onClick={() => setQuickFilter('thisWeek')}
                            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                                quickFilter === 'thisWeek'
                                    ? 'bg-yellow-600 text-white'
                                    : 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30'
                            }`}
                        >
                            📅 今週期限 ({stats.thisWeek})
                        </button>
                    </div>

                    {/* 詳細フィルタ */}
                    <div className="flex flex-wrap gap-3">
                        <input
                            type="text"
                            placeholder="タスクを検索..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                        />
                        <select
                            value={statusFilter.join(',')}
                            onChange={(e) => setStatusFilter(e.target.value ? e.target.value.split(',') : [])}
                            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                        >
                            <option value="">ステータス: すべて</option>
                            <option value="NOT_STARTED">未着手</option>
                            <option value="IN_PROGRESS">進行中</option>
                            <option value="DONE">完了</option>
                        </select>
                        <select
                            value={priorityFilter.join(',')}
                            onChange={(e) => setPriorityFilter(e.target.value ? e.target.value.split(',') : [])}
                            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                        >
                            <option value="">優先度: すべて</option>
                            <option value="HIGH">高</option>
                            <option value="MEDIUM">中</option>
                            <option value="LOW">低</option>
                        </select>
                        <select
                            value={ownerFilter}
                            onChange={(e) => setOwnerFilter(e.target.value)}
                            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-500"
                        >
                            <option value="">担当者: すべて</option>
                            {uniqueOwners.map(owner => (
                                <option key={owner} value={owner}>{owner}</option>
                            ))}
                        </select>
                    </div>
                </div>
            )}
            {/* Mobile: Card View */}
            {isMobile ? (
                <div className="space-y-3">
                    {visibleTasks.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="text-6xl mb-4">📋</div>
                            <p className="text-gray-400">タスクがありません</p>
                        </div>
                    ) : (
                        visibleTasks.map((task) => (
                            <MobileTaskCard key={task.task_id} task={task} />
                        ))
                    )}
                </div>
            ) : (
                /* Desktop: Table View */
                <div className="overflow-x-auto">
                    {visibleTasks.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="text-6xl mb-4">📋</div>
                            <p className="text-gray-400">タスクがありません</p>
                        </div>
                    ) : (
                        <table className="min-w-full text-left text-sm whitespace-nowrap">
                            <thead className="uppercase tracking-wider border-b border-white/10 bg-white/5">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-gray-300">タイトル</th>
                                    <th scope="col" className="px-6 py-3 text-gray-300">担当者</th>
                                    <th scope="col" className="px-6 py-3 text-gray-300">期限</th>
                                    <th scope="col" className="px-6 py-3 text-gray-300">ステータス</th>
                                    <th scope="col" className="px-6 py-3 text-gray-300">優先度</th>
                                    <th scope="col" className="px-6 py-3 text-gray-300">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/10">
                                {visibleTasks.map((task) => (
                                    <tr key={task.task_id} className={getRowClasses(task)}>
                                        <td className="px-6 py-4 font-medium text-white">
                                            <div className="flex items-center gap-2">
                                                {task.task_title}
                                                {isOverdue(task.due_date) && task.status !== 'DONE' && (
                                                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-500 text-white animate-pulse">
                                                        期限超過
                                                    </span>
                                                )}
                                                {isDueToday(task.due_date) && task.status !== 'DONE' && (
                                                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-500 text-black">
                                                        本日期限
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-300">{task.owner || '-'}</td>
                                        <td className={`px-6 py-4 ${
                                            isOverdue(task.due_date) && task.status !== 'DONE' 
                                                ? 'text-red-400 font-semibold' 
                                                : isDueToday(task.due_date) && task.status !== 'DONE'
                                                    ? 'text-yellow-400 font-semibold'
                                                    : 'text-gray-300'
                                        }`}>
                                            {task.due_date ? new Date(task.due_date).toLocaleDateString('ja-JP') : '-'}
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                type="button"
                                                onClick={() => handleStatusClick(task)}
                                                disabled={updateTaskMutation.isPending}
                                                className={`px-3 py-1 rounded-full text-xs font-semibold bg-transparent border cursor-pointer ${getStatusClasses(task.status)} disabled:opacity-50`}
                                                title="クリックでステータス変更"
                                            >
                                                {task.status === 'NOT_STARTED' ? '未着手' : 
                                                 task.status === 'IN_PROGRESS' ? '進行中' : 
                                                 task.status === 'DONE' ? '完了' : task.status}
                                            </button>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold
                                                ${task.priority === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                                                task.priority === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-green-500/20 text-green-400'}`}>
                                                {task.priority === 'HIGH' ? '高' : 
                                                 task.priority === 'MEDIUM' ? '中' : '低'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => handleDelete(task.task_id)}
                                                disabled={deleteTaskMutation.isPending}
                                                className="text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                                                title="タスクを削除"
                                            >
                                                🗑️
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    );
}
