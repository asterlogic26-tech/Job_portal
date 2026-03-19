-- Enum Types
-- Must run before schema creation

CREATE TYPE application_status AS ENUM (
    'saved',
    'applying',
    'applied',
    'phone_screen',
    'technical_interview',
    'onsite_interview',
    'offer',
    'accepted',
    'rejected',
    'withdrawn',
    'ghosted'
);

CREATE TYPE remote_policy AS ENUM (
    'remote',
    'hybrid',
    'onsite',
    'flexible'
);

CREATE TYPE seniority_level AS ENUM (
    'intern',
    'junior',
    'mid',
    'senior',
    'staff',
    'principal',
    'director',
    'vp',
    'c_level'
);

CREATE TYPE content_type AS ENUM (
    'cover_letter',
    'linkedin_post',
    'outreach_email',
    'follow_up_email',
    'thank_you_note',
    'connection_request'
);

CREATE TYPE content_status AS ENUM (
    'draft',
    'approved',
    'sent',
    'archived'
);

CREATE TYPE notification_type AS ENUM (
    'high_match',
    'daily_digest',
    'follow_up_reminder',
    'profile_health',
    'manual_task',
    'application_update',
    'content_ready',
    'general'
);

CREATE TYPE manual_task_type AS ENUM (
    'manual_apply',
    'captcha_solve',
    'login_required',
    'verify_identity',
    'follow_up',
    'research'
);

CREATE TYPE manual_task_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'skipped'
);

CREATE TYPE signal_type AS ENUM (
    'funding_round',
    'job_velocity_spike',
    'news_mention',
    'leadership_change',
    'product_launch',
    'expansion'
);
