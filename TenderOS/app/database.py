"""PostgreSQL persistence for the hosted pilot; SQLite remains a local choice.

Hosted connections never create tables or change schema. Run the explicit
PostgreSQL migration command before deploying. Local SQLite extensions have a
separate, idempotent initializer. Route reads and writes share one serializable
transaction so approval checks and their saved decision cannot diverge.
"""
from contextlib import contextmanager
import hashlib
import ipaddress
import re
from urllib.parse import parse_qsl, urlsplit


class ConfigurationError(RuntimeError):
    """A required server configuration is absent or unsafe."""


class StorageUnavailable(RuntimeError):
    """A database operation failed; messages never include connection details."""


class WriteConflict(RuntimeError):
    """The whole request must be retried after a concurrent modification."""


_INSERT_ID_TABLES = frozenset({
    'organizations', 'tenders', 'sources', 'requirements', 'evidence',
    'decisions', 'audit_events',
    'tender_inventory_items', 'evidence_files',
    'workflow_jobs', 'workflow_steps', 'workflow_artifacts',
    'workflow_events', 'workflow_candidate_reviews',
    'service_intakes', 'commercial_ledger', 'diagnostic_releases',
})
_INSERT_TABLE = re.compile(r'^\s*INSERT\s+INTO\s+([a-z_][a-z_0-9]*)\s*\(', re.I)
_FORBIDDEN_QUERY_OPTIONS = frozenset({
    'host', 'hostaddr', 'port', 'user', 'password', 'dbname', 'service',
    'servicefile', 'sslcert', 'sslkey', 'sslpassword', 'sslrootcert',
    'sslcrl', 'sslcrldir', 'options', 'passfile', 'sslnegotiation',
})


_LOCAL_EXTENSION_STATEMENTS = (
    '''CREATE UNIQUE INDEX IF NOT EXISTS idx_source_identity_tender
       ON sources(id,tender_id)''',
    '''CREATE TABLE IF NOT EXISTS tender_inventory_items (
       id INTEGER PRIMARY KEY,
       tender_id INTEGER NOT NULL REFERENCES tenders(id),
       title TEXT NOT NULL CHECK (length(trim(title)) > 0),
       document_type TEXT NOT NULL, publication_date TEXT,
       language TEXT NOT NULL DEFAULT '', version_label TEXT NOT NULL DEFAULT '',
       supersedes_item_id INTEGER, source_id INTEGER,
       availability TEXT NOT NULL CHECK (availability IN ('AVAILABLE','MISSING')),
       notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
       UNIQUE (id,tender_id),
       FOREIGN KEY (source_id,tender_id) REFERENCES sources(id,tender_id),
       FOREIGN KEY (supersedes_item_id,tender_id) REFERENCES tender_inventory_items(id,tender_id),
       CHECK (supersedes_item_id IS NULL OR supersedes_item_id <> id),
       CHECK ((availability='AVAILABLE' AND source_id IS NOT NULL)
           OR (availability='MISSING' AND source_id IS NULL))
    )''',
    '''CREATE INDEX IF NOT EXISTS idx_inventory_tender ON tender_inventory_items(tender_id)''',
    '''CREATE INDEX IF NOT EXISTS idx_inventory_source ON tender_inventory_items(source_id)''',
    '''CREATE INDEX IF NOT EXISTS idx_inventory_supersedes ON tender_inventory_items(supersedes_item_id)''',
    '''CREATE TABLE IF NOT EXISTS evidence_files (
       id INTEGER PRIMARY KEY, evidence_id INTEGER NOT NULL REFERENCES evidence(id),
       private_path TEXT NOT NULL UNIQUE,
       sha256 TEXT NOT NULL CHECK (length(sha256)=64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
       bytes INTEGER NOT NULL CHECK (bytes > 0),
       filename TEXT NOT NULL CHECK (length(trim(filename)) > 0),
       uploaded_at TEXT NOT NULL
    )''',
    '''CREATE INDEX IF NOT EXISTS idx_evidence_file_record ON evidence_files(evidence_id)''',
    '''CREATE TRIGGER IF NOT EXISTS evidence_files_no_update BEFORE UPDATE ON evidence_files
       BEGIN SELECT RAISE(ABORT,'Evidence file records are immutable'); END''',
    '''CREATE TRIGGER IF NOT EXISTS evidence_files_no_delete BEFORE DELETE ON evidence_files
       BEGIN SELECT RAISE(ABORT,'Evidence file records are immutable'); END''',
)
_LOCAL_EXTENSION_ID = 'tenderos_document_registry_v2'


def initialize_local_extensions(database):
    """Add document registries to a local SQLite DB without rewriting legacy rows.

    Call after the existing local core schema is initialized. This function is
    explicitly restricted to SQLite; it cannot run DDL through a hosted adapter.
    A savepoint makes all extension DDL and its digest marker atomic even when
    the caller already has an active transaction. No source/evidence records,
    hashes, attestations or historical approvals are invented or backfilled.
    """
    import sqlite3
    if not isinstance(database, sqlite3.Connection):
        raise ConfigurationError('Local extensions require a SQLite connection')
    digest = hashlib.sha256('\n'.join(_LOCAL_EXTENSION_STATEMENTS).encode('utf-8')).hexdigest()
    database.execute('SAVEPOINT tenderos_local_extensions')
    try:
        database.execute('''CREATE TABLE IF NOT EXISTS tenderos_local_schema_migrations (
            migration_id TEXT PRIMARY KEY, schema_sha256 TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )''')
        prior = database.execute(
            'SELECT schema_sha256 FROM tenderos_local_schema_migrations WHERE migration_id=?',
            (_LOCAL_EXTENSION_ID,),
        ).fetchone()
        if prior and prior[0] != digest:
            raise ConfigurationError('Local schema digest differs; an explicit migration is required')
        if not prior:
            existing = database.execute('''SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('tender_inventory_items','evidence_files')''').fetchone()
            if existing:
                raise ConfigurationError('Unversioned document registry tables require explicit migration')
            for statement in _LOCAL_EXTENSION_STATEMENTS:
                database.execute(statement)
            database.execute(
                'INSERT INTO tenderos_local_schema_migrations(migration_id,schema_sha256) VALUES(?,?)',
                (_LOCAL_EXTENSION_ID, digest),
            )
        database.execute('RELEASE SAVEPOINT tenderos_local_extensions')
    except Exception:
        database.execute('ROLLBACK TO SAVEPOINT tenderos_local_extensions')
        database.execute('RELEASE SAVEPOINT tenderos_local_extensions')
        raise


