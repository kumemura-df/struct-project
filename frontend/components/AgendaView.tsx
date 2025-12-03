'use client';

import { useState } from 'react';
import { GeneratedAgenda, AgendaItem } from '../lib/api';

interface AgendaViewProps {
  agenda: GeneratedAgenda;
  onRegenerate?: () => void;
  loading?: boolean;
}

export function AgendaView({ agenda, onRegenerate, loading }: AgendaViewProps) {
  const [expandedItem, setExpandedItem] = useState<number | null>(null);

  const priorityColors = {
    HIGH: 'bg-red-500/20 border-red-500 text-red-400',
    MEDIUM: 'bg-yellow-500/20 border-yellow-500 text-yellow-400',
    LOW: 'bg-green-500/20 border-green-500 text-green-400',
  };

  const priorityBadge = {
    HIGH: 'bg-red-500',
    MEDIUM: 'bg-yellow-500',
    LOW: 'bg-green-500',
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-white">
            Next Meeting Agenda
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            {agenda.project_name}
            {agenda.ai_generated !== false && (
              <span className="ml-2 text-purple-400">AI Generated</span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-2xl font-bold text-white">
              {agenda.suggested_duration_minutes} min
            </div>
            <div className="text-xs text-gray-400">Estimated Duration</div>
          </div>
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 text-white rounded-lg transition-colors"
            >
              {loading ? 'Generating...' : 'Regenerate'}
            </button>
          )}
        </div>
      </div>

      {/* Key Discussion Points */}
      {agenda.key_discussion_points.filter(Boolean).length > 0 && (
        <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <h3 className="text-sm font-medium text-blue-400 mb-2">Key Discussion Points</h3>
          <ul className="space-y-1">
            {agenda.key_discussion_points.filter(Boolean).map((point, i) => (
              <li key={i} className="text-sm text-gray-300 flex items-start">
                <span className="text-blue-400 mr-2">*</span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Agenda Items */}
      <div className="space-y-3">
        {agenda.agenda_items.map((item, index) => (
          <AgendaItemCard
            key={index}
            item={item}
            index={index}
            expanded={expandedItem === index}
            onToggle={() => setExpandedItem(expandedItem === index ? null : index)}
            priorityColors={priorityColors}
            priorityBadge={priorityBadge}
          />
        ))}
      </div>

      {/* Recommended Attendees */}
      {agenda.recommended_attendees && agenda.recommended_attendees.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Recommended Attendees</h3>
          <div className="flex flex-wrap gap-2">
            {agenda.recommended_attendees.map((attendee, i) => (
              <span
                key={i}
                className="px-3 py-1 bg-gray-700 rounded-full text-sm text-white"
              >
                {attendee}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700 flex justify-between items-center text-xs text-gray-500">
        <span>Generated: {new Date(agenda.generated_at).toLocaleString()}</span>
        {agenda.projects_count && (
          <span>{agenda.projects_count} projects included</span>
        )}
      </div>
    </div>
  );
}

interface AgendaItemCardProps {
  item: AgendaItem;
  index: number;
  expanded: boolean;
  onToggle: () => void;
  priorityColors: Record<string, string>;
  priorityBadge: Record<string, string>;
}

function AgendaItemCard({
  item,
  index,
  expanded,
  onToggle,
  priorityColors,
  priorityBadge,
}: AgendaItemCardProps) {
  return (
    <div
      className={`border rounded-lg overflow-hidden transition-all ${
        priorityColors[item.priority]
      }`}
    >
      <div
        className="p-4 cursor-pointer flex items-center justify-between"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-4">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 text-white font-bold">
            {index + 1}
          </div>
          <div>
            <h4 className="font-medium text-white">{item.title}</h4>
            <p className="text-sm text-gray-400">{item.estimated_minutes} min</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span
            className={`px-2 py-1 rounded text-xs font-medium text-white ${
              priorityBadge[item.priority]
            }`}
          >
            {item.priority}
          </span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${
              expanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-700/50">
          <p className="text-sm text-gray-300 mb-3">{item.description}</p>

          {item.related_tasks && item.related_tasks.length > 0 && (
            <div className="mb-2">
              <span className="text-xs font-medium text-gray-500">Related Tasks:</span>
              <ul className="mt-1 space-y-1">
                {item.related_tasks.map((task, i) => (
                  <li key={i} className="text-xs text-gray-400 pl-3">
                    - {task}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {item.related_risks && item.related_risks.length > 0 && (
            <div>
              <span className="text-xs font-medium text-gray-500">Related Risks:</span>
              <ul className="mt-1 space-y-1">
                {item.related_risks.map((risk, i) => (
                  <li key={i} className="text-xs text-red-400 pl-3">
                    - {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface AgendaExportProps {
  agenda: GeneratedAgenda;
}

export function AgendaExport({ agenda }: AgendaExportProps) {
  const handleCopyMarkdown = () => {
    const markdown = generateMarkdown(agenda);
    navigator.clipboard.writeText(markdown);
  };

  const handleDownload = () => {
    const markdown = generateMarkdown(agenda);
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agenda-${agenda.project_name.replace(/\s+/g, '-').toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex space-x-2">
      <button
        onClick={handleCopyMarkdown}
        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors"
      >
        Copy as Markdown
      </button>
      <button
        onClick={handleDownload}
        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors"
      >
        Download
      </button>
    </div>
  );
}

function generateMarkdown(agenda: GeneratedAgenda): string {
  let md = `# Meeting Agenda: ${agenda.project_name}\n\n`;
  md += `**Estimated Duration:** ${agenda.suggested_duration_minutes} minutes\n\n`;

  if (agenda.key_discussion_points.filter(Boolean).length > 0) {
    md += `## Key Discussion Points\n\n`;
    agenda.key_discussion_points.filter(Boolean).forEach((point) => {
      md += `- ${point}\n`;
    });
    md += '\n';
  }

  md += `## Agenda Items\n\n`;
  agenda.agenda_items.forEach((item, i) => {
    md += `### ${i + 1}. ${item.title} (${item.estimated_minutes} min) [${item.priority}]\n\n`;
    md += `${item.description}\n\n`;

    if (item.related_tasks && item.related_tasks.length > 0) {
      md += `**Related Tasks:**\n`;
      item.related_tasks.forEach((task) => {
        md += `- ${task}\n`;
      });
      md += '\n';
    }

    if (item.related_risks && item.related_risks.length > 0) {
      md += `**Related Risks:**\n`;
      item.related_risks.forEach((risk) => {
        md += `- ${risk}\n`;
      });
      md += '\n';
    }
  });

  if (agenda.recommended_attendees && agenda.recommended_attendees.length > 0) {
    md += `## Recommended Attendees\n\n`;
    agenda.recommended_attendees.forEach((attendee) => {
      md += `- ${attendee}\n`;
    });
  }

  md += `\n---\n*Generated: ${new Date(agenda.generated_at).toLocaleString()}*\n`;

  return md;
}
