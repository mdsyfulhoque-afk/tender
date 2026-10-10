"""Additive SQLite workflow schema v3; hosted DDL uses explicit migrations.

The frozen inputs and append-only outputs identify what each bounded run
actually used. Controller states remain mutable; no original approval or
source records are rewritten by this initializer.
"""
import hashlib
import sqlite3

from .database import ConfigurationError


_LOCAL_WORKFLOW_ID = 'tenderos_bounded_workflows_v3'
_WORKFLOW_TABLES = (
    'workflow_jobs', 'workflow_steps', 'workflow_artifacts',
    'workflow_events', 'workflow_candidate_reviews',
)

_LOCAL_WORKFLOW_STATEMENTS = (
    '''CREATE UNIQUE INDEX IF NOT EXISTS idx_tender_identity_org
       ON tenders(id,organization_id)''',
    '''CREATE TABLE workflow_jobs (
       id INTEGER PRIMARY KEY,
       tender_id INTEGER NOT NULL, organization_id INTEGER NOT NULL,
       workflow_kind TEXT NOT NULL CHECK (workflow_kind='READINESS_REVIEW'),
       processor_kind TEXT NOT NULL CHECK (processor_kind IN ('RULES','LOCAL_MODEL')),
       contract_version TEXT NOT NULL,
       state TEXT NOT NULL CHECK (state IN (
         'WAITING_INPUT','READY','RUNNING','WAITING_HUMAN','COMPLETED',
         'FAILED','CANCELLED','STALE','BUDGET_EXHAUSTED')),
       created_by TEXT NOT NULL,
       idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) BETWEEN 16 AND 128),
       request_sha256 TEXT NOT NULL CHECK (length(request_sha256)=64 AND request_sha256 NOT GLOB '*[^0-9a-f]*'),
       input_manifest TEXT NOT NULL,
       input_sha256 TEXT NOT NULL CHECK (length(input_sha256)=64 AND input_sha256 NOT GLOB '*[^0-9a-f]*'),
       policy_manifest TEXT NOT NULL,
       policy_sha256 TEXT NOT NULL CHECK (length(policy_sha256)=64 AND policy_sha256 NOT GLOB '*[^0-9a-f]*'),
       step_runs INTEGER NOT NULL DEFAULT 0 CHECK (typeof(step_runs)='integer' AND step_runs >= 0),
       elapsed_ms INTEGER NOT NULL DEFAULT 0 CHECK (typeof(elapsed_ms)='integer' AND elapsed_ms >= 0),
       external_model_calls INTEGER NOT NULL DEFAULT 0 CHECK (external_model_calls=0),
       model_spend_minor INTEGER NOT NULL DEFAULT 0 CHECK (model_spend_minor=0),
       cancel_requested INTEGER NOT NULL DEFAULT 0 CHECK (cancel_requested IN (0,1)),
       revision INTEGER NOT NULL DEFAULT 0 CHECK (typeof(revision)='integer' AND revision >= 0),
       restart_of_job_id INTEGER,
       last_error_code TEXT,
       created_at TEXT NOT NULL, updated_at TEXT NOT NULL, completed_at TEXT,
       UNIQUE (tender_id,idempotency_key), UNIQUE (id,tender_id),
       FOREIGN KEY (tender_id,organization_id) REFERENCES tenders(id,organization_id),
       FOREIGN KEY (restart_of_job_id,tender_id) REFERENCES workflow_jobs(id,tender_id)
    )''',
    '''CREATE TABLE workflow_steps (
       id INTEGER PRIMARY KEY,
       job_id INTEGER NOT NULL REFERENCES workflow_jobs(id),
       task_kind TEXT NOT NULL CHECK (task_kind IN (
         'SOURCE_INSPECT','REQUIREMENT_CANDIDATES','EVIDENCE_RELEVANCE','CITATION_CHECK')),
       task_key TEXT NOT NULL, contract_version TEXT NOT NULL, executor_label TEXT NOT NULL,
       state TEXT NOT NULL CHECK (state IN (
         'BLOCKED','READY','RUNNING','SUCCEEDED','FAILED','CANCELLED','STALE','NEEDS_OCR')),
       predecessor_step_id INTEGER,
       cursor_json TEXT NOT NULL DEFAULT '{}',
       attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (typeof(attempt_count)='integer' AND attempt_count BETWEEN 0 AND 2),
       lease_owner TEXT, lease_expires_at TEXT,
       fence INTEGER NOT NULL DEFAULT 0 CHECK (typeof(fence)='integer' AND fence >= 0),
       input_sha256 TEXT NOT NULL CHECK (length(input_sha256)=64 AND input_sha256 NOT GLOB '*[^0-9a-f]*'),
       elapsed_ms INTEGER NOT NULL DEFAULT 0 CHECK (typeof(elapsed_ms)='integer' AND elapsed_ms >= 0),
       last_error_code TEXT, started_at TEXT, completed_at TEXT,
       UNIQUE (job_id,task_key), UNIQUE (id,job_id),
       FOREIGN KEY (predecessor_step_id,job_id) REFERENCES workflow_steps(id,job_id)
    )''',
    '''CREATE TABLE workflow_artifacts (
       id INTEGER PRIMARY KEY,
       job_id INTEGER NOT NULL REFERENCES workflow_jobs(id), step_id INTEGER NOT NULL,
       artifact_key TEXT NOT NULL,
       artifact_kind TEXT NOT NULL CHECK (artifact_kind IN (
         'SOURCE_BATCH','REQUIREMENT_CANDIDATES','EVIDENCE_SUGGESTIONS','CITATION_CHECKS','RUN_RECEIPT')),
       schema_version TEXT NOT NULL,
       input_sha256 TEXT NOT NULL CHECK (length(input_sha256)=64 AND input_sha256 NOT GLOB '*[^0-9a-f]*'),
       payload_json TEXT NOT NULL,
       output_sha256 TEXT NOT NULL CHECK (length(output_sha256)=64 AND output_sha256 NOT GLOB '*[^0-9a-f]*'),
       created_at TEXT NOT NULL,
       UNIQUE (job_id,artifact_key), UNIQUE (id,job_id),
       FOREIGN KEY (step_id,job_id) REFERENCES workflow_steps(id,job_id)
    )''',
    '''CREATE TABLE workflow_events (
       id INTEGER PRIMARY KEY,
       job_id INTEGER NOT NULL REFERENCES workflow_jobs(id), step_id INTEGER,
       actor TEXT NOT NULL, action TEXT NOT NULL, event_json TEXT NOT NULL, created_at TEXT NOT NULL,
       FOREIGN KEY (step_id,job_id) REFERENCES workflow_steps(id,job_id)
    )''',
    '''CREATE TABLE workflow_candidate_reviews (
       id INTEGER PRIMARY KEY,
       job_id INTEGER NOT NULL REFERENCES workflow_jobs(id), artifact_id INTEGER NOT NULL,
       candidate_key TEXT NOT NULL,
       disposition TEXT NOT NULL CHECK (disposition IN ('ACCEPTED','REJECTED','DUPLICATE')),
       reviewer TEXT NOT NULL, note TEXT NOT NULL,
       requirement_id INTEGER REFERENCES requirements(id), reviewed_at TEXT NOT NULL,
       UNIQUE (job_id,candidate_key),
       FOREIGN KEY (artifact_id,job_id) REFERENCES workflow_artifacts(id,job_id)
    )''',
    'CREATE INDEX idx_workflow_jobs_tender ON workflow_jobs(tender_id,id)',
    'CREATE INDEX idx_workflow_steps_state ON workflow_steps(job_id,state,id)',
    'CREATE INDEX idx_workflow_events_job ON workflow_events(job_id,id)',
    '''CREATE TRIGGER workflow_jobs_frozen_inputs BEFORE UPDATE ON workflow_jobs
       WHEN OLD.id IS NOT NEW.id OR OLD.tender_id IS NOT NEW.tender_id
         OR OLD.organization_id IS NOT NEW.organization_id
         OR OLD.workflow_kind IS NOT NEW.workflow_kind OR OLD.processor_kind IS NOT NEW.processor_kind
         OR OLD.contract_version IS NOT NEW.contract_version OR OLD.created_by IS NOT NEW.created_by
         OR OLD.idempotency_key IS NOT NEW.idempotency_key OR OLD.request_sha256 IS NOT NEW.request_sha256
         OR OLD.input_manifest IS NOT NEW.input_manifest OR OLD.input_sha256 IS NOT NEW.input_sha256
         OR OLD.policy_manifest IS NOT NEW.policy_manifest OR OLD.policy_sha256 IS NOT NEW.policy_sha256
         OR OLD.restart_of_job_id IS NOT NEW.restart_of_job_id OR OLD.created_at IS NOT NEW.created_at
       BEGIN SELECT RAISE(ABORT,'Workflow inputs and identity are immutable'); END''',
    '''CREATE TRIGGER workflow_steps_frozen_inputs BEFORE UPDATE ON workflow_steps
       WHEN OLD.id IS NOT NEW.id OR OLD.job_id IS NOT NEW.job_id
         OR OLD.task_kind IS NOT NEW.task_kind OR OLD.task_key IS NOT NEW.task_key
         OR OLD.contract_version IS NOT NEW.contract_version OR OLD.executor_label IS NOT NEW.executor_label
         OR OLD.predecessor_step_id IS NOT NEW.predecessor_step_id OR OLD.input_sha256 IS NOT NEW.input_sha256
       BEGIN SELECT RAISE(ABORT,'Workflow task inputs and identity are immutable'); END''',
    '''CREATE TRIGGER workflow_review_requirement_scope BEFORE INSERT ON workflow_candidate_reviews
       WHEN NEW.requirement_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM requirements r JOIN workflow_jobs j ON r.tender_id=j.tender_id
         WHERE r.id=NEW.requirement_id AND j.id=NEW.job_id)
       BEGIN SELECT RAISE(ABORT,'Reviewed requirement must belong to the workflow tender'); END''',
    '''CREATE TRIGGER workflow_review_preserve_requirement_scope BEFORE UPDATE OF tender_id ON requirements
       WHEN EXISTS (
         SELECT 1 FROM workflow_candidate_reviews r JOIN workflow_jobs j ON j.id=r.job_id
         WHERE r.requirement_id=OLD.id AND j.tender_id<>NEW.tender_id)
       BEGIN SELECT RAISE(ABORT,'Reviewed requirement must remain in the workflow tender'); END''',
) + tuple(
    f'''CREATE TRIGGER {table}_no_{action.lower()} BEFORE {action} ON {table}
        BEGIN SELECT RAISE(ABORT,'Workflow history records are immutable'); END'''
    for table in ('workflow_artifacts', 'workflow_events', 'workflow_candidate_reviews')
    for action in ('UPDATE', 'DELETE')
)


