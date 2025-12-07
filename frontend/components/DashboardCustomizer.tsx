'use client';

import { useState, useEffect } from 'react';

export interface WidgetConfig {
    id: string;
    name: string;
    enabled: boolean;
    order: number;
}

export interface DashboardSettings {
    widgets: WidgetConfig[];
    viewMode: 'list' | 'byOwner';
}

const DEFAULT_SETTINGS: DashboardSettings = {
    widgets: [
        { id: 'projects', name: 'プロジェクト一覧', enabled: true, order: 0 },
        { id: 'tasks', name: 'タスク一覧', enabled: true, order: 1 },
        { id: 'tasksByOwner', name: '担当者別タスク', enabled: false, order: 2 },
    ],
    viewMode: 'list',
};

const STORAGE_KEY = 'dashboard-settings';

export function useDashboardSettings() {
    const [settings, setSettings] = useState<DashboardSettings>(DEFAULT_SETTINGS);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                // Merge with defaults to handle new widgets
                const mergedWidgets = DEFAULT_SETTINGS.widgets.map(defaultWidget => {
                    const storedWidget = parsed.widgets?.find((w: WidgetConfig) => w.id === defaultWidget.id);
                    return storedWidget || defaultWidget;
                });
                setSettings({
                    ...DEFAULT_SETTINGS,
                    ...parsed,
                    widgets: mergedWidgets,
                });
            } catch (e) {
                console.error('Failed to parse dashboard settings:', e);
            }
        }
        setIsLoaded(true);
    }, []);

    const updateSettings = (newSettings: Partial<DashboardSettings>) => {
        const updated = { ...settings, ...newSettings };
        setSettings(updated);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    };

    const toggleWidget = (widgetId: string) => {
        const updated = {
            ...settings,
            widgets: settings.widgets.map(w =>
                w.id === widgetId ? { ...w, enabled: !w.enabled } : w
            ),
        };
        setSettings(updated);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    };

    const setViewMode = (mode: 'list' | 'byOwner') => {
        updateSettings({ viewMode: mode });
    };

    const resetToDefaults = () => {
        setSettings(DEFAULT_SETTINGS);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_SETTINGS));
    };

    return {
        settings,
        isLoaded,
        updateSettings,
        toggleWidget,
        setViewMode,
        resetToDefaults,
    };
}

interface DashboardCustomizerProps {
    isOpen: boolean;
    onClose: () => void;
    settings: DashboardSettings;
    onToggleWidget: (widgetId: string) => void;
    onSetViewMode: (mode: 'list' | 'byOwner') => void;
    onReset: () => void;
}

export default function DashboardCustomizer({
    isOpen,
    onClose,
    settings,
    onToggleWidget,
    onSetViewMode,
    onReset,
}: DashboardCustomizerProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="bg-gray-900 border border-white/20 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white">ダッシュボード設定</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-6">
                    {/* View Mode */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-3">タスク表示モード</h3>
                        <div className="flex gap-2">
                            <button
                                onClick={() => onSetViewMode('list')}
                                className={`flex-1 px-4 py-3 rounded-lg border transition-colors ${
                                    settings.viewMode === 'list'
                                        ? 'bg-blue-600 border-blue-500 text-white'
                                        : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'
                                }`}
                            >
                                <div className="text-xl mb-1">📋</div>
                                <div className="text-sm font-medium">リスト表示</div>
                            </button>
                            <button
                                onClick={() => onSetViewMode('byOwner')}
                                className={`flex-1 px-4 py-3 rounded-lg border transition-colors ${
                                    settings.viewMode === 'byOwner'
                                        ? 'bg-blue-600 border-blue-500 text-white'
                                        : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'
                                }`}
                            >
                                <div className="text-xl mb-1">👥</div>
                                <div className="text-sm font-medium">担当者別</div>
                            </button>
                        </div>
                    </div>

                    {/* Widgets */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-3">ウィジェット表示</h3>
                        <div className="space-y-2">
                            {settings.widgets.map(widget => (
                                <div
                                    key={widget.id}
                                    className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                                >
                                    <span className="text-white">{widget.name}</span>
                                    <button
                                        onClick={() => onToggleWidget(widget.id)}
                                        className={`relative w-12 h-6 rounded-full transition-colors ${
                                            widget.enabled ? 'bg-blue-600' : 'bg-gray-600'
                                        }`}
                                    >
                                        <span
                                            className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                                                widget.enabled ? 'left-7' : 'left-1'
                                            }`}
                                        />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10 flex justify-between">
                    <button
                        onClick={onReset}
                        className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                    >
                        リセット
                    </button>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        完了
                    </button>
                </div>
            </div>
        </div>
    );
}

