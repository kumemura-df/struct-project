import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProjects, projectKeys } from '../useProjects';
import * as api from '../../api';

// Mock the API module
vi.mock('../../api', async () => {
    const actual = await vi.importActual('../../api');
    return {
        ...actual,
        getProjects: vi.fn(),
    };
});

const mockGetProjects = api.getProjects as vi.MockedFunction<typeof api.getProjects>;

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        );
    };
}

describe('useProjects', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('fetches projects successfully', async () => {
        const mockData = {
            items: [
                { project_id: '1', project_name: 'Project 1', updated_at: '2024-01-01' },
                { project_id: '2', project_name: 'Project 2', updated_at: '2024-01-02' },
            ],
            total: 2,
            limit: 20,
            offset: 0,
            has_more: false,
        };
        
        mockGetProjects.mockResolvedValue(mockData as api.PaginatedResponse<api.ProjectWithStats>);

        const { result } = renderHook(() => useProjects(), {
            wrapper: createWrapper(),
        });

        // Initially loading
        expect(result.current.isLoading).toBe(true);

        // Wait for data
        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        expect(result.current.data).toEqual(mockData);
        expect(mockGetProjects).toHaveBeenCalledOnce();
    });

    it('handles error state', async () => {
        mockGetProjects.mockRejectedValue(new Error('Failed to fetch'));

        const { result } = renderHook(() => useProjects(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => {
            expect(result.current.isError).toBe(true);
        });

        expect(result.current.error).toBeDefined();
    });

    it('passes filters to API', async () => {
        const mockData = {
            items: [],
            total: 0,
            limit: 20,
            offset: 0,
            has_more: false,
        };
        
        mockGetProjects.mockResolvedValue(mockData as api.PaginatedResponse<api.ProjectWithStats>);

        const filters = {
            search: 'test',
            include_stats: true,
        };

        renderHook(() => useProjects(filters), {
            wrapper: createWrapper(),
        });

        await waitFor(() => {
            expect(mockGetProjects).toHaveBeenCalledWith(filters);
        });
    });
});

describe('projectKeys', () => {
    it('generates correct query keys', () => {
        expect(projectKeys.all).toEqual(['projects']);
        expect(projectKeys.lists()).toEqual(['projects', 'list']);
        expect(projectKeys.list({ search: 'test' })).toEqual(['projects', 'list', { search: 'test' }]);
        expect(projectKeys.detail('123')).toEqual(['projects', 'detail', '123']);
        expect(projectKeys.stats('123')).toEqual(['projects', 'stats', '123']);
    });
});
