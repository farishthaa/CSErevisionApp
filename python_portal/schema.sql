-- Database schema definition for the Python Teaching Portal
-- Execute this SQL script in your Supabase SQL Editor.

CREATE TABLE IF NOT EXISTS public.python_portal_progress (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id character varying NOT NULL,
    day_id character varying NOT NULL,
    completed boolean NOT NULL DEFAULT false,
    score integer NOT NULL DEFAULT 0,
    code_submission text,
    feedback text,
    created_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT python_portal_progress_pkey PRIMARY KEY (id),
    CONSTRAINT python_portal_progress_user_id_day_id_key UNIQUE (user_id, day_id)
);

-- Enable Row-Level Security (RLS)
ALTER TABLE public.python_portal_progress ENABLE ROW LEVEL SECURITY;

-- Create public read/write RLS policies for rapid deployment.
-- NOTE: Refer to sde_portal_project_report.md for threat details and guidelines on restricting these policies in production.
CREATE POLICY "Allow public read access" ON public.python_portal_progress FOR SELECT USING (true);
CREATE POLICY "Allow public insert access" ON public.python_portal_progress FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access" ON public.python_portal_progress FOR UPDATE USING (true);
CREATE POLICY "Allow public delete access" ON public.python_portal_progress FOR DELETE USING (true);
