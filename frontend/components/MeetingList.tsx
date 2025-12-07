'use client';

import { useMemo } from 'react';
import { Meeting } from '../lib/api';

interface MeetingListProps {
    meetings: Meeting[];
    search?: string;
}

export default function MeetingList({ meetings, search }: MeetingListProps) {
    const filteredMeetings = useMemo(() => {
        if (!search) return meetings;

        const searchLower = search.toLowerCase();
        return meetings.filter(meeting =>
            meeting.title?.toLowerCase().includes(searchLower) ||
            meeting.meeting_id.toLowerCase().includes(searchLower)
        );
    }, [meetings, search]);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'DONE':
                return (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500">
                        ✅ 完了
                    </span>
                );
            case 'PENDING':
                return (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-400 border border-yellow-500 animate-pulse">
                        ⏳ 処理中
                    </span>
                );
            case 'ERROR':
                return (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500">
                        ❌ エラー
                    </span>
                );
            default:
                return (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-400 border border-gray-500">
                        {status}
                    </span>
                );
        }
    };

    if (filteredMeetings.length === 0) {
        return (
            <div className="glass p-12 rounded-xl text-center">
                <div className="text-6xl mb-4">📅</div>
                <p className="text-gray-400">会議がありません</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {filteredMeetings.map((meeting) => (
                <div key={meeting.meeting_id} className="glass p-6 rounded-xl hover:bg-white/15 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                            <span className="text-2xl">📝</span>
                            <div>
                                <h3 className="text-lg font-semibold text-white">
                                    {meeting.title || '無題の会議'}
                                </h3>
                                <p className="text-sm text-gray-400">
                                    {meeting.meeting_date ? new Date(meeting.meeting_date).toLocaleDateString('ja-JP', {
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric',
                                        weekday: 'short'
                                    }) : '日付なし'}
                                </p>
                            </div>
                        </div>
                        {getStatusBadge(meeting.status)}
                    </div>

                    {/* Extraction Stats */}
                    <div className="flex flex-wrap gap-4 mt-4">
                        <div className="flex items-center space-x-2">
                            <span className="text-blue-400">📋</span>
                            <span className="text-sm text-gray-300">
                                タスク: <span className="font-semibold text-white">{meeting.task_count || 0}</span>
                            </span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <span className="text-red-400">⚠️</span>
                            <span className="text-sm text-gray-300">
                                リスク: <span className="font-semibold text-white">{meeting.risk_count || 0}</span>
                            </span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <span className="text-green-400">✓</span>
                            <span className="text-sm text-gray-300">
                                決定事項: <span className="font-semibold text-white">{meeting.decision_count || 0}</span>
                            </span>
                        </div>
                    </div>

                    {/* Error Message */}
                    {meeting.status === 'ERROR' && meeting.error_message && (
                        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                            <p className="text-sm text-red-400">
                                <span className="font-semibold">エラー:</span> {meeting.error_message}
                            </p>
                        </div>
                    )}

                    {/* Metadata */}
                    <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                        <span className="text-xs text-gray-500">
                            ID: {meeting.meeting_id.slice(0, 8)}...
                        </span>
                        <span className="text-xs text-gray-500">
                            作成: {new Date(meeting.created_at).toLocaleString('ja-JP')}
                        </span>
                    </div>
                </div>
            ))}
        </div>
    );
}

