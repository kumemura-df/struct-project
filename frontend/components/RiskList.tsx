'use client';

import { useMemo } from 'react';
import { updateRisk, deleteRisk, RiskUpdate } from '../lib/api';
import { toast } from '../lib/toast';

interface Risk {
    risk_id: string;
    risk_description: string;
    risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
    project_id?: string;
    project_name?: string;
    owner?: string;
    source_sentence?: string;
    created_at: string;
}

interface RiskListProps {
    risks: Risk[];
    search?: string;
    onRiskDeleted?: (riskId: string) => void;
    onRiskUpdated?: (risk: Risk) => void;
}

export default function RiskList({ risks, search, onRiskDeleted, onRiskUpdated }: RiskListProps) {
    const filteredRisks = useMemo(() => {
        if (!search) return risks;

        const searchLower = search.toLowerCase();
        return risks.filter(risk =>
            risk.risk_description.toLowerCase().includes(searchLower) ||
            risk.owner?.toLowerCase().includes(searchLower) ||
            risk.project_name?.toLowerCase().includes(searchLower)
        );
    }, [risks, search]);

    const getRiskLevelColor = (level: string) => {
        switch (level) {
            case 'HIGH':
                return 'bg-red-500/20 border-red-500 text-red-400';
            case 'MEDIUM':
                return 'bg-yellow-500/20 border-yellow-500 text-yellow-400';
            case 'LOW':
                return 'bg-green-500/20 border-green-500 text-green-400';
            default:
                return 'bg-gray-500/20 border-gray-500 text-gray-400';
        }
    };

    const getRiskLevelIcon = (level: string) => {
        switch (level) {
            case 'HIGH':
                return '🔴';
            case 'MEDIUM':
                return '🟡';
            case 'LOW':
                return '🟢';
            default:
                return '⚪';
        }
    };

    const getRiskLevelLabel = (level: string) => {
        switch (level) {
            case 'HIGH':
                return '高';
            case 'MEDIUM':
                return '中';
            case 'LOW':
                return '低';
            default:
                return level;
        }
    };

    const handleRiskLevelChange = async (riskId: string, newLevel: string) => {
        try {
            const updated = await updateRisk(riskId, { risk_level: newLevel as RiskUpdate['risk_level'] });
            toast.success('リスクレベルを更新しました');
            onRiskUpdated?.(updated as Risk);
        } catch (error) {
            console.error('Failed to update risk:', error);
            toast.error('リスクレベルの更新に失敗しました');
        }
    };

    const handleDelete = async (riskId: string) => {
        if (!confirm('このリスクを削除してもよろしいですか？')) return;
        try {
            await deleteRisk(riskId);
            toast.success('リスクを削除しました');
            onRiskDeleted?.(riskId);
        } catch (error) {
            console.error('Failed to delete risk:', error);
            toast.error('リスクの削除に失敗しました');
        }
    };

    if (filteredRisks.length === 0) {
        return (
            <div className="glass p-12 rounded-xl text-center">
                <div className="text-6xl mb-4">📋</div>
                <p className="text-gray-400">リスクがありません</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {filteredRisks.map((risk) => (
                <div key={risk.risk_id} className="glass p-6 rounded-xl hover:bg-white/15 transition-colors group">
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                            <span className="text-2xl">{getRiskLevelIcon(risk.risk_level)}</span>
                            <select
                                value={risk.risk_level}
                                onChange={(e) => handleRiskLevelChange(risk.risk_id, e.target.value)}
                                className={`px-3 py-1 rounded-full text-xs font-semibold border bg-transparent cursor-pointer ${getRiskLevelColor(risk.risk_level)}`}
                            >
                                <option value="HIGH">高</option>
                                <option value="MEDIUM">中</option>
                                <option value="LOW">低</option>
                            </select>
                            {risk.project_name && (
                                <span className="px-3 py-1 rounded-full text-xs bg-blue-500/20 border border-blue-500 text-blue-400">
                                    {risk.project_name}
                                </span>
                            )}
                        </div>
                        <div className="flex items-center space-x-3">
                            {risk.owner && (
                                <span className="text-sm text-gray-400">👤 {risk.owner}</span>
                            )}
                            <button
                                onClick={() => handleDelete(risk.risk_id)}
                                className="text-red-400 hover:text-red-300 transition-colors opacity-0 group-hover:opacity-100"
                                title="リスクを削除"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>

                    <p className="text-white text-lg mb-3">{risk.risk_description}</p>

                    {risk.source_sentence && (
                        <div className="mt-4 pt-4 border-t border-white/10">
                            <p className="text-xs text-gray-400 mb-1">原文:</p>
                            <p className="text-sm text-gray-300 italic">「{risk.source_sentence}」</p>
                        </div>
                    )}

                    <div className="mt-3 text-xs text-gray-500">
                        {new Date(risk.created_at).toLocaleString('ja-JP')}
                    </div>
                </div>
            ))}
        </div>
    );
}
