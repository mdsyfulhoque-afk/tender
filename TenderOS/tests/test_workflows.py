import io
import sqlite3
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from app import main

@pytest.fixture
def client(tmp_path,monkeypatch):
    db=tmp_path/'test.db';storage=tmp_path/'uploads';storage.mkdir()
    monkeypatch.setattr(main,'DB',db);monkeypatch.setattr(main,'STORAGE',storage)
    with sqlite3.connect(db) as cx:
        cx.executescript(main.SCHEMA)
    return TestClient(main.app)

def add_org(client,name='Test Consulting'):
    x=client.post('/api/organizations',json={'name':name});assert x.status_code==201,x.text
    return x.json()['id']

def add_tender(client,org):
    x=client.post('/api/tenders',json={'organization_id':org,'title':'Synthetic consulting assignment'})
    assert x.status_code==201,x.text
    return x.json()['id']

def add_req(client,tender,mandatory=True):
    x=client.post(f'/api/tenders/{tender}/requirements',json={'text':'Three similar projects must be documented', 'source_page':2,'source_quote':'Three similar projects must be documented'})
    assert x.status_code==201,x.text
    req=x.json()['id']
    if mandatory is not None:
        x=client.put(f'/api/requirements/{req}/review',json={'text':'Three similar projects must be documented','mandatory':mandatory,'source_page':2,'source_quote':'Three similar projects must be documented'})
        assert x.status_code==200,x.text
    return req

def evidence(client,org,verified=True,expires_on=None):
    result=client.post('/api/evidence',json={'organization_id':org,'label':'Signed certificate','reference':'CERT-001',
       'verified':verified,'verification_note':'Checked signed original' if verified else '', 'expires_on':expires_on})
    assert result.status_code==201,result.text
    return result.json()['id']

def attest(client,tender):
    result=client.post(f'/api/tenders/{tender}/attest-source-scope',json={'reviewer':'Human Reviewer','note':'I inspected the complete source, schedules and amendments','checked_full_document_set':True})
    assert result.status_code==200,result.text

def verdict(client,tender,decision='BID'):
    return client.post(f'/api/tenders/{tender}/decisions',json={'decision':decision,'reviewer':'Human Reviewer','rationale':'Checked original documents and recorded commercial choice'})

def test_mandatory_blocker_and_human_gate(client):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t)
    blocked=client.put(f'/api/requirements/{r}/status',json={'status':'NOT_HELD','notes':'No evidence exists'})
    assert blocked.status_code==200
    d=client.get(f'/api/tenders/{t}').json()
    assert d['compliance']=='BLOCKED' and len(d['blockers'])==1
    assert verdict(client,t).status_code==409
    hold=verdict(client,t,'HOLD'); assert hold.status_code==201
    ev=evidence(client,org)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev,'notes':'Checked'}).status_code==200
    attest(client,t)
    d=client.get(f'/api/tenders/{t}').json()
    assert d['compliance']=='READY_FOR_HUMAN_DECISION' and d['coverage_percent']==100
    assert verdict(client,t).status_code==201
    assert len(client.get(f'/api/tenders/{t}').json()['decisions'])==2

def test_fail_closed_when_unreviewed(client):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t,mandatory=None)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED'}).status_code==422
    assert client.get(f'/api/tenders/{t}').json()['compliance']=='UNRESOLVED'
    assert verdict(client,t).status_code==409

def test_no_verified_without_current_evidence(client):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','notes':'none'}).status_code==422
    expired=(date.today()-timedelta(days=1)).isoformat()
    ev=evidence(client,org,expires_on=expired)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev}).status_code==422
    assert client.post('/api/evidence',json={'organization_id':org,'label':'Unsigned evidence','reference':'document','verified':True}).status_code==422

def test_cross_organization_evidence_rejected(client):
    org1=add_org(client,'Org Alpha');org2=add_org(client,'Org Beta');t=add_tender(client,org1);r=add_req(client,t)
    ev=evidence(client,org2)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev}).status_code==422

