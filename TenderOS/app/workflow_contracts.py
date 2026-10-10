"""Fixed contracts for document tools; document content never configures tools."""
import hashlib
import json
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION = 'tenderos_rules_review_v1'
TASKS = ('SOURCE_INSPECT', 'REQUIREMENT_CANDIDATES', 'EVIDENCE_RELEVANCE', 'CITATION_CHECK')
LIMITS = {
    'max_sources': 20, 'max_source_pages': 300, 'pages_per_batch': 10,
    'max_candidates': 1000, 'max_step_runs': 128, 'max_elapsed_ms': 180000,
    'batch_reservation_ms': 15000, 'lease_seconds': 45,
    'max_page_payload_bytes': 65536, 'max_artifact_bytes': 5 * 1024 * 1024,
    'max_page_characters': 20000, 'max_quote_characters': 4000,
    'max_requirements': 1000, 'max_evidence_records': 500,
    'max_input_manifest_bytes': 2 * 1024 * 1024,
    'matches_per_target': 5, 'targets_per_batch': 25,
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def policy(hosted=False):
    return {
        'version': CONTRACT_VERSION, 'processor_kind': 'RULES',
        'external_model_calls': False, 'model_spend_cap_minor': 0,
        'training_allowed': False, 'model_configuration_editable': False,
        'send_messages_allowed': False, 'payments_allowed': False,
        'bid_submission_allowed': False, 'approval_actions_allowed': False,
        'processor_egress': 'registered_database_and_private_documents_only' if hosted else 'none',
        'infrastructure_cost_status': 'UNKNOWN' if hosted else 'NOT_RECORDED',
        'limits': dict(LIMITS),
        'advancement': 'bounded_authenticated_requests; resume required when client stops',
    }


def processors(hosted=False):
    return {'policy': policy(hosted), 'processors': [
        {'kind': 'RULES', 'status': 'AVAILABLE', 'label': 'Local rules',
         'autonomous_ai_agent': False, 'model_usage_charges': 0},
        {'kind': 'LOCAL_MODEL', 'status': 'UNCONFIGURED', 'label': 'Local model',
         'autonomous_ai_agent': False,
         'reason': 'No permitted local model processor is configured. No provider is contacted.'},
    ]}


class FixedModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class WorkflowCreate(FixedModel):
    processor_kind: Literal['RULES'] = 'RULES'


class CandidateReview(FixedModel):
    disposition: Literal['ACCEPT', 'REJECT']
    note: str = Field(min_length=5, max_length=2000)


class Issue(FixedModel):
    code: str
    message: str
    source_id: Optional[int] = None
    page: Optional[int] = None


class SourcePage(FixedModel):
    source_id: int
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    page: int = Field(ge=1)
    text: str
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    character_count: int = Field(ge=0)
    coverage_status: Literal['TEXT_READY', 'NEEDS_OCR', 'NEEDS_MANUAL_REVIEW', 'EXTRACTION_FAILED', 'INCOMPLETE_BOUND']


class SourceBatch(FixedModel):
    schema_version: Literal['source_batch_v1'] = 'source_batch_v1'
    source_input_sha256: str
    pages: list[SourcePage]
    issues: list[Issue]


class Candidate(FixedModel):
    candidate_key: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_id: int
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    page: int = Field(ge=1)
    verbatim_quote: str = Field(min_length=5, max_length=4000)
    proposed_text: str = Field(min_length=5, max_length=4000)
    category_candidate: str
    mandatory_candidate: None = None
    uncertainty_notes: str
    processor: Literal['RULES'] = 'RULES'


class CandidateBatch(FixedModel):
    schema_version: Literal['candidate_batch_v1'] = 'candidate_batch_v1'
    source_input_sha256: str
    candidates: list[Candidate]
    issues: list[Issue]


class EvidenceSuggestion(FixedModel):
    requirement_or_candidate_key: str
    evidence_id: int
    file_id: Optional[int]
    file_sha256: Optional[str]
    overlap_terms: list[str]
    matching_rule: Literal['metadata_token_overlap_v1'] = 'metadata_token_overlap_v1'
    rationale: str
    unresolved_conditions: list[str]
    expiry_state: Literal['EXPIRED', 'NOT_EXPIRED', 'NO_EXPIRY_RECORDED']
    suggested_only: Literal[True] = True


class EvidenceBatch(FixedModel):
    schema_version: Literal['evidence_batch_v1'] = 'evidence_batch_v1'
    full_input_sha256: str
    suggestions: list[EvidenceSuggestion]
    unmatched_target_keys: list[str]
    issues: list[Issue]


class CitationItem(FixedModel):
    target_key: str
    status: Literal['CITATION_VALID', 'CITATION_INVALID', 'SOURCE_CHANGED', 'EVIDENCE_CHANGED', 'UNREADABLE']
    source_id: int
    page: int
    verified_document_sha256: Optional[str]
    reason: str


class EvidenceVersionCheck(FixedModel):
    schema_version: Literal['evidence_version_check_v1'] = 'evidence_version_check_v1'
    evidence_id: int = Field(gt=0)
    file_id: Optional[int] = Field(default=None, gt=0)
    file_sha256: Optional[str] = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    status: Literal['current', 'evidence_changed']
    content_verified: Literal[False] = False
    reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode='after')
    def validate_file_pair(self):
        # A file identity and its digest are one frozen pair. Both may be null
        # when the evidence record has no registered document.
        if (self.file_id is None) != (self.file_sha256 is None):
            raise ValueError('file_id and file_sha256 must both be present or both be null')
        return self


class CitationBatch(FixedModel):
    schema_version: Literal['citation_batch_v1'] = 'citation_batch_v1'
    full_input_sha256: str
    source_input_sha256: str
    checks: list[CitationItem]
    evidence_version_checks: list[EvidenceVersionCheck]
    issues: list[Issue]


ARTIFACT_SCHEMAS = {
    'SOURCE_BATCH': SourceBatch, 'REQUIREMENT_CANDIDATES': CandidateBatch,
    'EVIDENCE_SUGGESTIONS': EvidenceBatch, 'CITATION_CHECKS': CitationBatch,
}
