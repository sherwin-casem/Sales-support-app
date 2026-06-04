import { apiRequest } from "@/lib/api-client";

export interface EnrichmentRecord {
  id: string;
  lead_id: string;
  source: string;
  domain: string | null;
  scraped_title: string | null;
  scraped_description: string | null;
  inferred_industry: string | null;
  inferred_employee_count: number | null;
  enriched_at: string;
  created_at: string;
}

export const enrichmentService = {
  enrichLead(token: string, leadId: string) {
    return apiRequest<{ task_id: string; message: string }>(`/enrichment/leads/${leadId}`, {
      method: "POST",
      token,
    });
  },

  getHistory(token: string, leadId: string) {
    return apiRequest<EnrichmentRecord[]>(`/enrichment/leads/${leadId}`, { token });
  },

  getJobStatus(token: string, taskId: string) {
    return apiRequest<{ task_id: string; status: string; result: unknown }>(
      `/enrichment/jobs/${taskId}`,
      { token },
    );
  },
};
