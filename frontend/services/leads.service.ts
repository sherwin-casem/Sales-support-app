import { API_URL, ApiClientError, apiRequest } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api";
import type {
  DecisionMaker,
  DecisionMakerInput,
  Lead,
  LeadCreateInput,
  LeadDetail,
  LeadImportResult,
  LeadListParams,
  LeadUpdateInput,
} from "@/types/leads";

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const leadsService = {
  list(token: string, params: LeadListParams = {}) {
    return apiRequest<PaginatedResponse<Lead>>(
      `/leads${buildQuery({
        page: params.page,
        page_size: params.page_size,
        search: params.search,
        status: params.status,
        industry: params.industry,
        country: params.country,
      })}`,
      { token },
    );
  },

  get(token: string, id: string) {
    return apiRequest<LeadDetail>(`/leads/${id}`, { token });
  },

  create(token: string, payload: LeadCreateInput) {
    return apiRequest<Lead>("/leads", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    });
  },

  update(token: string, id: string, payload: LeadUpdateInput) {
    return apiRequest<Lead>(`/leads/${id}`, {
      method: "PATCH",
      token,
      body: JSON.stringify(payload),
    });
  },

  delete(token: string, id: string) {
    return apiRequest<void>(`/leads/${id}`, { method: "DELETE", token });
  },

  importCsv(token: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${API_URL}/leads/import`, {
      method: "POST",
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    }).then(async (response) => {
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new ApiClientError(
          data?.detail ?? "Import failed",
          data?.code ?? "IMPORT_FAILED",
          response.status,
        );
      }
      return data as LeadImportResult;
    });
  },

  async exportCsv(token: string, params: LeadListParams = {}) {
    const response = await fetch(
      `${API_URL}/leads/export${buildQuery({
        search: params.search,
        status: params.status,
        industry: params.industry,
        country: params.country,
      })}`,
      {
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!response.ok) {
      throw new ApiClientError("Export failed", "EXPORT_FAILED", response.status);
    }
    return response.blob();
  },

  listDecisionMakers(token: string, leadId: string) {
    return apiRequest<DecisionMaker[]>(`/leads/${leadId}/decision-makers`, { token });
  },

  addDecisionMaker(token: string, leadId: string, payload: DecisionMakerInput) {
    return apiRequest<DecisionMaker>(`/leads/${leadId}/decision-makers`, {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    });
  },

  removeDecisionMaker(token: string, leadId: string, dmId: string) {
    return apiRequest<void>(`/leads/${leadId}/decision-makers/${dmId}`, {
      method: "DELETE",
      token,
    });
  },

  verify(token: string, leadId: string) {
    return apiRequest<Lead>(`/leads/${leadId}/verify`, { method: "POST", token });
  },

  listDuplicates(token: string, page = 1) {
    return apiRequest<PaginatedResponse<Lead>>(`/leads/duplicates?page=${page}`, { token });
  },

  dismissDuplicate(token: string, leadId: string) {
    return apiRequest<void>(`/leads/duplicates/${leadId}`, { method: "DELETE", token });
  },
};
