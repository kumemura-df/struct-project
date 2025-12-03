'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AgendaView, AgendaExport } from '../../components/AgendaView';
import {
  getProjects,
  generateProjectAgenda,
  generatePortfolioAgenda,
  GeneratedAgenda,
} from '../../lib/api';
import { toast } from '../../lib/toast';

interface Project {
  project_id: string;
  project_name: string;
}

export default function AgendaPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [agenda, setAgenda] = useState<GeneratedAgenda | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const data = await getProjects();
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoadingProjects(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setLoading(true);
      let result: GeneratedAgenda;

      if (selectedProjectId) {
        result = await generateProjectAgenda(selectedProjectId);
      } else {
        result = await generatePortfolioAgenda();
      }

      setAgenda(result);
      toast.success('Agenda generated successfully');
    } catch (error) {
      console.error('Failed to generate agenda:', error);
      toast.error('Failed to generate agenda');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Meeting Agenda Generator
            </h1>
            <p className="text-gray-400 mt-1">
              AI-powered agenda suggestions based on project status
            </p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
          >
            Back
          </Link>
        </div>

        {/* Project Selection */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 mb-6">
          <h2 className="text-lg font-semibold text-white mb-4">Select Scope</h2>

          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                disabled={loadingProjects}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">All Projects (Portfolio View)</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.project_name}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading || loadingProjects}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 text-white font-semibold rounded-lg transition-colors shadow-lg shadow-purple-500/30"
            >
              {loading ? 'Generating...' : 'Generate Agenda'}
            </button>
          </div>

          <p className="text-sm text-gray-500 mt-3">
            The agenda will include overdue tasks, high risks, in-progress work, and recent decisions.
          </p>
        </div>

        {/* Agenda Display */}
        {agenda ? (
          <div className="space-y-4">
            <div className="flex justify-end">
              <AgendaExport agenda={agenda} />
            </div>
            <AgendaView
              agenda={agenda}
              onRegenerate={handleGenerate}
              loading={loading}
            />
          </div>
        ) : (
          <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-12 border border-gray-700/30 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-medium text-gray-300 mb-2">
              No Agenda Generated Yet
            </h3>
            <p className="text-gray-500">
              Select a project and click &quot;Generate Agenda&quot; to create a meeting agenda suggestion.
            </p>
          </div>
        )}

        {/* Help Section */}
        <div className="mt-8 bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700/30">
          <h3 className="text-lg font-medium text-gray-300 mb-3">
            How it works
          </h3>
          <ul className="space-y-2 text-gray-400 text-sm">
            <li className="flex items-start">
              <span className="text-purple-400 mr-2">1.</span>
              The system analyzes your project&apos;s tasks, risks, and recent meetings
            </li>
            <li className="flex items-start">
              <span className="text-purple-400 mr-2">2.</span>
              AI prioritizes items that need discussion (overdue tasks, high risks)
            </li>
            <li className="flex items-start">
              <span className="text-purple-400 mr-2">3.</span>
              A suggested agenda is generated with time estimates for each item
            </li>
            <li className="flex items-start">
              <span className="text-purple-400 mr-2">4.</span>
              Export the agenda as Markdown for your meeting notes
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
