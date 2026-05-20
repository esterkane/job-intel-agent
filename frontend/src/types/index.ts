export type Job = {
  id: number;
  source_name: string;
  source_type: string;
  company: string;
  title: string;
  location: string | null;
  remote_type: string | null;
  region: string | null;
  job_url: string;
  description: string | null;
  department: string | null;
  employment_type: string | null;
  first_seen_at: string;
  last_seen_at: string;
  status: string;
  ingestion_method: string;
  final_score: number;
  role_family: string | null;
  score_breakdown: Record<string, number>;
  why_this_matches: string | null;
  concerns: string | null;
  suggested_application_angle: string | null;
  suggested_cv_emphasis: string | null;
  notes: string | null;
};

export type Source = {
  id: number;
  company_name: string;
  career_url: string;
  source_type: string;
  adapter_type: string;
  remote_policy_notes: string | null;
  culture_notes: string | null;
  priority: string;
  include_keywords: string[];
  exclude_keywords: string[];
  target_regions: string[];
  enabled: boolean;
  last_status: string | null;
  last_error: string | null;
  last_successful_scrape: string | null;
};

export type Stats = {
  jobs_found_today: number;
  new_high_fit_jobs: number;
  saved_jobs: number;
  applied_jobs: number;
  sources_with_errors: number;
  latest_run_status: string;
};

export type ScrapeRun = {
  id: number;
  source_id: number | null;
  started_at: string;
  finished_at: string | null;
  status: string;
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  error_message: string | null;
};

export type ManualCapturePayload = {
  url?: string;
  title: string;
  company: string;
  location?: string;
  description: string;
  notes?: string;
};

export type SavedSearch = {
  id: number;
  platform: string;
  query_name: string;
  role_family: string | null;
  url: string;
  region: string | null;
  remote_filter: string | null;
  enabled: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type SavedSearchPayload = {
  platform: string;
  query_name: string;
  role_family?: string | null;
  url: string;
  region?: string | null;
  remote_filter?: string | null;
  enabled?: boolean;
  notes?: string | null;
};
