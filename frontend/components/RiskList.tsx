'use client';

import { useMemo } from 'react';

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
}

export default function RiskList({ risks, search }: RiskListProps) {
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

    if (filteredRisks.length === 0) {
        return (
            <div className="glass p-12 rounded-xl text-center">
                <div className="text-6xl mb-4">📋</div>
                <p className="text-gray-400">No risks found</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {filteredRisks.map((risk) => (
                <div key={risk.risk_id} className="glass p-6 rounded-xl hover:bg-white/15 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                            <span className="text-2xl">{getRiskLevelIcon(risk.risk_level)}</span>
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getRiskLevelColor(risk.risk_level)}`}>
                                {risk.risk_level}
                            </span>
                            {risk.project_name && (
                                <span className="px-3 py-1 rounded-full text-xs bg-blue-500/20 border border-blue-500 text-blue-400">
                                    {risk.project_name}
                                </span>
                            )}
                        </div>
                        {risk.owner && (
                            <span className="text-sm text-gray-400">👤 {risk.owner}</span>
                        )}
                    </div>

                    <p className="text-white text-lg mb-3">{risk.risk_description}</p>

                    {risk.source_sentence && (
                        <div className="mt-4 pt-4 border-t border-white/10">
                            <p className="text-xs text-gray-400 mb-1">Source:</p>
                            <p className="text-sm text-gray-300 italic">"{risk.source_sentence}"</p>
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
