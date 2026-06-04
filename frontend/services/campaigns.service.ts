import { apiRequest } from "@/lib/api-client";
import type {
  Campaign,
  CampaignAnalytics,
  CampaignDetail,
  GeneratedMessage,
  MessageChannel,
} from "@/types/campaigns";

export const campaignsService = {
  list(token: string) {
    return apiRequest<Campaign[]>("/campaigns", { token });
  },

  get(token: string, id: string) {
    return apiRequest<CampaignDetail>(`/campaigns/${id}`, { token });
  },

  create(token: string, payload: { name: string; description?: string; channel?: string }) {
    return apiRequest<Campaign>("/campaigns", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    });
  },

  addLeads(token: string, campaignId: string, leadIds: string[]) {
    return apiRequest<CampaignDetail>(`/campaigns/${campaignId}/leads`, {
      method: "POST",
      token,
      body: JSON.stringify({ lead_ids: leadIds }),
    });
  },

  schedule(token: string, campaignId: string, scheduledAt: string) {
    return apiRequest<Campaign>(`/campaigns/${campaignId}/schedule`, {
      method: "POST",
      token,
      body: JSON.stringify({ scheduled_at: scheduledAt }),
    });
  },

  sendNow(token: string, campaignId: string) {
    return apiRequest<{ enqueued: number; task_ids: string[] }>(`/campaigns/${campaignId}/send`, {
      method: "POST",
      token,
    });
  },

  generateMessage(
    token: string,
    payload: {
      lead_id: string;
      channel: MessageChannel;
      campaign_id?: string;
      tone?: string;
      context?: string;
    },
  ) {
    return apiRequest<GeneratedMessage>("/messages/generate", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    });
  },

  listMessages(token: string, params: { lead_id?: string; campaign_id?: string } = {}) {
    const q = new URLSearchParams();
    if (params.lead_id) q.set("lead_id", params.lead_id);
    if (params.campaign_id) q.set("campaign_id", params.campaign_id);
    const query = q.toString();
    return apiRequest<GeneratedMessage[]>(`/messages${query ? `?${query}` : ""}`, { token });
  },

  getCampaignAnalytics(token: string, campaignId: string) {
    return apiRequest<CampaignAnalytics>(`/analytics/campaigns/${campaignId}`, { token });
  },
};
