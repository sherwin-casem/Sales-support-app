export type CampaignStatus = "DRAFT" | "SCHEDULED" | "RUNNING" | "COMPLETED" | "PAUSED";
export type CampaignChannel = "EMAIL" | "LINKEDIN" | "WHATSAPP";
export type MessageChannel = "EMAIL" | "LINKEDIN" | "WHATSAPP";

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  status: CampaignStatus;
  channel: CampaignChannel;
  scheduled_at: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  lead_count: number;
}

export interface CampaignLead {
  id: string;
  campaign_id: string;
  lead_id: string;
  status: string;
  sent_at: string | null;
  replied_at: string | null;
}

export interface CampaignDetail extends Campaign {
  campaign_leads: CampaignLead[];
}

export interface GeneratedMessage {
  id: string;
  lead_id: string;
  campaign_id: string | null;
  channel: MessageChannel;
  subject: string | null;
  body: string;
  created_at: string;
}

export interface CampaignAnalytics {
  campaign_id: string;
  campaign_name: string;
  total_leads: number;
  sent: number;
  replied: number;
  failed: number;
  pending: number;
  reply_rate: number;
}
