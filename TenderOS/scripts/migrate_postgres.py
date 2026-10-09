"""Explicit, locked schema initialization for a new hosted TenderOS database.

Run: python scripts/migrate_postgres.py --apply
Provide TENDEROS_DATABASE_URL or DATABASE_URL in the process environment.
No customer records or local SQLite files are read, copied, or overwritten.
Use a dedicated database. Repeated runs check the saved schema digest.
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
        schema = (Path(__file__).parent / 'postgres_schema.sql').read_text(encoding='utf-8')
        digest = hashlib.sha256(schema.encode('utf-8')).hexdigest()
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
                prior = database.execute(
                    'SELECT schema_sha256 FROM tenderos_schema_migrations WHERE migration_id=%s',
                    (MIGRATION_ID,),
                ).fetchone()
                if prior and prior[0] != digest:
                    raise ConfigurationError('Schema digest differs; explicit new migration is required')
                if not prior:
                    existing = database.execute('''SELECT EXISTS (
                        SELECT 1 FROM pg_tables WHERE schemaname = current_schema()
                        AND tablename IN ('organizations','tenders','sources','evidence',
                                          'requirements','decisions','audit_events','pilot_metrics')
                    )''').fetchone()[0]
                    if existing:
                        raise ConfigurationError('An empty dedicated database is required for initialization')
                    # Multi-statement schema is trusted repository SQL, no parameters.
                    database.execute(schema)
                    database.execute(
                        'INSERT INTO tenderos_schema_migrations(migration_id,schema_sha256) VALUES(%s,%s)',
                        (MIGRATION_ID, digest),
                    )
        print('TenderOS PostgreSQL schema v1 is applied; no customer data was migrated')
        return 0
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
    except Exception:
        # Driver and connection exceptions may contain passwords or DSNs.
        print('PostgreSQL schema migration failed; transaction was not confirmed', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
