'use client';

import { useState, useEffect } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { UserMenu } from '@/components/UserMenu';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { DiffSummary, TaskDiffList, RiskDiffList, MeetingSelector } from '@/components/DiffView';
import {
  getProjects,
  getMeetings,
  getTasksDifference,
  getRisksDifference,
  TaskDiffResult,
  RiskDiffResult,
} from '@/lib/api';
import { toast } from '@/lib/toast';
import Link from 'next/link';

interface Project {
  project_id: string;
  project_name: string;
}

interface Meeting {
  meeting_id: string;
  meeting_date: string;
  title?: string;
}

export default function DifferencePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [prevMeetingId, setPrevMeetingId] = useState<string>('');
  const [currMeetingId, setCurrMeetingId] = useState<string>('');
  const [taskDiff, setTaskDiff] = useState<TaskDiffResult | null>(null);
  const [riskDiff, setRiskDiff] = useState<RiskDiffResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'tasks' | 'risks'>('tasks');

  // Load projects
  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await getProjects();
        setProjects(data);
      } catch (error) {
        console.error('Failed to load projects:', error);
      }
    }
    loadProjects();
  }, []);

  // Load meetings when project changes
  useEffect(() => {
    async function loadMeetings() {
      try {
        const data = await getMeetings(selectedProjectId || undefined);
        setMeetings(data);
        // Reset meeting selections
        setPrevMeetingId('');
        setCurrMeetingId('');
        setTaskDiff(null);
        setRiskDiff(null);
      } catch (error) {
        console.error('Failed to load meetings:', error);
      }
    }
    loadMeetings();
  }, [selectedProjectId]);

  // Auto-select latest two meetings
  useEffect(() => {
    if (meetings.length >= 2 && !prevMeetingId && !currMeetingId) {
      setCurrMeetingId(meetings[0].meeting_id);
      setPrevMeetingId(meetings[1].meeting_id);
    }
  }, [meetings, prevMeetingId, currMeetingId]);

  // Load diff when meetings are selected
  const handleCompare = async () => {
    if (!prevMeetingId || !currMeetingId) {
      toast.error('Please select both meetings to compare');
      return;
    }

    if (prevMeetingId === currMeetingId) {
      toast.error('Please select different meetings');
      return;
    }

    setLoading(true);
    try {
      const [tasks, risks] = await Promise.all([
        getTasksDifference(prevMeetingId, currMeetingId, selectedProjectId || undefined),
        getRisksDifference(prevMeetingId, currMeetingId, selectedProjectId || undefined),
      ]);

      setTaskDiff(tasks);
      setRiskDiff(risks);

      const totalChanges = tasks.summary.total_changes + risks.summary.total_changes;
      if (totalChanges > 0) {
        toast.success(`Found ${totalChanges} changes`);
      } else {
        toast.info('No changes detected');
      }
    } catch (error) {
      console.error('Failed to load diff:', error);
      toast.error('Failed to compare meetings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-500 hover:text-gray-700">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </Link>
              <h1 className="text-xl font-bold text-gray-900">Meeting Difference</h1>
            </div>
            <UserMenu />
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project (Optional)
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full md:w-64 border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Projects</option>
                {projects.map((p) => (
                  <option key={p.project_id} value={p.project_id}>
                    {p.project_name}
                  </option>
                ))}
              </select>
            </div>

            <MeetingSelector
              meetings={meetings}
              prevMeetingId={prevMeetingId}
              currMeetingId={currMeetingId}
              onPrevChange={setPrevMeetingId}
              onCurrChange={setCurrMeetingId}
            />

            <div className="flex justify-center">
              <button
                onClick={handleCompare}
                disabled={loading || !prevMeetingId || !currMeetingId}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {loading ? (
                  <>
                    <LoadingSpinner />
                    <span className="ml-2">Comparing...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    Compare Meetings
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results */}
          {(taskDiff || riskDiff) && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              {/* Summary */}
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary</h2>
              <div className="mb-6">
                <DiffSummary taskDiff={taskDiff || undefined} riskDiff={riskDiff || undefined} />
              </div>

              {/* Tabs */}
              <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('tasks')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'tasks'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Tasks
                    {taskDiff && (
                      <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                        {taskDiff.summary.total_changes}
                      </span>
                    )}
                  </button>
                  <button
                    onClick={() => setActiveTab('risks')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'risks'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Risks
                    {riskDiff && (
                      <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                        {riskDiff.summary.total_changes}
                      </span>
                    )}
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              {activeTab === 'tasks' && taskDiff && <TaskDiffList diff={taskDiff} />}
              {activeTab === 'risks' && riskDiff && <RiskDiffList diff={riskDiff} />}
            </div>
          )}

          {/* Empty State */}
          {!taskDiff && !riskDiff && !loading && (
            <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No comparison yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Select two meetings and click &quot;Compare Meetings&quot; to see the differences.
              </p>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