def initialize_local_workflows(database):
    """Atomically add v3 to an initialized SQLite core/document registry.

    Repeated calls validate the recorded digest. An existing unversioned
    workflow table or changed migration digest requires an explicit migration;
    it is never silently repaired or backfilled. Hosted adapters are rejected.
    """
    if not isinstance(database, sqlite3.Connection):
        raise ConfigurationError('Local workflows require a SQLite connection')
    digest = hashlib.sha256('\n'.join(_LOCAL_WORKFLOW_STATEMENTS).encode('utf-8')).hexdigest()
    database.execute('SAVEPOINT tenderos_local_workflows')
    try:
        database.execute('''CREATE TABLE IF NOT EXISTS tenderos_local_schema_migrations (
            migration_id TEXT PRIMARY KEY, schema_sha256 TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )''')
        prior = database.execute(
            'SELECT schema_sha256 FROM tenderos_local_schema_migrations WHERE migration_id=?',
            (_LOCAL_WORKFLOW_ID,),
        ).fetchone()
        if prior and prior[0] != digest:
            raise ConfigurationError('Local schema digest differs; an explicit migration is required')
        if not prior:
            placeholders = ','.join('?' for _ in _WORKFLOW_TABLES)
            existing = database.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({placeholders})",
                _WORKFLOW_TABLES,
            ).fetchone()
            if existing:
                raise ConfigurationError('Unversioned workflow tables require explicit migration')
            for statement in _LOCAL_WORKFLOW_STATEMENTS:
                database.execute(statement)
            database.execute(
                'INSERT INTO tenderos_local_schema_migrations(migration_id,schema_sha256) VALUES(?,?)',
                (_LOCAL_WORKFLOW_ID, digest),
            )
        database.execute('RELEASE SAVEPOINT tenderos_local_workflows')
    except Exception:
        database.execute('ROLLBACK TO SAVEPOINT tenderos_local_workflows')
        database.execute('RELEASE SAVEPOINT tenderos_local_workflows')
        raise