def validate_database_url(database_url):
    """Validate a remote PostgreSQL URL without resolving or connecting to it.

    TLS is mandatory. Connection authority cannot be overridden with query
    options. Connection details are never placed in exception messages.
    """
    try:
        if not isinstance(database_url, str) or not database_url:
            raise ValueError
        if any(character.isspace() or ord(character) < 32 for character in database_url):
            raise ValueError
        parsed = urlsplit(database_url)
        host = parsed.hostname
        if (parsed.scheme not in ('postgres', 'postgresql') or not host
                or not parsed.username or parsed.fragment
                or not parsed.path or parsed.path == '/' or ',' in host
                or parsed.port == 0):
            raise ValueError
        if host.lower().rstrip('.') in ('localhost', 'localhost.localdomain'):
            raise ValueError
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if '.' not in host or host.endswith('.localhost'):
                raise ValueError
        else:
            if not address.is_global:
                raise ValueError
        options = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
        keys = [key.lower() for key, _ in options]
        if len(keys) != len(set(keys)) or _FORBIDDEN_QUERY_OPTIONS.intersection(keys):
            raise ValueError
        if any(key != key.lower() for key, _ in options):
            raise ValueError
        if dict(options).get('sslmode') not in ('require', 'verify-ca', 'verify-full'):
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise ConfigurationError('A remote PostgreSQL URL with required TLS is needed') from None


def _driver():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        raise ConfigurationError('The PostgreSQL driver is not installed') from None
    return psycopg, dict_row


def _translate_qmarks(statement, parameters):
    """Translate this application's qmark SQL, keeping quoted literals intact.

    App statements have no comments or dollar-quoted SQL. Reject those forms
    rather than guessing at how arbitrary PostgreSQL syntax should be parsed.
    Values always remain bound parameters, never interpolated into SQL.
    """
    if not isinstance(statement, str):
        raise TypeError('SQL statement must be a string')
    translated = []
    quote = None
    count = 0
    index = 0
    while index < len(statement):
        character = statement[index]
        if quote:
            translated.append('%%' if character == '%' and parameters else character)
            if character == quote:
                if index + 1 < len(statement) and statement[index + 1] == quote:
                    translated.append(quote)
                    index += 1
                else:
                    quote = None
        elif character in ("'", '"'):
            quote = character
            translated.append(character)
        elif statement[index:index + 2] in ('--', '/*') or character == '$':
            raise ValueError('Unsupported SQL syntax in application statement')
        elif character == '?':
            translated.append('%s')
            count += 1
        else:
            translated.append('%%' if character == '%' and parameters else character)
        index += 1
    if quote or count != len(parameters):
        raise ValueError('Invalid SQL parameter binding')
    return ''.join(translated)


class _Cursor:
    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor)


class _Connection:
    def __init__(self, database):
        self._database = database

    def execute(self, statement, parameters=()):
        parameters = tuple(parameters)
        query = _translate_qmarks(statement, parameters).rstrip().rstrip(';')
        match = _INSERT_TABLE.match(query)
        returns_id = bool(match and match.group(1).lower() in _INSERT_ID_TABLES)
        if returns_id:
            query += ' RETURNING id'
        cursor = self._database.execute(query, parameters if parameters else None)
        lastrowid = None
        if returns_id:
            row = cursor.fetchone()
            if row is None:
                raise StorageUnavailable('Database insert did not return an identifier')
            lastrowid = int(row['id'])
        return _Cursor(cursor, lastrowid)


@contextmanager
def postgres_connection(database_url):
    """Yield a qmark adapter and commit once; never retry writes automatically.

    Database transport failures can have an ambiguous commit outcome. Callers
    must retain uploaded objects on these failures and must not retry approvals
    silently. Only psycopg exceptions are translated; domain errors propagate.
    """
    validate_database_url(database_url)
    psycopg, dict_row = _driver()
    database = None
    try:
        database = psycopg.connect(
            database_url, autocommit=True, row_factory=dict_row,
            connect_timeout=10, application_name='tenderos-persistent-pilot',
            prepare_threshold=None,  # Safe with transaction-mode managed poolers.
        )
        with database.transaction():
            database.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            database.execute("SET LOCAL statement_timeout = '15s'")
            database.execute("SET LOCAL lock_timeout = '5s'")
            database.execute("SET LOCAL idle_in_transaction_session_timeout = '20s'")
            yield _Connection(database)
    except (psycopg.errors.SerializationFailure, psycopg.errors.DeadlockDetected,
            psycopg.errors.UniqueViolation, psycopg.errors.ForeignKeyViolation,
            psycopg.errors.CheckViolation, psycopg.errors.LockNotAvailable):
        raise WriteConflict('Data changed concurrently; reload before retrying') from None
    except psycopg.Error:
        raise StorageUnavailable('Persistent database is temporarily unavailable') from None
    finally:
        if database is not None:
            try:
                database.close()
            except psycopg.Error:
                pass
