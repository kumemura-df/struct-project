'use client';

import { useState, useEffect } from 'react';
import AuthGuard from '../../../components/AuthGuard';
import AppLayout from '../../../components/AppLayout';
import LoadingSpinner from '../../../components/LoadingSpinner';
import { toast } from '../../../lib/toast';

interface IntegrationStatus {
    available: boolean;
    configured: boolean;
}

interface IntegrationStatuses {
    google: {
        drive: IntegrationStatus;
        docs: IntegrationStatus;
        calendar: IntegrationStatus;
    };
    slack: IntegrationStatus & { webhook_configured?: boolean };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function IntegrationsPage() {
    const [statuses, setStatuses] = useState<IntegrationStatuses | null>(null);
    const [loading, setLoading] = useState(true);
    const [slackWebhookUrl, setSlackWebhookUrl] = useState('');
    const [testingSlack, setTestingSlack] = useState(false);
    const [sendingNotification, setSendingNotification] = useState<string | null>(null);

    useEffect(() => {
        loadStatuses();
    }, []);

    const loadStatuses = async () => {
        try {
            const res = await fetch(`${API_URL}/integrations/status`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error('Failed to load');
            const data = await res.json();
            setStatuses(data);
        } catch (error) {
            console.error('Failed to load integration statuses:', error);
            toast.error('連携ステータスの読み込みに失敗しました');
        } finally {
            setLoading(false);
        }
    };

    const testSlackConnection = async () => {
        if (!slackWebhookUrl.trim()) {
            toast.error('Webhook URLを入力してください');
            return;
        }

        setTestingSlack(true);
        try {
            const res = await fetch(`${API_URL}/integrations/slack/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ webhook_url: slackWebhookUrl })
            });
            
            const data = await res.json();
            if (res.ok) {
                toast.success('Slack接続テストに成功しました！');
            } else {
                toast.error(data.detail || 'テストに失敗しました');
            }
        } catch (error) {
            console.error('Slack test failed:', error);
            toast.error('Slack接続テストに失敗しました');
        } finally {
            setTestingSlack(false);
        }
    };

    const sendSlackNotification = async (type: string) => {
        setSendingNotification(type);
        try {
            const res = await fetch(`${API_URL}/integrations/slack/notify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    type,
                    webhook_url: slackWebhookUrl || undefined
                })
            });
            
            const data = await res.json();
            if (res.ok) {
                toast.success('通知を送信しました');
            } else {
                toast.error(data.detail || '送信に失敗しました');
            }
        } catch (error) {
            console.error('Notification failed:', error);
            toast.error('通知の送信に失敗しました');
        } finally {
            setSendingNotification(null);
        }
    };

    const StatusBadge = ({ status }: { status: IntegrationStatus }) => {
        if (!status.available) {
            return (
                <span className="px-2 py-1 text-xs rounded bg-gray-600 text-gray-300">
                    未インストール
                </span>
            );
        }
        if (status.configured) {
            return (
                <span className="px-2 py-1 text-xs rounded bg-green-600 text-white">
                    設定済み
                </span>
            );
        }
        return (
            <span className="px-2 py-1 text-xs rounded bg-yellow-600 text-white">
                未設定
            </span>
        );
    };

    return (
        <AuthGuard>
            <AppLayout>
                <div className="space-y-6">
                    {/* Header */}
                    <div>
                        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-teal-400">
                            外部連携設定
                        </h1>
                        <p className="text-gray-400 mt-1">
                            外部サービスとの連携を設定
                        </p>
                    </div>

                    {loading ? (
                        <div className="flex justify-center py-20">
                            <LoadingSpinner size="large" />
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Google Integration */}
                            <div className="glass p-6 rounded-xl">
                                <div className="flex items-center gap-3 mb-6">
                                    <span className="text-3xl">🔵</span>
                                    <div>
                                        <h2 className="text-xl font-semibold text-white">Google連携</h2>
                                        <p className="text-sm text-gray-400">
                                            Drive、Docs、Calendarからデータを取り込み
                                        </p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {/* Drive */}
                                    <div className="p-4 bg-white/5 rounded-lg">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-white">📁 Drive</span>
                                            {statuses && <StatusBadge status={statuses.google.drive} />}
                                        </div>
                                        <p className="text-xs text-gray-400 mb-3">
                                            議事録ファイルをインポート
                                        </p>
                                        <button
                                            className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
                                            disabled={!statuses?.google.drive.available}
                                        >
                                            接続する
                                        </button>
                                    </div>

                                    {/* Docs */}
                                    <div className="p-4 bg-white/5 rounded-lg">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-white">📄 Docs</span>
                                            {statuses && <StatusBadge status={statuses.google.docs} />}
                                        </div>
                                        <p className="text-xs text-gray-400 mb-3">
                                            ドキュメントから直接取得
                                        </p>
                                        <button
                                            className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
                                            disabled={!statuses?.google.docs.available}
                                        >
                                            接続する
                                        </button>
                                    </div>

                                    {/* Calendar */}
                                    <div className="p-4 bg-white/5 rounded-lg">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-white">📅 Calendar</span>
                                            {statuses && <StatusBadge status={statuses.google.calendar} />}
                                        </div>
                                        <p className="text-xs text-gray-400 mb-3">
                                            会議予定を自動取得
                                        </p>
                                        <button
                                            className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
                                            disabled={!statuses?.google.calendar.available}
                                        >
                                            接続する
                                        </button>
                                    </div>
                                </div>

                                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                                    <p className="text-sm text-yellow-300">
                                        ⚠️ Google連携には追加のOAuth認証設定が必要です。管理者にお問い合わせください。
                                    </p>
                                </div>
                            </div>

                            {/* Slack Integration */}
                            <div className="glass p-6 rounded-xl">
                                <div className="flex items-center gap-3 mb-6">
                                    <span className="text-3xl">💬</span>
                                    <div>
                                        <h2 className="text-xl font-semibold text-white">Slack連携</h2>
                                        <p className="text-sm text-gray-400">
                                            遅延タスク・高リスクの通知を送信
                                        </p>
                                    </div>
                                    {statuses && <StatusBadge status={statuses.slack} />}
                                </div>

                                <div className="space-y-4">
                                    {/* Webhook URL Input */}
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-2">
                                            Incoming Webhook URL
                                        </label>
                                        <div className="flex gap-2">
                                            <input
                                                type="url"
                                                value={slackWebhookUrl}
                                                onChange={(e) => setSlackWebhookUrl(e.target.value)}
                                                placeholder="https://hooks.slack.com/services/..."
                                                className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                                            />
                                            <button
                                                onClick={testSlackConnection}
                                                disabled={testingSlack || !slackWebhookUrl}
                                                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                                            >
                                                {testingSlack ? (
                                                    <>
                                                        <LoadingSpinner size="small" />
                                                        テスト中
                                                    </>
                                                ) : (
                                                    '接続テスト'
                                                )}
                                            </button>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Slackで Incoming Webhook アプリを設定し、URLを入力してください
                                        </p>
                                    </div>

                                    {/* Notification Buttons */}
                                    <div className="border-t border-white/10 pt-4 mt-4">
                                        <h3 className="text-sm font-medium text-gray-300 mb-3">
                                            通知を手動送信
                                        </h3>
                                        <div className="flex flex-wrap gap-2">
                                            <button
                                                onClick={() => sendSlackNotification('overdue_tasks')}
                                                disabled={sendingNotification !== null}
                                                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                                            >
                                                {sendingNotification === 'overdue_tasks' ? (
                                                    <LoadingSpinner size="small" />
                                                ) : (
                                                    '🚨'
                                                )}
                                                期限超過タスク
                                            </button>
                                            <button
                                                onClick={() => sendSlackNotification('high_risks')}
                                                disabled={sendingNotification !== null}
                                                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                                            >
                                                {sendingNotification === 'high_risks' ? (
                                                    <LoadingSpinner size="small" />
                                                ) : (
                                                    '⚠️'
                                                )}
                                                高リスク
                                            </button>
                                            <button
                                                onClick={() => sendSlackNotification('weekly_summary')}
                                                disabled={sendingNotification !== null}
                                                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                                            >
                                                {sendingNotification === 'weekly_summary' ? (
                                                    <LoadingSpinner size="small" />
                                                ) : (
                                                    '📊'
                                                )}
                                                週次サマリー
                                            </button>
                                        </div>
                                    </div>

                                    {/* Auto Notification Settings */}
                                    <div className="border-t border-white/10 pt-4 mt-4">
                                        <h3 className="text-sm font-medium text-gray-300 mb-3">
                                            自動通知設定
                                        </h3>
                                        <div className="space-y-3">
                                            <label className="flex items-center gap-3 cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    className="w-5 h-5 rounded border-white/20 bg-white/10 text-blue-500 focus:ring-blue-500"
                                                    disabled
                                                />
                                                <span className="text-gray-300">
                                                    毎週月曜日に週次サマリーを送信
                                                </span>
                                                <span className="text-xs text-gray-500">(Coming soon)</span>
                                            </label>
                                            <label className="flex items-center gap-3 cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    className="w-5 h-5 rounded border-white/20 bg-white/10 text-blue-500 focus:ring-blue-500"
                                                    disabled
                                                />
                                                <span className="text-gray-300">
                                                    高リスク発生時に即時通知
                                                </span>
                                                <span className="text-xs text-gray-500">(Coming soon)</span>
                                            </label>
                                            <label className="flex items-center gap-3 cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    className="w-5 h-5 rounded border-white/20 bg-white/10 text-blue-500 focus:ring-blue-500"
                                                    disabled
                                                />
                                                <span className="text-gray-300">
                                                    タスク期限超過時に通知
                                                </span>
                                                <span className="text-xs text-gray-500">(Coming soon)</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Help Section */}
                            <div className="glass p-6 rounded-xl">
                                <h2 className="text-lg font-semibold text-white mb-4">📚 連携ガイド</h2>
                                <div className="space-y-4 text-sm text-gray-300">
                                    <div>
                                        <h3 className="font-medium text-white mb-1">Slack Webhook の設定方法</h3>
                                        <ol className="list-decimal list-inside space-y-1 text-gray-400">
                                            <li>Slackの「Apps」から「Incoming Webhooks」を検索して追加</li>
                                            <li>通知を送信したいチャンネルを選択</li>
                                            <li>生成されたWebhook URLをコピー</li>
                                            <li>上記の入力欄に貼り付けて「接続テスト」をクリック</li>
                                        </ol>
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-white mb-1">Google連携の設定について</h3>
                                        <p className="text-gray-400">
                                            Google連携にはGCP Console でのOAuth同意画面とAPIキーの設定が必要です。
                                            詳細は管理者にお問い合わせください。
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </AppLayout>
        </AuthGuard>
    );
}
