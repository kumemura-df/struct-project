'use client';

import { useState, useEffect } from 'react';
import { toast as toastManager, type ToastMessage } from '../lib/toast';
import Toast from './Toast';

export default function ToastContainer() {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    useEffect(() => {
        const unsubscribe = toastManager.subscribe((newToast) => {
            setToasts((prev) => [...prev, newToast]);
        });

        return unsubscribe;
    }, []);

    const dismissToast = (id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return (
        <div className="fixed top-4 right-4 z-50 space-y-3">
            {toasts.map((toast) => (
                <Toast key={toast.id} toast={toast} onDismiss={dismissToast} />
            ))}
        </div>
    );
}
