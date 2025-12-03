'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getAuditLogs, getAuditStats, getAuditActions, AuditLog, AuditStats } from '../../lib/api';
import { toast } from '../../lib/toast';

const ACTION_COLORS: Record<string, string> = {
    LOGIN: 'bg-green-500/20 text-green-400',
    LOGOUT: 'bg-gray-500/20 text-gray-400',
    UPLOAD_MEETING: 'bg-blue-500/20 text-blue-400',
    VIEW_PROJECT: 'bg-cyan-500/20 text-cyan-400',
    VIEW_TASK: 'bg-cyan-500/20 text-cyan-400',
    VIEW_RISK: 'bg-orange-500/20 text-orange-400',
    EXPORT_DATA: 'bg-purple-500/20 text-purple-400',
    UPDATE_SETTINGS: 'bg-yellow-500/20 text-yellow-400',
    UPDATE_USER_ROLE: 'bg-red-500/20 text-red-400',
    DELETE_USER: 'bg-red-500/20 text-red-400',
    GENERATE_AGENDA: 'bg-indigo-500/20 text-indigo-400',
    VIEW_DIFF: 'bg-pink-500/20 text-pink-400',
};

export default function AuditPage() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [stats, setStats] = useState<AuditStats | null>(null);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [actionFilter, setActionFilter] = useState<string>('');
    const [availableActions, setAvailableActions] = useState<string[]>([]);
    const [actionDescriptions, setActionDescriptions] = useState<Record<string, string>>({});
    const [page, setPage] = useState(0);
    const [showStats, setShowStats] = useState(true);
    const limit = 20;

    useEffect(() => {
        loadActions();
        loadStats();
    }, []);

    useEffect(() => {
        loadLogs();
    }, [page, actionFilter]);

    async function loadActions() {
        try {
            const data = await getAuditActions();
            setAvailableActions(data.actions);
            setActionDescriptions(data.descriptions);
        } catch (error) {
            console.error('Failed to load actions:', error);
        }
    }

    async function loadStats() {
        try {
            const data = await getAuditStats(30);
            setStats(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async function loadLogs() {
        try {
            setLoading(true);
            const data = await getAuditLogs({
                limit,
                offset: page * limit,
                action: actionFilter || undefined,
            });
            setLogs(data.logs);
            setTotal(data.total);
        } catch (error) {
            console.error('Failed to load audit logs:', error);
            toast.error('Failed to load audit logs');
        } finally {
            setLoading(false);
        }
    }

    function formatDate(timestamp: string) {
        return new Date(timestamp).toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    }

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                    Audit Logs
                </h1>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => setShowStats(!showStats)}
                        className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                            showStats
                                ? 'bg-indigo-700 text-white'
                                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                        }`}
                    >
                        {showStats ? 'Hide Stats' : 'Show Stats'}
                    </button>
                    <Link
                        href="/admin"
                        className="px-4 py-2 rounded-lg bg-gray-600 hover:bg-gray-700 text-white font-semibold transition-colors"
                    >
                        Back to Admin
                    </Link>
                </div>
            </div>

            {showStats && stats && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="glass rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Activity Summary</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-400">Period</span>
                                <span className="text-white">{stats.period_days} days</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Total Actions</span>
                                <span className="text-white font-bold">{stats.total}</span>
                            </div>
                        </div>
                    </div>

                    <div className="glass rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Actions by Type</h3>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                            {Object.entries(stats.by_action).map(([action, count]) => (
                                <div key={action} className="flex justify-between items-center">
                                    <span className={`text-xs px-2 py-1 rounded ${ACTION_COLORS[action] || 'bg-gray-500/20 text-gray-400'}`}>
                                        {action}
                                    </span>
                                    <span className="text-white">{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="glass rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Top Users</h3>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                            {stats.by_user.map((user, index) => (
                                <div key={user.email} className="flex justify-between items-center">
                                    <span className="text-gray-300 truncate max-w-[150px]" title={user.email}>
                                        {index + 1}. {user.email}
                                    </span>
                                    <span className="text-white">{user.count}</span>
                                </div>
                            ))}
                            {stats.by_user.length === 0 && (
                                <p className="text-gray-500">No data</p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <div className="glass rounded-xl p-6">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold text-white">Log Entries</h3>
                    <div className="flex items-center space-x-4">
                        <select
                            value={actionFilter}
                            onChange={(e) => {
                                setActionFilter(e.target.value);
                                setPage(0);
                            }}
                            className="bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600"
                        >
                            <option value="">All Actions</option>
                            {availableActions.map((action) => (
                                <option key={action} value={action}>
                                    {action}
                                </option>
                            ))}
                        </select>
                        <span className="text-gray-400">
                            {total} total entries
                        </span>
                    </div>
                </div>

                {loading ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="text-gray-400 mt-2">Loading...</p>
                    </div>
                ) : logs.length === 0 ? (
                    <div className="text-center py-8">
                        <p className="text-gray-400">No audit logs found</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-gray-400 border-b border-gray-700">
                                    <th className="pb-3 px-2">Timestamp</th>
                                    <th className="pb-3 px-2">User</th>
                                    <th className="pb-3 px-2">Action</th>
                                    <th className="pb-3 px-2">Resource</th>
                                    <th className="pb-3 px-2">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.map((log) => (
                                    <tr key={log.log_id} className="border-b border-gray-700/50 hover:bg-white/5">
                                        <td className="py-3 px-2 text-gray-300 text-sm whitespace-nowrap">
                                            {formatDate(log.timestamp)}
                                        </td>
                                        <td className="py-3 px-2">
                                            <div className="text-white text-sm truncate max-w-[150px]" title={log.user_email}>
                                                {log.user_name || log.user_email || '-'}
                                            </div>
                                        </td>
                                        <td className="py-3 px-2">
                                            <span
                                                className={`text-xs px-2 py-1 rounded ${ACTION_COLORS[log.action] || 'bg-gray-500/20 text-gray-400'}`}
                                                title={actionDescriptions[log.action]}
                                            >
                                                {log.action}
                                            </span>
                                        </td>
                                        <td className="py-3 px-2 text-gray-300 text-sm">
                                            {log.resource_type && (
                                                <span className="text-gray-400">
                                                    {log.resource_type}
                                                    {log.resource_id && (
                                                        <span className="text-gray-500 ml-1 truncate max-w-[100px] inline-block" title={log.resource_id}>
                                                            ({log.resource_id.substring(0, 8)}...)
                                                        </span>
                                                    )}
                                                </span>
                                            )}
                                        </td>
                                        <td className="py-3 px-2 text-gray-400 text-sm truncate max-w-[200px]" title={log.details || ''}>
                                            {log.details || '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {totalPages > 1 && (
                    <div className="flex justify-center items-center space-x-4 mt-6">
                        <button
                            onClick={() => setPage(Math.max(0, page - 1))}
                            disabled={page === 0}
                            className="px-4 py-2 rounded-lg bg-gray-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
                        >
                            Previous
                        </button>
                        <span className="text-gray-400">
                            Page {page + 1} of {totalPages}
                        </span>
                        <button
                            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                            disabled={page >= totalPages - 1}
                            className="px-4 py-2 rounded-lg bg-gray-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
