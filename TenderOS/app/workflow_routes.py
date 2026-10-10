"""Owner-authenticated HTTP boundary for the fixed document workflow."""
from fastapi import Header
from fastapi.responses import Response

from .workflow_contracts import CandidateReview, WorkflowCreate, canonical, processors
from .workflows import WorkflowEngine


def register_routes(app, domain):
    engine = WorkflowEngine(domain)
    app.state.workflow_engine = engine

    @app.get('/api/processors')
    def processor_status():
        return processors(domain.HOSTED)

    @app.get('/api/tenders/{tender_id}/workflows')
    def workflows(tender_id: int):
        return engine.list(tender_id)

    @app.post('/api/tenders/{tender_id}/workflows', status_code=201)
    def create(tender_id: int, item: WorkflowCreate, idempotency_key: str = Header(default='', alias='Idempotency-Key')):
        return engine.create(tender_id, idempotency_key, item.model_dump())

    @app.get('/api/tenders/{tender_id}/workflows/{job_id}')
    def detail(tender_id: int, job_id: int):
        return engine.detail(tender_id, job_id)

    @app.post('/api/tenders/{tender_id}/workflows/{job_id}/advance')
    def advance(tender_id: int, job_id: int):
        return engine.advance(tender_id, job_id)

    @app.post('/api/tenders/{tender_id}/workflows/{job_id}/cancel')
    def cancel(tender_id: int, job_id: int):
        return engine.cancel(tender_id, job_id)

    @app.post('/api/tenders/{tender_id}/workflows/{job_id}/restart', status_code=201)
    def restart(tender_id: int, job_id: int, item: WorkflowCreate,
                idempotency_key: str = Header(default='', alias='Idempotency-Key')):
        return engine.create(tender_id, idempotency_key, item.model_dump(), restart_of=job_id)

    @app.post('/api/tenders/{tender_id}/workflows/{job_id}/candidates/{candidate_key}/review')
    def review(tender_id: int, job_id: int, candidate_key: str, item: CandidateReview):
        return engine.review(tender_id, job_id, candidate_key, item)

    @app.get('/api/tenders/{tender_id}/workflows/{job_id}/receipt.json')
    def receipt(tender_id: int, job_id: int):
        return Response(canonical(engine.receipt(tender_id, job_id)), media_type='application/json',
                        headers={'Content-Disposition': f'attachment; filename="tenderos-workflow-{job_id}-receipt.json"'})
