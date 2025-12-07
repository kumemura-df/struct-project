'use client';

import { useMemo } from 'react';
import { deleteDecision, Decision } from '../lib/api';
import { toast } from '../lib/toast';

interface DecisionListProps {
    decisions: Decision[];
    search?: string;
    onDecisionDeleted?: (decisionId: string) => void;
}

export default function DecisionList({ decisions, search, onDecisionDeleted }: DecisionListProps) {
    const filteredDecisions = useMemo(() => {
        if (!search) return decisions;

        const searchLower = search.toLowerCase();
        return decisions.filter(decision =>
            decision.decision_description?.toLowerCase().includes(searchLower) ||
            decision.decided_by?.toLowerCase().includes(searchLower)
        );
    }, [decisions, search]);

    const handleDelete = async (decisionId: string) => {
        if (!confirm('この決定事項を削除してもよろしいですか？')) return;
        try {
            await deleteDecision(decisionId);
            toast.success('決定事項を削除しました');
            onDecisionDeleted?.(decisionId);
        } catch (error) {
            console.error('Failed to delete decision:', error);
            toast.error('決定事項の削除に失敗しました');
        }
    };

    if (filteredDecisions.length === 0) {
        return (
            <div className="glass p-12 rounded-xl text-center">
                <div className="text-6xl mb-4">✓</div>
                <p className="text-gray-400">決定事項がありません</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {filteredDecisions.map((decision) => (
                <div key={decision.decision_id} className="glass p-6 rounded-xl hover:bg-white/15 transition-colors group">
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                            <span className="text-2xl text-green-400">✓</span>
                            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 border border-green-500 text-green-400">
                                決定
                            </span>
                        </div>
                        <div className="flex items-center space-x-3">
                            {decision.decided_by && (
                                <span className="text-sm text-gray-400">👤 {decision.decided_by}</span>
                            )}
                            <button
                                onClick={() => handleDelete(decision.decision_id)}
                                className="text-red-400 hover:text-red-300 transition-colors opacity-0 group-hover:opacity-100"
                                title="削除"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>

                    <p className="text-white text-lg mb-3">{decision.decision_description}</p>

                    <div className="mt-3 text-xs text-gray-500">
                        {new Date(decision.created_at).toLocaleString('ja-JP')}
                    </div>
                </div>
            ))}
        </div>
    );
}

