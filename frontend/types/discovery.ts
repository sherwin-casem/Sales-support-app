export interface DiscoveryProfile {
  id: string;
  name: string;
  description: string | null;
  industries: string[];
  countries: string[];
  seed_urls: string[];
  crawl_depth: number;
  max_pages: number;
  schedule_cron: string | null;
  is_active: boolean;
  created_by: string | null;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DiscoveryProfileInput {
  name: string;
  description?: string | null;
  industries?: string[];
  countries?: string[];
  seed_urls: string[];
  crawl_depth?: number;
  max_pages?: number;
  schedule_cron?: string | null;
  is_active?: boolean;
}

export interface CrawlRun {
  id: string;
  profile_id: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  pages_crawled: number;
  leads_found: number;
  leads_created: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  celery_task_id: string | null;
  created_at: string;
}

export interface RunDiscoveryResponse {
  crawl_run_id: string;
  task_id: string;
  message: string;
}
