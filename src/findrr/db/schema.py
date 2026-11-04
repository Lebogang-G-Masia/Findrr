"""SQLite relational database schema definitions."""

SCHEMA_SQL = """
-- Core Profile & Search Configuration Tables

CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    location TEXT,
    professional_summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profile_entries (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    organization TEXT,
    start_date TEXT,
    end_date TEXT,
    description TEXT,
    metadata_json TEXT,
    source TEXT NOT NULL,
    collection_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_verified INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_profile_entries_cat
ON profile_entries(profile_id, category);

CREATE TABLE IF NOT EXISTS generalized_titles (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    primary_title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    supporting_skills TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_configurations (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL UNIQUE,
    target_locations TEXT NOT NULL,
    remote_preference TEXT NOT NULL,
    seniority_level TEXT,
    min_compensation REAL,
    currency TEXT DEFAULT 'USD',
    min_results_per_title INTEGER NOT NULL DEFAULT 2,
    max_results_per_title INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
    CHECK (
        min_results_per_title >= 2 AND
        max_results_per_title <= 10 AND
        min_results_per_title <= max_results_per_title
    )
);

CREATE TABLE IF NOT EXISTS search_terms (
    id TEXT PRIMARY KEY,
    generalized_title_id TEXT NOT NULL,
    generated_term TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    validation_status TEXT NOT NULL,
    model_version TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generalized_title_id) REFERENCES generalized_titles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_search_terms_status
ON search_terms(generalized_title_id, validation_status);

CREATE TABLE IF NOT EXISTS job_postings (
    id TEXT PRIMARY KEY,
    search_term_id TEXT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT NOT NULL,
    requirements_extracted TEXT,
    source_url TEXT NOT NULL,
    direct_apply_url TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    posting_date TEXT,
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (search_term_id) REFERENCES search_terms(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_job_postings_hash
ON job_postings(content_hash);

CREATE TABLE IF NOT EXISTS application_records (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    job_posting_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    applied_at TIMESTAMP,
    notes TEXT,
    contact_person TEXT,
    contact_email TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (job_posting_id) REFERENCES job_postings(id) ON DELETE CASCADE,
    CHECK (
        status IN (
            'DISCOVERED', 'SAVED', 'APPLIED',
            'INTERVIEWING', 'OFFERED', 'REJECTED', 'WITHDRAWN'
        )
    )
);

CREATE TABLE IF NOT EXISTS application_documents (
    id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_text TEXT NOT NULL,
    model_version TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES application_records(id) ON DELETE CASCADE,
    CHECK (document_type IN ('TAILORED_CV', 'COVER_LETTER', 'COMPANY_RESEARCH'))
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    module TEXT NOT NULL,
    details_json TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
