'use client';

import { useState } from 'react';
import ProjectList from './ProjectList';
import TaskList from './TaskList';
import UserMenu from './UserMenu';
import ExportButton from './ExportButton';
import Link from 'next/link';
import { exportProjects, exportTasks } from '../lib/api';

export default function Dashboard() {
    const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>(undefined);

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                    Project Progress DB
                </h1>
                <div className="flex items-center space-x-3">
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
                    <UserMenu />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-1">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold text-white">プロジェクト一覧</h2>
                        <ExportButton onExport={exportProjects} label="エクスポート" size="small" />
                    </div>
                    <ProjectList onSelectProject={setSelectedProjectId} />
                </div>
                <div className="lg:col-span-2">
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
            </div>
        </div>
    );
}
