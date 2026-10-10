"""Explicit, locked versioned migrations for a hosted TenderOS database.

Run: python scripts/migrate_postgres.py --apply
Provide TENDEROS_DATABASE_URL or DATABASE_URL in the process environment.
No customer records or local SQLite files are read, copied, or overwritten.
Use a dedicated database. Repeated runs check every saved schema digest.
Existing installations receive only missing additive, checksum-verified migrations.
"""
import argparse
import hashlib
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.database import ConfigurationError, validate_database_url  # noqa: E402


MIGRATION_ID = 'tenderos_persistent_pilot_v1'
DOCUMENT_REGISTRY_ID = 'tenderos_document_registry_v2'
BOUNDED_WORKFLOWS_ID = 'tenderos_bounded_workflows_v3'
COMMERCIAL_OPERATIONS_ID = 'tenderos_commercial_operations_v4'
# Transaction advisory lock shared by every invocation of this command.
MIGRATION_LOCK_ID = 762143096015021


def main():
    parser = argparse.ArgumentParser(description='Apply TenderOS PostgreSQL schema explicitly')
    parser.add_argument('--apply', action='store_true', help='Apply the schema to the configured database')
    args = parser.parse_args()
    if not args.apply:
        parser.error('--apply is required; no database was contacted')
    try:
        database_url = os.environ.get('TENDEROS_DATABASE_URL') or os.environ.get('DATABASE_URL')
        validate_database_url(database_url)
        import psycopg
        scripts = Path(__file__).parent
        migrations = (
            (MIGRATION_ID, scripts / 'postgres_schema.sql'),
            (DOCUMENT_REGISTRY_ID, scripts / 'postgres_migrations' / '002_document_registry.sql'),
            (BOUNDED_WORKFLOWS_ID, scripts / 'postgres_migrations' / '003_bounded_workflows.sql'),
            (COMMERCIAL_OPERATIONS_ID, scripts / 'postgres_migrations' / '004_commercial_operations.sql'),
        )
        schemas = [(identifier, path.read_text(encoding='utf-8')) for identifier, path in migrations]
        # READ COMMITTED sees the preceding command's migration after lock wait.
        with psycopg.connect(database_url, connect_timeout=10) as database:
            with database.transaction():
                database.execute("SET LOCAL statement_timeout = '60s'")
                database.execute("SET LOCAL lock_timeout = '30s'")
                database.execute('SELECT pg_advisory_xact_lock(%s)', (MIGRATION_LOCK_ID,))
                database.execute('''CREATE TABLE IF NOT EXISTS tenderos_schema_migrations (
                    migration_id TEXT PRIMARY KEY, schema_sha256 TEXT NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
                )''')
                for identifier, schema in schemas:
                    digest = hashlib.sha256(schema.encode('utf-8')).hexdigest()
                    prior = database.execute(
                        'SELECT schema_sha256 FROM tenderos_schema_migrations WHERE migration_id=%s',
                        (identifier,),
                    ).fetchone()
                    if prior and prior[0] != digest:
                        raise ConfigurationError('Schema digest differs; explicit new migration is required')
                    if prior:
                        continue
                    table_names = {
                        MIGRATION_ID: ['organizations','tenders','sources','evidence','requirements',
                                       'decisions','audit_events','pilot_metrics'],
                        DOCUMENT_REGISTRY_ID: ['tender_inventory_items','evidence_files'],
                        BOUNDED_WORKFLOWS_ID: ['workflow_jobs','workflow_steps','workflow_artifacts',
                                              'workflow_events','workflow_candidate_reviews'],
                        COMMERCIAL_OPERATIONS_ID: ['service_intakes','commercial_ledger','diagnostic_releases'],
                    }[identifier]
                    existing = database.execute('''SELECT EXISTS (
                        SELECT 1 FROM pg_tables WHERE schemaname = current_schema()
                        AND tablename = ANY(%s)
                    )''', (table_names,)).fetchone()[0]
                    if existing:
                        raise ConfigurationError('Unversioned application tables require explicit migration')
                    # Multi-statement schema is trusted repository SQL, no parameters.
                    database.execute(schema)
                    database.execute(
                        'INSERT INTO tenderos_schema_migrations(migration_id,schema_sha256) VALUES(%s,%s)',
                        (identifier, digest),
                    )
        print('TenderOS PostgreSQL schemas v1 through v4 are applied; legacy records were preserved')
        return 0
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
    except Exception:
        # Driver and connection exceptions may contain passwords or DSNs.
        print('PostgreSQL schema migration failed; transaction was not confirmed', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
