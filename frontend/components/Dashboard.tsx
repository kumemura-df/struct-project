'use client';

import { useState, useEffect } from 'react';
import ProjectList from './ProjectList';
import TaskList from './TaskList';
import UserMenu from './UserMenu';
import ExportButton from './ExportButton';
import { HealthScoreSummary, HealthScoreList } from './HealthScore';
import Link from 'next/link';
import { exportProjects, exportTasks, getAllProjectHealthScores, ProjectHealthScore } from '../lib/api';

export default function Dashboard() {
    const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>(undefined);
    const [healthScores, setHealthScores] = useState<ProjectHealthScore[]>([]);
    const [showHealthScores, setShowHealthScores] = useState(false);

    useEffect(() => {
        loadHealthScores();
    }, []);

    const loadHealthScores = async () => {
        try {
            const scores = await getAllProjectHealthScores();
            setHealthScores(scores);
        } catch (error) {
            console.error('Failed to load health scores:', error);
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                    Project Progress DB
                </h1>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => setShowHealthScores(!showHealthScores)}
                        className={`px-4 py-2 rounded-lg font-semibold transition-colors shadow-lg ${
                            showHealthScores
                                ? 'bg-green-700 shadow-green-500/30'
                                : 'bg-green-600 hover:bg-green-700 shadow-green-500/30'
                        } text-white`}
                    >
                        Health
                    </button>
                    <Link
                        href="/difference"
                        className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-colors shadow-lg shadow-purple-500/30"
                    >
                        Diff
                    </Link>
                    <Link
                        href="/risks"
                        className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors shadow-lg shadow-red-500/30"
                    >
                        Risks
                    </Link>
                    <Link
                        href="/upload"
                        className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors shadow-lg shadow-blue-500/30"
                    >
                        Upload
                    </Link>
                    <UserMenu />
                </div>
            </div>

            {showHealthScores && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-1">
                        <HealthScoreSummary scores={healthScores} />
                    </div>
                    <div className="lg:col-span-2">
                        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
                            <h3 className="text-lg font-semibold text-white mb-4">Project Health Scores</h3>
                            <HealthScoreList
                                scores={healthScores}
                                onSelectProject={(id) => {
                                    setSelectedProjectId(id);
                                    setShowHealthScores(false);
                                }}
                            />
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-1">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold text-white">Projects</h2>
                        <ExportButton onExport={exportProjects} label="Export" size="small" />
                    </div>
                    <ProjectList onSelectProject={setSelectedProjectId} />
                </div>
                <div className="lg:col-span-2">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold text-white">
                            Tasks {selectedProjectId && '(filtered)'}
                        </h2>
                        <ExportButton
                            onExport={() => exportTasks(selectedProjectId)}
                            label="Export"
                            size="small"
                        />
                    </div>
                    <TaskList projectId={selectedProjectId} />
                </div>
            </div>
        </div>
    );
}