def test_exports_and_metrics(client):
    org=add_org(client);t=add_tender(client,org);add_req(client,t)
    for ext,content_type in [('csv','text/csv'),('xlsx','application/vnd.openxmlformats'),('docx','application/vnd.openxmlformats')]:
        x=client.get(f'/api/tenders/{t}/export.{ext}')
        assert x.status_code==200,x.text[:200]
        assert content_type in x.headers['content-type']
        assert len(x.content)>70
    m=client.post(f'/api/tenders/{t}/metrics',json={'quoted_bdt':20000,'paid_bdt':0,'actual_minutes':90,'decision_changed':False})
    assert m.status_code==200
    assert client.get(f'/api/tenders/{t}').json()['metrics']['paid_bdt']==0

def test_pdf_has_source_provenance(client):
    reportlab=pytest.importorskip('reportlab')
    from reportlab.pdfgen.canvas import Canvas
    org=add_org(client);t=add_tender(client,org)
    buf=io.BytesIO();c=Canvas(buf);c.drawString(50,750,'Bidders must show at least three similar projects completed.');c.showPage();c.save()
    pdf=buf.getvalue()
    up=client.post(f'/api/tenders/{t}/upload-pdf',files={'file':('requirements.pdf',pdf,'application/pdf')})
    assert up.status_code==201,up.text
    assert up.json()['candidates']>=1
    d=client.get(f'/api/tenders/{t}').json()
    assert d['requirements'][0]['source_page']==1
    assert d['requirements'][0]['reviewed']==0
    assert d['requirements'][0]['mandatory'] is None
    assert len(d['sources'][0]['sha256'])==64
    assert d['compliance']=='UNRESOLVED'

def test_health_and_demo(client):
    h=client.get('/api/health');assert h.status_code==200
    assert h.json()['external_model_calls'] is False
    d=client.post('/api/demo');assert d.status_code==201
    snap=client.get(f"/api/tenders/{d.json()['tender_id']}").json()
    assert snap['compliance']=='BLOCKED'
    assert verdict(client,snap['tender']['id']).status_code==409

def test_missing_provenance_keeps_mandatory_unresolved(client):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t)
    ev=evidence(client,org)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev}).status_code==200
    # Removing the exact source quote must stop BID even when evidence has been verified.
    assert client.put(f'/api/requirements/{r}/review',json={'text':'Three similar projects must be documented','mandatory':True,'source_page':2,'source_quote':''}).status_code==200
    snap=client.get(f'/api/tenders/{t}').json()
    assert snap['compliance']=='UNRESOLVED'
    assert verdict(client,t).status_code==409

def test_changed_requirements_invalidate_prior_bid(client):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t)
    ev=evidence(client,org)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev}).status_code==200
    assert verdict(client,t).status_code==409 # missing source-inventory attestation
    attest(client,t)
    assert verdict(client,t).status_code==201
    assert client.get(f'/api/tenders/{t}').json()['current_decision']=='BID'
    assert client.post(f'/api/tenders/{t}/requirements',json={'text':'New mandatory condition from addendum', 'source_page':3,'source_quote':'New mandatory condition from addendum'}).status_code==201
    snap=client.get(f'/api/tenders/{t}').json()
    assert snap['current_decision'] is None
    assert snap['decisions'][0]['is_current'] is False
    assert verdict(client,t).status_code==409

def test_excel_formula_injection_blocked(client):
    from openpyxl import load_workbook
    org=add_org(client);t=add_tender(client,org)
    x=client.post(f'/api/tenders/{t}/requirements',json={'text':'=SUM(1,2) external injection attempt','source_quote':'Original textual clause','source_page':1})
    assert x.status_code==201
    output=client.get(f'/api/tenders/{t}/export.xlsx')
    assert output.status_code==200
    book=load_workbook(io.BytesIO(output.content))
    assert book.active['E8'].data_type!='f'
    assert book.active['E8'].value.startswith("'=SUM")
