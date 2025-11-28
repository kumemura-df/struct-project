'use client';

import { useState } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface ExportButtonProps {
    onExport: () => Promise<void>;
    label?: string;
    size?: 'small' | 'medium';
}

export default function ExportButton({
    onExport,
    label = 'CSVエクスポート',
    size = 'medium'
}: ExportButtonProps) {
    const [loading, setLoading] = useState(false);

    const handleExport = async () => {
        setLoading(true);
        try {
            await onExport();
        } catch (error) {
            console.error('Export failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const sizeClasses = {
        small: 'px-3 py-1.5 text-sm',
        medium: 'px-4 py-2'
    };

    return (
        <button
            onClick={handleExport}
            disabled={loading}
            className={`${sizeClasses[size]} bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center space-x-2 shadow-lg`}
        >
            {loading ? (
                <>
                    <LoadingSpinner size="small" />
                    <span>エクスポート中...</span>
                </>
            ) : (
                <>
                    <span>📥</span>
                    <span>{label}</span>
                </>
            )}
        </button>
    );
}
