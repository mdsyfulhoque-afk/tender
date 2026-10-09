"""Access controls for the explicitly configured, single-owner hosted pilot."""
import base64
import binascii
import hashlib
import hmac
import os
from contextvars import ContextVar
from dataclasses import dataclass, field
from urllib.parse import urlsplit


HOSTED = os.environ.get('VERCEL') == '1' or os.environ.get('TENDEROS_HOSTED') == '1'
MAX_UPLOAD_BYTES = (4 if HOSTED else 10) * 1024 * 1024
principal = ContextVar('tenderos_principal', default=None)


class HostingConfigurationError(Exception):
    """Deliberately contains no environment variable values or credentials."""


def canonical_origin(value):
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                or parsed.port not in (None, 443)):
            raise ValueError
        hostname = parsed.hostname.encode('idna').decode('ascii').lower()
        if not all(part and len(part) <= 63 and all(c.isalnum() or c == '-' for c in part)
                   and not part.startswith('-') and not part.endswith('-') for part in hostname.split('.')):
            raise ValueError
        return 'https://' + hostname
    except (ValueError, UnicodeError):
        raise HostingConfigurationError('Hosted origin configuration is invalid') from None


@dataclass(frozen=True)
class HostedConfiguration:
    username: str
    password: str = field(repr=False)
    database_url: str = field(repr=False)
    origins: frozenset

    def csrf_token(self, origin):
        return hmac.new(self.password.encode('utf-8'),
                        ('tenderos-pilot-csrf:' + self.username + ':' + origin).encode('utf-8'),
                        hashlib.sha256).hexdigest()


def hosted_configuration():
    username = os.environ.get('TENDEROS_PILOT_USERNAME', '')
    password = os.environ.get('TENDEROS_PILOT_PASSWORD', '')
    database_url = os.environ.get('TENDEROS_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
    if (not 2 <= len(username) <= 100 or ':' in username or any(ord(c) < 33 for c in username)
            or len(password) < 32 or any(ord(c) < 32 for c in password) or not database_url):
        raise HostingConfigurationError('Hosted pilot credentials or durable database are not configured')
    origins = set()
    if os.environ.get('TENDEROS_APP_ORIGIN'):
        origins.add(canonical_origin(os.environ['TENDEROS_APP_ORIGIN']))
    # These are platform environment values, never request forwarding headers.
    for variable in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL'):
        if os.environ.get(variable):
            origins.add(canonical_origin('https://' + os.environ[variable]))
    if not origins:
        raise HostingConfigurationError('Hosted origin is not configured')
    return HostedConfiguration(username, password, database_url, frozenset(origins))


def authenticate_basic(header, config):
    try:
        scheme, encoded = (header or '').split(' ', 1)
        if scheme.lower() != 'basic' or len(encoded) > 4096:
            return False
        decoded = base64.b64decode(encoded, validate=True).decode('utf-8')
        username, password = decoded.split(':', 1)
    except (ValueError, UnicodeError, binascii.Error):
        return False
    user_valid = hmac.compare_digest(hashlib.sha256(username.encode('utf-8')).digest(),
                                    hashlib.sha256(config.username.encode('utf-8')).digest())
    password_valid = hmac.compare_digest(hashlib.sha256(password.encode('utf-8')).digest(),
                                        hashlib.sha256(config.password.encode('utf-8')).digest())
    return user_valid and password_valid


def authenticated_actor(local_actor='local-operator'):
    actor = principal.get()
    if HOSTED and not actor:
        raise HostingConfigurationError('Authenticated principal is required')
    return actor if HOSTED else local_actor


def request_origin(request, config):
    # Host is matched against exact configured/platform hosts. X-Forwarded-Host is ignored.
    origin = canonical_origin('https://' + request.headers.get('host', ''))
    if origin not in config.origins:
        raise HostingConfigurationError('Request origin is not permitted')
    # Vercel terminates TLS and supplies X-Forwarded-Proto to its Python runtime.
    secure = request.url.scheme == 'https' or (
        os.environ.get('VERCEL') == '1' and request.headers.get('x-forwarded-proto') == 'https')
    if not secure:
        raise HostingConfigurationError('HTTPS is required')
    return origin


def csrf_valid(request, config, origin):
    supplied_origin = request.headers.get('origin')
    referer = request.headers.get('referer')
    try:
        if supplied_origin and canonical_origin(supplied_origin) != origin:
            return False
        if not supplied_origin and referer:
            parsed = urlsplit(referer)
            if canonical_origin(parsed.scheme + '://' + parsed.netloc) != origin:
                return False
    except (HostingConfigurationError, ValueError, UnicodeError):
        return False
    # A token issued only by the authenticated health endpoint is also required.
    # This permits authenticated API clients without allowing ambient Basic credentials
    # to authorize cross-site HTML form submissions.
    return hmac.compare_digest(request.headers.get('x-tenderos-csrf', '').encode('utf-8'),
                               config.csrf_token(origin).encode('ascii'))
