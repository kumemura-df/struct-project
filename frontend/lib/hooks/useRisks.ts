'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
    getRisks, 
    getRisk,
    getRiskStats,
    updateRisk, 
    deleteRisk,
    Risk,
    RiskUpdate,
    PaginatedResponse
} from '../api';
import { toast } from '../toast';

// Query keys
export const riskKeys = {
    all: ['risks'] as const,
    lists: () => [...riskKeys.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...riskKeys.lists(), filters] as const,
    details: () => [...riskKeys.all, 'detail'] as const,
    detail: (id: string) => [...riskKeys.details(), id] as const,
    stats: () => [...riskKeys.all, 'stats'] as const,
};

// Risk stats type
export interface RiskStats {
    total: number;
    by_level: {
        HIGH?: number;
        MEDIUM?: number;
        LOW?: number;
    };
}

// Fetch risks list
export function useRisks(filters?: {
    project_id?: string;
    risk_level?: string[];
    meeting_id?: string;
    owner?: string;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
}) {
    return useQuery<PaginatedResponse<Risk>>({
        queryKey: riskKeys.list(filters || {}),
        queryFn: () => getRisks(filters),
    });
}

// Fetch single risk
export function useRisk(riskId: string | undefined) {
    return useQuery<Risk>({
        queryKey: riskKeys.detail(riskId!),
        queryFn: () => getRisk(riskId!),
        enabled: !!riskId,
    });
}

// Fetch risk stats
export function useRiskStats() {
    return useQuery<RiskStats>({
        queryKey: riskKeys.stats(),
        queryFn: getRiskStats,
    });
}

// Update risk mutation
export function useUpdateRisk() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ riskId, updates }: { riskId: string; updates: RiskUpdate }) =>
            updateRisk(riskId, updates),
        onSuccess: (data, variables) => {
            queryClient.setQueryData(riskKeys.detail(variables.riskId), data);
            queryClient.invalidateQueries({ queryKey: riskKeys.lists() });
            queryClient.invalidateQueries({ queryKey: riskKeys.stats() });
            toast.success('リスクレベルを更新しました');
        },
        onError: () => {
            toast.error('リスクレベルの更新に失敗しました');
        },
    });
}

// Delete risk mutation
export function useDeleteRisk() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (riskId: string) => deleteRisk(riskId),
        onMutate: async (riskId) => {
            await queryClient.cancelQueries({ queryKey: riskKeys.lists() });

            const previousRisks = queryClient.getQueriesData({ queryKey: riskKeys.lists() });

            queryClient.setQueriesData(
                { queryKey: riskKeys.lists() },
                (old: PaginatedResponse<Risk> | undefined) => {
                    if (!old) return old;
                    return {
                        ...old,
                        items: old.items.filter((risk) => risk.risk_id !== riskId),
                        total: old.total - 1,
                    };
                }
            );

            return { previousRisks };
        },
        onError: (_, __, context) => {
            if (context?.previousRisks) {
                context.previousRisks.forEach(([queryKey, data]) => {
                    queryClient.setQueryData(queryKey, data);
                });
            }
            toast.error('リスクの削除に失敗しました');
        },
        onSuccess: (_, riskId) => {
            queryClient.removeQueries({ queryKey: riskKeys.detail(riskId) });
            queryClient.invalidateQueries({ queryKey: riskKeys.stats() });
            toast.success('リスクを削除しました');
        },
    });
}

