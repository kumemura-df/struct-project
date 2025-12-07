'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { getTasks, updateTask, deleteTask, Task, TaskUpdate } from '../lib/api';
import { toast } from '../lib/toast';
import LoadingSpinner from './LoadingSpinner';

interface TasksByOwnerViewProps {
    projectId?: string;
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

interface OwnerGroup {
    owner: string;
    tasks: Task[];
    overdueCount: number;
    inProgressCount: number;
}

export default function TasksByOwnerView({ projectId }: TasksByOwnerViewProps) {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedOwners, setExpandedOwners] = useState<Set<string>>(new Set());

    const loadTasks = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getTasks({
                project_id: projectId,
                limit: 500, // Load more for grouping
            });
            setTasks(data.items);
            // Expand all by default
            const owners = new Set(data.items.map(t => t.owner || '未割り当て'));
            setExpandedOwners(owners);
        } catch (error) {
            console.error('Failed to load tasks:', error);
            toast.error('タスクの読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        loadTasks();
    }, [loadTasks]);

    // Group tasks by owner
    const ownerGroups = useMemo((): OwnerGroup[] => {
        const groups: Record<string, Task[]> = {};
        
        tasks.filter(t => t.status !== 'DONE').forEach(task => {
            const owner = task.owner || '未割り当て';
            if (!groups[owner]) {
                groups[owner] = [];
            }
            groups[owner].push(task);
        });

        return Object.entries(groups)
            .map(([owner, ownerTasks]) => ({
                owner,
                tasks: ownerTasks.sort((a, b) => {
                    // Sort by priority first, then by due date
                    const priorityOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
                    const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] ?? 2;
                    const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] ?? 2;
                    if (aPriority !== bPriority) return aPriority - bPriority;
                    
                    if (!a.due_date && !b.due_date) return 0;
                    if (!a.due_date) return 1;
                    if (!b.due_date) return -1;
                    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
                }),
                overdueCount: ownerTasks.filter(t => isOverdue(t.due_date)).length,
                inProgressCount: ownerTasks.filter(t => t.status === 'IN_PROGRESS').length,
            }))
            .sort((a, b) => {
                // Sort by overdue count (descending), then by task count (descending)
                if (b.overdueCount !== a.overdueCount) return b.overdueCount - a.overdueCount;
                return b.tasks.length - a.tasks.length;
            });
    }, [tasks]);

    const toggleOwner = (owner: string) => {
        setExpandedOwners(prev => {
            const next = new Set(prev);
            if (next.has(owner)) {
                next.delete(owner);
            } else {
                next.add(owner);
            }
            return next;
        });
    };

    const expandAll = () => {
        setExpandedOwners(new Set(ownerGroups.map(g => g.owner)));
    };

    const collapseAll = () => {
        setExpandedOwners(new Set());
    };

    const getNextStatus = (current: string): TaskUpdate['status'] => {
        if (current === 'NOT_STARTED') return 'IN_PROGRESS';
        if (current === 'IN_PROGRESS') return 'DONE';
        return 'NOT_STARTED';
    };

    const handleStatusClick = async (task: Task) => {
        const newStatus = getNextStatus(task.status);
        try {
            await updateTask(task.task_id, { status: newStatus });
            toast.success('ステータスを更新しました');
            
            setTasks(prev => {
                if (newStatus === 'DONE') {
                    return prev.filter(t => t.task_id !== task.task_id);
                }
                return prev.map(t =>
                    t.task_id === task.task_id ? { ...t, status: newStatus } : t
                );
            });
        } catch (error) {
            console.error('Failed to update task:', error);
            toast.error('ステータスの更新に失敗しました');
        }
    };

    const handleDelete = async (taskId: string) => {
        if (!confirm('このタスクを削除してもよろしいですか？')) return;
        try {
            await deleteTask(taskId);
            toast.success('タスクを削除しました');
            setTasks(prev => prev.filter(t => t.task_id !== taskId));
        } catch (error) {
            console.error('Failed to delete task:', error);
            toast.error('タスクの削除に失敗しました');
        }
    };

    if (loading) {
        return (
            <div className="glass p-6 rounded-xl flex justify-center">
                <LoadingSpinner size="medium" />
            </div>
        );
    }

    if (ownerGroups.length === 0) {
        return (
            <div className="glass p-6 rounded-xl text-center py-12">
                <div className="text-6xl mb-4">👤</div>
                <p className="text-gray-400">タスクがありません</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Controls */}
            <div className="flex justify-end gap-2">
                <button
                    onClick={expandAll}
                    className="px-3 py-1 text-sm bg-white/10 hover:bg-white/20 rounded-lg text-gray-300 transition-colors"
                >
                    すべて展開
                </button>
                <button
                    onClick={collapseAll}
                    className="px-3 py-1 text-sm bg-white/10 hover:bg-white/20 rounded-lg text-gray-300 transition-colors"
                >
                    すべて折りたたむ
                </button>
            </div>

            {/* Owner Groups */}
            {ownerGroups.map(group => (
                <div key={group.owner} className="glass rounded-xl overflow-hidden">
                    {/* Owner Header */}
                    <button
                        onClick={() => toggleOwner(group.owner)}
                        className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <span className={`transform transition-transform ${
                                expandedOwners.has(group.owner) ? 'rotate-90' : ''
                            }`}>
                                ▶
                            </span>
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                                {group.owner.charAt(0).toUpperCase()}
                            </div>
                            <div className="text-left">
                                <h3 className="text-white font-semibold">{group.owner}</h3>
                                <p className="text-sm text-gray-400">
                                    {group.tasks.length}件のタスク
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            {group.overdueCount > 0 && (
                                <span className="px-2 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400">
                                    🔴 遅延 {group.overdueCount}
                                </span>
                            )}
                            {group.inProgressCount > 0 && (
                                <span className="px-2 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400">
                                    進行中 {group.inProgressCount}
                                </span>
                            )}
                        </div>
                    </button>

                    {/* Task List */}
                    {expandedOwners.has(group.owner) && (
                        <div className="border-t border-white/10">
                            {group.tasks.map(task => (
                                <div
                                    key={task.task_id}
                                    className={`p-4 border-b border-white/5 last:border-b-0 flex items-center gap-4 ${
                                        isOverdue(task.due_date)
                                            ? 'bg-red-500/10 border-l-4 border-l-red-500'
                                            : isDueToday(task.due_date)
                                                ? 'bg-yellow-500/10 border-l-4 border-l-yellow-500'
                                                : 'hover:bg-white/5'
                                    }`}
                                >
                                    {/* Status button */}
                                    <button
                                        onClick={() => handleStatusClick(task)}
                                        className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                                            task.status === 'IN_PROGRESS'
                                                ? 'border-blue-500 bg-blue-500/20'
                                                : 'border-gray-500 hover:border-blue-400'
                                        }`}
                                        title="クリックでステータス変更"
                                    >
                                        {task.status === 'IN_PROGRESS' && (
                                            <div className="w-2 h-2 rounded-full bg-blue-500" />
                                        )}
                                    </button>

                                    {/* Task content */}
                                    <div className="flex-grow min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="text-white font-medium truncate">
                                                {task.task_title}
                                            </span>
                                            {isOverdue(task.due_date) && (
                                                <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-500 text-white animate-pulse flex-shrink-0">
                                                    期限超過
                                                </span>
                                            )}
                                            {isDueToday(task.due_date) && (
                                                <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-500 text-black flex-shrink-0">
                                                    本日期限
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
                                            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                                task.priority === 'HIGH'
                                                    ? 'bg-red-500/20 text-red-400'
                                                    : task.priority === 'MEDIUM'
                                                        ? 'bg-yellow-500/20 text-yellow-400'
                                                        : 'bg-green-500/20 text-green-400'
                                            }`}>
                                                {task.priority === 'HIGH' ? '高' : task.priority === 'MEDIUM' ? '中' : '低'}
                                            </span>
                                            {task.due_date && (
                                                <span className={
                                                    isOverdue(task.due_date)
                                                        ? 'text-red-400'
                                                        : isDueToday(task.due_date)
                                                            ? 'text-yellow-400'
                                                            : ''
                                                }>
                                                    📅 {new Date(task.due_date).toLocaleDateString('ja-JP')}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Delete button */}
                                    <button
                                        onClick={() => handleDelete(task.task_id)}
                                        className="flex-shrink-0 text-red-400 hover:text-red-300 transition-colors opacity-0 group-hover:opacity-100"
                                        title="タスクを削除"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}

