'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
    getDecisions, 
    getDecision,
    deleteDecision,
    Decision,
    PaginatedResponse
} from '../api';
import { toast } from '../toast';

// Query keys
export const decisionKeys = {
    all: ['decisions'] as const,
    lists: () => [...decisionKeys.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...decisionKeys.lists(), filters] as const,
    details: () => [...decisionKeys.all, 'detail'] as const,
    detail: (id: string) => [...decisionKeys.details(), id] as const,
};

// Fetch decisions list
export function useDecisions(filters?: {
    project_id?: string;
    meeting_id?: string;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
}) {
    return useQuery<PaginatedResponse<Decision>>({
        queryKey: decisionKeys.list(filters || {}),
        queryFn: () => getDecisions(filters),
    });
}

// Fetch single decision
export function useDecision(decisionId: string | undefined) {
    return useQuery<Decision>({
        queryKey: decisionKeys.detail(decisionId!),
        queryFn: () => getDecision(decisionId!),
        enabled: !!decisionId,
    });
}

// Delete decision mutation
export function useDeleteDecision() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (decisionId: string) => deleteDecision(decisionId),
        onSuccess: (_, decisionId) => {
            queryClient.removeQueries({ queryKey: decisionKeys.detail(decisionId) });
            queryClient.invalidateQueries({ queryKey: decisionKeys.lists() });
            toast.success('決定事項を削除しました');
        },
        onError: () => {
            toast.error('決定事項の削除に失敗しました');
        },
    });
}

