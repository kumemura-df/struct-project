'use client';

import { useEffect, useState } from 'react';
import { getProjects } from '../lib/api';
import { toast } from '../lib/toast';
import LoadingSpinner from './LoadingSpinner';

export default function ProjectList({ onSelectProject }: { onSelectProject: (id: string) => void }) {
    const [projects, setProjects] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadProjects();
    }, []);

    async function loadProjects() {
        try {
            const data = await getProjects();
            setProjects(data);
        } catch (error) {
            console.error('Failed to load projects:', error);
            toast.error('Failed to load projects');
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="glass p-6 rounded-xl flex justify-center">
                <LoadingSpinner size="medium" />
            </div>
        );
    }

    return (
        <div className="glass p-6 rounded-xl">
            <div className="space-y-3">
                {projects.map((p) => (
                    <div
                        key={p.project_id}
                        onClick={() => onSelectProject(p.project_id)}
                        className="p-4 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors border border-white/10"
                    >
                        <h3 className="font-semibold text-white">{p.project_name}</h3>
                        <p className="text-sm text-gray-400">Last updated: {new Date(p.updated_at).toLocaleDateString()}</p>
                    </div>
                ))}
                {projects.length === 0 && (
                    <div className="text-center py-8">
                        <div className="text-4xl mb-2">📁</div>
                        <p className="text-gray-400">No projects found.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
