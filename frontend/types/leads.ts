export type LeadStatus = "NEW" | "ENRICHED" | "CONTACTED" | "REPLIED" | "CONVERTED";
export type LeadSource = "MANUAL" | "IMPORT" | "DISCOVERY" | "SEARCH";
export type VerificationStatus = "UNKNOWN" | "VALID_FORMAT" | "MX_FOUND" | "INVALID";

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
  source?: LeadSource;
  domain_normalized?: string | null;
  email_verification_status?: VerificationStatus;
  phone_verification_status?: VerificationStatus;
  intent_score?: number;
  is_duplicate?: boolean;
  duplicate_of_id?: string | null;
  discovery_profile_id?: string | null;
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
