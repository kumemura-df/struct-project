'use client';

import { useQuery } from '@tanstack/react-query';
import { 
    getMeetings, 
    getMeeting,
    Meeting,
    PaginatedResponse
} from '../api';

// Query keys
export const meetingKeys = {
    all: ['meetings'] as const,
    lists: () => [...meetingKeys.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...meetingKeys.lists(), filters] as const,
    details: () => [...meetingKeys.all, 'detail'] as const,
    detail: (id: string) => [...meetingKeys.details(), id] as const,
};

// Fetch meetings list
export function useMeetings(filters?: {
    status?: string;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
}) {
    return useQuery<PaginatedResponse<Meeting>>({
        queryKey: meetingKeys.list(filters || {}),
        queryFn: () => getMeetings(filters),
        // Refetch more frequently if there are pending meetings
        refetchInterval: (query) => {
            const data = query.state.data;
            if (data?.items?.some(m => m.status === 'PENDING')) {
                return 5000; // 5 seconds for pending meetings
            }
            return false;
        },
    });
}

// Fetch single meeting
export function useMeeting(meetingId: string | undefined) {
    return useQuery<Meeting>({
        queryKey: meetingKeys.detail(meetingId!),
        queryFn: () => getMeeting(meetingId!),
        enabled: !!meetingId,
    });
}

