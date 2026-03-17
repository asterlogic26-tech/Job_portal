-- Reference schema for documentation purposes.
-- In production, Alembic manages migrations.
-- This file can be used to inspect the intended schema.

CREATE TABLE IF NOT EXISTS user_profile (
    id              UUID PRIMARY KEY,
    full_name       VARCHAR(255) NOT NULL,
    current_title   VARCHAR(255) DEFAULT '',
    target_titles   TEXT[] DEFAULT '{}',
    skills          JSONB DEFAULT '[]',
    experience_years INTEGER DEFAULT 0,
    location        VARCHAR(255) DEFAULT 'Remote',
    remote_preference VARCHAR(50) DEFAULT 'remote',
    target_salary_min INTEGER,
    target_salary_max INTEGER,
    linkedin_url    TEXT DEFAULT '',
    github_url      TEXT DEFAULT '',
    resume_url      TEXT,
    bio             TEXT DEFAULT '',
    preferences     JSONB DEFAULT '{}',
    profile_embedding_id VARCHAR(255),
    health_score    INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     VARCHAR(512) UNIQUE NOT NULL,
    source          VARCHAR(100) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    normalized_title VARCHAR(512) DEFAULT '',
    company_name    VARCHAR(255) NOT NULL,
    company_id      UUID REFERENCES companies(id),
    description     TEXT DEFAULT '',
    description_html TEXT DEFAULT '',
    location        VARCHAR(255) DEFAULT '',
    remote_policy   VARCHAR(50) DEFAULT 'unknown',
    seniority_level VARCHAR(50) DEFAULT 'unknown',
    salary_min      INTEGER,
    salary_max      INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    required_skills JSONB DEFAULT '[]',
    preferred_skills JSONB DEFAULT '[]',
    url             TEXT NOT NULL,
    apply_url       TEXT DEFAULT '',
    posted_at       VARCHAR(100),
    raw_data        JSONB DEFAULT '{}',
    embedding_id    VARCHAR(255),
    is_hidden       BOOLEAN DEFAULT FALSE,
    is_saved        BOOLEAN DEFAULT FALSE,
    is_applied      BOOLEAN DEFAULT FALSE,
    is_duplicate    BOOLEAN DEFAULT FALSE,
    content_hash    VARCHAR(64) DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_company_name ON jobs(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_remote_policy ON jobs(remote_policy);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_is_hidden ON jobs(is_hidden);

CREATE TABLE IF NOT EXISTS job_matches (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id              UUID UNIQUE NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL,
    total_score         FLOAT DEFAULT 0,
    skill_score         FLOAT DEFAULT 0,
    seniority_score     FLOAT DEFAULT 0,
    salary_score        FLOAT DEFAULT 0,
    recency_score       FLOAT DEFAULT 0,
    culture_score       FLOAT DEFAULT 0,
    company_growth_score FLOAT DEFAULT 0,
    interview_probability FLOAT DEFAULT 0,
    matching_skills     JSONB DEFAULT '[]',
    missing_skills      JSONB DEFAULT '[]',
    score_breakdown     JSONB DEFAULT '{}',
    user_rating         INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_matches_total_score ON job_matches(total_score DESC);

CREATE TABLE IF NOT EXISTS applications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID REFERENCES jobs(id) ON DELETE SET NULL,
    user_id         UUID NOT NULL,
    status          VARCHAR(50) DEFAULT 'saved',
    applied_at      TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    follow_up_at    TIMESTAMPTZ,
    notes           TEXT DEFAULT '',
    resume_version_url TEXT DEFAULT '',
    cover_letter_id UUID,
    interview_date  TIMESTAMPTZ,
    offer_amount    INTEGER,
    custom_fields   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) UNIQUE NOT NULL,
    normalized_name VARCHAR(255) DEFAULT '',
    domain          VARCHAR(255) DEFAULT '',
    website         TEXT DEFAULT '',
    linkedin_url    TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    industry        VARCHAR(255) DEFAULT '',
    size_range      VARCHAR(50) DEFAULT '',
    stage           VARCHAR(50) DEFAULT '',
    founded_year    INTEGER,
    headquarters    VARCHAR(255) DEFAULT '',
    hiring_score    FLOAT DEFAULT 0,
    job_velocity    FLOAT DEFAULT 0,
    is_watched      BOOLEAN DEFAULT FALSE,
    total_funding_usd INTEGER,
    last_funding_round VARCHAR(100) DEFAULT '',
    last_funding_amount_usd INTEGER,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_signals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    signal_type VARCHAR(50) NOT NULL,
    title       VARCHAR(512) DEFAULT '',
    summary     TEXT DEFAULT '',
    source_url  TEXT DEFAULT '',
    amount_usd  INTEGER,
    signal_date TIMESTAMPTZ,
    raw_data    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    content_type    VARCHAR(50) NOT NULL,
    status          VARCHAR(50) DEFAULT 'draft',
    title           VARCHAR(512) DEFAULT '',
    body            TEXT DEFAULT '',
    subject         VARCHAR(512) DEFAULT '',
    job_id          UUID,
    company_id      UUID,
    application_id  UUID,
    prompt_used     TEXT DEFAULT '',
    model_used      VARCHAR(100) DEFAULT '',
    generation_metadata JSONB DEFAULT '{}',
    is_approved     BOOLEAN DEFAULT FALSE,
    approved_at     VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    notification_type   VARCHAR(50) NOT NULL,
    title               VARCHAR(512) NOT NULL,
    body                TEXT DEFAULT '',
    is_read             BOOLEAN DEFAULT FALSE,
    priority            VARCHAR(20) DEFAULT 'normal',
    action_url          TEXT DEFAULT '',
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read);

CREATE TABLE IF NOT EXISTS manual_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    task_type       VARCHAR(50) NOT NULL,
    status          VARCHAR(50) DEFAULT 'pending',
    title           VARCHAR(512) NOT NULL,
    description     TEXT DEFAULT '',
    site_url        TEXT DEFAULT '',
    instructions    TEXT DEFAULT '',
    context_data    JSONB DEFAULT '{}',
    completed_at    TIMESTAMPTZ,
    completion_notes TEXT DEFAULT '',
    job_id          UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recruiter_contacts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    title       VARCHAR(255) DEFAULT '',
    company_name VARCHAR(255) DEFAULT '',
    email       VARCHAR(255) DEFAULT '',
    linkedin_url TEXT DEFAULT '',
    is_outreached BOOLEAN DEFAULT FALSE,
    notes       TEXT DEFAULT '',
    job_id      UUID,
    extra       JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS network_connections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    full_name           VARCHAR(255) NOT NULL,
    current_company     VARCHAR(255) DEFAULT '',
    title               VARCHAR(255) DEFAULT '',
    linkedin_url        TEXT DEFAULT '',
    relationship_strength FLOAT DEFAULT 0.5,
    notes               TEXT DEFAULT '',
    can_refer           BOOLEAN DEFAULT FALSE,
    extra               JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
