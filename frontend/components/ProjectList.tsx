'use client';

import { useEffect, useState } from 'react';
import { getProjects, deleteProject, getProjectStats, Project, ProjectStats } from '../lib/api';
import { toast } from '../lib/toast';
import LoadingSpinner from './LoadingSpinner';

interface ProjectListProps {
    onSelectProject: (id: string | undefined) => void;
}

export default function ProjectList({ onSelectProject }: ProjectListProps) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectStats, setProjectStats] = useState<Record<string, ProjectStats>>({});
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
    const [search, setSearch] = useState('');

    useEffect(() => {
        loadProjects();
    }, [search]);

    async function loadProjects() {
        try {
            const data = await getProjects({ search: search || undefined });
            setProjects(data.items);
            
            // Load stats for each project
            const statsPromises = data.items.map(async (p: Project) => {
                try {
                    const stats = await getProjectStats(p.project_id);
                    return { id: p.project_id, stats };
                } catch {
                    return { id: p.project_id, stats: null };
                }
            });
            
            const statsResults = await Promise.all(statsPromises);
            const statsMap: Record<string, ProjectStats> = {};
            statsResults.forEach(({ id, stats }) => {
                if (stats) statsMap[id] = stats;
            });
            setProjectStats(statsMap);
        } catch (error) {
            console.error('Failed to load projects:', error);
            toast.error('プロジェクトの読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    }

    const handleSelect = (projectId: string) => {
        const newId = selectedId === projectId ? undefined : projectId;
        setSelectedId(newId);
        onSelectProject(newId);
    };

    const handleDelete = async (e: React.MouseEvent, projectId: string) => {
        e.stopPropagation();
        if (!confirm('このプロジェクトを削除してもよろしいですか？')) return;
        
        try {
            await deleteProject(projectId);
            toast.success('プロジェクトを削除しました');
            setProjects(prev => prev.filter(p => p.project_id !== projectId));
            if (selectedId === projectId) {
                setSelectedId(undefined);
                onSelectProject(undefined);
            }
        } catch (error) {
            console.error('Failed to delete project:', error);
            toast.error('プロジェクトの削除に失敗しました');
        }
    };

    if (loading) {
        return (
            <div className="glass p-6 rounded-xl flex justify-center">
                <LoadingSpinner size="medium" />
            </div>
        );
    }

    return (
        <div className="glass p-6 rounded-xl">
            <div className="mb-4">
                <input
                    type="text"
                    placeholder="プロジェクトを検索..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
            </div>
            <div className="space-y-3">
                {projects.map((p) => {
                    const stats = projectStats[p.project_id];
                    return (
                        <div
                            key={p.project_id}
                            onClick={() => handleSelect(p.project_id)}
                            className={`p-4 rounded-lg cursor-pointer transition-colors border group
                                ${selectedId === p.project_id 
                                    ? 'bg-blue-600/20 border-blue-500' 
                                    : 'bg-white/5 hover:bg-white/10 border-white/10'}`}
                        >
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <h3 className="font-semibold text-white">{p.project_name}</h3>
                                    <p className="text-sm text-gray-400">
                                        更新: {new Date(p.updated_at).toLocaleDateString('ja-JP')}
                                    </p>
                                    
                                    {/* Project Stats */}
                                    {stats && (
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">
                                                📋 タスク {stats.incomplete_tasks}
                                            </span>
                                            {stats.overdue_tasks > 0 && (
                                                <span className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-400">
                                                    🔴 遅延 {stats.overdue_tasks}
                                                </span>
                                            )}
                                            {stats.total_risks > 0 && (
                                                <span className="text-xs px-2 py-1 rounded bg-yellow-500/20 text-yellow-400">
                                                    ⚠️ リスク {stats.total_risks}
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={(e) => handleDelete(e, p.project_id)}
                                    className="text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
                                    title="プロジェクトを削除"
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>
                    );
                })}
                {projects.length === 0 && (
                    <div className="text-center py-8">
                        <div className="text-4xl mb-2">📁</div>
                        <p className="text-gray-400">プロジェクトがありません</p>
                    </div>
                )}
            </div>
        </div>
    );
}
