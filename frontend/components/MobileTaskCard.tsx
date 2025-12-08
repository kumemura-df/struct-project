'use client';

import { Task, TaskUpdate } from '../lib/api';
import { useUpdateTask, useDeleteTask } from '../lib/hooks';

interface MobileTaskCardProps {
    task: Task;
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

export default function MobileTaskCard({ task }: MobileTaskCardProps) {
    const updateTaskMutation = useUpdateTask();
    const deleteTaskMutation = useDeleteTask();

    const getNextStatus = (current: string): TaskUpdate['status'] => {
        if (current === 'NOT_STARTED') return 'IN_PROGRESS';
        if (current === 'IN_PROGRESS') return 'DONE';
        return 'NOT_STARTED';
    };

    const getStatusInfo = (status: string) => {
        switch (status) {
            case 'NOT_STARTED':
                return { label: '未着手', color: 'bg-gray-500', textColor: 'text-gray-400' };
            case 'IN_PROGRESS':
                return { label: '進行中', color: 'bg-blue-500', textColor: 'text-blue-400' };
            case 'DONE':
                return { label: '完了', color: 'bg-green-500', textColor: 'text-green-400' };
            default:
                return { label: status, color: 'bg-gray-500', textColor: 'text-gray-400' };
        }
    };

    const getPriorityInfo = (priority: string) => {
        switch (priority) {
            case 'HIGH':
                return { label: '高', color: 'bg-red-500/20 text-red-400 border-red-500/50' };
            case 'MEDIUM':
                return { label: '中', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' };
            case 'LOW':
                return { label: '低', color: 'bg-green-500/20 text-green-400 border-green-500/50' };
            default:
                return { label: priority, color: 'bg-gray-500/20 text-gray-400 border-gray-500/50' };
        }
    };

    const handleStatusClick = () => {
        const newStatus = getNextStatus(task.status);
        updateTaskMutation.mutate({ taskId: task.task_id, updates: { status: newStatus } });
    };

    const handleDelete = () => {
        if (confirm('このタスクを削除しますか？')) {
            deleteTaskMutation.mutate(task.task_id);
        }
    };

    const statusInfo = getStatusInfo(task.status);
    const priorityInfo = getPriorityInfo(task.priority);
    const overdue = isOverdue(task.due_date) && task.status !== 'DONE';
    const dueToday = isDueToday(task.due_date) && task.status !== 'DONE';

    return (
        <div
            className={`glass p-4 rounded-xl ${
                overdue ? 'border-l-4 border-red-500 bg-red-500/5' :
                dueToday ? 'border-l-4 border-yellow-500 bg-yellow-500/5' :
                ''
            }`}
        >
            {/* Header: Title + Delete */}
            <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex-1">
                    <h3 className="font-medium text-white line-clamp-2">
                        {task.task_title}
                    </h3>
                    {(overdue || dueToday) && (
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-bold ${
                            overdue ? 'bg-red-500 text-white' : 'bg-yellow-500 text-black'
                        }`}>
                            {overdue ? '期限超過' : '本日期限'}
                        </span>
                    )}
                </div>
                <button
                    onClick={handleDelete}
                    disabled={deleteTaskMutation.isPending}
                    className="p-2 -mt-1 -mr-1 text-gray-500 hover:text-red-400 transition-colors"
                    aria-label="削除"
                >
                    🗑️
                </button>
            </div>

            {/* Info Row */}
            <div className="flex flex-wrap items-center gap-2 text-sm mb-3">
                {task.owner && (
                    <span className="text-gray-400">
                        👤 {task.owner}
                    </span>
                )}
                {task.due_date && (
                    <span className={`${
                        overdue ? 'text-red-400 font-semibold' :
                        dueToday ? 'text-yellow-400 font-semibold' :
                        'text-gray-400'
                    }`}>
                        📅 {new Date(task.due_date).toLocaleDateString('ja-JP')}
                    </span>
                )}
            </div>

            {/* Actions Row */}
            <div className="flex items-center justify-between">
                {/* Priority Badge */}
                <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${priorityInfo.color}`}>
                    優先度: {priorityInfo.label}
                </span>

                {/* Status Button */}
                <button
                    onClick={handleStatusClick}
                    disabled={updateTaskMutation.isPending}
                    className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                        task.status === 'DONE'
                            ? 'bg-green-500/20 text-green-400'
                            : task.status === 'IN_PROGRESS'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-gray-500/20 text-gray-400'
                    } active:scale-95 disabled:opacity-50`}
                >
                    {updateTaskMutation.isPending ? '...' : statusInfo.label}
                </button>
            </div>
        </div>
    );
}

