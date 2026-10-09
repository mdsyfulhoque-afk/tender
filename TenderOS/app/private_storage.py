"""Server-only private PDF storage through the native Vercel Blob API.

Wire protocol follows vercel/storage commit
d15b9b37f9042edafee0245af7df74f4bbc9bad4 (@vercel/blob 2.8.1):
packages/blob/src/{put,put-helpers,api,helpers}.ts. A private Blob store must
be bound to the project. This module never publishes URLs, read credentials,
or browser upload tokens and never deletes an object after an ambiguous commit.
"""
import json
import hashlib
import hmac
from http.client import HTTPException as HTTPProtocolError
import os
import re
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_PRIVATE_PDF_BYTES = 4 * 1024 * 1024
_BLOB_API = 'https://vercel.com/api/blob/'
_KEY_PREFIX = 'tenderos/private-pdf/'
_KEY_FORMAT = re.compile(r'^tenderos/private-pdf/[a-f0-9]{32}\.pdf$')
_HASH_FORMAT = re.compile(r'^[a-f0-9]{64}$')
_TOKEN_FORMAT = re.compile(r'^vercel_blob_rw_([A-Za-z0-9]+)_[A-Za-z0-9_-]+$')
_STORE_ID_FORMAT = re.compile(r'^[A-Za-z0-9]+$')
_OIDC_FORMAT = re.compile(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')


class PrivateStorageError(RuntimeError):
    """A private storage configuration or operation failed safely."""


class PrivateFileNotFound(PrivateStorageError):
    """The authorized stored PDF no longer exists in the private store."""


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        # Never forward the server's bearer token to a redirected origin.
        return None


def _configuration():
    if os.environ.get('TENDEROS_PRIVATE_STORAGE', 'vercel_blob') != 'vercel_blob':
        raise PrivateStorageError('Native private Blob storage is required')
    if os.environ.get('TENDEROS_BLOB_ACCESS') != 'private':
        raise PrivateStorageError('A private Blob store must be configured')
    token = os.environ.get('BLOB_READ_WRITE_TOKEN', '')
    if token:
        match = _TOKEN_FORMAT.fullmatch(token)
        if not match:
            raise PrivateStorageError('Server private Blob credentials are required')
        return token, match.group(1)
    # The official API also accepts a Vercel OIDC bearer token with its store
    # identifier header. Project/store permissions are verified by Vercel.
    oidc_token = os.environ.get('VERCEL_OIDC_TOKEN', '')
    store_id = os.environ.get('BLOB_STORE_ID', '').strip()
    if store_id.startswith('store_'):
        store_id = store_id[len('store_'):]
    if _OIDC_FORMAT.fullmatch(oidc_token) and _STORE_ID_FORMAT.fullmatch(store_id):
        return oidc_token, store_id
    raise PrivateStorageError('Server private Blob credentials are required')


def validate_private_storage_config():
    """Configuration-only check; no provider requests or secret disclosure."""
    _configuration()


def store_private_pdf(data: bytes, name: str) -> str:
    """Store the exact PDF bytes, returning only a server-generated object key.

    The source filename is deliberately excluded from the object key and wire
    metadata. Its provenance remains in the database record created by the
    caller. Upload errors are not retried: the first request may have succeeded.
    """
    token, store_id = _configuration()
    if not isinstance(data, bytes) or not data.startswith(b'%PDF-'):
        raise PrivateStorageError('Only PDF bytes may be stored')
    if len(data) > MAX_PRIVATE_PDF_BYTES:
        raise PrivateStorageError('PDF exceeds the hosted upload limit')
    if not isinstance(name, str):
        raise PrivateStorageError('PDF source name is required')
    key = _KEY_PREFIX + uuid.uuid4().hex + '.pdf'
    request = Request(
        _BLOB_API + '?' + urlencode({'pathname': key}), data=data, method='PUT',
        headers={
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/pdf',
            'x-content-type': 'application/pdf',
            'x-content-length': str(len(data)),
            'x-api-version': '12',
            'x-vercel-blob-store-id': store_id,
            'x-vercel-blob-access': 'private',
            'x-add-random-suffix': '0',
            'x-allow-overwrite': '0',
        },
    )
    try:
        with build_opener(_NoRedirects()).open(request, timeout=25) as response:
            if response.status not in (200, 201):
                raise PrivateStorageError('Private storage upload could not be confirmed')
            raw = response.read(65537)
            if len(raw) > 65536:
                raise PrivateStorageError('Private storage upload could not be confirmed')
            result = json.loads(raw)
        if not isinstance(result, dict) or result.get('pathname') != key:
            raise PrivateStorageError('Private storage upload could not be confirmed')
        blob_url = urlsplit(result.get('url', ''))
        if (blob_url.scheme != 'https'
                or blob_url.hostname != store_id.lower() + '.private.blob.vercel-storage.com'
                or blob_url.username is not None or blob_url.password is not None
                or blob_url.port not in (None, 443)
                or blob_url.path != '/' + key or blob_url.query or blob_url.fragment
                or result.get('contentType') != 'application/pdf'):
            raise PrivateStorageError('Private storage upload could not be confirmed')
    except PrivateStorageError:
        raise
    except (HTTPError, URLError, HTTPProtocolError, OSError, ValueError, TypeError):
        raise PrivateStorageError('Private storage is temporarily unavailable') from None
    return key


def read_private_pdf(key: str, max_bytes: int, expected_sha256: str) -> bytes:
    """Fetch only an authorized DB-owned opaque key and verify bounded PDF bytes.

    The caller must load the key/hash from the authorized source/evidence row.
    Client-supplied URLs or paths are never accepted. The fixed private store
    URL and bearer GET protocol follow the already inspected official
    vercel/storage packages/blob/src/get.ts. No provider URL/token is returned.
    """
    if (not isinstance(key, str) or not _KEY_FORMAT.fullmatch(key)
            or type(max_bytes) is not int or not 0 < max_bytes <= MAX_PRIVATE_PDF_BYTES
            or not isinstance(expected_sha256, str) or not _HASH_FORMAT.fullmatch(expected_sha256)):
        raise PrivateStorageError('Stored private PDF metadata is invalid')
    token, store_id = _configuration()
    request = Request(
        'https://' + store_id.lower() + '.private.blob.vercel-storage.com/' + key + '?cache=0',
        method='GET', headers={'Authorization': 'Bearer ' + token},
    )
    try:
        with build_opener(_NoRedirects()).open(request, timeout=25) as response:
            if response.status != 200:
                raise PrivateStorageError('Private PDF could not be retrieved')
            media_type = (response.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            content_length = response.headers.get('Content-Length')
            if media_type != 'application/pdf':
                raise PrivateStorageError('Private PDF content could not be verified')
            if content_length is not None and not 0 < int(content_length) <= max_bytes:
                raise PrivateStorageError('Private PDF exceeds its stored size limit')
            data = response.read(max_bytes + 1)
        if not data.startswith(b'%PDF-') or len(data) > max_bytes:
            raise PrivateStorageError('Private PDF content could not be verified')
        if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), expected_sha256):
            raise PrivateStorageError('Private PDF content could not be verified')
    except HTTPError as error:
        if error.code == 404:
            raise PrivateFileNotFound('Private PDF file is unavailable') from None
        raise PrivateStorageError('Private file storage is temporarily unavailable') from None
    except PrivateStorageError:
        raise
    except (URLError, HTTPProtocolError, OSError, ValueError, TypeError):
        raise PrivateStorageError('Private file storage is temporarily unavailable') from None
    return data


def fetch_private_pdf(key: str, expected_sha256: str, expected_bytes: int) -> bytes:
    """Read a stored PDF and additionally require its exact recorded byte size."""
    data = read_private_pdf(key, expected_bytes, expected_sha256)
    if len(data) != expected_bytes:
        raise PrivateStorageError('Private PDF content could not be verified')
    return data
