'use client';

import { TaskDiffResult, RiskDiffResult } from '@/lib/api';

interface DiffSummaryProps {
  taskDiff?: TaskDiffResult;
  riskDiff?: RiskDiffResult;
}

export function DiffSummary({ taskDiff, riskDiff }: DiffSummaryProps) {
  const taskSummary = taskDiff?.summary;
  const riskSummary = riskDiff?.summary;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {/* Task Summary */}
      {taskSummary && (
        <>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">{taskSummary.added_count}</div>
            <div className="text-sm text-green-700">New Tasks</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-600">{taskSummary.removed_count}</div>
            <div className="text-sm text-red-700">Removed Tasks</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-600">{taskSummary.status_changed_count}</div>
            <div className="text-sm text-yellow-700">Status Changed</div>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-600">{taskSummary.unchanged_count}</div>
            <div className="text-sm text-gray-700">Unchanged</div>
          </div>
        </>
      )}

      {/* Risk Summary */}
      {riskSummary && (
        <>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">{riskSummary.added_count}</div>
            <div className="text-sm text-green-700">New Risks</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-600">{riskSummary.removed_count}</div>
            <div className="text-sm text-red-700">Resolved Risks</div>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-orange-600">
              {riskDiff?.escalated?.length || 0}
            </div>
            <div className="text-sm text-orange-700">Escalated</div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">
              {riskDiff?.de_escalated?.length || 0}
            </div>
            <div className="text-sm text-blue-700">De-escalated</div>
          </div>
        </>
      )}
    </div>
  );
}

interface TaskDiffListProps {
  diff: TaskDiffResult;
}

