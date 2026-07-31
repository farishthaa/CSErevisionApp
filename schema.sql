-- SQL Script to set up database table in Supabase SQL Editor
-- This table tracks user completion, score, and submission history for the 90-day SDE portal.

CREATE TABLE IF NOT EXISTS sde_portal_progress (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    day_id VARCHAR(50) NOT NULL,
    completed BOOLEAN DEFAULT FALSE NOT NULL,
    score INT DEFAULT 0 NOT NULL,
    code_submission TEXT,
    feedback TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(user_id, day_id)
);

-- Index for fast user queries (e.g. loading all days for a specific user)
CREATE INDEX IF NOT EXISTS idx_sde_progress_user ON sde_portal_progress(user_id);

-- Index for searching progress on specific days
CREATE INDEX IF NOT EXISTS idx_sde_progress_day ON sde_portal_progress(day_id);

-- Enable Row Level Security (RLS) if you want to restrict access, or keep it public for dev testing.
-- Below is a policy to allow anyone to read and write (for development purposes).
ALTER TABLE sde_portal_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access" 
ON sde_portal_progress FOR SELECT 
USING (true);

CREATE POLICY "Allow public write access" 
ON sde_portal_progress FOR ALL 
USING (true) 
WITH CHECK (true);
