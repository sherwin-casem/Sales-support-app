DROP TRIGGER IF EXISTS trg_intent_signals_updated_at ON intent_signals;
DROP TABLE IF EXISTS intent_signals;

ALTER TABLE decision_makers DROP COLUMN IF EXISTS email_verification_status;

ALTER TABLE leads DROP COLUMN IF EXISTS is_duplicate;
ALTER TABLE leads DROP COLUMN IF EXISTS duplicate_of_id;
ALTER TABLE leads DROP COLUMN IF EXISTS intent_score;
ALTER TABLE leads DROP COLUMN IF EXISTS email_verified_at;
ALTER TABLE leads DROP COLUMN IF EXISTS phone_verification_status;
ALTER TABLE leads DROP COLUMN IF EXISTS email_verification_status;
ALTER TABLE leads DROP COLUMN IF EXISTS discovery_profile_id;
ALTER TABLE leads DROP COLUMN IF EXISTS domain_normalized;
ALTER TABLE leads DROP COLUMN IF EXISTS source;

DROP TRIGGER IF EXISTS trg_crawl_runs_updated_at ON crawl_runs;
DROP TABLE IF EXISTS crawl_runs;

DROP TRIGGER IF EXISTS trg_discovery_profiles_updated_at ON discovery_profiles;
DROP TABLE IF EXISTS discovery_profiles;

DROP TYPE IF EXISTS intent_signal_type;
DROP TYPE IF EXISTS phone_verification_status;
DROP TYPE IF EXISTS email_verification_status;
DROP TYPE IF EXISTS crawl_run_status;
DROP TYPE IF EXISTS lead_source;
