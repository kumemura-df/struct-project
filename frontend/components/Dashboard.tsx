'use client';

import { useState } from 'react';
import ProjectList from './ProjectList';
import TaskList from './TaskList';
import TasksByOwnerView from './TasksByOwnerView';
import UserMenu from './UserMenu';
import ExportButton from './ExportButton';
import GlobalSearch from './GlobalSearch';
import DashboardCustomizer, { useDashboardSettings } from './DashboardCustomizer';
import AIChatWidget from './AIChatWidget';
import Link from 'next/link';
import { exportProjects, exportTasks } from '../lib/api';

export default function Dashboard() {
    const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>(undefined);
    const [showCustomizer, setShowCustomizer] = useState(false);
    const { settings, isLoaded, toggleWidget, setViewMode, resetToDefaults } = useDashboardSettings();

    const isWidgetEnabled = (widgetId: string) => {
        return settings.widgets.find(w => w.id === widgetId)?.enabled ?? true;
    };

    if (!isLoaded) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                    Project Progress DB
                </h1>
                <div className="flex flex-wrap items-center gap-3">
                    {/* Global Search */}
                    <GlobalSearch />
                    
                    {/* Navigation Links */}
                    <Link
                        href="/reports"
                        className="px-3 py-2 rounded-lg bg-orange-600 hover:bg-orange-700 text-white font-semibold transition-colors shadow-lg shadow-orange-500/30 text-sm"
                    >
                        📊 レポート
                    </Link>
                    <Link
                        href="/meetings"
                        className="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white font-semibold transition-colors shadow-lg shadow-cyan-500/30 text-sm"
                    >
                        📅 会議
                    </Link>
                    <Link
                        href="/decisions"
                        className="px-3 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white font-semibold transition-colors shadow-lg shadow-green-500/30 text-sm"
                    >
                        ✓ 決定事項
                    </Link>
                    <Link
                        href="/risks"
                        className="px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors shadow-lg shadow-red-500/30 text-sm"
                    >
                        ⚠️ リスク
                    </Link>
                    <Link
                        href="/upload"
                        className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors shadow-lg shadow-blue-500/30 text-sm"
                    >
                        📤 アップロード
                    </Link>
                    
                    {/* Settings Button */}
                    <button
                        onClick={() => setShowCustomizer(true)}
                        className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors text-sm"
                        title="ダッシュボード設定"
                    >
                        ⚙️
                    </button>
                    
                    <UserMenu />
                </div>
            </div>

            {/* View Mode Tabs */}
            <div className="flex gap-2 border-b border-white/10 pb-2">
                <button
                    onClick={() => setViewMode('list')}
                    className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                        settings.viewMode === 'list'
                            ? 'bg-white/10 text-white border-b-2 border-blue-500'
                            : 'text-gray-400 hover:text-white'
                    }`}
                >
                    📋 リスト表示
                </button>
                <button
                    onClick={() => setViewMode('byOwner')}
                    className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                        settings.viewMode === 'byOwner'
                            ? 'bg-white/10 text-white border-b-2 border-blue-500'
                            : 'text-gray-400 hover:text-white'
                    }`}
                >
                    👥 担当者別
                </button>
            </div>

            {/* Dashboard Content */}
            {settings.viewMode === 'list' ? (
                // List View
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Projects Column */}
                    {isWidgetEnabled('projects') && (
                        <div className="lg:col-span-1">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold text-white">プロジェクト一覧</h2>
                                <ExportButton onExport={exportProjects} label="エクスポート" size="small" />
                            </div>
                            <ProjectList onSelectProject={setSelectedProjectId} />
                        </div>
                    )}
                    
                    {/* Tasks Column */}
                    {isWidgetEnabled('tasks') && (
                        <div className={isWidgetEnabled('projects') ? 'lg:col-span-2' : 'lg:col-span-3'}>
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold text-white">
                                    タスク {selectedProjectId && '(フィルタ中)'}
                                </h2>
                                <ExportButton
                                    onExport={() => exportTasks(selectedProjectId)}
                                    label="エクスポート"
                                    size="small"
                                />
                            </div>
                            <TaskList projectId={selectedProjectId} />
                        </div>
                    )}
                </div>
            ) : (
                // By Owner View
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Projects Column */}
                    {isWidgetEnabled('projects') && (
                        <div className="lg:col-span-1">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold text-white">プロジェクト</h2>
                                <ExportButton onExport={exportProjects} label="エクスポート" size="small" />
                            </div>
                            <ProjectList onSelectProject={setSelectedProjectId} />
                        </div>
                    )}
                    
                    {/* Tasks by Owner */}
                    <div className={isWidgetEnabled('projects') ? 'lg:col-span-3' : 'lg:col-span-4'}>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold text-white">
                                担当者別タスク {selectedProjectId && '(フィルタ中)'}
                            </h2>
                            <ExportButton
                                onExport={() => exportTasks(selectedProjectId)}
                                label="エクスポート"
                                size="small"
                            />
                        </div>
                        <TasksByOwnerView projectId={selectedProjectId} />
                    </div>
                </div>
            )}

            {/* Dashboard Customizer Modal */}
            <DashboardCustomizer
                isOpen={showCustomizer}
                onClose={() => setShowCustomizer(false)}
                settings={settings}
                onToggleWidget={toggleWidget}
                onSetViewMode={setViewMode}
                onReset={resetToDefaults}
            />

            {/* AI Chat Widget */}
            <AIChatWidget />
        </div>
    );
}
