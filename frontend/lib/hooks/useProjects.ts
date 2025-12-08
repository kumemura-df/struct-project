'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
    getProjects, 
    getProject, 
    getProjectStats,
    updateProject, 
    deleteProject,
    Project,
    ProjectWithStats,
    ProjectStats,
    ProjectUpdate,
    PaginatedResponse
} from '../api';
import { toast } from '../toast';

// Query keys
export const projectKeys = {
    all: ['projects'] as const,
    lists: () => [...projectKeys.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...projectKeys.lists(), filters] as const,
    details: () => [...projectKeys.all, 'detail'] as const,
    detail: (id: string) => [...projectKeys.details(), id] as const,
    stats: (id: string) => [...projectKeys.all, 'stats', id] as const,
};

// Fetch projects list (with optional stats included)
export function useProjects(filters?: {
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
    include_stats?: boolean;
}) {
    return useQuery<PaginatedResponse<ProjectWithStats>>({
        queryKey: projectKeys.list(filters || {}),
        queryFn: () => getProjects(filters),
    });
}

// Fetch single project
export function useProject(projectId: string | undefined) {
    return useQuery<Project>({
        queryKey: projectKeys.detail(projectId!),
        queryFn: () => getProject(projectId!),
        enabled: !!projectId,
    });
}

// Fetch project stats (kept for backward compatibility, but prefer include_stats in useProjects)
export function useProjectStats(projectId: string | undefined) {
    return useQuery<ProjectStats>({
        queryKey: projectKeys.stats(projectId!),
        queryFn: () => getProjectStats(projectId!),
        enabled: !!projectId,
    });
}

// Update project mutation
export function useUpdateProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ projectId, updates }: { projectId: string; updates: ProjectUpdate }) =>
            updateProject(projectId, updates),
        onSuccess: (data, variables) => {
            // Update cache
            queryClient.setQueryData(projectKeys.detail(variables.projectId), data);
            // Invalidate lists
            queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
            toast.success('プロジェクトを更新しました');
        },
        onError: () => {
            toast.error('プロジェクトの更新に失敗しました');
        },
    });
}

// Delete project mutation
export function useDeleteProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (projectId: string) => deleteProject(projectId),
        onSuccess: (_, projectId) => {
            // Remove from cache
            queryClient.removeQueries({ queryKey: projectKeys.detail(projectId) });
            // Invalidate lists
            queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
            toast.success('プロジェクトを削除しました');
        },
        onError: () => {
            toast.error('プロジェクトの削除に失敗しました');
        },
    });
}

