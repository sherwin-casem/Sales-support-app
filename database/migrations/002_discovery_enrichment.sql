-- Migration: 002_discovery_enrichment
-- Discovery profiles, crawl runs, lead extensions, intent signals

CREATE TYPE lead_source AS ENUM ('MANUAL', 'IMPORT', 'DISCOVERY');
CREATE TYPE crawl_run_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');
CREATE TYPE email_verification_status AS ENUM ('UNKNOWN', 'VALID_FORMAT', 'MX_FOUND', 'INVALID');
CREATE TYPE phone_verification_status AS ENUM ('UNKNOWN', 'VALID_FORMAT', 'INVALID');
CREATE TYPE intent_signal_type AS ENUM ('HIRING', 'EXPANSION', 'FUNDING', 'OTHER');

-- Discovery profiles
CREATE TABLE discovery_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    industries TEXT[] NOT NULL DEFAULT '{}',
    countries TEXT[] NOT NULL DEFAULT '{}',
    seed_urls TEXT[] NOT NULL DEFAULT '{}',
    crawl_depth INTEGER NOT NULL DEFAULT 2,
    max_pages INTEGER NOT NULL DEFAULT 50,
    schedule_cron VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_discovery_profiles_active ON discovery_profiles (is_active);
CREATE INDEX idx_discovery_profiles_created_by ON discovery_profiles (created_by);

CREATE TRIGGER trg_discovery_profiles_updated_at
    BEFORE UPDATE ON discovery_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Crawl runs
CREATE TABLE crawl_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES discovery_profiles(id) ON DELETE CASCADE,
    status crawl_run_status NOT NULL DEFAULT 'PENDING',
    pages_crawled INTEGER NOT NULL DEFAULT 0,
    leads_found INTEGER NOT NULL DEFAULT 0,
    leads_created INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    celery_task_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crawl_runs_profile_id ON crawl_runs (profile_id);
CREATE INDEX idx_crawl_runs_status ON crawl_runs (status);

CREATE TRIGGER trg_crawl_runs_updated_at
    BEFORE UPDATE ON crawl_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Lead extensions
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source lead_source NOT NULL DEFAULT 'MANUAL';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS domain_normalized VARCHAR(512);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS discovery_profile_id UUID REFERENCES discovery_profiles(id) ON DELETE SET NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_verification_status email_verification_status NOT NULL DEFAULT 'UNKNOWN';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_verification_status phone_verification_status NOT NULL DEFAULT 'UNKNOWN';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS intent_score INTEGER NOT NULL DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS duplicate_of_id UUID REFERENCES leads(id) ON DELETE SET NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX idx_leads_source ON leads (source);
CREATE INDEX idx_leads_domain_normalized ON leads (domain_normalized);
CREATE INDEX idx_leads_discovery_profile_id ON leads (discovery_profile_id);
CREATE INDEX idx_leads_intent_score ON leads (intent_score);
CREATE INDEX idx_leads_is_duplicate ON leads (is_duplicate);

ALTER TABLE decision_makers ADD COLUMN IF NOT EXISTS email_verification_status email_verification_status NOT NULL DEFAULT 'UNKNOWN';

-- Intent signals
CREATE TABLE intent_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    signal_type intent_signal_type NOT NULL,
    evidence TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 1,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_intent_signals_lead_id ON intent_signals (lead_id);
CREATE INDEX idx_intent_signals_type ON intent_signals (signal_type);

CREATE TRIGGER trg_intent_signals_updated_at
    BEFORE UPDATE ON intent_signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
