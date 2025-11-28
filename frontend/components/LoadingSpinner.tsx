'use client';

interface LoadingSpinnerProps {
    size?: 'small' | 'medium' | 'large';
    text?: string;
    overlay?: boolean;
}

export default function LoadingSpinner({
    size = 'medium',
    text,
    overlay = false
}: LoadingSpinnerProps) {
    const sizeClasses = {
        small: 'h-6 w-6 border-2',
        medium: 'h-12 w-12 border-4',
        large: 'h-16 w-16 border-4'
    };

    const spinner = (
        <div className="flex flex-col items-center justify-center space-y-3">
            <div
                className={`${sizeClasses[size]} border-blue-400 border-t-transparent rounded-full animate-spin`}
            />
            {text && <p className="text-gray-300 text-sm">{text}</p>}
        </div>
    );

    if (overlay) {
        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                {spinner}
            </div>
        );
    }

    return spinner;
}
