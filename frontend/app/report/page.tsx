'use client';

import { useState } from 'react';
import Link from 'next/link';
import { generateWeeklyReportText, generateWeeklyReportHtml, WeeklyReportText, WeeklyReportHtml } from '../../lib/api';
import { toast } from '../../lib/toast';

type ReportFormat = 'text' | 'html';

export default function ReportPage() {
    const [loading, setLoading] = useState(false);
    const [format, setFormat] = useState<ReportFormat>('html');
    const [includeHealth, setIncludeHealth] = useState(true);
    const [textReport, setTextReport] = useState<WeeklyReportText | null>(null);
    const [htmlReport, setHtmlReport] = useState<WeeklyReportHtml | null>(null);

    async function generateReport() {
        try {
            setLoading(true);
            if (format === 'text') {
                const report = await generateWeeklyReportText(includeHealth);
                setTextReport(report);
                setHtmlReport(null);
            } else {
                const report = await generateWeeklyReportHtml(includeHealth);
                setHtmlReport(report);
                setTextReport(null);
            }
            toast.success('Report generated successfully');
        } catch (error) {
            console.error('Failed to generate report:', error);
            toast.error('Failed to generate report');
        } finally {
            setLoading(false);
        }
    }

    function copyToClipboard(text: string) {
        navigator.clipboard.writeText(text);
        toast.success('Copied to clipboard');
    }

    function copySubject() {
        const subject = textReport?.subject || htmlReport?.subject || '';
        copyToClipboard(subject);
    }

    function copyBody() {
        if (textReport) {
            copyToClipboard(textReport.body);
        } else if (htmlReport) {
            copyToClipboard(htmlReport.body_html);
        }
    }

    const currentReport = textReport || htmlReport;

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                        Weekly Report Generator
                    </h1>
                    <p className="text-gray-400 mt-1">
                        Generate email draft with overdue tasks and high risks
                    </p>
                </div>
                <Link
                    href="/"
                    className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                >
                    Back
                </Link>
            </div>

            {/* Options */}
            <div className="glass rounded-xl p-6 mb-6">
                <h3 className="text-lg font-semibold text-white mb-4">Report Options</h3>
                <div className="flex flex-wrap gap-6">
                    <div>
                        <label className="block text-sm text-gray-400 mb-2">Format</label>
                        <div className="flex space-x-4">
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="format"
                                    value="html"
                                    checked={format === 'html'}
                                    onChange={() => setFormat('html')}
                                    className="text-blue-500"
                                />
                                <span className="text-white">HTML (Rich)</span>
                            </label>
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="format"
                                    value="text"
                                    checked={format === 'text'}
                                    onChange={() => setFormat('text')}
                                    className="text-blue-500"
                                />
                                <span className="text-white">Plain Text</span>
                            </label>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-2">Content</label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={includeHealth}
                                onChange={(e) => setIncludeHealth(e.target.checked)}
                                className="text-blue-500 rounded"
                            />
                            <span className="text-white">Include Project Health Summary</span>
                        </label>
                    </div>
                    <div className="flex-grow flex justify-end items-end">
                        <button
                            onClick={generateReport}
                            disabled={loading}
                            className="px-6 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-semibold disabled:opacity-50 transition-all"
                        >
                            {loading ? 'Generating...' : 'Generate Report'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Summary */}
            {currentReport && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="glass rounded-xl p-4 text-center">
                        <div className="text-3xl font-bold text-red-400">
                            {currentReport.summary.overdue_tasks_count}
                        </div>
                        <div className="text-gray-400">Overdue Tasks</div>
                    </div>
                    <div className="glass rounded-xl p-4 text-center">
                        <div className="text-3xl font-bold text-orange-400">
                            {currentReport.summary.high_risks_count}
                        </div>
                        <div className="text-gray-400">High Risks</div>
                    </div>
                    <div className="glass rounded-xl p-4 text-center">
                        <div className="text-3xl font-bold text-blue-400">
                            {currentReport.summary.projects_analyzed}
                        </div>
                        <div className="text-gray-400">Projects Analyzed</div>
                    </div>
                </div>
            )}

            {/* Report Output */}
            {currentReport && (
                <div className="glass rounded-xl p-6">
                    {/* Subject */}
                    <div className="mb-6">
                        <div className="flex justify-between items-center mb-2">
                            <label className="text-sm font-medium text-gray-400">Subject</label>
                            <button
                                onClick={copySubject}
                                className="text-sm text-blue-400 hover:text-blue-300"
                            >
                                Copy
                            </button>
                        </div>
                        <div className="bg-gray-800 rounded-lg p-3 text-white font-medium">
                            {currentReport.subject}
                        </div>
                    </div>

                    {/* Body */}
                    <div>
                        <div className="flex justify-between items-center mb-2">
                            <label className="text-sm font-medium text-gray-400">Body</label>
                            <button
                                onClick={copyBody}
                                className="text-sm text-blue-400 hover:text-blue-300"
                            >
                                Copy
                            </button>
                        </div>

                        {textReport ? (
                            <pre className="bg-gray-800 rounded-lg p-4 text-white text-sm overflow-x-auto whitespace-pre-wrap max-h-[600px] overflow-y-auto">
                                {textReport.body}
                            </pre>
                        ) : htmlReport ? (
                            <div className="bg-white rounded-lg p-4 max-h-[600px] overflow-y-auto">
                                <div dangerouslySetInnerHTML={{ __html: htmlReport.body_html }} />
                            </div>
                        ) : null}
                    </div>

                    {/* Generated timestamp */}
                    <div className="mt-4 text-sm text-gray-500 text-right">
                        Generated at: {new Date(currentReport.generated_at).toLocaleString('ja-JP')}
                    </div>
                </div>
            )}

            {/* Empty state */}
            {!currentReport && !loading && (
                <div className="glass rounded-xl p-12 text-center">
                    <div className="text-6xl mb-4">📧</div>
                    <h3 className="text-xl font-semibold text-white mb-2">Generate Your Weekly Report</h3>
                    <p className="text-gray-400 mb-6">
                        Create an email draft summarizing overdue tasks, high risks, and project health.
                    </p>
                    <button
                        onClick={generateReport}
                        disabled={loading}
                        className="px-6 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-semibold disabled:opacity-50 transition-all"
                    >
                        Generate Report
                    </button>
                </div>
            )}
        </div>
    );
}
