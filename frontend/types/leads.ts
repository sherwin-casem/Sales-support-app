export type LeadStatus = "NEW" | "ENRICHED" | "CONTACTED" | "REPLIED" | "CONVERTED";

export interface Lead {
  id: string;
  company_name: string;
  website: string | null;
  email: string | null;
  phone: string | null;
  industry: string | null;
  employee_count: number | null;
  revenue: string | null;
  country: string | null;
  status: LeadStatus;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface DecisionMaker {
  id: string;
  lead_id: string;
  name: string;
  role: string | null;
  email: string | null;
  linkedin: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadDetail extends Lead {
  decision_makers: DecisionMaker[];
}

export interface LeadCreateInput {
  company_name: string;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
  industry?: string | null;
  employee_count?: number | null;
  revenue?: number | null;
  country?: string | null;
  status?: LeadStatus;
}

export type LeadUpdateInput = Partial<LeadCreateInput>;

export interface DecisionMakerInput {
  name: string;
  role?: string | null;
  email?: string | null;
  linkedin?: string | null;
}

export interface LeadImportResult {
  created: number;
  failed: number;
  errors: string[];
}

export interface LeadListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: LeadStatus;
  industry?: string;
  country?: string;
}
