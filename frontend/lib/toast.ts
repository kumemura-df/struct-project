/**
 * Toast notification manager using events.
 */

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

type ToastListener = (toast: ToastMessage) => void;

class ToastManager {
    private listeners: ToastListener[] = [];
    private idCounter = 0;

    subscribe(listener: ToastListener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    private emit(toast: ToastMessage) {
        this.listeners.forEach(listener => listener(toast));
    }

    show(type: ToastType, message: string, duration = 5000) {
        const toast: ToastMessage = {
            id: `toast-${++this.idCounter}-${Date.now()}`,
            type,
            message,
            duration
        };
        this.emit(toast);
    }

    success(message: string, duration?: number) {
        this.show('success', message, duration);
    }

    error(message: string, duration?: number) {
        this.show('error', message, duration);
    }

    warning(message: string, duration?: number) {
        this.show('warning', message, duration);
    }

    info(message: string, duration?: number) {
        this.show('info', message, duration);
    }
}

export const toast = new ToastManager();
