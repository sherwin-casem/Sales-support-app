import type { LeadStatus } from "@/types/leads";

export const LEAD_STATUSES: LeadStatus[] = ["NEW", "ENRICHED", "CONTACTED", "REPLIED", "CONVERTED"];

export const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  NEW: "New",
  ENRICHED: "Enriched",
  CONTACTED: "Contacted",
  REPLIED: "Replied",
  CONVERTED: "Converted",
};

export const LEAD_STATUS_VARIANT: Record<
  LeadStatus,
  "default" | "secondary" | "success" | "warning" | "outline"
> = {
  NEW: "secondary",
  ENRICHED: "default",
  CONTACTED: "warning",
  REPLIED: "outline",
  CONVERTED: "success",
};
