export interface CVProfile {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  district?: string | null;
  summary?: string | null;
  skills: string[];
  years_of_experience: number;
  preferred_job_titles: string[];
  preferred_locations: string[];
  open_to_remote: boolean;
  raw_text_char_count: number;
  job_function?: string;
}

export interface JobItem {
  id: string;
  title: string;
  company: string;
  location: string;
  district: string;
  is_remote: boolean;
  job_type: string;
  source: string;
  url: string;
  description: string;
  salary?: string | null;
  tags: string[];
  posted_date?: string | null;
  match_score: number;
  match_reason?: string | null;
  cover_letter?: string | null;
  status: "SAVED" | "APPLIED" | "ARCHIVED";
  sectors?: string[];
  job_function?: string;
  deadline?: string | null;
  days_left?: number | null;
  urgency?: "expired" | "critical" | "urgent" | "soon" | "normal" | "unknown";
}

export interface PipelineResponse {
  profile: CVProfile;
  total_found: number;
  matched_jobs: JobItem[];
}