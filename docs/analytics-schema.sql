-- Create this schema in the dedicated Cloudflare D1 database only.
-- Do not run against CRM or any existing database.
CREATE TABLE IF NOT EXISTS analytics_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_name TEXT NOT NULL CHECK (event_name IN ('page_view', 'cta_click')),
  page_path TEXT NOT NULL CHECK (length(page_path) <= 64),
  source TEXT NOT NULL CHECK (source IN ('direct', 'search', 'social', 'referral', 'campaign', 'other')),
  device_class TEXT NOT NULL CHECK (device_class IN ('mobile', 'desktop', 'tablet', 'unknown')),
  cta_id TEXT NULL CHECK (cta_id IS NULL OR cta_id IN ('hero_launch', 'hero_features', 'nav_contact', 'footer_top')),
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS analytics_events_created_at_idx ON analytics_events(created_at);
CREATE INDEX IF NOT EXISTS analytics_events_page_idx ON analytics_events(page_path, created_at);
CREATE INDEX IF NOT EXISTS analytics_events_source_idx ON analytics_events(source, created_at);
