export interface AnalyticsOverview {
  total_leads: number;
  total_campaigns: number;
  sent_messages: number;
  reply_rate: number;
  conversion_rate: number;
  leads_by_status: Record<string, number>;
}
