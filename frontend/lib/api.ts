import { toast } from './toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Task {
  task_id: string;
  task_title: string;
  task_description?: string;
  owner?: string;
  due_date?: string;
  status: string;
  priority: string;
  project_id?: string;
  meeting_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface Risk {
  risk_id: string;
  risk_description: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  project_id?: string;
  project_name?: string;
  owner?: string;
  source_sentence?: string;
  created_at: string;
}

export interface Project {
  project_id: string;
  project_name: string;
  latest_meeting_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Decision {
  decision_id: string;
  decision_description: string;
  decided_by?: string;
  project_id?: string;
  meeting_id?: string;
  created_at: string;
}

export interface Meeting {
  meeting_id: string;
  title: string;
  meeting_date: string;
  status: 'PENDING' | 'DONE' | 'ERROR';
  source_file_uri?: string;
  language?: string;
  error_message?: string;
  created_at: string;
  task_count?: number;
  risk_count?: number;
  decision_count?: number;
}

export interface ProjectStats {
  project_id: string;
  total_tasks: number;
  incomplete_tasks: number;
  overdue_tasks: number;
  total_risks: number;
  risks_by_level: Record<string, number>;
  total_decisions: number;
}

export interface TaskUpdate {
  task_title?: string;
  task_description?: string;
  owner?: string;
  due_date?: string;
  status?: 'NOT_STARTED' | 'IN_PROGRESS' | 'DONE' | 'UNKNOWN';
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface RiskUpdate {
  risk_description?: string;
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  owner?: string;
}

export interface ProjectUpdate {
  project_name?: string;
}

export interface SearchResults {
  tasks: Array<{ entity_type: string; id: string; title: string; description: string }>;
  risks: Array<{ entity_type: string; id: string; title: string; description: string }>;
  projects: Array<{ entity_type: string; id: string; title: string; description: string }>;
  decisions: Array<{ entity_type: string; id: string; title: string; description: string }>;
}

/**
 * Fetch wrapper that includes credentials and handles auth errors.
 */
async function authenticatedFetch(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Always include cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // Handle authentication errors
    if (response.status === 401) {
      toast.error('ログインしてください');
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      throw new Error('認証エラー');
    }

    // Handle rate limit exceeded
    if (response.status === 429) {
      toast.error('リクエストが多すぎます。しばらく待ってから再試行してください。');
      throw new Error('レート制限超過');
    }

    // Handle server errors with structured error response
    if (!response.ok) {
      let errorMessage = 'エラーが発生しました';
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
      toast.error('ネットワークエラー。接続を確認してください。');
    }
    throw error;
  }
}

export interface UploadResponse {
  meeting_id: string;
  status: 'PENDING' | 'DONE' | 'ERROR';
  message?: string;
  message_id?: string;
  transcript_format?: string;
  transcript_segments?: number;
  extracted?: {
    projects: number;
    tasks: number;
    risks: number;
    decisions: number;
  };
}

export async function uploadFile(
  file: File, 
  date: string, 
  title?: string,
  sourceType: string = 'auto'
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('meeting_date', date);
  formData.append('source_type', sourceType);
  if (title) formData.append('title', title);

  const res = await authenticatedFetch(`${API_URL}/upload/`, {
    method: 'POST',
    body: formData,
    headers: {}, // Remove Content-Type for FormData
  });

  return res.json();
}

export async function uploadText(
  text: string, 
  date: string, 
  title?: string,
  sourceType: string = 'auto'
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('meeting_date', date);
  formData.append('source_type', sourceType);
  if (title) formData.append('title', title);

  const res = await authenticatedFetch(`${API_URL}/upload/text`, {
    method: 'POST',
    body: formData,
    headers: {}, // Remove Content-Type for FormData
  });

  return res.json();
}

export async function getUploadFormats(): Promise<{
  formats: Array<{
    format: string;
    name: string;
    extensions: string[];
    description: string;
    example_source: string;
  }>;
  supported_extensions: string[];
}> {
  const res = await authenticatedFetch(`${API_URL}/upload/formats`);
  return res.json();
}

// ===== PROJECTS =====

export async function getProjects(filters?: {
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Project>> {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const res = await authenticatedFetch(`${API_URL}/projects/?${params.toString()}`);
  return res.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await authenticatedFetch(`${API_URL}/projects/${projectId}`);
  return res.json();
}

export async function updateProject(projectId: string, updates: ProjectUpdate): Promise<Project> {
  const res = await authenticatedFetch(`${API_URL}/projects/${projectId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function deleteProject(projectId: string): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });
  return res.json();
}

// ===== TASKS =====

export async function getTasks(filters?: {
  project_id?: string;
  status?: string[];
  priority?: string[];
  owner?: string;
  due_date_from?: string;
  due_date_to?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Task>> {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.status) filters.status.forEach(s => params.append('status', s));
  if (filters?.priority) filters.priority.forEach(p => params.append('priority', p));
  if (filters?.owner) params.append('owner', filters.owner);
  if (filters?.due_date_from) params.append('due_date_from', filters.due_date_from);
  if (filters?.due_date_to) params.append('due_date_to', filters.due_date_to);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const res = await authenticatedFetch(`${API_URL}/tasks/?${params.toString()}`);
  return res.json();
}

export async function getTask(taskId: string): Promise<Task> {
  const res = await authenticatedFetch(`${API_URL}/tasks/${taskId}`);
  return res.json();
}

export async function updateTask(taskId: string, updates: TaskUpdate): Promise<Task> {
  const res = await authenticatedFetch(`${API_URL}/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function deleteTask(taskId: string): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/tasks/${taskId}`, {
    method: 'DELETE',
  });
  return res.json();
}

// ===== RISKS =====

export async function getRisks(filters?: {
  project_id?: string;
  risk_level?: string[];
  meeting_id?: string;
  owner?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Risk>> {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.risk_level) filters.risk_level.forEach(r => params.append('risk_level', r));
  if (filters?.meeting_id) params.append('meeting_id', filters.meeting_id);
  if (filters?.owner) params.append('owner', filters.owner);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const res = await authenticatedFetch(`${API_URL}/risks/?${params.toString()}`);
  return res.json();
}

export async function getRisk(riskId: string): Promise<Risk> {
  const res = await authenticatedFetch(`${API_URL}/risks/${riskId}`);
  return res.json();
}

export async function updateRisk(riskId: string, updates: RiskUpdate): Promise<Risk> {
  const res = await authenticatedFetch(`${API_URL}/risks/${riskId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function deleteRisk(riskId: string): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/risks/${riskId}`, {
    method: 'DELETE',
  });
  return res.json();
}

export async function getRiskStats() {
  const res = await authenticatedFetch(`${API_URL}/risks/stats`);
  return res.json();
}

// ===== DECISIONS =====

export async function getDecisions(filters?: {
  project_id?: string;
  meeting_id?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Decision>> {
  const params = new URLSearchParams();
  if (filters?.project_id) params.append('project_id', filters.project_id);
  if (filters?.meeting_id) params.append('meeting_id', filters.meeting_id);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const res = await authenticatedFetch(`${API_URL}/risks/decisions?${params.toString()}`);
  return res.json();
}

export async function getDecision(decisionId: string): Promise<Decision> {
  const res = await authenticatedFetch(`${API_URL}/risks/decisions/${decisionId}`);
  return res.json();
}

export async function deleteDecision(decisionId: string): Promise<{ message: string }> {
  const res = await authenticatedFetch(`${API_URL}/risks/decisions/${decisionId}`, {
    method: 'DELETE',
  });
  return res.json();
}

// ===== MEETINGS =====

export async function getMeetings(filters?: {
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Meeting>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const res = await authenticatedFetch(`${API_URL}/meetings/?${params.toString()}`);
  return res.json();
}

export async function getMeeting(meetingId: string): Promise<Meeting> {
  const res = await authenticatedFetch(`${API_URL}/meetings/${meetingId}`);
  return res.json();
}

// ===== PROJECT STATS =====

export async function getProjectStats(projectId: string): Promise<ProjectStats> {
  const res = await authenticatedFetch(`${API_URL}/projects/${projectId}/stats`);
  return res.json();
}

// ===== SEARCH =====

export async function searchAll(query: string, limit?: number): Promise<SearchResults> {
  const params = new URLSearchParams();
  params.append('q', query);
  if (limit) params.append('limit', limit.toString());

  const res = await authenticatedFetch(`${API_URL}/search/?${params.toString()}`);
  return res.json();
}

// ===== AUDIT LOG =====

export async function getAuditLog(filters?: {
  entity_type?: string;
  entity_id?: string;
  limit?: number;
  offset?: number;
}) {
  const params = new URLSearchParams();
  if (filters?.entity_type) params.append('entity_type', filters.entity_type);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const res = await authenticatedFetch(`${API_URL}/search/audit?${params.toString()}`);
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
  toast.success('プロジェクトをエクスポートしました');
}

export async function exportTasks(projectId?: string) {
  const url = projectId
    ? `${API_URL}/export/tasks?project_id=${projectId}`
    : `${API_URL}/export/tasks`;
  const res = await authenticatedFetch(url);
  const blob = await res.blob();
  const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || 'tasks.csv';
  await downloadBlob(blob, filename);
  toast.success('タスクをエクスポートしました');
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
  toast.success('リスクをエクスポートしました');
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
  toast.success('決定事項をエクスポートしました');
}
