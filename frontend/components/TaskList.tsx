'use client';

import { useEffect, useState } from 'react';
import { getTasks } from '../lib/api';
import { toast } from '../lib/toast';
import LoadingSpinner from './LoadingSpinner';

export default function TaskList({ projectId }: { projectId?: string }) {
    const [tasks, setTasks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadTasks();
    }, [projectId]);

    async function loadTasks() {
        setLoading(true);
        try {
            const data = await getTasks(projectId);
            setTasks(data);
        } catch (error) {
            console.error('Failed to load tasks:', error);
            toast.error('Failed to load tasks');
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
            <div className="overflow-x-auto">
                {tasks.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="text-6xl mb-4">📋</div>
                        <p className="text-gray-400">No tasks found.</p>
                    </div>
                ) : (
                    <table className="min-w-full text-left text-sm whitespace-nowrap">
                        <thead className="uppercase tracking-wider border-b border-white/10 bg-white/5">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-gray-300">Title</th>
                                <th scope="col" className="px-6 py-3 text-gray-300">Owner</th>
                                <th scope="col" className="px-6 py-3 text-gray-300">Due Date</th>
                                <th scope="col" className="px-6 py-3 text-gray-300">Status</th>
                                <th scope="col" className="px-6 py-3 text-gray-300">Priority</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/10">
                            {tasks.map((task) => (
                                <tr key={task.task_id} className="hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4 font-medium text-white">{task.task_title}</td>
                                    <td className="px-6 py-4 text-gray-300">{task.owner || '-'}</td>
                                    <td className="px-6 py-4 text-gray-300">
                                        {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold
                    ${task.status === 'DONE' ? 'bg-green-500/20 text-green-400' :
                                                task.status === 'IN_PROGRESS' ? 'bg-blue-500/20 text-blue-400' :
                                                    'bg-gray-500/20 text-gray-400'}`}>
                                            {task.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold
                    ${task.priority === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                                                task.priority === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    'bg-green-500/20 text-green-400'}`}>
                                            {task.priority}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
