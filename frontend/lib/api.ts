import { toast } from './toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch wrapper that includes credentials and handles auth errors.
 */
async function authenticatedFetch(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Always include cookies
      headers: {
        ...options.headers,
      },
    });

    // Handle authentication errors
    if (response.status === 401) {
      toast.error('Please log in to continue');
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      throw new Error('Unauthorized');
    }

    // Handle server errors with structured error response
    if (!response.ok) {
      let errorMessage = 'An error occurred';
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.error || errorMessage;
      } catch {
        // If JSON parsing fails, use status text
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    return response;
  } catch (error) {
    // Network errors
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      toast.error('Network error. Please check your connection.');
    }
    throw error;
  }
}

export async function uploadFile(file: File, date: string, title?: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('meeting_date', date);
  if (title) formData.append('title', title);

  const res = await authenticatedFetch(`${API_URL}/upload/`, {
    method: 'POST',
    body: formData,
  });

  return res.json();
}

export async function getProjects() {
  const res = await authenticatedFetch(`${API_URL}/projects/`);
  return res.json();
}

export async function getTasks(projectId?: string) {
  const url = projectId ? `${API_URL}/tasks/?project_id=${projectId}` : `${API_URL}/tasks/`;
  const res = await authenticatedFetch(url);
  return res.json();
}

// Risk endpoints
export async function getRisks(filters?: {
  project_id?: string;
  risk_level?: string;
  meeting_id?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.risk_level) params.append('risk_level', filters.risk_level);
  if (filters?.meeting_id) params.append('meeting_id', filters.meeting_id);

  const url = `${API_URL}/risks/?${params.toString()}`;
  const res = await authenticatedFetch(url);
  return res.json();
}

export async function getRiskStats() {
  const res = await authenticatedFetch(`${API_URL}/risks/stats`);
  return res.json();
}

export async function getDecisions(filters?: {
  project_id?: string;
  meeting_id?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.meeting_id) params.append('meeting_id', filters.meeting_id);

  const url = `${API_URL}/risks/decisions?${params.toString()}`;
  const res = await authenticatedFetch(url);
  return res.json();
}

// Export functions
async function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export async function exportProjects() {
  const res = await authenticatedFetch(`${API_URL}/export/projects`);
  const blob = await res.blob();
  const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || 'projects.csv';
  await downloadBlob(blob, filename);
  toast.success('Projects exported successfully');
}

export async function exportTasks(projectId?: string) {
  const url = projectId
    ? `${API_URL}/export/tasks?project_id=${projectId}`
    : `${API_URL}/export/tasks`;
  const res = await authenticatedFetch(url);
  const blob = await res.blob();
  const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || 'tasks.csv';
  await downloadBlob(blob, filename);
  toast.success('Tasks exported successfully');
}

export async function exportRisks(filters?: {
  project_id?: string;
  risk_level?: string;
  meeting_id?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.risk_level) params.append('risk_level', filters.risk_level);
  if (filters?.meeting_id) params.append('meeting_id', filters.meeting_id);

  const url = `${API_URL}/export/risks?${params.toString()}`;
  const res = await authenticatedFetch(url);
  const blob = await res.blob();
  const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || 'risks.csv';
  await downloadBlob(blob, filename);
  toast.success('Risks exported successfully');
}

export async function exportDecisions(filters?: {
  project_id?: string;
  meeting_id?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.meeting_id) params.append('meeting_id', filters.meeting_id);

  const url = `${API_URL}/export/decisions?${params.toString()}`;
  const res = await authenticatedFetch(url);
  const blob = await res.blob();
  const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || 'decisions.csv';
  await downloadBlob(blob, filename);
  toast.success('Decisions exported successfully');
}

// Meeting endpoints
export async function getMeetings(projectId?: string) {
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);

  const url = `${API_URL}/meetings/?${params.toString()}`;
  const res = await authenticatedFetch(url);
  return res.json();
}

// Difference detection endpoints
export interface TaskDiffResult {
  added: Array<Record<string, unknown>>;
  removed: Array<Record<string, unknown>>;
  status_changed: Array<{
    task: Record<string, unknown>;
    prev_status: string;
    curr_status: string;
  }>;
  priority_changed: Array<{
    task: Record<string, unknown>;
    prev_priority: string;
    curr_priority: string;
  }>;
  unchanged: Array<Record<string, unknown>>;
  summary: {
    added_count: number;
    removed_count: number;
    status_changed_count: number;
    priority_changed_count: number;
    unchanged_count: number;
    total_changes: number;
  };
}

