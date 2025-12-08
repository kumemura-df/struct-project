'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
    getTasks, 
    getTask, 
    updateTask, 
    deleteTask,
    Task,
    TaskUpdate,
    PaginatedResponse
} from '../api';
import { toast } from '../toast';

// Query keys
export const taskKeys = {
    all: ['tasks'] as const,
    lists: () => [...taskKeys.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...taskKeys.lists(), filters] as const,
    details: () => [...taskKeys.all, 'detail'] as const,
    detail: (id: string) => [...taskKeys.details(), id] as const,
};

// Fetch tasks list
export function useTasks(filters?: {
    project_id?: string;
    status?: string[];
    priority?: string[];
    owner?: string;
    due_date_from?: string;
    due_date_to?: string;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
}) {
    return useQuery<PaginatedResponse<Task>>({
        queryKey: taskKeys.list(filters || {}),
        queryFn: () => getTasks(filters),
    });
}

// Fetch single task
export function useTask(taskId: string | undefined) {
    return useQuery<Task>({
        queryKey: taskKeys.detail(taskId!),
        queryFn: () => getTask(taskId!),
        enabled: !!taskId,
    });
}

// Update task mutation with optimistic update
export function useUpdateTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ taskId, updates }: { taskId: string; updates: TaskUpdate }) =>
            updateTask(taskId, updates),
        onMutate: async ({ taskId, updates }) => {
            // Cancel outgoing refetches
            await queryClient.cancelQueries({ queryKey: taskKeys.lists() });

            // Snapshot previous value
            const previousTasks = queryClient.getQueriesData({ queryKey: taskKeys.lists() });

            // Optimistically update lists
            queryClient.setQueriesData(
                { queryKey: taskKeys.lists() },
                (old: PaginatedResponse<Task> | undefined) => {
                    if (!old) return old;
                    return {
                        ...old,
                        items: old.items.map((task) =>
                            task.task_id === taskId ? { ...task, ...updates } : task
                        ),
                    };
                }
            );

            return { previousTasks };
        },
        onError: (_, __, context) => {
            // Rollback on error
            if (context?.previousTasks) {
                context.previousTasks.forEach(([queryKey, data]) => {
                    queryClient.setQueryData(queryKey, data);
                });
            }
            toast.error('タスクの更新に失敗しました');
        },
        onSuccess: (data, variables) => {
            // Update cache with server response
            queryClient.setQueryData(taskKeys.detail(variables.taskId), data);
            toast.success('ステータスを更新しました');
        },
        onSettled: () => {
            // Refetch to ensure consistency
            queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
        },
    });
}

// Delete task mutation
export function useDeleteTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (taskId: string) => deleteTask(taskId),
        onMutate: async (taskId) => {
            await queryClient.cancelQueries({ queryKey: taskKeys.lists() });

            const previousTasks = queryClient.getQueriesData({ queryKey: taskKeys.lists() });

            // Optimistically remove from lists
            queryClient.setQueriesData(
                { queryKey: taskKeys.lists() },
                (old: PaginatedResponse<Task> | undefined) => {
                    if (!old) return old;
                    return {
                        ...old,
                        items: old.items.filter((task) => task.task_id !== taskId),
                        total: old.total - 1,
                    };
                }
            );

            return { previousTasks };
        },
        onError: (_, __, context) => {
            if (context?.previousTasks) {
                context.previousTasks.forEach(([queryKey, data]) => {
                    queryClient.setQueryData(queryKey, data);
                });
            }
            toast.error('タスクの削除に失敗しました');
        },
        onSuccess: (_, taskId) => {
            queryClient.removeQueries({ queryKey: taskKeys.detail(taskId) });
            toast.success('タスクを削除しました');
        },
    });
}

