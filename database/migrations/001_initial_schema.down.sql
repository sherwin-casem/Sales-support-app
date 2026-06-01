-- Rollback: 001_initial_schema
-- Run manually to revert initial migration

DROP TRIGGER IF EXISTS trg_generated_messages_updated_at ON generated_messages;
DROP TRIGGER IF EXISTS trg_campaign_messages_updated_at ON campaign_messages;
DROP TRIGGER IF EXISTS trg_campaign_leads_updated_at ON campaign_leads;
DROP TRIGGER IF EXISTS trg_campaigns_updated_at ON campaigns;
DROP TRIGGER IF EXISTS trg_enrichment_records_updated_at ON enrichment_records;
DROP TRIGGER IF EXISTS trg_decision_makers_updated_at ON decision_makers;
DROP TRIGGER IF EXISTS trg_leads_updated_at ON leads;
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;

DROP TABLE IF EXISTS generated_messages;
DROP TABLE IF EXISTS campaign_messages;
DROP TABLE IF EXISTS campaign_leads;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS enrichment_records;
DROP TABLE IF EXISTS decision_makers;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS refresh_tokens;
DROP TABLE IF EXISTS users;

DROP FUNCTION IF EXISTS update_updated_at();

DROP TYPE IF EXISTS message_channel;
DROP TYPE IF EXISTS campaign_lead_status;
DROP TYPE IF EXISTS campaign_channel;
DROP TYPE IF EXISTS campaign_status;
DROP TYPE IF EXISTS lead_status;
DROP TYPE IF EXISTS user_role;
