import { apiRequest } from "@/lib/api-client";

export interface LeadPreviewItem {
  company_name: string;
  website: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  industry: string | null;
  match_score: number;
  match_reason: string;
  scraped_title: string | null;
  already_in_pipeline: boolean;
}

export interface LeadSearchRun {
  id: string;
  query_text: string;
  seed_urls: string[];
  parsed_criteria: Record<string, unknown>;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  preview_items: LeadPreviewItem[];
  pages_crawled: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface LeadSearchStartResponse {
  search_id: string;
  task_id: string;
  message: string;
}

export interface LeadSearchSaveResponse {
  created: number;
  skipped: number;
  lead_ids: string[];
}

const POLL_INTERVAL_MS = 2500;
const MAX_POLL_ATTEMPTS = 60;

export const leadSearchService = {
  start(token: string, query: string, maxResults = 20) {
    return apiRequest<LeadSearchStartResponse>("/leads/search", {
      method: "POST",
      token,
      body: JSON.stringify({ query, max_results: maxResults }),
    });
  },

  getRun(token: string, searchId: string) {
    return apiRequest<LeadSearchRun>(`/leads/search/${searchId}`, { token });
  },

  save(token: string, searchId: string, items: LeadPreviewItem[]) {
    return apiRequest<LeadSearchSaveResponse>(`/leads/search/${searchId}/save`, {
      method: "POST",
      token,
      body: JSON.stringify({
        items: items.map((item) => ({
          company_name: item.company_name,
          website: item.website,
          email: item.email,
          phone: item.phone,
          country: item.country,
          industry: item.industry,
        })),
      }),
    });
  },

  async pollUntilComplete(token: string, searchId: string): Promise<LeadSearchRun> {
    for (let i = 0; i < MAX_POLL_ATTEMPTS; i++) {
      const run = await this.getRun(token, searchId);
      if (run.status === "COMPLETED" || run.status === "FAILED") {
        return run;
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }
    throw new Error("Search timed out. Check that the Celery worker is running.");
  },
};
