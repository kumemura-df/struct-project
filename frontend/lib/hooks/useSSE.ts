'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { meetingKeys } from './useMeetings';
import { taskKeys } from './useTasks';
import { riskKeys } from './useRisks';
import { projectKeys } from './useProjects';
import { toast } from '../toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SSEEvent {
    type: string;
    data: {
        entity_type?: string;
        entity_id?: string;
        action?: string;
        meeting_id?: string;
        status?: string;
        message?: string;
        [key: string]: unknown;
    };
}

export function useSSE(enabled: boolean = true) {
    const queryClient = useQueryClient();
    const eventSourceRef = useRef<EventSource | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    const handleEvent = useCallback((event: SSEEvent) => {
        const { type, data } = event;

        switch (type) {
            case 'meeting_processing_complete':
                // Meeting processing finished
                queryClient.invalidateQueries({ queryKey: meetingKeys.all });
                queryClient.invalidateQueries({ queryKey: taskKeys.all });
                queryClient.invalidateQueries({ queryKey: riskKeys.all });
                queryClient.invalidateQueries({ queryKey: projectKeys.all });
                
                toast.success(`会議「${data.meeting_id}」の処理が完了しました`);
                
                // Browser notification
                if (Notification.permission === 'granted') {
                    new Notification('会議処理完了', {
                        body: `会議の解析が完了しました`,
                        icon: '/favicon.ico'
                    });
                }
                break;

            case 'meeting_processing_error':
                queryClient.invalidateQueries({ queryKey: meetingKeys.all });
                toast.error(`会議の処理中にエラーが発生しました`);
                break;

            case 'task_created':
            case 'task_updated':
            case 'task_deleted':
                queryClient.invalidateQueries({ queryKey: taskKeys.all });
                if (data.entity_id) {
                    queryClient.invalidateQueries({ queryKey: taskKeys.detail(data.entity_id) });
                }
                break;

            case 'risk_created':
            case 'risk_updated':
            case 'risk_deleted':
                queryClient.invalidateQueries({ queryKey: riskKeys.all });
                queryClient.invalidateQueries({ queryKey: riskKeys.stats() });
                if (data.entity_id) {
                    queryClient.invalidateQueries({ queryKey: riskKeys.detail(data.entity_id) });
                }
                break;

            case 'project_updated':
            case 'project_deleted':
                queryClient.invalidateQueries({ queryKey: projectKeys.all });
                if (data.entity_id) {
                    queryClient.invalidateQueries({ queryKey: projectKeys.detail(data.entity_id) });
                    queryClient.invalidateQueries({ queryKey: projectKeys.stats(data.entity_id) });
                }
                break;

            case 'ping':
                // Keep-alive ping, no action needed
                break;

            default:
                console.log('[SSE] Unknown event type:', type, data);
        }
    }, [queryClient]);

    const connect = useCallback(() => {
        if (eventSourceRef.current?.readyState === EventSource.OPEN) {
            return;
        }

        try {
            const eventSource = new EventSource(`${API_URL}/events/stream`, {
                withCredentials: true,
            });

            eventSource.onopen = () => {
                console.log('[SSE] Connected');
                reconnectAttempts.current = 0;
            };

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleEvent(data);
                } catch (error) {
                    console.error('[SSE] Failed to parse event:', error);
                }
            };

            eventSource.onerror = (error) => {
                console.error('[SSE] Connection error:', error);
                eventSource.close();
                eventSourceRef.current = null;

                // Attempt reconnection with exponential backoff
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                    reconnectAttempts.current++;
                    
                    console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
                    
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, delay);
                } else {
                    console.error('[SSE] Max reconnection attempts reached');
                }
            };

            eventSourceRef.current = eventSource;
        } catch (error) {
            console.error('[SSE] Failed to create EventSource:', error);
        }
    }, [handleEvent]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        
        reconnectAttempts.current = 0;
    }, []);

    useEffect(() => {
        if (enabled) {
            connect();
        }

        return () => {
            disconnect();
        };
    }, [enabled, connect, disconnect]);

    return {
        connected: eventSourceRef.current?.readyState === EventSource.OPEN,
        reconnect: connect,
        disconnect,
    };
}

// Hook to request notification permission
export function useNotificationPermission() {
    useEffect(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            // Request permission after user interaction
            const handleClick = () => {
                Notification.requestPermission();
                document.removeEventListener('click', handleClick);
            };
            document.addEventListener('click', handleClick, { once: true });
        }
    }, []);
}

