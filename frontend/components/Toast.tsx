'use client';

import { useEffect } from 'react';
import type { ToastMessage } from '../lib/toast';

interface ToastProps {
    toast: ToastMessage;
    onDismiss: (id: string) => void;
}

export default function Toast({ toast, onDismiss }: ToastProps) {
    useEffect(() => {
        if (toast.duration) {
            const timer = setTimeout(() => {
                onDismiss(toast.id);
            }, toast.duration);
            return () => clearTimeout(timer);
        }
    }, [toast.id, toast.duration, onDismiss]);

    const getBackgroundColor = () => {
        switch (toast.type) {
            case 'success':
                return 'bg-green-500';
            case 'error':
                return 'bg-red-500';
            case 'warning':
                return 'bg-yellow-500';
            case 'info':
                return 'bg-blue-500';
        }
    };

    const getIcon = () => {
        switch (toast.type) {
            case 'success':
                return '✓';
            case 'error':
                return '✕';
            case 'warning':
                return '⚠';
            case 'info':
                return 'ℹ';
        }
    };

    return (
        <div
            className={`${getBackgroundColor()} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 min-w-[300px] max-w-md animate-slide-in`}
        >
            <span className="text-2xl">{getIcon()}</span>
            <p className="flex-1 text-sm">{toast.message}</p>
            <button
                onClick={() => onDismiss(toast.id)}
                className="text-white hover:text-gray-200 transition-colors text-xl"
            >
                ×
            </button>
        </div>
    );
}
