"""Additive local v4 commercial registers; no hosted startup DDL."""
import hashlib
import sqlite3

from .database import ConfigurationError

COMMERCIAL_MIGRATION_ID = 'tenderos_commercial_operations_v4'
COMMERCIAL_ID_TABLES = ('service_intakes', 'commercial_ledger', 'diagnostic_releases')

_LOCAL_COMMERCIAL_STATEMENTS = (
    '''CREATE TABLE IF NOT EXISTS service_intakes (
       id INTEGER PRIMARY KEY, tender_id INTEGER NOT NULL UNIQUE REFERENCES tenders(id),
       scope TEXT NOT NULL, exclusions TEXT NOT NULL DEFAULT '',
       agreed_inventory_ids_json TEXT NOT NULL, due_at TEXT,
       quoted_fee_minor INTEGER CHECK (quoted_fee_minor IS NULL OR
          (typeof(quoted_fee_minor)='integer' AND quoted_fee_minor >= 0)),
       currency TEXT NOT NULL CHECK (currency='BDT'), reviewer TEXT NOT NULL,
       checklist_json TEXT NOT NULL, actor TEXT NOT NULL, updated_at TEXT NOT NULL
    )''',
    '''CREATE TABLE IF NOT EXISTS commercial_ledger (
       id INTEGER PRIMARY KEY, tender_id INTEGER NOT NULL REFERENCES tenders(id),
       kind TEXT NOT NULL CHECK (kind IN ('RECEIPT','DIRECT_COST','REFUND','REVERSAL')),
       amount_minor INTEGER NOT NULL CHECK (typeof(amount_minor)='integer' AND amount_minor > 0),
       currency TEXT NOT NULL CHECK (currency='BDT'), reverses_entry_id INTEGER,
       idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL,
       reference TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
       actor TEXT NOT NULL, created_at TEXT NOT NULL,
       UNIQUE (id,tender_id), UNIQUE (tender_id,idempotency_key), UNIQUE (tender_id,kind,reference),
       FOREIGN KEY (reverses_entry_id,tender_id) REFERENCES commercial_ledger(id,tender_id),
       CHECK ((kind IN ('RECEIPT','DIRECT_COST') AND reverses_entry_id IS NULL)
          OR (kind IN ('REFUND','REVERSAL') AND reverses_entry_id IS NOT NULL)),
       CHECK (reverses_entry_id IS NULL OR reverses_entry_id <> id)
    )''',
    '''CREATE INDEX IF NOT EXISTS idx_commercial_ledger_tender ON commercial_ledger(tender_id,id)''',
    '''CREATE INDEX IF NOT EXISTS idx_commercial_ledger_original ON commercial_ledger(reverses_entry_id)''',
    '''CREATE TRIGGER IF NOT EXISTS commercial_ledger_no_update BEFORE UPDATE ON commercial_ledger
       BEGIN SELECT RAISE(ABORT,'Commercial ledger entries are immutable'); END''',
    '''CREATE TRIGGER IF NOT EXISTS commercial_ledger_no_delete BEFORE DELETE ON commercial_ledger
       BEGIN SELECT RAISE(ABORT,'Commercial ledger entries are immutable'); END''',
    '''CREATE TABLE IF NOT EXISTS diagnostic_releases (
       id INTEGER PRIMARY KEY, tender_id INTEGER NOT NULL REFERENCES tenders(id),
       release_version INTEGER NOT NULL CHECK (release_version > 0),
       idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL,
       snapshot_json TEXT NOT NULL, snapshot_sha256 TEXT NOT NULL CHECK
          (length(snapshot_sha256)=64 AND snapshot_sha256 NOT GLOB '*[^0-9a-f]*'),
       currency_fingerprint TEXT NOT NULL CHECK
          (length(currency_fingerprint)=64 AND currency_fingerprint NOT GLOB '*[^0-9a-f]*'),
       template_version TEXT NOT NULL, actor TEXT NOT NULL, reviewer TEXT NOT NULL,
       created_at TEXT NOT NULL,
       UNIQUE (tender_id,release_version), UNIQUE (tender_id,idempotency_key)
    )''',
    '''CREATE INDEX IF NOT EXISTS idx_diagnostic_releases_tender ON diagnostic_releases(tender_id,id)''',
    '''CREATE TRIGGER IF NOT EXISTS diagnostic_releases_no_update BEFORE UPDATE ON diagnostic_releases
       BEGIN SELECT RAISE(ABORT,'Diagnostic releases are immutable'); END''',
    '''CREATE TRIGGER IF NOT EXISTS diagnostic_releases_no_delete BEFORE DELETE ON diagnostic_releases
       BEGIN SELECT RAISE(ABORT,'Diagnostic releases are immutable'); END''',
)


def initialize_local_commercial(database):
    """Install only on SQLite, after core/v2/v3; refuse drift/unversioned tables."""
    if not isinstance(database, sqlite3.Connection):
        raise ConfigurationError('Local commercial schema requires a SQLite connection')
    digest = hashlib.sha256('\n'.join(_LOCAL_COMMERCIAL_STATEMENTS).encode()).hexdigest()
    database.execute('SAVEPOINT tenderos_local_commercial')
    try:
        database.execute('''CREATE TABLE IF NOT EXISTS tenderos_local_schema_migrations (
            migration_id TEXT PRIMARY KEY, schema_sha256 TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )''')
        prior = database.execute('SELECT schema_sha256 FROM tenderos_local_schema_migrations WHERE migration_id=?',
                                 (COMMERCIAL_MIGRATION_ID,)).fetchone()
        if prior and prior[0] != digest:
            raise ConfigurationError('Local commercial schema digest differs; explicit migration required')
        if not prior:
            existing = database.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('service_intakes','commercial_ledger','diagnostic_releases')").fetchone()
            if existing:
                raise ConfigurationError('Unversioned commercial tables require explicit migration')
            for statement in _LOCAL_COMMERCIAL_STATEMENTS:
                database.execute(statement)
            database.execute('INSERT INTO tenderos_local_schema_migrations(migration_id,schema_sha256) VALUES(?,?)',
                             (COMMERCIAL_MIGRATION_ID, digest))
        database.execute('RELEASE SAVEPOINT tenderos_local_commercial')
    except Exception:
        database.execute('ROLLBACK TO SAVEPOINT tenderos_local_commercial')
        database.execute('RELEASE SAVEPOINT tenderos_local_commercial')
        raise
