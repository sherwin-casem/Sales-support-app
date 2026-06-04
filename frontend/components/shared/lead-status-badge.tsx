import { Badge } from "@/components/ui/badge";
import { LEAD_STATUS_LABELS, LEAD_STATUS_VARIANT } from "@/lib/constants";
import type { LeadStatus } from "@/types/leads";

export function LeadStatusBadge({ status }: { status: LeadStatus }) {
  return <Badge variant={LEAD_STATUS_VARIANT[status]}>{LEAD_STATUS_LABELS[status]}</Badge>;
}
