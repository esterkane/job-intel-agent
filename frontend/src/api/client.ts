import type { Job, ManualCapturePayload, ScrapeRun, Source, Stats } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const api = {
  stats: () => request<Stats>('/api/stats'),
  jobs: (query = '') => request<Job[]>(`/api/jobs${query}`),
  job: (id: number) => request<Job>(`/api/jobs/${id}`),
  updateJob: (id: number, payload: Partial<Job>) => request<Job>(`/api/jobs/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  sources: () => request<Source[]>('/api/sources'),
  updateSource: (id: number, payload: Partial<Source>) => request<Source>(`/api/sources/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  runScrape: (fresh = false) => request<{ queued: number; fresh: boolean; deleted: number }>(`/api/scrape/run${fresh ? '?fresh=true' : ''}`, { method: 'POST' }),
  runSource: (id: number, fresh = false) => request<ScrapeRun>(`/api/scrape/run/${id}${fresh ? '?fresh=true' : ''}`, { method: 'POST' }),
  manualCapture: (payload: ManualCapturePayload) => request<Job>('/api/manual-capture', { method: 'POST', body: JSON.stringify(payload) }),
  runs: () => request<ScrapeRun[]>('/api/scrape/runs'),
  profile: () => request<Record<string, unknown>>('/api/search-profile'),
};
