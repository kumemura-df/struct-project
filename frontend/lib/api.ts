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
