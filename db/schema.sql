CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    dog_id TEXT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    run_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id),
    run_kind TEXT NOT NULL,
    status TEXT NOT NULL,
    manifest JSONB NOT NULL,
    input_asset_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    execution_plan JSONB NULL,
    stage_results JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    error JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_session_created ON runs (session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs (status);

CREATE TABLE IF NOT EXISTS run_events (
    event_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(run_id),
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_run_events_run_created ON run_events (run_id, created_at ASC);

CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    session_id UUID NULL REFERENCES sessions(session_id),
    run_id UUID NULL REFERENCES runs(run_id),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB NULL,
    error JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status_type ON jobs (status, job_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_session_created ON jobs (session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_run_created ON jobs (run_id, created_at DESC);

CREATE TABLE IF NOT EXISTS assets (
    asset_id UUID PRIMARY KEY,
    run_id UUID NULL REFERENCES runs(run_id),
    session_id UUID NULL REFERENCES sessions(session_id),
    kind TEXT NOT NULL,
    blob_path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/json',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (run_id, kind, blob_path),
    UNIQUE (run_id, checksum)
);

CREATE INDEX IF NOT EXISTS idx_assets_run_kind ON assets (run_id, kind);
CREATE INDEX IF NOT EXISTS idx_assets_session_kind ON assets (session_id, kind);

CREATE TABLE IF NOT EXISTS metric_definitions (
    metric_definition_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL,
    config_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS metric_results (
    metric_result_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(run_id),
    metric_definition_id UUID NOT NULL REFERENCES metric_definitions(metric_definition_id),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metric_results_run_metric ON metric_results (run_id, metric_definition_id);

CREATE TABLE IF NOT EXISTS formula_definitions (
    formula_definition_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT NOT NULL,
    input_requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution_spec JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS formula_proposals (
    formula_proposal_id UUID PRIMARY KEY,
    formula_definition_id UUID NULL REFERENCES formula_definitions(formula_definition_id),
    source_run_id UUID NULL REFERENCES runs(run_id),
    research_question TEXT NOT NULL,
    proposal_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_formula_proposals_definition ON formula_proposals (formula_definition_id, created_at DESC);

CREATE TABLE IF NOT EXISTS formula_evaluations (
    formula_evaluation_id UUID PRIMARY KEY,
    formula_definition_id UUID NOT NULL REFERENCES formula_definitions(formula_definition_id),
    run_id UUID NOT NULL REFERENCES runs(run_id),
    dataset_ref TEXT NULL,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_formula_evaluations_definition ON formula_evaluations (formula_definition_id, created_at DESC);

CREATE TABLE IF NOT EXISTS formula_reviews (
    formula_review_id UUID PRIMARY KEY,
    formula_definition_id UUID NOT NULL REFERENCES formula_definitions(formula_definition_id),
    formula_evaluation_id UUID NULL REFERENCES formula_evaluations(formula_evaluation_id),
    reviewer_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    notes TEXT NOT NULL,
    evidence_bundle JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_formula_reviews_definition ON formula_reviews (formula_definition_id, created_at DESC);
