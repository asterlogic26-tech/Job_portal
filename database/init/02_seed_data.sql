-- Default single-user profile seed
-- This runs only if the table exists and the row is not already present
INSERT INTO user_profile (
    id,
    full_name,
    current_title,
    target_titles,
    skills,
    experience_years,
    location,
    remote_preference,
    target_salary_min,
    target_salary_max,
    linkedin_url,
    github_url,
    preferences,
    created_at,
    updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Job Seeker',
    'Software Engineer',
    ARRAY['Software Engineer', 'Senior Software Engineer', 'Full Stack Developer'],
    '[{"name": "Python", "level": "expert", "years": 5}, {"name": "React", "level": "intermediate", "years": 3}, {"name": "PostgreSQL", "level": "intermediate", "years": 3}, {"name": "Docker", "level": "intermediate", "years": 2}]'::jsonb,
    5,
    'Remote',
    'remote',
    100000,
    180000,
    '',
    '',
    '{"notify_high_match": true, "notify_digest": true, "min_match_score": 50}'::jsonb,
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;