export interface RiskDiffResult {
  added: Array<Record<string, unknown>>;
  removed: Array<Record<string, unknown>>;
  level_changed: Array<{
    risk: Record<string, unknown>;
    prev_level: string;
    curr_level: string;
  }>;
  unchanged: Array<Record<string, unknown>>;
  escalated: Array<{
    risk: Record<string, unknown>;
    prev_level: string;
    curr_level: string;
  }>;
  de_escalated: Array<{
    risk: Record<string, unknown>;
    prev_level: string;
    curr_level: string;
  }>;
  summary: {
    added_count: number;
    removed_count: number;
    level_changed_count: number;
    unchanged_count: number;
    total_changes: number;
  };
}

export async function getTasksDifference(
  prevMeetingId: string,
  currMeetingId: string,
  projectId?: string
): Promise<TaskDiffResult> {
  const params = new URLSearchParams();
  params.append('prev_meeting_id', prevMeetingId);
  params.append('curr_meeting_id', currMeetingId);
  if (projectId) params.append('project_id', projectId);

  const url = `${API_URL}/tasks/difference?${params.toString()}`;
  const res = await authenticatedFetch(url);
  return res.json();
}

export async function getRisksDifference(
  prevMeetingId: string,
  currMeetingId: string,
  projectId?: string
): Promise<RiskDiffResult> {
  const params = new URLSearchParams();
  params.append('prev_meeting_id', prevMeetingId);
  params.append('curr_meeting_id', currMeetingId);
  if (projectId) params.append('project_id', projectId);

  const url = `${API_URL}/risks/difference?${params.toString()}`;
  const res = await authenticatedFetch(url);
  return res.json();
}

// Settings endpoints
export interface SlackSettings {
  webhook_url: string;
  webhook_url_masked?: string;
  notify_on_high_risk: boolean;
  notify_on_overdue: boolean;
  notify_on_meeting_processed: boolean;
}

export async function getSlackSettings(): Promise<SlackSettings> {
  const res = await authenticatedFetch(`${API_URL}/settings/slack`);
  return res.json();
}

export async function updateSlackSettings(settings: {
  webhook_url: string;
  notify_on_high_risk?: boolean;
  notify_on_overdue?: boolean;
  notify_on_meeting_processed?: boolean;
}): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/settings/slack`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}

export async function deleteSlackSettings(): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/settings/slack`, {
    method: 'DELETE',
  });
  return res.json();
}

export async function testSlackNotification(
  webhookUrl?: string,
  message?: string
): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/settings/slack/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      webhook_url: webhookUrl,
      message: message || 'Test notification from Project Progress DB',
    }),
  });
  return res.json();
}

export async function sendImmediateNotifications(): Promise<{
  high_risks_notified: boolean;
  overdue_tasks_notified: boolean;
  high_risks_count: number;
  overdue_tasks_count: number;
}> {
  const res = await authenticatedFetch(`${API_URL}/settings/slack/notify-now`, {
    method: 'POST',
  });
  return res.json();
}

// Health score endpoints
export interface HealthScoreBreakdown {
  task_completion: number;
  overdue: number;
  risk_level: number;
  activity: number;
}

export interface HealthScoreDetails {
  total_tasks: number;
  done_tasks: number;
  overdue_tasks: number;
  total_risks: number;
  high_risks: number;
  recent_meetings: number;
}

export interface ProjectHealthScore {
  project_id: string;
  project_name?: string;
  score: number;
  status: 'HEALTHY' | 'AT_RISK' | 'WARNING' | 'CRITICAL';
  breakdown: HealthScoreBreakdown;
  details: HealthScoreDetails;
}

export async function getAllProjectHealthScores(): Promise<ProjectHealthScore[]> {
  const res = await authenticatedFetch(`${API_URL}/projects/health`);
  return res.json();
}

export async function getProjectHealthScore(projectId: string): Promise<ProjectHealthScore> {
  const res = await authenticatedFetch(`${API_URL}/projects/${projectId}/health`);
  return res.json();
}

