'use client';

import { ProjectHealthScore } from '../lib/api';

interface HealthScoreBadgeProps {
  score: number;
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export function HealthScoreBadge({ score, status, size = 'md' }: HealthScoreBadgeProps) {
  const statusColors = {
    HEALTHY: 'bg-green-500',
    AT_RISK: 'bg-yellow-500',
    WARNING: 'bg-orange-500',
    CRITICAL: 'bg-red-500',
  };

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-12 h-12 text-sm',
    lg: 'w-16 h-16 text-lg',
  };

  const bgColor = statusColors[status as keyof typeof statusColors] || 'bg-gray-500';

  return (
    <div
      className={`${sizeClasses[size]} ${bgColor} rounded-full flex items-center justify-center text-white font-bold`}
      title={`Health: ${status} (${score}/100)`}
    >
      {score}
    </div>
  );
}

interface HealthScoreCardProps {
  healthScore: ProjectHealthScore;
  showDetails?: boolean;
}

export function HealthScoreCard({ healthScore, showDetails = false }: HealthScoreCardProps) {
  const statusColors = {
    HEALTHY: 'border-green-500 bg-green-500/10',
    AT_RISK: 'border-yellow-500 bg-yellow-500/10',
    WARNING: 'border-orange-500 bg-orange-500/10',
    CRITICAL: 'border-red-500 bg-red-500/10',
  };

  const statusLabels = {
    HEALTHY: 'Healthy',
    AT_RISK: 'At Risk',
    WARNING: 'Warning',
    CRITICAL: 'Critical',
  };

  const borderColor = statusColors[healthScore.status] || 'border-gray-500';

  return (
    <div className={`rounded-xl p-4 border-2 ${borderColor}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          {healthScore.project_name && (
            <h3 className="text-lg font-semibold text-white">{healthScore.project_name}</h3>
          )}
          <span className="text-sm text-gray-400">
            {statusLabels[healthScore.status]}
          </span>
        </div>
        <HealthScoreBadge score={healthScore.score} status={healthScore.status} size="lg" />
      </div>

      {/* Score breakdown bars */}
      <div className="space-y-2">
        <ScoreBar label="Task Completion" value={healthScore.breakdown.task_completion} max={30} />
        <ScoreBar label="On Schedule" value={healthScore.breakdown.overdue} max={25} />
        <ScoreBar label="Risk Level" value={healthScore.breakdown.risk_level} max={25} />
        <ScoreBar label="Activity" value={healthScore.breakdown.activity} max={20} />
      </div>

      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-gray-400">Tasks</div>
            <div className="text-white text-right">
              {healthScore.details.done_tasks}/{healthScore.details.total_tasks} done
            </div>
            <div className="text-gray-400">Overdue</div>
            <div className="text-white text-right">
              {healthScore.details.overdue_tasks} tasks
            </div>
            <div className="text-gray-400">Risks</div>
            <div className="text-white text-right">
              {healthScore.details.high_risks} HIGH / {healthScore.details.total_risks} total
            </div>
            <div className="text-gray-400">Recent Meetings</div>
            <div className="text-white text-right">
              {healthScore.details.recent_meetings} (30 days)
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface ScoreBarProps {
  label: string;
  value: number;
  max: number;
}

function ScoreBar({ label, value, max }: ScoreBarProps) {
  const percentage = (value / max) * 100;

  let barColor = 'bg-green-500';
  if (percentage < 50) barColor = 'bg-red-500';
  else if (percentage < 75) barColor = 'bg-yellow-500';

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300">{value.toFixed(1)}/{max}</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface HealthScoreListProps {
  scores: ProjectHealthScore[];
  onSelectProject?: (projectId: string) => void;
}

export function HealthScoreList({ scores, onSelectProject }: HealthScoreListProps) {
  // Sort by score (lowest first for attention)
  const sortedScores = [...scores].sort((a, b) => a.score - b.score);

  return (
    <div className="space-y-3">
      {sortedScores.map((score) => (
        <div
          key={score.project_id}
          className={`flex items-center justify-between p-3 rounded-lg bg-gray-800/50 border border-gray-700/50 ${
            onSelectProject ? 'cursor-pointer hover:bg-gray-700/50' : ''
          }`}
          onClick={() => onSelectProject?.(score.project_id)}
        >
          <div className="flex items-center space-x-3">
            <HealthScoreBadge score={score.score} status={score.status} size="sm" />
            <div>
              <div className="text-white font-medium">{score.project_name}</div>
              <div className="text-xs text-gray-400">
                {score.details.overdue_tasks > 0 && (
                  <span className="text-orange-400 mr-2">
                    {score.details.overdue_tasks} overdue
                  </span>
                )}
                {score.details.high_risks > 0 && (
                  <span className="text-red-400">
                    {score.details.high_risks} high risk
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="text-sm text-gray-400">
            {score.details.done_tasks}/{score.details.total_tasks} tasks
          </div>
        </div>
      ))}
    </div>
  );
}

interface HealthScoreSummaryProps {
  scores: ProjectHealthScore[];
}

export function HealthScoreSummary({ scores }: HealthScoreSummaryProps) {
  if (scores.length === 0) return null;

  const avgScore = Math.round(scores.reduce((acc, s) => acc + s.score, 0) / scores.length);
  const criticalCount = scores.filter((s) => s.status === 'CRITICAL').length;
  const warningCount = scores.filter((s) => s.status === 'WARNING').length;
  const atRiskCount = scores.filter((s) => s.status === 'AT_RISK').length;
  const healthyCount = scores.filter((s) => s.status === 'HEALTHY').length;

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
      <h3 className="text-lg font-semibold text-white mb-4">Portfolio Health</h3>

      <div className="flex items-center justify-center mb-6">
        <div className="text-center">
          <div className="text-5xl font-bold text-white">{avgScore}</div>
          <div className="text-sm text-gray-400 mt-1">Average Score</div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 text-center">
        <div className="p-2 rounded-lg bg-red-500/20">
          <div className="text-2xl font-bold text-red-400">{criticalCount}</div>
          <div className="text-xs text-gray-400">Critical</div>
        </div>
        <div className="p-2 rounded-lg bg-orange-500/20">
          <div className="text-2xl font-bold text-orange-400">{warningCount}</div>
          <div className="text-xs text-gray-400">Warning</div>
        </div>
        <div className="p-2 rounded-lg bg-yellow-500/20">
          <div className="text-2xl font-bold text-yellow-400">{atRiskCount}</div>
          <div className="text-xs text-gray-400">At Risk</div>
        </div>
        <div className="p-2 rounded-lg bg-green-500/20">
          <div className="text-2xl font-bold text-green-400">{healthyCount}</div>
          <div className="text-xs text-gray-400">Healthy</div>
        </div>
      </div>
    </div>
  );
}
