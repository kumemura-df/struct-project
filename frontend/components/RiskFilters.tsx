'use client';

import { useState } from 'react';

interface RiskFiltersProps {
    projects: Array<{ project_id: string; project_name: string }>;
    onFilterChange: (filters: {
        project_id?: string;
        risk_level?: string;
        search?: string;
    }) => void;
}

export default function RiskFilters({ projects, onFilterChange }: RiskFiltersProps) {
    const [projectId, setProjectId] = useState<string>('');
    const [riskLevel, setRiskLevel] = useState<string>('');
    const [search, setSearch] = useState<string>('');

    const handleFilterChange = (newFilters: {
        project_id?: string;
        risk_level?: string;
        search?: string;
    }) => {
        const filters = {
            project_id: newFilters.project_id || projectId,
            risk_level: newFilters.risk_level || riskLevel,
            search: newFilters.search !== undefined ? newFilters.search : search,
        };

        // Remove empty values
        const cleanFilters: any = {};
        if (filters.project_id) cleanFilters.project_id = filters.project_id;
        if (filters.risk_level) cleanFilters.risk_level = filters.risk_level;
        if (filters.search) cleanFilters.search = filters.search;

        onFilterChange(cleanFilters);
    };

    const handleProjectChange = (value: string) => {
        setProjectId(value);
        handleFilterChange({ project_id: value });
    };

    const handleRiskLevelChange = (value: string) => {
        setRiskLevel(value);
        handleFilterChange({ risk_level: value });
    };

    const handleSearchChange = (value: string) => {
        setSearch(value);
        handleFilterChange({ search: value });
    };

    const handleClearFilters = () => {
        setProjectId('');
        setRiskLevel('');
        setSearch('');
        onFilterChange({});
    };

    return (
        <div className="glass p-6 rounded-xl space-y-4">
            <h3 className="text-lg font-semibold text-white mb-4">フィルタ</h3>

            {/* Search */}
            <div>
                <label className="block text-sm text-gray-300 mb-2">説明を検索</label>
                <input
                    type="text"
                    value={search}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    placeholder="リスクを検索..."
                    className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>

            {/* Project Filter */}
            <div>
                <label className="block text-sm text-gray-300 mb-2">プロジェクト</label>
                <select
                    value={projectId}
                    onChange={(e) => handleProjectChange(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">全プロジェクト</option>
                    {projects.map((project) => (
                        <option key={project.project_id} value={project.project_id} className="bg-gray-800">
                            {project.project_name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Risk Level Filter */}
            <div>
                <label className="block text-sm text-gray-300 mb-2">リスクレベル</label>
                <select
                    value={riskLevel}
                    onChange={(e) => handleRiskLevelChange(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">全レベル</option>
                    <option value="HIGH" className="bg-gray-800">高</option>
                    <option value="MEDIUM" className="bg-gray-800">中</option>
                    <option value="LOW" className="bg-gray-800">低</option>
                </select>
            </div>

            {/* Clear Filters Button */}
            {(projectId || riskLevel || search) && (
                <button
                    onClick={handleClearFilters}
                    className="w-full px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors"
                >
                    フィルタをクリア
                </button>
            )}
        </div>
    );
}
