"""Durable, fenced document analysis with no model transport or approval tool.

Each advance commits a lease, computes outside a database transaction, then
publishes only if its fence, revision, scope, inputs and lease remain current.
This is a rules controller, not an autonomous AI agent or an always-on worker.
"""
import hashlib
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import HTTPException

from .workflow_contracts import (ARTIFACT_SCHEMAS, CONTRACT_VERSION, LIMITS, TASKS,
                                 canonical, digest, policy)

TERMINAL = {'WAITING_INPUT', 'WAITING_HUMAN', 'COMPLETED', 'FAILED', 'CANCELLED', 'STALE', 'BUDGET_EXHAUSTED'}
PATTERN = re.compile(r'\b(must|shall|required|minimum|at least|eligible|eligibility|experience|turnover|certificate|qualification|not permitted|prohibited)\b', re.I)
STOP_WORDS = frozenset('the a an and or for to of in by with is are be must shall required minimum at least bidder bidders document documents'.split())


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def whitespace(text):
    return ' '.join(text.split())


def tokens(text):
    return set(re.findall(r'[^\W_]{3,}', text.casefold(), flags=re.UNICODE)) - STOP_WORDS


class WorkflowEngine:
    def __init__(self, domain):
        self.d = domain

    @contextmanager
    def write(self):
        with self.d.conn() as db:
            # Acquire the local writer before reading controller state. Hosted
            # serializable transactions use their existing conflict boundary.
            if isinstance(db, sqlite3.Connection):
                db.execute('BEGIN IMMEDIATE')
            yield db

    def job(self, db, tender_id, job_id):
        self.d.require(db, 'tenders', tender_id)
        row = db.execute('SELECT * FROM workflow_jobs WHERE id=? AND tender_id=?', (job_id, tender_id)).fetchone()
        if not row:
            raise HTTPException(404, 'Workflow not found in this tender')
        return dict(row)

    def event(self, db, job_id, action, data, step_id=None, actor='SYSTEM:rules-controller'):
        db.execute('INSERT INTO workflow_events(job_id,step_id,actor,action,event_json,created_at) VALUES(?,?,?,?,?,?)',
                   (job_id, step_id, actor, action, canonical(data), timestamp()))

    def source_input_sha256(self, db, tender_id, snapshot=None):
        """Hash the independently inspectable source scope without evidence rows."""
        tender_record = self.d.require(db, 'tenders', tender_id)
        snapshot = snapshot or self.d.get_snapshot(db, tender_id)
        tender = snapshot['tender']
        source_scope = {
            'contract_version': CONTRACT_VERSION,
            'tender': {k: tender.get(k) for k in ('id', 'organization_id', 'title', 'buyer', 'notice_id', 'source_url', 'deadline')},
            'sources': snapshot['sources'], 'inventory': snapshot['inventory'],
        }
        return digest(source_scope)

    def manifest(self, db, tender_id):
        tender_record = self.d.require(db, 'tenders', tender_id)
        req_count = db.execute('SELECT COUNT(*) AS n FROM requirements WHERE tender_id=?', (tender_id,)).fetchone()['n']
        evidence_count = db.execute('SELECT COUNT(*) AS n FROM evidence WHERE organization_id=?', (tender_record['organization_id'],)).fetchone()['n']
        if req_count > LIMITS['max_requirements'] or evidence_count > LIMITS['max_evidence_records']:
            raise HTTPException(413, 'Input record limit exceeded; split the assessment scope before analysis')
        snapshot = self.d.get_snapshot(db, tender_id)
        tender = snapshot['tender']
        source_scope = {
            'contract_version': CONTRACT_VERSION,
            'tender': {k: tender.get(k) for k in ('id', 'organization_id', 'title', 'buyer', 'notice_id', 'source_url', 'deadline')},
            'sources': snapshot['sources'], 'inventory': snapshot['inventory'],
        }
        evidence = []
        for raw in db.execute('SELECT * FROM evidence WHERE organization_id=? ORDER BY id', (tender['organization_id'],)):
            ev = self.d.evidence_view(db, raw)
            latest = ev['files'][0] if ev['files'] else None
            evidence.append({k: ev[k] for k in ('id', 'organization_id', 'label', 'reference', 'expires_on', 'verified',
                                                 'document_verified', 'verification_event_id', 'verification_current')} | {
                'verification_note_sha256': digest(ev['verification_note']), 'latest_file': latest,
            })
        # Exact dates matter to expiry; no wall clock timestamp enters the hash.
        return {
            'schema_version': 'workflow_input_v1', 'contract_version': CONTRACT_VERSION,
            'as_of_date': date.today().isoformat(), 'source_scope': source_scope,
            'source_input_sha256': digest(source_scope),
            'requirements': snapshot['requirements'], 'evidence': evidence,
            'readiness_fingerprint': snapshot['fingerprint'],
            'source_scope_fingerprint': snapshot['source_scope_fingerprint'],
            'source_scope_attestation': snapshot['source_scope_attestation'],
            'inventory_issues': snapshot['inventory_issues'],
        }

    def currency(self, db, job):
        tender_record = self.d.require(db, 'tenders', job['tender_id'])
        req_count = db.execute('SELECT COUNT(*) AS n FROM requirements WHERE tender_id=?', (job['tender_id'],)).fetchone()['n']
        evidence_count = db.execute('SELECT COUNT(*) AS n FROM evidence WHERE organization_id=?',
                                    (tender_record['organization_id'],)).fetchone()['n']
        frozen = json.loads(job['input_manifest'])
        source_current = self.source_input_sha256(db, job['tender_id']) == frozen['source_input_sha256']
        if req_count > LIMITS['max_requirements'] or evidence_count > LIMITS['max_evidence_records']:
            # Reads of frozen runs remain available when current organizational
            # inputs are too large to compare. Source currency is still checked
            # independently; full currency is conservatively reported false.
            exceeded = []
            if req_count > LIMITS['max_requirements']:
                exceeded.append(f"requirements ({req_count}/{LIMITS['max_requirements']})")
            if evidence_count > LIMITS['max_evidence_records']:
                exceeded.append(f"organization evidence ({evidence_count}/{LIMITS['max_evidence_records']})")
            return {'full_current': False, 'source_current': source_current,
                    'full_current_reason': 'BOUNDED_CURRENT_INPUT',
                    'reason_detail': 'Current ' + ' and '.join(exceeded) +
                                     ' exceed configured comparison limits; full input currency was not compared.'}
        current = self.manifest(db, job['tender_id'])
        full_current = digest(current) == job['input_sha256']
        return {'full_current': full_current,
                'source_current': source_current,
                'full_current_reason': 'MATCHED' if full_current else 'INPUTS_CHANGED',
                'reason_detail': None}

    def stale(self, db, job, currency):
        if not currency['full_current'] and job['state'] not in {'CANCELLED', 'STALE', 'FAILED', 'BUDGET_EXHAUSTED'}:
            db.execute("UPDATE workflow_jobs SET state='STALE',revision=revision+1,updated_at=?,last_error_code='INPUT_CHANGED' WHERE id=?",
                       (timestamp(), job['id']))
            db.execute("UPDATE workflow_steps SET state='STALE',fence=fence+1,lease_owner=NULL,lease_expires_at=NULL WHERE job_id=? AND state IN ('READY','BLOCKED','RUNNING')", (job['id'],))
            self.event(db, job['id'], 'INPUT_CHANGED', currency)
            job = self.job(db, job['tender_id'], job['id'])
        return job

    def create(self, tender_id, key, request, restart_of=None):
        if not re.fullmatch(r'[A-Za-z0-9._:-]{16,128}', key or ''):
            raise HTTPException(422, 'Provide a random Idempotency-Key of 16–128 safe characters')
        request_hash = digest({'request': request, 'restart_of_job_id': restart_of})
        with self.write() as db:
            tender = self.d.require(db, 'tenders', tender_id)
            if restart_of is not None:
                self.job(db, tender_id, restart_of)
            prior = db.execute('SELECT * FROM workflow_jobs WHERE tender_id=? AND idempotency_key=?', (tender_id, key)).fetchone()
            if prior:
                if prior['request_sha256'] != request_hash:
                    raise HTTPException(409, 'Idempotency key was used for a different request')
                return self.detail_in(db, dict(prior))
            manifest = self.manifest(db, tender_id)
            if len(canonical(manifest).encode('utf-8')) > LIMITS['max_input_manifest_bytes']:
                raise HTTPException(413, 'Frozen input manifest exceeds the analysis size limit')
            limits = policy(self.d.HOSTED)
            sources = manifest['source_scope']['sources']
            state = 'READY' if sources else 'WAITING_INPUT'
            exceeded = (len(sources) > LIMITS['max_sources'] or sum(x['pages'] for x in sources) > LIMITS['max_source_pages']
                        or len(manifest['requirements']) > LIMITS['max_requirements']
                        or len(manifest['evidence']) > LIMITS['max_evidence_records'])
            if exceeded:
                state = 'BUDGET_EXHAUSTED'
            created = timestamp()
            cur = db.execute('''INSERT INTO workflow_jobs(tender_id,organization_id,workflow_kind,processor_kind,contract_version,
                state,created_by,idempotency_key,request_sha256,input_manifest,input_sha256,policy_manifest,policy_sha256,
                restart_of_job_id,last_error_code,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (tender_id, tender['organization_id'], 'READINESS_REVIEW', 'RULES', CONTRACT_VERSION, state,
                 self.d.authenticated_actor(), key, request_hash, canonical(manifest), digest(manifest), canonical(limits),
                 digest(limits), restart_of, 'INCOMPLETE_BOUND' if exceeded else None, created, created))
            job_id = cur.lastrowid
            predecessor = None
            for index, kind in enumerate(TASKS):
                step = db.execute('''INSERT INTO workflow_steps(job_id,task_kind,task_key,contract_version,executor_label,
                    state,predecessor_step_id,input_sha256) VALUES(?,?,?,?,?,?,?,?)''',
                    (job_id, kind, kind.lower() + ':v1', CONTRACT_VERSION, 'SYSTEM:local-rules',
                     'READY' if index == 0 and state == 'READY' else 'BLOCKED', predecessor, digest(manifest)))
                predecessor = step.lastrowid
            self.event(db, job_id, 'CREATED', {'input_sha256': digest(manifest), 'source_input_sha256': manifest['source_input_sha256'],
                                             'policy_sha256': digest(limits), 'state': state}, actor=self.d.authenticated_actor())
            return self.detail_in(db, self.job(db, tender_id, job_id))

    def artifacts(self, db, job_id):
        return [dict(x) for x in db.execute('SELECT * FROM workflow_artifacts WHERE job_id=? ORDER BY id', (job_id,))]

    def detail_in(self, db, job):
        currency = self.currency(db, job)
        job = self.stale(db, job, currency)
        artifacts = self.artifacts(db, job['id'])
        candidates, suggestions, issues, pages, checks = [], [], [], [], {}
        for artifact in artifacts:
            payload = json.loads(artifact['payload_json'])
            candidates.extend(payload.get('candidates', []))
            suggestions.extend(payload.get('suggestions', []))
            issues.extend(payload.get('issues', []))
            pages.extend(payload.get('pages', []))
            for check in payload.get('checks', []):
                checks[check['target_key']] = check
        reviews = {r['candidate_key']: dict(r) for r in db.execute('SELECT * FROM workflow_candidate_reviews WHERE job_id=? ORDER BY id', (job['id'],))}
        for candidate in candidates:
            candidate['citation_status'] = checks.get(candidate['candidate_key'], {}).get('status', 'NOT_CHECKED')
            candidate['review'] = reviews.get(candidate['candidate_key'])
        frozen = json.loads(job['input_manifest'])
        for inventory_issue in frozen['inventory_issues']:
            issues.append({'code': 'SOURCE_INVENTORY_UNRESOLVED', 'message': inventory_issue['reason'], 'source_id': None, 'page': None})
        if not frozen['source_scope']['sources']:
            issues.append({'code': 'DOCUMENTS_REQUIRED', 'message': 'Register source PDFs and restart analysis.', 'source_id': None, 'page': None})
        if job['last_error_code']:
            issues.append({'code': job['last_error_code'], 'message': 'Analysis needs attention; retained artifacts remain historical.', 'source_id': None, 'page': None})
        safe_fields = ('id', 'tender_id', 'organization_id', 'state', 'processor_kind', 'contract_version', 'created_by',
                       'input_sha256', 'policy_sha256', 'step_runs', 'elapsed_ms', 'revision', 'restart_of_job_id',
                       'last_error_code', 'created_at', 'updated_at', 'completed_at')
        result = {k: job[k] for k in safe_fields}
        result.update(processor_label='Local rules', autonomous_ai_agent=False, currency=currency,
                      candidates=candidates, evidence_suggestions=suggestions, issues=issues,
                      source_coverage=pages,
                      progress={'pages_processed': len(pages), 'pages_total': sum(s['pages'] for s in frozen['source_scope']['sources']),
                                'task_batches': job['step_runs'], 'max_task_batches': LIMITS['max_step_runs']},
                      usage={'external_model_calls': 0, 'model_spend_minor': 0, 'elapsed_ms': job['elapsed_ms']},
                      steps=[{k: v for k, v in dict(s).items() if k not in ('lease_owner', 'cursor_json')} |
                             {'cursor': {k: v for k, v in json.loads(s['cursor_json']).items() if not k.startswith('_')}}
                             for s in db.execute('SELECT * FROM workflow_steps WHERE job_id=? ORDER BY id', (job['id'],))],
                      artifacts=[{k: a[k] for k in ('id', 'step_id', 'artifact_kind', 'artifact_key', 'schema_version', 'input_sha256', 'output_sha256', 'created_at')} |
                                 {'payload': json.loads(a['payload_json'])} for a in artifacts])
        return result

    def detail(self, tender_id, job_id):
        with self.write() as db:
            return self.detail_in(db, self.job(db, tender_id, job_id))

    def list(self, tender_id):
        with self.write() as db:
            self.d.require(db, 'tenders', tender_id)
            rows = [dict(x) for x in db.execute('SELECT * FROM workflow_jobs WHERE tender_id=? ORDER BY id DESC', (tender_id,))]
            summaries = []
            for job in rows:
                currency = self.currency(db, job)
                job = self.stale(db, job, currency)
                summaries.append({k: job[k] for k in ('id', 'tender_id', 'state', 'processor_kind', 'contract_version', 'created_at', 'updated_at', 'step_runs', 'last_error_code')} |
                                 {'processor_label': 'Local rules', 'autonomous_ai_agent': False, 'currency': currency})
            return summaries

    def _exhaust(self, db, job, code='INCOMPLETE_BOUND'):
        db.execute("UPDATE workflow_jobs SET state='BUDGET_EXHAUSTED',revision=revision+1,last_error_code=?,updated_at=? WHERE id=?",
                   (code, timestamp(), job['id']))
        db.execute("UPDATE workflow_steps SET state='CANCELLED',fence=fence+1,lease_owner=NULL,lease_expires_at=NULL WHERE job_id=? AND state IN ('READY','BLOCKED','RUNNING')", (job['id'],))
        self.event(db, job['id'], 'BUDGET_EXHAUSTED', {'code': code})

    def claim(self, tender_id, job_id):
        with self.write() as db:
            job = self.job(db, tender_id, job_id)
            job = self.stale(db, job, self.currency(db, job))
            if job['state'] in TERMINAL:
                return None
            active = db.execute("SELECT * FROM workflow_steps WHERE job_id=? AND state='RUNNING' ORDER BY id LIMIT 1", (job_id,)).fetchone()
            if active:
                active = dict(active)
                if active['lease_expires_at'] > timestamp():
                    return None
                # Reservation was charged at claim and remains charged after a crash.
                recovered_state = 'READY' if active['attempt_count'] < 2 else 'FAILED'
                db.execute('UPDATE workflow_steps SET state=?,fence=fence+1,lease_owner=NULL,lease_expires_at=NULL,last_error_code=? WHERE id=?',
                           (recovered_state, 'LEASE_EXPIRED', active['id']))
                db.execute('UPDATE workflow_jobs SET state=?,revision=revision+1,last_error_code=?,updated_at=? WHERE id=?',
                           ('READY' if recovered_state == 'READY' else 'FAILED', None if recovered_state == 'READY' else 'ATTEMPTS_EXHAUSTED', timestamp(), job_id))
                self.event(db, job_id, 'LEASE_RECOVERED', {'fence': active['fence'] + 1, 'attempt': active['attempt_count'], 'reservation_charged_ms': LIMITS['batch_reservation_ms']}, active['id'])
                job = self.job(db, tender_id, job_id)
                if recovered_state == 'FAILED':
                    return None
            if job['step_runs'] >= LIMITS['max_step_runs'] or job['elapsed_ms'] + LIMITS['batch_reservation_ms'] > LIMITS['max_elapsed_ms']:
                self._exhaust(db, job)
                return None
            row = db.execute("SELECT * FROM workflow_steps WHERE job_id=? AND state='READY' ORDER BY id LIMIT 1", (job_id,)).fetchone()
            if not row:
                return None
            step = dict(row)
            if step['attempt_count'] >= 2:
                db.execute("UPDATE workflow_jobs SET state='FAILED',last_error_code='ATTEMPTS_EXHAUSTED',updated_at=? WHERE id=?", (timestamp(), job_id))
                return None
            owner = uuid.uuid4().hex
            deadline = (datetime.now(timezone.utc) + timedelta(seconds=LIMITS['lease_seconds'])).isoformat(timespec='milliseconds')
            cursor = json.loads(step['cursor_json'])
            cursor['_reservation_ms'] = LIMITS['batch_reservation_ms']
            claimed = db.execute("UPDATE workflow_steps SET state='RUNNING',attempt_count=attempt_count+1,fence=fence+1,lease_owner=?,lease_expires_at=?,started_at=?,cursor_json=? WHERE id=? AND state='READY' AND fence=?",
                                 (owner, deadline, timestamp(), canonical(cursor), step['id'], step['fence']))
            if claimed.rowcount != 1:
                raise HTTPException(409, 'Task was claimed elsewhere; reload saved analysis')
            updated = db.execute("UPDATE workflow_jobs SET state='RUNNING',revision=revision+1,step_runs=step_runs+1,elapsed_ms=elapsed_ms+?,last_error_code=NULL,updated_at=? WHERE id=? AND revision=? AND cancel_requested=0",
                                 (LIMITS['batch_reservation_ms'], timestamp(), job_id, job['revision']))
            if updated.rowcount != 1:
                raise HTTPException(409, 'Workflow changed; reload saved analysis')
            self.event(db, job_id, 'ATTEMPT_STARTED', {'application_attempt_id': owner, 'fence': step['fence'] + 1,
                       'cursor': {k: v for k, v in cursor.items() if not k.startswith('_')}, 'attempt': step['attempt_count'] + 1,
                       'reservation_ms': LIMITS['batch_reservation_ms'], 'executor': 'SYSTEM:local-rules',
                       'autonomous_ai_agent': False}, step['id'])
            step.update(fence=step['fence'] + 1, lease_owner=owner, lease_expires_at=deadline, cursor_json=canonical(cursor))
            return {'job': self.job(db, tender_id, job_id), 'step': step, 'artifacts': self.artifacts(db, job_id)}

    def source(self, tender_id, frozen_source):
        with self.d.conn() as db:
            raw = db.execute('SELECT * FROM sources WHERE id=? AND tender_id=?', (frozen_source['id'], tender_id)).fetchone()
            if not raw or raw['sha256'] != frozen_source['sha256'] or raw['bytes'] != frozen_source['bytes'] or raw['pages'] != frozen_source['pages']:
                raise HTTPException(409, 'Source metadata changed')
            registered = dict(raw)
        return self.d.checked_pdf(self.d.read_registered_pdf(registered))

    def _payloads(self, claim, kind):
        return [json.loads(a['payload_json']) for a in claim['artifacts'] if a['artifact_kind'] == kind]

    def compute(self, claim):
        job, step = claim['job'], claim['step']
        manifest = json.loads(job['input_manifest'])
        cursor = json.loads(step['cursor_json'])
        index = cursor.get('index', 0)
        kind = step['task_kind']
        issues = []
        if kind == 'SOURCE_INSPECT':
            pages = [(source, p) for source in manifest['source_scope']['sources'] for p in range(1, source['pages'] + 1)]
            selected = pages[index:index + LIMITS['pages_per_batch']]
            results, readers = [], {}
            for source, page in selected:
                if source['id'] not in readers:
                    readers[source['id']] = self.source(job['tender_id'], source)
                status, text = 'TEXT_READY', ''
                try:
                    text = readers[source['id']].pages[page - 1].extract_text() or ''
                except Exception:
                    status = 'EXTRACTION_FAILED'
                count = len(text)
                if status == 'TEXT_READY' and not text.strip():
                    status = 'NEEDS_OCR'
                elif status == 'TEXT_READY' and len(text.strip()) < 30:
                    status = 'NEEDS_MANUAL_REVIEW'
                if count > LIMITS['max_page_characters'] or len(text.encode('utf-8')) + 500 > LIMITS['max_page_payload_bytes']:
                    status, text = 'INCOMPLETE_BOUND', ''
                if status != 'TEXT_READY':
                    issues.append({'code': status, 'source_id': source['id'], 'page': page,
                                   'message': 'This page needs a readable replacement or explicit manual source review; extraction does not prove completeness.'})
                page_record = {'source_id': source['id'], 'source_sha256': source['sha256'], 'page': page, 'text': text,
                               'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'character_count': count,
                               'coverage_status': status}
                if len(canonical(page_record).encode('utf-8')) > LIMITS['max_page_payload_bytes']:
                    status, text = 'INCOMPLETE_BOUND', ''
                    issues.append({'code': status, 'source_id': source['id'], 'page': page,
                                   'message': 'Canonical page record exceeds the per-page payload limit; extracted text was omitted for review.'})
                    page_record = {'source_id': source['id'], 'source_sha256': source['sha256'], 'page': page, 'text': text,
                                   'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'character_count': count,
                                   'coverage_status': status}
                results.append(page_record)
            payload = {'schema_version': 'source_batch_v1', 'source_input_sha256': manifest['source_input_sha256'], 'pages': results, 'issues': issues}
            return 'SOURCE_BATCH', payload, index + len(selected), index + len(selected) >= len(pages)
        if kind == 'REQUIREMENT_CANDIDATES':
            batches = self._payloads(claim, 'SOURCE_BATCH')
            selected = batches[index:index + 1]
            candidates, seen = [], set()
            for batch in selected:
                for page in batch['pages']:
                    if page['coverage_status'] in ('EXTRACTION_FAILED', 'INCOMPLETE_BOUND', 'NEEDS_OCR'):
                        continue
                    for line in page['text'].splitlines():
                        quote = whitespace(line)
                        if len(quote) < 12 or not PATTERN.search(quote):
                            continue
                        if len(quote) > LIMITS['max_quote_characters']:
                            issues.append({'code': 'INCOMPLETE_BOUND', 'source_id': page['source_id'], 'page': page['page'],
                                           'message': 'A requirement-shaped text span exceeds the candidate size limit; review the original page.'})
                            continue
                        key = digest({'source_input_sha256': manifest['source_input_sha256'], 'source_sha256': page['source_sha256'],
                                      'source_id': page['source_id'], 'page': page['page'], 'quote': quote})
                        if key in seen:
                            continue
                        seen.add(key)
                        candidates.append({'candidate_key': key, 'source_id': page['source_id'], 'source_sha256': page['source_sha256'],
                                           'page': page['page'], 'verbatim_quote': quote, 'proposed_text': quote, 'category_candidate': 'REVIEW_REQUIRED',
                                           'mandatory_candidate': None, 'uncertainty_notes': 'Keyword suggestion only. A human must check context, conditions and mandatory status.', 'processor': 'RULES'})
            count = sum(len(b.get('candidates', [])) for b in self._payloads(claim, 'REQUIREMENT_CANDIDATES'))
            if count + len(candidates) > LIMITS['max_candidates']:
                raise WorkflowBound('CANDIDATE_LIMIT')
            payload = {'schema_version': 'candidate_batch_v1', 'source_input_sha256': manifest['source_input_sha256'], 'candidates': candidates, 'issues': issues}
            return 'REQUIREMENT_CANDIDATES', payload, index + len(selected), index + len(selected) >= len(batches)
        candidates = [c for b in self._payloads(claim, 'REQUIREMENT_CANDIDATES') for c in b['candidates']]
        targets = [{'key': 'requirement:' + str(r['id']), 'text': r['text'], 'source_id': r['source_id'], 'page': r['source_page'], 'verbatim_quote': r['source_quote']} for r in manifest['requirements']] + [dict(c, key=c['candidate_key'], text=c['proposed_text']) for c in candidates]
        selected = targets[index:index + LIMITS['targets_per_batch']]
        if kind == 'EVIDENCE_RELEVANCE':
            suggestions, unmatched = [], []
            for target in selected:
                relevant = []
                for evidence in manifest['evidence']:
                    terms = sorted(tokens(target['text']) & tokens(evidence['label'] + ' ' + evidence['reference']))
                    if not terms:
                        continue
                    file = evidence['latest_file']
                    conditions = ['Metadata overlap does not demonstrate substantive compliance; inspect the evidence.']
                    if not file:
                        conditions.append('No private evidence document is registered.')
                    if not evidence['verification_current']:
                        conditions.append('Evidence lacks current human document verification or has expired.')
                    expiry = ('EXPIRED' if evidence['expires_on'] < manifest['as_of_date'] else 'NOT_EXPIRED') if evidence['expires_on'] else 'NO_EXPIRY_RECORDED'
                    relevant.append({'requirement_or_candidate_key': target['key'], 'evidence_id': evidence['id'], 'file_id': file['id'] if file else None,
                                     'file_sha256': file['sha256'] if file else None, 'overlap_terms': terms,
                                     'matching_rule': 'metadata_token_overlap_v1', 'rationale': 'Shared words in requirement text and evidence label/reference.',
                                     'unresolved_conditions': conditions, 'expiry_state': expiry, 'suggested_only': True})
                relevant.sort(key=lambda s: (-len(s['overlap_terms']), s['evidence_id']))
                suggestions.extend(relevant[:LIMITS['matches_per_target']])
                if not relevant:
                    unmatched.append(target['key'])
            payload = {'schema_version': 'evidence_batch_v1', 'full_input_sha256': job['input_sha256'], 'suggestions': suggestions, 'unmatched_target_keys': unmatched, 'issues': []}
            return 'EVIDENCE_SUGGESTIONS', payload, index + len(selected), index + len(selected) >= len(targets)
        if kind == 'CITATION_CHECK':
            sources = {s['id']: s for s in manifest['source_scope']['sources']}
            checks, readers = [], {}
            for target in selected:
                source = sources.get(target['source_id'])
                status, reason, checked_hash = 'CITATION_INVALID', 'Source/page/quote provenance is incomplete.', None
                if source and type(target['page']) is int and 1 <= target['page'] <= source['pages']:
                    try:
                        if source['id'] not in readers:
                            readers[source['id']] = self.source(job['tender_id'], source)
                        # Independently re-read the original, not the extracted artifact.
                        actual = whitespace(readers[source['id']].pages[target['page'] - 1].extract_text() or '')
                        quote = whitespace(target['verbatim_quote'] or '')
                        checked_hash = source['sha256']
                        if len(quote) >= 5 and quote in actual:
                            status, reason = 'CITATION_VALID', 'Exact whitespace-normalized quote found on the registered source page; substantive review is still required.'
                        else:
                            reason = 'The quote was not found on the original page.'
                    except HTTPException as error:
                        status = 'SOURCE_CHANGED' if error.status_code == 409 else 'UNREADABLE'
                        reason = 'The registered source could not be safely verified.'
                    except Exception:
                        status, reason = 'UNREADABLE', 'The source page could not be independently extracted.'
                checks.append({'target_key': target['key'], 'status': status, 'source_id': target['source_id'] or 0, 'page': target['page'] or 0,
                               'verified_document_sha256': checked_hash, 'reason': reason})
            # The matcher only used metadata. Check scope and exact latest file
            # version without presenting metadata checks as content verification.
            selected_keys = {target['key'] for target in selected}
            matches = [s for b in self._payloads(claim, 'EVIDENCE_SUGGESTIONS') for s in b['suggestions'] if s['requirement_or_candidate_key'] in selected_keys]
            versions, seen_versions = [], set()
            with self.d.conn() as db:
                for suggestion in matches:
                    pair = (suggestion['evidence_id'], suggestion['file_id'])
                    if pair in seen_versions:
                        continue
                    seen_versions.add(pair)
                    evidence = db.execute('SELECT id FROM evidence WHERE id=? AND organization_id=?', (pair[0], job['organization_id'])).fetchone()
                    latest = db.execute('SELECT id,sha256 FROM evidence_files WHERE evidence_id=? ORDER BY id DESC LIMIT 1', (pair[0],)).fetchone() if evidence else None
                    valid = bool(evidence and ((latest is None and pair[1] is None) or
                                 (latest and latest['id'] == pair[1] and latest['sha256'] == suggestion['file_sha256'])))
                    versions.append({'schema_version': 'evidence_version_check_v1',
                                     'evidence_id': pair[0], 'file_id': pair[1], 'file_sha256': suggestion['file_sha256'],
                                     'status': 'current' if valid else 'evidence_changed',
                                     'content_verified': False, 'reason': 'Organization and latest registered file version checked; metadata matching does not verify document content.'})
            payload = {'schema_version': 'citation_batch_v1', 'full_input_sha256': job['input_sha256'], 'source_input_sha256': manifest['source_input_sha256'], 'checks': checks,
                       'evidence_version_checks': versions, 'issues': []}
            return 'CITATION_CHECKS', payload, index + len(selected), index + len(selected) >= len(targets)
        raise RuntimeError('Unregistered task')

    def advance(self, tender_id, job_id):
        claim = self.claim(tender_id, job_id)
        if not claim:
            return self.detail(tender_id, job_id)
        started = time.monotonic()
        output, error = None, None
        try:
            output = self.compute(claim)
            output = (output[0], ARTIFACT_SCHEMAS[output[0]].model_validate(output[1]).model_dump(), output[2], output[3])
        except WorkflowBound as err:
            error = err.code
        except HTTPException as err:
            error = {409: 'INTEGRITY_FAILED', 422: 'PARSE_FAILED', 503: 'DOCUMENT_UNAVAILABLE'}.get(err.status_code, 'PROCESSING_FAILED')
        except Exception:
            error = 'OUTPUT_INVALID'
        elapsed = max(1, int((time.monotonic() - started) * 1000))
        self.publish(claim, output, elapsed, error)
        return self.detail(tender_id, job_id)

    def publish(self, claim, output, elapsed, error):
        claimed_job, claimed_step = claim['job'], claim['step']
        with self.write() as db:
            job = self.job(db, claimed_job['tender_id'], claimed_job['id'])
            step = dict(db.execute('SELECT * FROM workflow_steps WHERE id=? AND job_id=?', (claimed_step['id'], job['id'])).fetchone())
            valid = (job['revision'] == claimed_job['revision'] and job['state'] == 'RUNNING' and not job['cancel_requested']
                     and step['state'] == 'RUNNING' and step['fence'] == claimed_step['fence']
                     and step['lease_owner'] == claimed_step['lease_owner'] and step['lease_expires_at'] > timestamp())
            if not valid:
                return False
            currency = self.currency(db, job)
            if not currency['full_current']:
                self.stale(db, job, currency)
                return False
            actual_charge = max(elapsed, 1)
            reserved = LIMITS['batch_reservation_ms']
            charged = job['elapsed_ms'] - reserved + actual_charge
            db.execute('UPDATE workflow_jobs SET elapsed_ms=?,updated_at=? WHERE id=?', (charged, timestamp(), job['id']))
            job['elapsed_ms'] = charged
            if charged > LIMITS['max_elapsed_ms']:
                self._exhaust(db, job, 'TIME_LIMIT')
                return False
            if error in {'CANDIDATE_LIMIT', 'ARTIFACT_LIMIT'}:
                self._exhaust(db, job, error)
                return False
            if error:
                state = 'READY' if step['attempt_count'] < 2 else 'FAILED'
                db.execute('UPDATE workflow_steps SET state=?,elapsed_ms=elapsed_ms+?,lease_owner=NULL,lease_expires_at=NULL,last_error_code=? WHERE id=?', (state, elapsed, error, step['id']))
                db.execute('UPDATE workflow_jobs SET state=?,revision=revision+1,last_error_code=?,updated_at=? WHERE id=?', (state, error, timestamp(), job['id']))
                self.event(db, job['id'], 'ATTEMPT_FAILED', {'code': error, 'elapsed_ms': elapsed, 'application_attempt_id': claimed_step['lease_owner']}, step['id'])
                return False
            kind, payload, next_index, complete = output
            encoded = canonical(payload)
            size = sum(len(a['payload_json'].encode('utf-8')) for a in self.artifacts(db, job['id'])) + len(encoded.encode('utf-8'))
            if size > LIMITS['max_artifact_bytes']:
                self._exhaust(db, job, 'ARTIFACT_LIMIT')
                return False
            old_index = json.loads(claimed_step['cursor_json']).get('index', 0)
            key = step['task_key'] + ':' + str(old_index)
            input_hash = json.loads(job['input_manifest'])['source_input_sha256'] if kind in ('SOURCE_BATCH', 'REQUIREMENT_CANDIDATES') else job['input_sha256']
            db.execute('''INSERT INTO workflow_artifacts(job_id,step_id,artifact_key,artifact_kind,schema_version,input_sha256,payload_json,output_sha256,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)''', (job['id'], step['id'], key, kind, payload['schema_version'], input_hash, encoded, digest(payload), timestamp()))
            step_state = 'SUCCEEDED' if complete else 'READY'
            db.execute('UPDATE workflow_steps SET state=?,cursor_json=?,attempt_count=0,elapsed_ms=elapsed_ms+?,lease_owner=NULL,lease_expires_at=NULL,last_error_code=NULL,completed_at=? WHERE id=?',
                       (step_state, canonical({'index': next_index}), elapsed, timestamp() if complete else None, step['id']))
            job_state = 'READY'
            if complete:
                db.execute("UPDATE workflow_steps SET state='READY' WHERE job_id=? AND predecessor_step_id=? AND state='BLOCKED'", (job['id'], step['id']))
                if step['task_kind'] == 'CITATION_CHECK':
                    job_state = 'WAITING_HUMAN'
                    receipt = self.receipt_in(db, job, state_at_capture=job_state)
                    receipt_encoded = canonical(receipt)
                    # The receipt is itself a stored artifact and includes the
                    # citation output just published above. Charge both against
                    # the same aggregate bound before making the run reviewable.
                    with_receipt = sum(len(a['payload_json'].encode('utf-8')) for a in self.artifacts(db, job['id']))
                    with_receipt += len(receipt_encoded.encode('utf-8'))
                    if with_receipt > LIMITS['max_artifact_bytes']:
                        # Keep the bounded citation artifact for inspection, but
                        # do not claim the run reached its human gate without a
                        # frozen receipt. The final task failed to publish its
                        # complete bounded result.
                        db.execute("UPDATE workflow_steps SET state='FAILED',last_error_code='ARTIFACT_LIMIT' WHERE id=?", (step['id'],))
                        self.event(db, job['id'], 'BATCH_PUBLISHED', {'artifact_key': key, 'output_sha256': digest(payload), 'elapsed_ms': elapsed,
                                    'next_index': next_index, 'stage_complete': complete, 'application_attempt_id': claimed_step['lease_owner']}, step['id'])
                        self._exhaust(db, job, 'ARTIFACT_LIMIT')
                        return False
                    db.execute('''INSERT INTO workflow_artifacts(job_id,step_id,artifact_key,artifact_kind,schema_version,input_sha256,payload_json,output_sha256,created_at)
                        VALUES(?,?,?,?,?,?,?,?,?)''', (job['id'], step['id'], 'run_receipt:v1', 'RUN_RECEIPT', 'run_receipt_v1', job['input_sha256'], receipt_encoded, digest(receipt), timestamp()))
            db.execute('UPDATE workflow_jobs SET state=?,revision=revision+1,last_error_code=NULL,updated_at=? WHERE id=?', (job_state, timestamp(), job['id']))
            self.event(db, job['id'], 'BATCH_PUBLISHED', {'artifact_key': key, 'output_sha256': digest(payload), 'elapsed_ms': elapsed,
                        'next_index': next_index, 'stage_complete': complete, 'application_attempt_id': claimed_step['lease_owner']}, step['id'])
            return True

    def cancel(self, tender_id, job_id):
        with self.write() as db:
            job = self.job(db, tender_id, job_id)
            if job['state'] != 'CANCELLED':
                db.execute("UPDATE workflow_jobs SET state='CANCELLED',cancel_requested=1,revision=revision+1,updated_at=?,completed_at=? WHERE id=?", (timestamp(), timestamp(), job_id))
                db.execute("UPDATE workflow_steps SET state='CANCELLED',fence=fence+1,lease_owner=NULL,lease_expires_at=NULL WHERE job_id=? AND state IN ('READY','BLOCKED','RUNNING')", (job_id,))
                self.event(db, job_id, 'CANCELLED', {'retained_artifacts': True}, actor=self.d.authenticated_actor())
            return self.detail_in(db, self.job(db, tender_id, job_id))

    def review(self, tender_id, job_id, key, request):
        with self.write() as db:
            job = self.job(db, tender_id, job_id)
            detail = self.detail_in(db, job)
            prior = db.execute('SELECT * FROM workflow_candidate_reviews WHERE job_id=? AND candidate_key=?', (job_id, key)).fetchone()
            if prior:
                action = 'REJECT' if prior['disposition'] == 'REJECTED' else 'ACCEPT'
                if action != request.disposition:
                    raise HTTPException(409, 'Candidate disposition is immutable')
                return detail
            if detail['state'] not in ('WAITING_HUMAN', 'STALE', 'COMPLETED'):
                raise HTTPException(409, 'Finish citation checks before reviewing candidates')
            candidate = next((c for c in detail['candidates'] if c['candidate_key'] == key), None)
            if not candidate:
                raise HTTPException(404, 'Candidate not found in this workflow')
            artifact = next(a for a in detail['artifacts'] if a['artifact_kind'] == 'REQUIREMENT_CANDIDATES'
                            and any(c['candidate_key'] == key for c in a['payload']['candidates']))
            disposition, req_id = 'REJECTED', None
            if request.disposition == 'ACCEPT':
                if not detail['currency']['source_current']:
                    raise HTTPException(409, 'Source inputs changed; restart analysis before accepting suggestions')
                if candidate['citation_status'] != 'CITATION_VALID':
                    raise HTTPException(409, 'An independently checked source citation is required')
                proposed = SimpleNamespace(source_id=candidate['source_id'], source_page=candidate['page'],
                                           source_quote=candidate['verbatim_quote'], text=candidate['proposed_text'])
                self.d.validate_requirement_source(db, tender_id, proposed)
                existing = [dict(r) for r in db.execute('SELECT id,source_quote FROM requirements WHERE tender_id=? AND source_id=? AND source_page=?',
                                                       (tender_id, proposed.source_id, proposed.source_page))]
                duplicate = next((r for r in existing if whitespace(r['source_quote'] or '') == whitespace(proposed.source_quote)), None)
                if duplicate:
                    disposition, req_id = 'DUPLICATE', duplicate['id']
                else:
                    created = timestamp()
                    cur = db.execute('''INSERT INTO requirements(tender_id,source_id,source_page,source_quote,text,mandatory,reviewed,extraction_method,status,created_at,updated_at)
                        VALUES(?,?,?,?,?,NULL,0,'rules_workflow_v1','UNKNOWN',?,?)''',
                        (tender_id, proposed.source_id, proposed.source_page, proposed.source_quote, proposed.text, created, created))
                    disposition, req_id = 'ACCEPTED', cur.lastrowid
            db.execute('''INSERT INTO workflow_candidate_reviews(job_id,artifact_id,candidate_key,disposition,reviewer,note,requirement_id,reviewed_at)
                VALUES(?,?,?,?,?,?,?,?)''', (job_id, artifact['id'], key, disposition, self.d.authenticated_actor(), request.note.strip(), req_id, timestamp()))
            self.event(db, job_id, 'CANDIDATE_REVIEWED', {'candidate_key': key, 'disposition': disposition, 'requirement_id': req_id,
                        'note_sha256': digest(request.note.strip())}, actor=self.d.authenticated_actor())
            self.d.log(db, tender_id, 'workflow_candidate_human_reviewed', {'job_id': job_id, 'candidate_key': key, 'disposition': disposition, 'requirement_id': req_id})
            remaining = len(detail['candidates']) - db.execute('SELECT COUNT(*) AS n FROM workflow_candidate_reviews WHERE job_id=?', (job_id,)).fetchone()['n']
            # Newly accepted requirements change full currency; source artifacts
            # remain reviewable. Completion never substitutes for eligibility.
            current = self.currency(db, self.job(db, tender_id, job_id))
            if remaining == 0 and current['full_current']:
                db.execute("UPDATE workflow_jobs SET state='COMPLETED',revision=revision+1,updated_at=?,completed_at=? WHERE id=?", (timestamp(), timestamp(), job_id))
            return self.detail_in(db, self.job(db, tender_id, job_id))

    def receipt_in(self, db, job, state_at_capture=None):
        manifest = json.loads(job['input_manifest'])
        artifacts = self.artifacts(db, job['id'])
        return {
            'schema_version': 'run_receipt_v1', 'job_id': job['id'], 'tender_id': job['tender_id'],
            'processor_kind': 'RULES', 'executor_label': 'SYSTEM:local-rules', 'autonomous_ai_agent': False,
            'platform_agent_id': None, 'platform_run_id': None, 'platform_trace_id': None,
            'contract_version': job['contract_version'], 'state_at_capture': state_at_capture or job['state'],
            'input_sha256': job['input_sha256'], 'source_input_sha256': manifest['source_input_sha256'],
            'policy_sha256': job['policy_sha256'], 'policy': json.loads(job['policy_manifest']),
            'sources': [{k: s[k] for k in ('id', 'sha256', 'bytes', 'pages')} for s in manifest['source_scope']['sources']],
            'evidence_file_versions': [{'evidence_id': e['id'], 'file_id': e['latest_file']['id'], 'sha256': e['latest_file']['sha256']} for e in manifest['evidence'] if e['latest_file']],
            'artifacts': [{k: a[k] for k in ('id', 'step_id', 'artifact_key', 'artifact_kind', 'input_sha256', 'output_sha256', 'created_at')} for a in artifacts if a['artifact_kind'] != 'RUN_RECEIPT'],
            'usage': {'step_runs': job['step_runs'], 'elapsed_ms': job['elapsed_ms'], 'external_model_calls': 0, 'model_spend_minor': 0},
            'limitations': ['No model inference or automatic approval.', 'Text extraction is not OCR or proof of requirement completeness.',
                            'No unattended scheduler; advance requests must resume saved work.', 'Parser is bounded cooperatively; no hard process resource isolation.'],
        }

    def receipt(self, tender_id, job_id):
        with self.write() as db:
            job = self.job(db, tender_id, job_id)
            currency = self.currency(db, job)
            job = self.stale(db, job, currency)
            return {'receipt': self.receipt_in(db, job), 'currency_at_export': currency,
                    'events': [dict(e) | {'event': json.loads(e['event_json'])} for e in db.execute(
                        'SELECT id,step_id,actor,action,event_json,created_at FROM workflow_events WHERE job_id=? ORDER BY id', (job_id,))]}


class WorkflowBound(RuntimeError):
    def __init__(self, code):
        self.code = code
