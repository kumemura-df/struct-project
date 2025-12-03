'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  getSlackSettings,
  updateSlackSettings,
  deleteSlackSettings,
  testSlackNotification,
  sendImmediateNotifications,
  SlackSettings,
} from '../../lib/api';
import { toast } from '../../lib/toast';

export default function SettingsPage() {
  const [settings, setSettings] = useState<SlackSettings | null>(null);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [notifyHighRisk, setNotifyHighRisk] = useState(true);
  const [notifyOverdue, setNotifyOverdue] = useState(true);
  const [notifyMeeting, setNotifyMeeting] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await getSlackSettings();
      setSettings(data);
      setWebhookUrl(data.webhook_url || '');
      setNotifyHighRisk(data.notify_on_high_risk);
      setNotifyOverdue(data.notify_on_overdue);
      setNotifyMeeting(data.notify_on_meeting_processed);
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await updateSlackSettings({
        webhook_url: webhookUrl,
        notify_on_high_risk: notifyHighRisk,
        notify_on_overdue: notifyOverdue,
        notify_on_meeting_processed: notifyMeeting,
      });
      toast.success('Settings saved successfully');
      await loadSettings();
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete Slack integration?')) {
      return;
    }
    try {
      await deleteSlackSettings();
      toast.success('Slack integration removed');
      setWebhookUrl('');
      await loadSettings();
    } catch (error) {
      console.error('Failed to delete settings:', error);
      toast.error('Failed to delete settings');
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      await testSlackNotification(webhookUrl || undefined);
      toast.success('Test notification sent!');
    } catch (error) {
      console.error('Failed to send test:', error);
      toast.error('Failed to send test notification');
    } finally {
      setTesting(false);
    }
  };

  const handleNotifyNow = async () => {
    try {
      const result = await sendImmediateNotifications();
      const messages = [];
      if (result.high_risks_count > 0) {
        messages.push(`${result.high_risks_count} high risks`);
      }
      if (result.overdue_tasks_count > 0) {
        messages.push(`${result.overdue_tasks_count} overdue tasks`);
      }
      if (messages.length > 0) {
        toast.success(`Notifications sent: ${messages.join(', ')}`);
      } else {
        toast.info('No items to notify about');
      }
    } catch (error) {
      console.error('Failed to send notifications:', error);
      toast.error('Failed to send notifications');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="animate-pulse text-gray-400">Loading settings...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            Settings
          </h1>
          <Link
            href="/"
            className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
          >
            Back
          </Link>
        </div>

        {/* Slack Integration Section */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <span className="mr-2">Slack Integration</span>
          </h2>

          <div className="space-y-4">
            {/* Webhook URL */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Webhook URL
              </label>
              <input
                type="url"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {settings?.webhook_url_masked && (
                <p className="mt-1 text-sm text-gray-400">
                  Current: {settings.webhook_url_masked}
                </p>
              )}
            </div>

            {/* Notification Options */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-300">
                Notification Settings
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={notifyHighRisk}
                  onChange={(e) => setNotifyHighRisk(e.target.checked)}
                  className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500"
                />
                <span className="text-gray-300">Notify on HIGH level risks</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={notifyOverdue}
                  onChange={(e) => setNotifyOverdue(e.target.checked)}
                  className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500"
                />
                <span className="text-gray-300">Notify on overdue tasks</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={notifyMeeting}
                  onChange={(e) => setNotifyMeeting(e.target.checked)}
                  className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500"
                />
                <span className="text-gray-300">Notify when meeting is processed</span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3 pt-4">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg transition-colors"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>

              <button
                onClick={handleTest}
                disabled={testing || !webhookUrl}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 text-white rounded-lg transition-colors"
              >
                {testing ? 'Sending...' : 'Send Test'}
              </button>

              <button
                onClick={handleNotifyNow}
                disabled={!settings?.webhook_url}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 text-white rounded-lg transition-colors"
              >
                Notify Now
              </button>

              {settings?.webhook_url && (
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  Remove
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Help Section */}
        <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700/30">
          <h3 className="text-lg font-medium text-gray-300 mb-3">
            How to set up Slack notifications
          </h3>
          <ol className="list-decimal list-inside space-y-2 text-gray-400 text-sm">
            <li>Go to your Slack workspace settings</li>
            <li>Navigate to &quot;Apps&quot; &rarr; &quot;Manage&quot; &rarr; &quot;Custom Integrations&quot;</li>
            <li>Create an &quot;Incoming Webhook&quot;</li>
            <li>Select the channel for notifications</li>
            <li>Copy the Webhook URL and paste it above</li>
            <li>Click &quot;Send Test&quot; to verify the integration</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
