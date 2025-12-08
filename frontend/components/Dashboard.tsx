'use client';

import { useState } from 'react';
import ProjectList from './ProjectList';
import TaskList from './TaskList';
import TasksByOwnerView from './TasksByOwnerView';
import ExportButton from './ExportButton';
import DashboardCustomizer, { useDashboardSettings } from './DashboardCustomizer';
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
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                        ダッシュボード
                    </h1>
                    <p className="text-gray-400 mt-1">プロジェクトの進捗とタスクを管理</p>
                </div>
                <button
                    onClick={() => setShowCustomizer(true)}
                    className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors flex items-center gap-2"
                    title="ダッシュボード設定"
                >
                    <span>⚙️</span>
                    <span className="text-sm">カスタマイズ</span>
                </button>
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
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Projects Column */}
                    {isWidgetEnabled('projects') && (
                        <div className="lg:col-span-1" data-tour="projects">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold text-white">プロジェクト一覧</h2>
                                <ExportButton onExport={exportProjects} label="エクスポート" size="small" />
                            </div>
                            <ProjectList onSelectProject={setSelectedProjectId} />
                        </div>
                    )}
                    
                    {/* Tasks Column */}
                    {isWidgetEnabled('tasks') && (
                        <div className={isWidgetEnabled('projects') ? 'lg:col-span-2' : 'lg:col-span-3'} data-tour="tasks">
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
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
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
        </div>
    );
}
