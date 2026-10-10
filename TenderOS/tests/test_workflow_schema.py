"""Behavior checks for additive workflow persistence, without remote services."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from app.database import ConfigurationError, _Connection, initialize_local_extensions
from app import workflow_schema as schema


ROOT = Path(__file__).resolve().parents[1]
HASH = 'a' * 64
STAMP = '2026-10-09T20:00:00+00:00'


def core_sql():
    """Read unchanged core literal without importing the application/server."""
    tree = ast.parse((ROOT / 'app/main.py').read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'SCHEMA' for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError('Core schema literal is missing')


@pytest.fixture
def db():
    database = sqlite3.connect(':memory:')
    database.execute('PRAGMA foreign_keys=ON')
    database.executescript(core_sql())
    initialize_local_extensions(database)
    schema.initialize_local_workflows(database)
    database.execute('INSERT INTO organizations(id,name,created_at) VALUES(1,?,?)', ('Org A', STAMP))
    database.execute('INSERT INTO organizations(id,name,created_at) VALUES(2,?,?)', ('Org B', STAMP))
    for tender, organization in ((1, 1), (2, 1), (3, 2)):
        database.execute('INSERT INTO tenders(id,organization_id,title,created_at) VALUES(?,?,?,?)',
                         (tender, organization, f'Tender {tender}', STAMP))
    yield database
    database.close()


def add_job(db, tender=1, organization=1, key=None, **changes):
    values = dict(tender_id=tender, organization_id=organization,
                  workflow_kind='READINESS_REVIEW', processor_kind='RULES',
                  contract_version='rules_workflow_v1', state='READY', created_by='owner',
                  idempotency_key=key or f'job-{tender}-unique-key-0001', request_sha256=HASH,
                  input_manifest='{"version":1}', input_sha256=HASH,
                  policy_manifest='{"spend":0}', policy_sha256=HASH,
                  created_at=STAMP, updated_at=STAMP)
    values.update(changes)
    columns = ','.join(values)
    marks = ','.join('?' for _ in values)
    return db.execute(f'INSERT INTO workflow_jobs({columns}) VALUES({marks})',
                      tuple(values.values())).lastrowid


def add_step(db, job, key='source', **changes):
    values = dict(job_id=job, task_kind='SOURCE_INSPECT', task_key=key,
                  contract_version='rules_v1', executor_label='Local rules',
                  state='READY', input_sha256=HASH)
    values.update(changes)
    return db.execute(
        f"INSERT INTO workflow_steps({','.join(values)}) VALUES({','.join('?' for _ in values)})",
        tuple(values.values()),
    ).lastrowid


def add_artifact(db, job, step, key='page-1'):
    return db.execute('''INSERT INTO workflow_artifacts(job_id,step_id,artifact_key,artifact_kind,
        schema_version,input_sha256,payload_json,output_sha256,created_at)
        VALUES(?,?,?,'SOURCE_BATCH','source_v1',?,'{}',?,?)''',
        (job, step, key, HASH, HASH, STAMP)).lastrowid


def add_requirement(db, tender=1):
    return db.execute('''INSERT INTO requirements(tender_id,text,extraction_method,created_at,updated_at)
        VALUES(?,'Requirement','manual',?,?)''', (tender, STAMP, STAMP)).lastrowid


def add_review(db, job, artifact, key='candidate-1', requirement=None):
    return db.execute('''INSERT INTO workflow_candidate_reviews(job_id,artifact_id,candidate_key,
        disposition,reviewer,note,requirement_id,reviewed_at)
        VALUES(?,?,?,'ACCEPTED','owner','Checked source',?,?)''',
        (job, artifact, key, requirement, STAMP)).lastrowid


def test_fresh_migration_is_atomic_repeatable_and_preserves_existing_records():
    database = sqlite3.connect(':memory:')
    database.executescript(core_sql())
    database.execute('INSERT INTO organizations VALUES(1,?,?)', ('Historical organization', STAMP))
    database.execute('INSERT INTO tenders(id,organization_id,title,created_at) VALUES(1,1,?,?)',
                     ('Historical assessment', STAMP))
    database.execute('''INSERT INTO decisions(tender_id,decision,reviewer,rationale,decision_snapshot,created_at)
        VALUES(1,'HOLD','Human','Historical hold','{"historical":true}',?)''', (STAMP,))
    before = database.execute('SELECT * FROM decisions').fetchall()
    initialize_local_extensions(database)
    v2_before = database.execute('SELECT * FROM tenderos_local_schema_migrations').fetchall()
    schema.initialize_local_workflows(database)
    schema.initialize_local_workflows(database)
    assert database.execute('SELECT * FROM decisions').fetchall() == before
    markers = database.execute('SELECT * FROM tenderos_local_schema_migrations ORDER BY migration_id').fetchall()
    assert len(markers) == 2
    assert next(row for row in markers if row[0] == v2_before[0][0]) == v2_before[0]
    assert database.execute('SELECT count(*) FROM workflow_jobs').fetchone()[0] == 0
    assert database.execute('PRAGMA foreign_key_check').fetchall() == []
    database.close()


def test_digest_change_is_refused_without_schema_rewrite(db, monkeypatch):
    before = db.execute('SELECT * FROM tenderos_local_schema_migrations').fetchall()
    monkeypatch.setattr(schema, '_LOCAL_WORKFLOW_STATEMENTS',
                        schema._LOCAL_WORKFLOW_STATEMENTS + ('CREATE TABLE forbidden(id INTEGER)',))
    with pytest.raises(ConfigurationError, match='digest differs'):
        schema.initialize_local_workflows(db)
    assert db.execute("SELECT name FROM sqlite_master WHERE name='forbidden'").fetchone() is None
    assert db.execute('SELECT * FROM tenderos_local_schema_migrations').fetchall() == before


def test_unversioned_partial_schema_is_refused():
    database = sqlite3.connect(':memory:')
    database.executescript(core_sql())
    initialize_local_extensions(database)
    database.execute('CREATE TABLE workflow_events(id INTEGER PRIMARY KEY, legacy TEXT)')
    database.execute("INSERT INTO workflow_events VALUES(1,'untouched')")
    with pytest.raises(ConfigurationError, match='Unversioned workflow'):
        schema.initialize_local_workflows(database)
    assert database.execute('SELECT * FROM workflow_events').fetchall() == [(1, 'untouched')]
    assert database.execute('SELECT 1 FROM tenderos_local_schema_migrations WHERE migration_id=?',
                            (schema._LOCAL_WORKFLOW_ID,)).fetchone() is None
    database.close()


def test_failure_rolls_back_all_extension_ddl_and_marker(monkeypatch):
    database = sqlite3.connect(':memory:')
    database.executescript(core_sql())
    initialize_local_extensions(database)
    monkeypatch.setattr(schema, '_LOCAL_WORKFLOW_STATEMENTS',
                        schema._LOCAL_WORKFLOW_STATEMENTS + ('INVALID SQL',))
    with pytest.raises(sqlite3.OperationalError):
        schema.initialize_local_workflows(database)
    assert database.execute("SELECT name FROM sqlite_master WHERE name LIKE 'workflow_%'").fetchall() == []
    assert database.execute('SELECT 1 FROM tenderos_local_schema_migrations WHERE migration_id=?',
                            (schema._LOCAL_WORKFLOW_ID,)).fetchone() is None
    database.close()


def test_initializer_uses_caller_transaction(db):
    db.rollback()
    db.execute('CREATE TABLE caller_record(id INTEGER)')
    db.execute('INSERT INTO caller_record VALUES(1)')
    schema.initialize_local_workflows(db)
    db.rollback()
    assert db.execute('SELECT * FROM caller_record').fetchall() == []


def test_hosted_adapter_cannot_apply_local_ddl():
    with pytest.raises(ConfigurationError, match='SQLite'):
        schema.initialize_local_workflows(object())


def test_job_scope_and_restart_scope_are_enforced(db):
    original = add_job(db)
    with pytest.raises(sqlite3.IntegrityError):
        add_job(db, tender=1, organization=2, key='incorrect-org-000001')
    with pytest.raises(sqlite3.IntegrityError):
        add_job(db, tender=2, restart_of_job_id=original)
    restarted = add_job(db, key='restart-key-00000001', restart_of_job_id=original)
    assert restarted != original


def test_duplicate_job_idempotency_key_rejected_only_within_tender(db):
    add_job(db, key='shared-client-key-0001')
    with pytest.raises(sqlite3.IntegrityError):
        add_job(db, key='shared-client-key-0001')
    assert add_job(db, tender=2, key='shared-client-key-0001')


@pytest.mark.parametrize('field,value', [
    ('input_manifest','{"replaced":true}'), ('input_sha256','b'*64),
    ('policy_manifest','{"spend":100}'), ('policy_sha256','b'*64),
    ('created_by','worker'), ('contract_version','changed'),
    ('processor_kind','LOCAL_MODEL'), ('request_sha256','b'*64),
    ('idempotency_key','replacement-key-00001'), ('created_at','later'),
    ('restart_of_job_id',1), ('organization_id',2), ('tender_id',2),
])
def test_frozen_job_inputs_cannot_be_rewritten(db, field, value):
    job = add_job(db)
    before = db.execute('SELECT * FROM workflow_jobs WHERE id=?', (job,)).fetchone()
    with pytest.raises(sqlite3.IntegrityError, match='immutable'):
        db.execute(f'UPDATE workflow_jobs SET {field}=? WHERE id=?', (value, job))
    assert db.execute('SELECT * FROM workflow_jobs WHERE id=?', (job,)).fetchone() == before


def test_job_controller_can_update_state_and_reserved_budgets(db):
    job = add_job(db)
    db.execute('''UPDATE workflow_jobs SET state='RUNNING',revision=1,step_runs=1,
        elapsed_ms=15000,updated_at=? WHERE id=?''', (STAMP, job))
    db.execute("UPDATE workflow_jobs SET elapsed_ms=321,state='WAITING_HUMAN',revision=2 WHERE id=?", (job,))
    assert db.execute('SELECT state,elapsed_ms,revision FROM workflow_jobs WHERE id=?',
                      (job,)).fetchone() == ('WAITING_HUMAN', 321, 2)


@pytest.mark.parametrize('field,value', [
    ('external_model_calls',1), ('model_spend_minor',1),
    ('step_runs',-1), ('elapsed_ms',-1), ('revision',-1),
    ('elapsed_ms',0.5), ('state','APPROVED'), ('cancel_requested',2),
])
def test_invalid_job_budget_or_state_is_refused(db, field, value):
    job = add_job(db)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(f'UPDATE workflow_jobs SET {field}=? WHERE id=?', (value, job))


@pytest.mark.parametrize('hash_value', ['A'*64, 'x'*64, 'a'*63, 'a'*65, ''])
def test_invalid_hash_is_refused(db, hash_value):
    with pytest.raises(sqlite3.IntegrityError):
        add_job(db, input_sha256=hash_value)


def test_step_scope_immutability_and_mutable_leases(db):
    first_job, second_job = add_job(db), add_job(db, tender=2)
    step = add_step(db, first_job)
    with pytest.raises(sqlite3.IntegrityError):
        add_step(db, second_job, predecessor_step_id=step)
    with pytest.raises(sqlite3.IntegrityError, match='immutable'):
        db.execute('UPDATE workflow_steps SET input_sha256=? WHERE id=?', ('b'*64, step))
    db.execute('''UPDATE workflow_steps SET state='RUNNING',cursor_json='{"next":1}',
        attempt_count=1,lease_owner='attempt-1',lease_expires_at=?,fence=1 WHERE id=?''', (STAMP, step))
    assert db.execute('SELECT state,fence FROM workflow_steps WHERE id=?', (step,)).fetchone() == ('RUNNING',1)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute('UPDATE workflow_steps SET attempt_count=3 WHERE id=?', (step,))


def test_artifact_and_event_cannot_link_step_from_another_job(db):
    first_job, second_job = add_job(db), add_job(db, tender=2)
    first_step, second_step = add_step(db, first_job), add_step(db, second_job)
    with pytest.raises(sqlite3.IntegrityError):
        add_artifact(db, first_job, second_step)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute('''INSERT INTO workflow_events(job_id,step_id,actor,action,event_json,created_at)
            VALUES(?,?,'SYSTEM','ATTEMPT','{}',?)''', (first_job, second_step, STAMP))
    assert add_artifact(db, first_job, first_step)


@pytest.mark.parametrize('table', ['workflow_artifacts','workflow_events','workflow_candidate_reviews'])
@pytest.mark.parametrize('operation', ['UPDATE','DELETE'])
def test_workflow_outputs_and_review_receipts_are_append_only(db, table, operation):
    job = add_job(db)
    step = add_step(db, job)
    artifact = add_artifact(db, job, step)
    db.execute('''INSERT INTO workflow_events(job_id,actor,action,event_json,created_at)
        VALUES(?,'SYSTEM','PUBLISHED','{}',?)''', (job, STAMP))
    add_review(db, job, artifact, requirement=add_requirement(db))
    before = db.execute(f'SELECT * FROM {table}').fetchall()
    statement = f'UPDATE {table} SET id=id' if operation == 'UPDATE' else f'DELETE FROM {table}'
    with pytest.raises(sqlite3.IntegrityError, match='immutable'):
        db.execute(statement)
    assert db.execute(f'SELECT * FROM {table}').fetchall() == before


def test_candidate_requirement_and_artifact_scope_and_duplicate_acceptance(db):
    job = add_job(db)
    step = add_step(db, job)
    artifact = add_artifact(db, job, step)
    other_job = add_job(db, tender=2)
    other_artifact = add_artifact(db, other_job, add_step(db, other_job))
    with pytest.raises(sqlite3.IntegrityError):
        add_review(db, job, other_artifact)
    foreign_requirement = add_requirement(db, tender=2)
    with pytest.raises(sqlite3.IntegrityError, match='workflow tender'):
        add_review(db, job, artifact, requirement=foreign_requirement)
    requirement = add_requirement(db)
    add_review(db, job, artifact, requirement=requirement)
    with pytest.raises(sqlite3.IntegrityError):
        add_review(db, job, artifact, requirement=requirement)
    with pytest.raises(sqlite3.IntegrityError, match='workflow tender'):
        db.execute('UPDATE requirements SET tender_id=2 WHERE id=?', (requirement,))


@pytest.mark.parametrize('table', list(schema._WORKFLOW_TABLES) +
                         ['service_intakes','commercial_ledger','diagnostic_releases'])
def test_postgres_adapter_returns_ids_for_new_registered_tables(table):
    queries = []
    class RawDatabase:
        def execute(self, query, parameters):
            queries.append((query, parameters))
            return SimpleNamespace(fetchone=lambda: {'id': 42}, rowcount=1)
    cursor = _Connection(RawDatabase()).execute(f'INSERT INTO {table}(id) VALUES(?)', (42,))
    assert cursor.lastrowid == 42
    assert queries == [(f'INSERT INTO {table}(id) VALUES(%s) RETURNING id', (42,))]


def test_prior_postgres_sql_digests_are_unchanged():
    expected = {
        'scripts/postgres_schema.sql': '92dab3cbda0388c278f06ca7610a0b53bde2b13edff3bed770b4f709093a268e',
        'scripts/postgres_migrations/002_document_registry.sql':
            '3e10701dc7ce074663fa3ab051e8ee4c3ebc9be51a0d02fb7dd4341b0d2bc5c7',
    }
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def migration_module():
    spec = importlib.util.spec_from_file_location('workflow_migration_script', ROOT / 'scripts/migrate_postgres.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MigrationDatabase:
    """Record the explicit CLI transaction contract, never contact a database."""
    def __init__(self, markers=None, existing_tables=()):
        self.markers = dict(markers or {})
        self.existing_tables = set(existing_tables)
        self.operations = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def transaction(self):
        return self
    def execute(self, query, parameters=None):
        self.operations.append((query, parameters))
        if query.startswith('SELECT schema_sha256'):
            digest = self.markers.get(parameters[0])
            result = (digest,) if digest else None
        elif 'SELECT EXISTS' in query:
            result = (bool(self.existing_tables.intersection(parameters[0])),)
        elif query.startswith('INSERT INTO tenderos_schema_migrations'):
            self.markers[parameters[0]] = parameters[1]
            result = None
        else:
            result = None
        return SimpleNamespace(fetchone=lambda: result)


def run_migration(monkeypatch, database):
    monkeypatch.setattr(sys, 'argv', ['migrate_postgres.py','--apply'])
    monkeypatch.setenv('TENDEROS_DATABASE_URL', 'postgresql://test:unused@db.example.com/test?sslmode=require')
    monkeypatch.setitem(sys.modules, 'psycopg', SimpleNamespace(connect=lambda *args, **kwargs: database))
    return migration_module().main()


def test_postgres_cli_applies_versions_under_one_advisory_lock_and_rechecks(monkeypatch):
    database = MigrationDatabase()
    assert run_migration(monkeypatch, database) == 0
    applied = [params[0] for query, params in database.operations
               if query.startswith('INSERT INTO tenderos_schema_migrations')]
    assert applied[:3] == ['tenderos_persistent_pilot_v1','tenderos_document_registry_v2',
                          'tenderos_bounded_workflows_v3']
    lock_position = next(i for i, (query, _) in enumerate(database.operations) if 'pg_advisory_xact_lock' in query)
    ddl_position = next(i for i, (query, _) in enumerate(database.operations) if query.startswith('-- TenderOS'))
    assert lock_position < ddl_position
    before = dict(database.markers)
    database.operations.clear()
    assert run_migration(monkeypatch, database) == 0
    assert database.markers == before
    assert not any(query.startswith('INSERT INTO tenderos_schema_migrations')
                   for query, _ in database.operations)


def test_postgres_cli_refuses_unversioned_workflow_tables(monkeypatch, capsys):
    database = MigrationDatabase(existing_tables=['workflow_artifacts'])
    assert run_migration(monkeypatch, database) == 1
    assert 'Unversioned application tables' in capsys.readouterr().err
    assert 'tenderos_bounded_workflows_v3' not in database.markers
    assert not any(query.startswith('-- Additive bounded workflow') for query, _ in database.operations)


def test_postgres_cli_refuses_changed_saved_digest(monkeypatch, capsys):
    database = MigrationDatabase(markers={'tenderos_bounded_workflows_v3':'b'*64})
    assert run_migration(monkeypatch, database) == 1
    assert 'Schema digest differs' in capsys.readouterr().err


def test_postgres_cli_requires_explicit_apply_before_contact(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['migrate_postgres.py'])
    contacted = []
    monkeypatch.setitem(sys.modules, 'psycopg', SimpleNamespace(connect=lambda *args, **kwargs: contacted.append(True)))
    with pytest.raises(SystemExit):
        migration_module().main()
    assert contacted == []