export function TaskDiffList({ diff }: TaskDiffListProps) {
  const getTaskTitle = (task: Record<string, unknown>) => task.task_title as string || 'Untitled';
  const getTaskOwner = (task: Record<string, unknown>) => task.owner as string || '-';
  const getTaskStatus = (task: Record<string, unknown>) => task.status as string || '-';
  const getTaskPriority = (task: Record<string, unknown>) => task.priority as string || '-';

  const statusColors: Record<string, string> = {
    'NOT_STARTED': 'bg-gray-100 text-gray-800',
    'IN_PROGRESS': 'bg-blue-100 text-blue-800',
    'DONE': 'bg-green-100 text-green-800',
    'BLOCKED': 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-6">
      {/* Added Tasks */}
      {diff.added.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
            New Tasks ({diff.added.length})
          </h3>
          <div className="bg-green-50 border border-green-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-green-100">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Task</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Owner</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Status</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Priority</th>
                </tr>
              </thead>
              <tbody>
                {diff.added.map((task, idx) => (
                  <tr key={idx} className="border-t border-green-200">
                    <td className="px-4 py-2 text-sm">{getTaskTitle(task)}</td>
                    <td className="px-4 py-2 text-sm">{getTaskOwner(task)}</td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${statusColors[getTaskStatus(task)] || ''}`}>
                        {getTaskStatus(task)}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm">{getTaskPriority(task)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Status Changed Tasks */}
      {diff.status_changed.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-yellow-700 mb-3 flex items-center">
            <span className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></span>
            Status Changed ({diff.status_changed.length})
          </h3>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-yellow-100">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-yellow-800">Task</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-yellow-800">Owner</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-yellow-800">Change</th>
                </tr>
              </thead>
              <tbody>
                {diff.status_changed.map((item, idx) => (
                  <tr key={idx} className="border-t border-yellow-200">
                    <td className="px-4 py-2 text-sm">{getTaskTitle(item.task)}</td>
                    <td className="px-4 py-2 text-sm">{getTaskOwner(item.task)}</td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${statusColors[item.prev_status] || ''}`}>
                        {item.prev_status}
                      </span>
                      <span className="mx-2">→</span>
                      <span className={`px-2 py-1 rounded text-xs ${statusColors[item.curr_status] || ''}`}>
                        {item.curr_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Removed Tasks */}
      {diff.removed.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-red-700 mb-3 flex items-center">
            <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
            Removed Tasks ({diff.removed.length})
          </h3>
          <div className="bg-red-50 border border-red-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-red-100">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-red-800">Task</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-red-800">Owner</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-red-800">Last Status</th>
                </tr>
              </thead>
              <tbody>
                {diff.removed.map((task, idx) => (
                  <tr key={idx} className="border-t border-red-200">
                    <td className="px-4 py-2 text-sm line-through text-red-600">{getTaskTitle(task)}</td>
                    <td className="px-4 py-2 text-sm text-red-600">{getTaskOwner(task)}</td>
                    <td className="px-4 py-2 text-sm text-red-600">{getTaskStatus(task)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No Changes */}
      {diff.summary.total_changes === 0 && (
        <div className="text-center py-8 text-gray-500">
          No changes detected between the selected meetings.
        </div>
      )}
    </div>
  );
}

interface RiskDiffListProps {
  diff: RiskDiffResult;
}

export function RiskDiffList({ diff }: RiskDiffListProps) {
  const getRiskDesc = (risk: Record<string, unknown>) => risk.risk_description as string || 'No description';
  const getRiskOwner = (risk: Record<string, unknown>) => risk.owner as string || '-';
  const getRiskLevel = (risk: Record<string, unknown>) => risk.risk_level as string || '-';

  const levelColors: Record<string, string> = {
    'LOW': 'bg-green-100 text-green-800',
    'MEDIUM': 'bg-yellow-100 text-yellow-800',
    'HIGH': 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-6">
      {/* Escalated Risks */}
      {diff.escalated && diff.escalated.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-orange-700 mb-3 flex items-center">
            <span className="w-3 h-3 bg-orange-500 rounded-full mr-2"></span>
            Escalated Risks ({diff.escalated.length})
          </h3>
          <div className="bg-orange-50 border border-orange-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-orange-100">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-orange-800">Risk</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-orange-800">Owner</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-orange-800">Level Change</th>
                </tr>
              </thead>
              <tbody>
                {diff.escalated.map((item, idx) => (
                  <tr key={idx} className="border-t border-orange-200">
                    <td className="px-4 py-2 text-sm">{getRiskDesc(item.risk)}</td>
                    <td className="px-4 py-2 text-sm">{getRiskOwner(item.risk)}</td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${levelColors[item.prev_level] || ''}`}>
                        {item.prev_level}
                      </span>
                      <span className="mx-2">→</span>
                      <span className={`px-2 py-1 rounded text-xs ${levelColors[item.curr_level] || ''}`}>
                        {item.curr_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Added Risks */}
      {diff.added.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
            New Risks ({diff.added.length})
          </h3>
          <div className="bg-green-50 border border-green-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-green-100">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Risk</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Owner</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-green-800">Level</th>
                </tr>
              </thead>
              <tbody>
                {diff.added.map((risk, idx) => (
                  <tr key={idx} className="border-t border-green-200">
                    <td className="px-4 py-2 text-sm">{getRiskDesc(risk)}</td>
                    <td className="px-4 py-2 text-sm">{getRiskOwner(risk)}</td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${levelColors[getRiskLevel(risk)] || ''}`}>
                        {getRiskLevel(risk)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Resolved Risks */}
      {diff.removed.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-blue-700 mb-3 flex items-center">
            <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
            Resolved Risks ({diff.removed.length})
          </h3>
          <div className="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-blue-100">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-blue-800">Risk</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-blue-800">Owner</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-blue-800">Level</th>
                </tr>
              </thead>
              <tbody>
                {diff.removed.map((risk, idx) => (
                  <tr key={idx} className="border-t border-blue-200">
                    <td className="px-4 py-2 text-sm line-through text-blue-600">{getRiskDesc(risk)}</td>
                    <td className="px-4 py-2 text-sm text-blue-600">{getRiskOwner(risk)}</td>
                    <td className="px-4 py-2 text-sm text-blue-600">{getRiskLevel(risk)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No Changes */}
      {diff.summary.total_changes === 0 && (
        <div className="text-center py-8 text-gray-500">
          No changes detected between the selected meetings.
        </div>
      )}
    </div>
  );
}

interface MeetingSelectorProps {
  meetings: Array<{
    meeting_id: string;
    meeting_date: string;
    title?: string;
  }>;
  prevMeetingId: string;
  currMeetingId: string;
  onPrevChange: (id: string) => void;
  onCurrChange: (id: string) => void;
}

export function MeetingSelector({
  meetings,
  prevMeetingId,
  currMeetingId,
  onPrevChange,
  onCurrChange,
}: MeetingSelectorProps) {
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('ja-JP');
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Previous Meeting (Before)
        </label>
        <select
          value={prevMeetingId}
          onChange={(e) => onPrevChange(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select a meeting...</option>
          {meetings.map((m) => (
            <option key={m.meeting_id} value={m.meeting_id}>
              {formatDate(m.meeting_date)} - {m.title || 'Untitled'}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center justify-center text-gray-400">
        <svg className="w-6 h-6 transform md:rotate-0 rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      </div>

      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Current Meeting (After)
        </label>
        <select
          value={currMeetingId}
          onChange={(e) => onCurrChange(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select a meeting...</option>
          {meetings.map((m) => (
            <option key={m.meeting_id} value={m.meeting_id}>
              {formatDate(m.meeting_date)} - {m.title || 'Untitled'}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
