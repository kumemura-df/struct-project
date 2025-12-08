'use client';

import { useState } from 'react';
import { useProjects, useDeleteProject } from '../lib/hooks';
import { ProjectWithStats } from '../lib/api';
import LoadingSpinner from './LoadingSpinner';

interface ProjectListProps {
    onSelectProject: (id: string | undefined) => void;
}

// Individual project card - stats now come from API response
function ProjectCard({ 
    project, 
    isSelected, 
    onSelect, 
    onDelete 
}: { 
    project: ProjectWithStats;
    isSelected: boolean;
    onSelect: () => void;
    onDelete: (e: React.MouseEvent) => void;
}) {
    return (
        <div
            onClick={onSelect}
            className={`p-4 rounded-lg cursor-pointer transition-colors border group
                ${isSelected 
                    ? 'bg-blue-600/20 border-blue-500' 
                    : 'bg-white/5 hover:bg-white/10 border-white/10'}`}
        >
            <div className="flex justify-between items-start">
                <div className="flex-1">
                    <h3 className="font-semibold text-white">{project.project_name}</h3>
                    <p className="text-sm text-gray-400">
                        更新: {new Date(project.updated_at).toLocaleDateString('ja-JP')}
                    </p>
                    
                    {/* Project Stats - now included in API response */}
                    <div className="flex flex-wrap gap-2 mt-2">
                        <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">
                            📋 タスク {project.incomplete_tasks ?? 0}
                        </span>
                        {(project.overdue_tasks ?? 0) > 0 && (
                            <span className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-400">
                                🔴 遅延 {project.overdue_tasks}
                            </span>
                        )}
                        {(project.total_risks ?? 0) > 0 && (
                            <span className="text-xs px-2 py-1 rounded bg-yellow-500/20 text-yellow-400">
                                ⚠️ リスク {project.total_risks}
                            </span>
                        )}
                    </div>
                </div>
                <button
                    onClick={onDelete}
                    className="text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="プロジェクトを削除"
                >
                    🗑️
                </button>
            </div>
        </div>
    );
}

export default function ProjectList({ onSelectProject }: ProjectListProps) {
    const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
    const [search, setSearch] = useState('');

    // Use include_stats=true to get stats with projects in a single query (N+1 fix)
    const { data, isLoading, error } = useProjects({ 
        search: search || undefined,
        include_stats: true
    });
    const deleteProjectMutation = useDeleteProject();

    const projects = data?.items || [];

    const handleSelect = (projectId: string) => {
        const newId = selectedId === projectId ? undefined : projectId;
        setSelectedId(newId);
        onSelectProject(newId);
    };

    const handleDelete = async (e: React.MouseEvent, projectId: string) => {
        e.stopPropagation();
        if (!confirm('このプロジェクトを削除してもよろしいですか？')) return;
        
        deleteProjectMutation.mutate(projectId, {
            onSuccess: () => {
                if (selectedId === projectId) {
                    setSelectedId(undefined);
                    onSelectProject(undefined);
                }
            }
        });
    };

    if (isLoading) {
        return (
            <div className="glass p-6 rounded-xl flex justify-center">
                <LoadingSpinner size="medium" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass p-6 rounded-xl">
                <div className="text-center py-8">
                    <div className="text-4xl mb-2">❌</div>
                    <p className="text-red-400">プロジェクトの読み込みに失敗しました</p>
                </div>
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
                {projects.map((p) => (
                    <ProjectCard
                        key={p.project_id}
                        project={p}
                        isSelected={selectedId === p.project_id}
                        onSelect={() => handleSelect(p.project_id)}
                        onDelete={(e) => handleDelete(e, p.project_id)}
                    />
                ))}
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
