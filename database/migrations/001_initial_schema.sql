-- Migration: 001_initial_schema
-- Description: Initial schema for Sales Intelligence & AI Outreach Platform (Alpha MVP)
-- Created: Phase 1

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums
CREATE TYPE user_role AS ENUM ('ADMIN', 'MANAGER', 'SALES');
CREATE TYPE lead_status AS ENUM ('NEW', 'ENRICHED', 'CONTACTED', 'REPLIED', 'CONVERTED');
CREATE TYPE campaign_status AS ENUM ('DRAFT', 'SCHEDULED', 'RUNNING', 'COMPLETED', 'PAUSED');
CREATE TYPE campaign_channel AS ENUM ('EMAIL', 'LINKEDIN', 'WHATSAPP');
CREATE TYPE campaign_lead_status AS ENUM ('PENDING', 'SENT', 'FAILED', 'REPLIED', 'CONVERTED');
CREATE TYPE message_channel AS ENUM ('EMAIL', 'LINKEDIN', 'WHATSAPP');

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'SALES',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Refresh tokens
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);

-- Leads
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    website VARCHAR(512),
    email VARCHAR(255),
    phone VARCHAR(50),
    industry VARCHAR(255),
    employee_count INTEGER,
    revenue NUMERIC(15, 2),
    country VARCHAR(100),
    status lead_status NOT NULL DEFAULT 'NEW',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leads_status ON leads (status);
CREATE INDEX idx_leads_company_name ON leads (company_name);
CREATE INDEX idx_leads_created_by ON leads (created_by);
CREATE INDEX idx_leads_industry ON leads (industry);
CREATE INDEX idx_leads_country ON leads (country);

CREATE TRIGGER trg_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Decision makers
CREATE TABLE decision_makers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    email VARCHAR(255),
    linkedin VARCHAR(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_decision_makers_lead_id ON decision_makers (lead_id);
CREATE INDEX idx_decision_makers_role ON decision_makers (role);

CREATE TRIGGER trg_decision_makers_updated_at
    BEFORE UPDATE ON decision_makers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Enrichment records
CREATE TABLE enrichment_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    source VARCHAR(100) NOT NULL,
    raw_data JSONB NOT NULL DEFAULT '{}',
    domain VARCHAR(255),
    scraped_title VARCHAR(512),
    scraped_description TEXT,
    inferred_industry VARCHAR(255),
    inferred_employee_count INTEGER,
    enriched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_enrichment_records_lead_id ON enrichment_records (lead_id);
CREATE INDEX idx_enrichment_records_domain ON enrichment_records (domain);

CREATE TRIGGER trg_enrichment_records_updated_at
    BEFORE UPDATE ON enrichment_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status campaign_status NOT NULL DEFAULT 'DRAFT',
    channel campaign_channel NOT NULL DEFAULT 'EMAIL',
    scheduled_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_status ON campaigns (status);
CREATE INDEX idx_campaigns_created_by ON campaigns (created_by);
CREATE INDEX idx_campaigns_scheduled_at ON campaigns (scheduled_at);

CREATE TRIGGER trg_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Campaign leads
CREATE TABLE campaign_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    status campaign_lead_status NOT NULL DEFAULT 'PENDING',
    sent_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_campaign_leads_campaign_lead UNIQUE (campaign_id, lead_id)
);

CREATE INDEX idx_campaign_leads_campaign_id ON campaign_leads (campaign_id);
CREATE INDEX idx_campaign_leads_lead_id ON campaign_leads (lead_id);
CREATE INDEX idx_campaign_leads_status ON campaign_leads (status);

CREATE TRIGGER trg_campaign_leads_updated_at
    BEFORE UPDATE ON campaign_leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Campaign messages
CREATE TABLE campaign_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_lead_id UUID NOT NULL REFERENCES campaign_leads(id) ON DELETE CASCADE,
    subject VARCHAR(512),
    body TEXT NOT NULL,
    generated_by_ai BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaign_messages_campaign_lead_id ON campaign_messages (campaign_lead_id);

CREATE TRIGGER trg_campaign_messages_updated_at
    BEFORE UPDATE ON campaign_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Generated messages (AI output store)
CREATE TABLE generated_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    channel message_channel NOT NULL,
    subject VARCHAR(512),
    body TEXT NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_generated_messages_lead_id ON generated_messages (lead_id);
CREATE INDEX idx_generated_messages_campaign_id ON generated_messages (campaign_id);
CREATE INDEX idx_generated_messages_channel ON generated_messages (channel);

CREATE TRIGGER trg_generated_messages_updated_at
    BEFORE UPDATE ON generated_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