// Agenda generation endpoints
export interface AgendaItem {
  title: string;
  description: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  estimated_minutes: number;
  related_tasks?: string[];
  related_risks?: string[];
}

export interface GeneratedAgenda {
  agenda_items: AgendaItem[];
  suggested_duration_minutes: number;
  key_discussion_points: (string | null)[];
  recommended_attendees?: string[];
  generated_at: string;
  project_name: string;
  ai_generated?: boolean;
  projects_count?: number;
}

export async function generateProjectAgenda(projectId: string): Promise<GeneratedAgenda> {
  const res = await authenticatedFetch(`${API_URL}/agenda/generate?project_id=${projectId}`);
  return res.json();
}

export async function generatePortfolioAgenda(): Promise<GeneratedAgenda> {
  const res = await authenticatedFetch(`${API_URL}/agenda/generate/all`);
  return res.json();
}

// User management endpoints
export type UserRole = 'ADMIN' | 'PM' | 'MEMBER';

export interface User {
  user_id: string;
  email: string;
  name?: string;
  picture?: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface CurrentUser {
  email: string;
  name?: string;
  picture?: string;
  role: UserRole;
  user_id?: string;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const res = await authenticatedFetch(`${API_URL}/users/me`);
  return res.json();
}

export async function listUsers(): Promise<User[]> {
  const res = await authenticatedFetch(`${API_URL}/users/`);
  return res.json();
}

export async function getUser(email: string): Promise<User> {
  const res = await authenticatedFetch(`${API_URL}/users/${encodeURIComponent(email)}`);
  return res.json();
}

export async function updateUserRole(email: string, role: UserRole): Promise<{ message: string; user: User }> {
  const res = await authenticatedFetch(`${API_URL}/users/${encodeURIComponent(email)}/role`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role }),
  });
  return res.json();
}

export async function deleteUser(email: string): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/users/${encodeURIComponent(email)}`, {
    method: 'DELETE',
  });
  return res.json();
}

export async function getAvailableRoles(): Promise<{
  roles: UserRole[];
  descriptions: Record<UserRole, string>;
}> {
  const res = await authenticatedFetch(`${API_URL}/users/roles/available`);
  return res.json();
}

// Audit log endpoints
export interface AuditLog {
  log_id: string;
  timestamp: string;
  user_email?: string;
  user_name?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  user_agent?: string;
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditStats {
  period_days: number;
  total: number;
  by_action: Record<string, number>;
  by_user: Array<{ email: string; count: number }>;
  daily: Array<{ date: string; count: number }>;
}

export async function getAuditLogs(filters?: {
  limit?: number;
  offset?: number;
  user_email?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
}): Promise<AuditLogListResponse> {
  const params = new URLSearchParams();
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());
  if (filters?.user_email) params.append('user_email', filters.user_email);
  if (filters?.action) params.append('action', filters.action);
  if (filters?.resource_type) params.append('resource_type', filters.resource_type);
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);

  const res = await authenticatedFetch(`${API_URL}/audit/logs?${params.toString()}`);
  return res.json();
}

export async function getAuditStats(days: number = 30): Promise<AuditStats> {
  const res = await authenticatedFetch(`${API_URL}/audit/stats?days=${days}`);
  return res.json();
}

export async function getAuditActions(): Promise<{
  actions: string[];
  descriptions: Record<string, string>;
}> {
  const res = await authenticatedFetch(`${API_URL}/audit/actions`);
  return res.json();
}

// Email report endpoints
export interface WeeklyReportSummary {
  overdue_tasks_count: number;
  high_risks_count: number;
  projects_analyzed: number;
}

export interface WeeklyReportText {
  subject: string;
  body: string;
  summary: WeeklyReportSummary;
  generated_at: string;
}

export interface WeeklyReportHtml {
  subject: string;
  body_html: string;
  summary: WeeklyReportSummary;
  generated_at: string;
}

export async function generateWeeklyReportText(includeHealth: boolean = true): Promise<WeeklyReportText> {
  const res = await authenticatedFetch(`${API_URL}/email/weekly-report?include_health=${includeHealth}`);
  return res.json();
}

export async function generateWeeklyReportHtml(includeHealth: boolean = true): Promise<WeeklyReportHtml> {
  const res = await authenticatedFetch(`${API_URL}/email/weekly-report/html?include_health=${includeHealth}`);
  return res.json();
}
