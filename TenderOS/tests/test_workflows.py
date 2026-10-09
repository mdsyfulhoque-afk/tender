import io
import json
import sqlite3
import hashlib
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from openpyxl.cell.cell import ERROR_CODES
from app import main

@pytest.fixture
def client(tmp_path,monkeypatch):
    db=tmp_path/'test.db';storage=tmp_path/'uploads';storage.mkdir()
    monkeypatch.setattr(main,'DB',db);monkeypatch.setattr(main,'STORAGE',storage)
    with sqlite3.connect(db) as cx:
        cx.executescript(main.SCHEMA)
        main.initialize_local_extensions(cx)
    return TestClient(main.app)

SOURCE_TEXT='Three similar projects must be documented'
SOURCE_QUOTE='Three completed projects are documented.'

def synthetic_pdf(*pages):
    """Small real text PDF; no optional package or customer document is needed."""
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>', b'',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    children=[]
    for lines in pages:
        page_id=len(objects)+1
        children.append(f'{page_id} 0 R')
        objects.append((f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
                        f'/Resources << /Font << /F1 3 0 R >> >> '
                        f'/Contents {page_id+1} 0 R >>').encode())
        commands=['BT /F1 12 Tf 50 750 Td']
        for line in lines:
            escaped=line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            commands.append(f'({escaped}) Tj 0 -16 Td')
        commands.append('ET')
        stream='\n'.join(commands).encode('ascii')
        objects.append(f'<< /Length {len(stream)} >>\nstream\n'.encode()+stream+b'\nendstream')
    objects[1]=f'<< /Type /Pages /Kids [{" ".join(children)}] /Count {len(pages)} >>'.encode()
    output=bytearray(b'%PDF-1.4\n')
    offsets=[0]
    for index,value in enumerate(objects,1):
        offsets.append(len(output))
        output.extend(f'{index} 0 obj\n'.encode()+value+b'\nendobj\n')
    xref=len(output)
    output.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        output.extend(f'{offset:010d} 00000 n \n'.encode())
    output.extend((f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n'
                   f'startxref\n{xref}\n%%EOF\n').encode())
    return bytes(output)

def confirm_inventory(client,uploaded,**changes):
    values={'title':'Synthetic source PDF','document_type':'RFP','language':'English',
            'version_label':'Original','availability':'AVAILABLE','source_id':uploaded['source_id']}
    values.update(changes)
    response=client.put(f"/api/inventory/{uploaded['inventory_item_id']}",json=values)
    assert response.status_code==200,response.text

def add_source(client,tender,quote=SOURCE_QUOTE,confirm=True,name='requirements.pdf'):
    data=synthetic_pdf(('Synthetic administrative cover page.',),(quote,))
    response=client.post(f'/api/tenders/{tender}/upload-pdf',files={'file':(name,data,'application/pdf')})
    assert response.status_code==201,response.text
    uploaded=response.json()
    assert uploaded['candidates']==0,uploaded
    if confirm:
        confirm_inventory(client,uploaded)
    return uploaded

def review_requirement(client,tender,req,**changes):
    requirement=next(x for x in client.get(f'/api/tenders/{tender}').json()['requirements'] if x['id']==req)
    values={key:requirement[key] for key in ('text','source_id','source_page','source_quote')}
    values['mandatory']=True
    values.update(changes)
    return client.put(f'/api/requirements/{req}/review',json=values)

def add_org(client,name='Test Consulting'):
    x=client.post('/api/organizations',json={'name':name});assert x.status_code==201,x.text
    return x.json()['id']

def add_tender(client,org):
    x=client.post('/api/tenders',json={'organization_id':org,'title':'Synthetic consulting assignment'})
    assert x.status_code==201,x.text
    return x.json()['id']

def add_req(client,tender,mandatory=True):
    source=add_source(client,tender)
    x=client.post(f'/api/tenders/{tender}/requirements',json={'text':SOURCE_TEXT,
       'source_id':source['source_id'],'source_page':2,'source_quote':SOURCE_QUOTE})
    assert x.status_code==201,x.text
    req=x.json()['id']
    if mandatory is not None:
        x=review_requirement(client,tender,req,mandatory=mandatory)
        assert x.status_code==200,x.text
    return req

def evidence(client,org,verified=True,expires_on=None,label='Signed certificate'):
    result=client.post('/api/evidence',json={'organization_id':org,'label':label,'reference':'CERT-001',
       'verified':False,'expires_on':expires_on})
    assert result.status_code==201,result.text
    ev=result.json()['id']
    uploaded=client.post(f'/api/evidence/{ev}/upload-pdf',
       files={'file':('certificate.pdf',synthetic_pdf(('Signed synthetic certificate CERT-001.',)),'application/pdf')})
    assert uploaded.status_code==201,uploaded.text
    if verified:
        result=client.post(f'/api/evidence/{ev}/verify',json={'verified':True,
           'verification_note':'Checked signed original synthetic certificate','document_hash':uploaded.json()['sha256']})
        assert result.status_code==200,result.text
    return ev

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
    ev=evidence(client,org,verified=False,expires_on=expired)
    document=client.get(f'/api/tenders/{t}').json()['evidence'][0]
    assert client.post(f'/api/evidence/{ev}/verify',json={'verified':True,
       'verification_note':'Reviewed the expired signed original','document_hash':document['document_hash']}).status_code==422
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
    org=add_org(client);t=add_tender(client,org)
    pdf=synthetic_pdf(('Bidders must show at least three similar projects completed.',))
    up=client.post(f'/api/tenders/{t}/upload-pdf',files={'file':('requirements.pdf',pdf,'application/pdf')})
    assert up.status_code==201,up.text
    assert up.json()['candidates']>=1
    d=client.get(f'/api/tenders/{t}').json()
    assert d['requirements'][0]['source_page']==1
    assert d['requirements'][0]['reviewed']==0
    assert d['requirements'][0]['mandatory'] is None
    assert len(d['sources'][0]['sha256'])==64
    assert d['inventory_complete'] is False
    assert d['inventory'][0]['language']=='Unconfirmed'
    assert d['inventory'][0]['version_label']=='Unconfirmed'
    assert d['compliance']=='UNRESOLVED'

def test_source_attestation_requires_nonempty_confirmed_inventory(client):
    org=add_org(client);t=add_tender(client,org)
    payload={'reviewer':'Human Reviewer','note':'Reviewed the complete registered tender set',
             'checked_full_document_set':True}
    assert client.post(f'/api/tenders/{t}/attest-source-scope',json=payload).status_code==409
    source=add_source(client,t,confirm=False)
    result=client.post(f'/api/tenders/{t}/requirements',json={'text':SOURCE_TEXT,
       'source_id':source['source_id'],'source_page':2,'source_quote':SOURCE_QUOTE,'reviewed':True,'mandatory':True})
    assert result.status_code==201,result.text
    r=result.json()['id']
    # The create payload cannot substitute for a human review action.
    assert client.get(f'/api/tenders/{t}').json()['requirements'][0]['reviewed']==0
    assert review_requirement(client,t,r).status_code==200
    assert client.post(f'/api/tenders/{t}/attest-source-scope',json=payload).status_code==409
    confirm_inventory(client,source)
    assert client.post(f'/api/tenders/{t}/attest-source-scope',json=payload).status_code==200
    assert client.get(f'/api/tenders/{t}').json()['inventory_complete'] is True
    assert verdict(client,t).status_code==409  # No verified supporting evidence.

def test_known_missing_document_invalidates_bid_and_keeps_history(client):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    result=client.post(f'/api/tenders/{t}/inventory',json={
       'title':'Known annex not yet received','document_type':'ANNEX','language':'English',
       'version_label':'Original','availability':'MISSING','notes':'Buyer lists this annex in the source set'})
    assert result.status_code==201,result.text
    snap=client.get(f'/api/tenders/{t}').json()
    assert snap['inventory_complete'] is False and snap['source_scope_verified'] is False
    assert snap['compliance']=='UNRESOLVED' and snap['current_decision'] is None
    assert verdict(client,t).status_code==409
    assert client.post(f'/api/tenders/{t}/attest-source-scope',json={
       'reviewer':'Human Reviewer','note':'Reviewed the known but incomplete tender source set',
       'checked_full_document_set':True}).status_code==409
    assert stored_decisions(t)==history
    supplied=client.post(f'/api/tenders/{t}/upload-pdf',
       data={'inventory_item_id':str(result.json()['id'])},
       files={'file':('received-annex.pdf',synthetic_pdf(('Supplemental administrative contact details.',)),'application/pdf')})
    assert supplied.status_code==201,supplied.text
    assert supplied.json()['inventory_item_id']==result.json()['id']
    snapshot=client.get(f'/api/tenders/{t}').json()
    assert snapshot['inventory_complete'] is True and len(snapshot['inventory'])==2
    item=next(x for x in snapshot['inventory'] if x['id']==result.json()['id'])
    assert item['availability']=='AVAILABLE' and item['document_type']=='ANNEX'
    assert item['source_id']==supplied.json()['source_id']
    assert snapshot['current_decision'] is None and stored_decisions(t)==history
    attest(client,t)
    assert client.get(f'/api/tenders/{t}').json()['compliance']=='READY_FOR_HUMAN_DECISION'
    assert verdict(client,t).status_code==201
    assert stored_decisions(t)[:len(history)]==history

@pytest.mark.parametrize('foreign',[False,True])
def test_upload_cannot_fulfill_available_or_cross_tender_inventory(client,foreign):
    org=add_org(client);t=add_tender(client,org)
    if foreign:
        second=add_tender(client,org)
        result=client.post(f'/api/tenders/{second}/inventory',json={
           'title':'Missing foreign annex','document_type':'ANNEX','availability':'MISSING'})
        assert result.status_code==201,result.text
        item_id=result.json()['id']
    else:
        item_id=add_source(client,t)['inventory_item_id']
    before=client.get(f'/api/tenders/{t}').json()['sources']
    uploaded=client.post(f'/api/tenders/{t}/upload-pdf',data={'inventory_item_id':str(item_id)},
       files={'file':('wrong-target.pdf',synthetic_pdf(('Administrative contact details.',)),'application/pdf')})
    assert uploaded.status_code==422,uploaded.text
    assert client.get(f'/api/tenders/{t}').json()['sources']==before

@pytest.mark.parametrize('changes',[
    {'source_page':3}, {'source_page':1}, {'source_quote':'A clause that does not occur in the PDF.'},
    {'source_quote':'   '}, {'source_id':None}, {'source_page':0},
])
def test_requirement_creation_rejects_invalid_registered_provenance(client,changes):
    org=add_org(client);t=add_tender(client,org);source=add_source(client,t)
    values={'text':SOURCE_TEXT,'source_id':source['source_id'],'source_page':2,'source_quote':SOURCE_QUOTE}
    values.update(changes)
    assert client.post(f'/api/tenders/{t}/requirements',json=values).status_code==422
    assert client.get(f'/api/tenders/{t}').json()['requirements']==[]

def test_cross_tender_sources_cannot_be_claimed_or_downloaded(client):
    org=add_org(client);first=add_tender(client,org);second=add_tender(client,org)
    source=add_source(client,first)
    result=client.post(f'/api/tenders/{second}/requirements',json={
       'text':SOURCE_TEXT,'source_id':source['source_id'],'source_page':2,'source_quote':SOURCE_QUOTE})
    assert result.status_code==422,result.text
    result=client.post(f'/api/tenders/{second}/inventory',json={
       'title':'Foreign source','document_type':'RFP','availability':'AVAILABLE','source_id':source['source_id']})
    assert result.status_code==422,result.text
    assert client.get(f"/api/tenders/{second}/sources/{source['source_id']}/file").status_code==404
    document=client.get(f"/api/tenders/{first}/sources/{source['source_id']}/file")
    assert document.status_code==200 and document.headers['content-type']=='application/pdf'
    assert hashlib.sha256(document.content).hexdigest()==source['sha256']

def test_typed_evidence_reference_cannot_become_verified_without_document(client):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t)
    values={'organization_id':org,'label':'Typed certificate reference','reference':'CERT-TYPED',
            'verification_note':'A typed reference is not an inspected file'}
    assert client.post('/api/evidence',json={**values,'verified':True}).status_code==422
    response=client.post('/api/evidence',json=values)
    assert response.status_code==201,response.text
    ev=response.json()['id']
    assert client.post(f'/api/evidence/{ev}/verify',json={'verified':True,
       'verification_note':'Claimed review without any document','document_hash':'a'*64}).status_code==409
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev}).status_code==422
    assert verdict(client,t).status_code==409

def test_new_evidence_file_revokes_verification_and_invalidates_bid(client):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    before=client.get(f'/api/tenders/{t}').json()
    previous=before['evidence'][0]['files'][0]
    replacement=synthetic_pdf(('Replacement signed synthetic certificate CERT-002.',))
    uploaded=client.post(f'/api/evidence/{ev}/upload-pdf',
       files={'file':('replacement.pdf',replacement,'application/pdf')})
    assert uploaded.status_code==201,uploaded.text
    after=client.get(f'/api/tenders/{t}').json();document=after['evidence'][0]
    assert document['verified']==0 and document['verification_current'] is False
    assert len(document['files'])==2 and document['files'][1]==previous
    assert after['source_scope_verified'] is True and after['fingerprint']!=before['fingerprint']
    assert after['compliance']=='UNRESOLVED' and after['current_decision'] is None
    assert client.post(f'/api/evidence/{ev}/verify',json={'verified':True,
       'verification_note':'Attempted review against the older certificate','document_hash':previous['sha256']}).status_code==409
    assert stored_decisions(t)==history
    assert client.post(f'/api/evidence/{ev}/verify',json={'verified':True,
       'verification_note':'Checked the newly uploaded signed certificate','document_hash':uploaded.json()['sha256']}).status_code==200
    reviewed=client.get(f'/api/tenders/{t}').json()
    assert reviewed['compliance']=='READY_FOR_HUMAN_DECISION' and reviewed['current_decision'] is None
    assert verdict(client,t).status_code==201
    assert stored_decisions(t)[:len(history)]==history

def test_evidence_download_is_scoped_and_hash_checked(client):
    org,t,r,ev=ready_bid(client);other=add_org(client,'Another organization')
    record=client.get(f'/api/tenders/{t}').json()['evidence'][0]['files'][0]
    url=f"/api/organizations/{org}/evidence/{ev}/files/{record['id']}"
    document=client.get(url)
    assert document.status_code==200 and document.content.startswith(b'%PDF-')
    assert hashlib.sha256(document.content).hexdigest()==record['sha256']
    assert client.get(f"/api/organizations/{other}/evidence/{ev}/files/{record['id']}").status_code==404
    with sqlite3.connect(main.DB) as db:
        key=db.execute('SELECT private_path FROM evidence_files WHERE id=?',(record['id'],)).fetchone()[0]
    (main.STORAGE/key).write_bytes(b'%PDF- changed private bytes')
    assert client.get(url).status_code==409

def test_material_requirement_review_revokes_previous_evidence_mapping(client):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    assert review_requirement(client,t,r,text='A revised interpretation of the same documented projects').status_code==200
    snapshot=client.get(f'/api/tenders/{t}').json();requirement=snapshot['requirements'][0]
    assert requirement['status']=='UNKNOWN' and requirement['evidence_id'] is None
    assert snapshot['source_scope_verified'] is False and snapshot['current_decision'] is None
    assert snapshot['compliance']=='UNRESOLVED' and stored_decisions(t)==history

def test_unchanged_requirement_review_preserves_verified_mapping(client):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    assert review_requirement(client,t,r).status_code==200
    snapshot=client.get(f'/api/tenders/{t}').json();requirement=snapshot['requirements'][0]
    assert requirement['status']=='VERIFIED' and requirement['evidence_id']==ev
    assert snapshot['current_decision']=='BID' and stored_decisions(t)==history

def test_health_and_demo(client):
    h=client.get('/api/health');assert h.status_code==200
    assert h.json()['external_model_calls'] is False
    d=client.post('/api/demo');assert d.status_code==201
    snap=client.get(f"/api/tenders/{d.json()['tender_id']}").json()
    assert snap['compliance']=='BLOCKED'
    assert verdict(client,snap['tender']['id']).status_code==409

def test_missing_provenance_keeps_mandatory_unresolved(client):
    org,t,r,ev=ready_bid(client)
    # Invalid provenance cannot be introduced by review. Legacy invalid records
    # must still stop BID even when their evidence was verified previously.
    assert review_requirement(client,t,r,source_quote='').status_code==422
    assert client.get(f'/api/tenders/{t}').json()['current_decision']=='BID'
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE requirements SET source_quote=? WHERE id=?',('',r))
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
    quote='The new document describes a further condition.'
    source=add_source(client,t,quote=quote,name='additional-condition.pdf')
    assert client.post(f'/api/tenders/{t}/requirements',json={'text':'New mandatory condition from addendum',
       'source_id':source['source_id'],'source_page':2,'source_quote':quote}).status_code==201
    snap=client.get(f'/api/tenders/{t}').json()
    assert snap['current_decision'] is None
    assert snap['decisions'][0]['is_current'] is False
    assert verdict(client,t).status_code==409

def test_excel_formula_injection_blocked(client):
    from openpyxl import load_workbook
    org=add_org(client);t=add_tender(client,org)
    source=add_source(client,t,quote='Original textual clause')
    x=client.post(f'/api/tenders/{t}/requirements',json={'text':'=SUM(1,2) external injection attempt',
       'source_id':source['source_id'],'source_quote':'Original textual clause','source_page':2})
    assert x.status_code==201
    output=client.get(f'/api/tenders/{t}/export.xlsx')
    assert output.status_code==200
    book=load_workbook(io.BytesIO(output.content))
    assert book.active['E8'].data_type!='f'
    assert book.active['E8'].value.startswith("'=SUM")

def ready_bid(client,expires_on=None):
    org=add_org(client);t=add_tender(client,org);r=add_req(client,t)
    ev=evidence(client,org,expires_on=expires_on)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev,'notes':'Checked original evidence'}).status_code==200
    attest(client,t)
    assert verdict(client,t).status_code==201
    assert client.get(f'/api/tenders/{t}').json()['current_decision']=='BID'
    return org,t,r,ev

def stored_decisions(tender):
    with sqlite3.connect(main.DB) as db:
        return db.execute('SELECT * FROM decisions WHERE tender_id=? ORDER BY id',(tender,)).fetchall()

def upload_non_candidate_pdf(client,tender):
    pdf=synthetic_pdf(('This document records administrative contact information.',))
    result=client.post(f'/api/tenders/{tender}/upload-pdf',files={'file':('additional-document.pdf',pdf,'application/pdf')})
    assert result.status_code==201,result.text
    assert result.json()['candidates']==0
    confirm_inventory(client,result.json(),document_type='OTHER')
    return result.json()['source_id']

def test_zero_candidate_addendum_invalidates_bid_without_rewriting_history(client):
    org,t,r,ev=ready_bid(client)
    before=client.get(f'/api/tenders/{t}').json();history=stored_decisions(t)
    upload_non_candidate_pdf(client,t)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['requirements']==before['requirements']
    assert after['fingerprint']==before['fingerprint']
    assert after['source_scope_fingerprint']!=before['source_scope_fingerprint']
    assert after['source_scope_verified'] is False
    assert after['compliance']=='UNRESOLVED'
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert verdict(client,t).status_code==409
    assert stored_decisions(t)==history
    attest(client,t)
    reviewed=client.get(f'/api/tenders/{t}').json()
    assert reviewed['compliance']=='READY_FOR_HUMAN_DECISION'
    assert reviewed['current_decision'] is None
    assert stored_decisions(t)==history
    assert verdict(client,t).status_code==201
    latest=client.get(f'/api/tenders/{t}').json()
    assert latest['current_decision']=='BID'
    assert [d['is_current'] for d in latest['decisions']]==[True,False]
    assert stored_decisions(t)[:len(history)]==history

@pytest.mark.parametrize('field,value',[
    ('name','revised-addendum.pdf'),('sha256','a'*64),('bytes',12345),
    ('pages',2),('uploaded_at','2030-01-01T00:00:00+00:00')
])
def test_source_inventory_mutation_invalidates_bid(client,field,value):
    org,t,r,ev=ready_bid(client)
    source=upload_non_candidate_pdf(client,t)
    attest(client,t);assert verdict(client,t).status_code==201
    before=client.get(f'/api/tenders/{t}').json();history=stored_decisions(t)
    with sqlite3.connect(main.DB) as db:
        db.execute(f'UPDATE sources SET {field}=? WHERE id=?',(value,source))
    after=client.get(f'/api/tenders/{t}').json()
    assert after['source_scope_fingerprint']!=before['source_scope_fingerprint']
    assert after['source_scope_verified'] is False
    assert after['current_decision'] is None
    assert after['compliance']=='UNRESOLVED'
    assert stored_decisions(t)==history

def test_changed_requirement_source_association_invalidates_bid(client):
    org,t,r,ev=ready_bid(client)
    first=add_source(client,t,name='first-copy.pdf')['source_id']
    second=add_source(client,t,name='second-copy.pdf')['source_id']
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE requirements SET source_id=? WHERE id=?',(first,r))
    attest(client,t);assert verdict(client,t).status_code==201
    before=client.get(f'/api/tenders/{t}').json();history=stored_decisions(t)
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE requirements SET source_id=? WHERE id=?',(second,r))
    after=client.get(f'/api/tenders/{t}').json()
    assert after['source_scope_fingerprint']!=before['source_scope_fingerprint']
    assert after['fingerprint']!=before['fingerprint']
    assert after['source_scope_verified'] is False and after['current_decision'] is None
    assert verdict(client,t).status_code==409
    assert stored_decisions(t)==history

@pytest.mark.parametrize('field,value',[
    ('label','Replacement certificate'),('reference','CERT-REVISED'),
    ('verification_note','Rechecked against a replacement signed original'),
    ('expires_on',(date.today()+timedelta(days=90)).isoformat()),('verified',0)
])
def test_linked_evidence_mutations_invalidate_bid(client,field,value):
    org,t,r,ev=ready_bid(client,expires_on=(date.today()+timedelta(days=60)).isoformat())
    before=client.get(f'/api/tenders/{t}').json();history=stored_decisions(t)
    # Evidence has no update API; change the linked fixture record directly.
    with sqlite3.connect(main.DB) as db:
        db.execute(f'UPDATE evidence SET {field}=? WHERE id=?',(value,ev))
    after=client.get(f'/api/tenders/{t}').json()
    assert after['fingerprint']!=before['fingerprint']
    assert after['source_scope_verified'] is True
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert after['compliance']==('UNRESOLVED' if field=='verified' else 'READY_FOR_HUMAN_DECISION')
    assert stored_decisions(t)==history

def test_linked_evidence_expiry_invalidates_bid_without_a_write(client,monkeypatch):
    expiry=date.today()+timedelta(days=1)
    org,t,r,ev=ready_bid(client,expires_on=expiry.isoformat());history=stored_decisions(t)
    class AfterExpiry(date):
        @classmethod
        def today(cls):
            return expiry+timedelta(days=1)
    monkeypatch.setattr(main,'date',AfterExpiry)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['requirements'][0]['effective_status']=='UNKNOWN'
    assert after['compliance']=='UNRESOLVED' and after['current_decision'] is None
    assert after['decisions'][0]['is_current'] is False
    assert verdict(client,t).status_code==409
    assert stored_decisions(t)==history

def test_unrelated_evidence_and_metrics_preserve_current_bid_and_history(client):
    org,t,r,ev=ready_bid(client)
    before=client.get(f'/api/tenders/{t}').json();history=stored_decisions(t)
    unrelated=evidence(client,org)
    other_org=add_org(client,'Other consulting organization');other=evidence(client,other_org)
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE evidence SET reference=?,verified=0 WHERE id IN (?,?)',('UNRELATED-REVISED',unrelated,other))
    assert client.post(f'/api/tenders/{t}/metrics',json={'paid_bdt':15000,'actual_minutes':75,'notes':'Updated commercial pilot observation'}).status_code==200
    for _ in range(2):
        after=client.get(f'/api/tenders/{t}').json()
        assert after['fingerprint']==before['fingerprint']
        assert after['source_scope_fingerprint']==before['source_scope_fingerprint']
        assert after['current_decision']=='BID' and after['decisions'][0]['is_current'] is True
        assert stored_decisions(t)==history

def test_changed_evidence_mapping_notes_invalidate_bid(client):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev,'notes':'Changed supporting evidence interpretation'}).status_code==200
    after=client.get(f'/api/tenders/{t}').json()
    assert after['compliance']=='READY_FOR_HUMAN_DECISION'
    assert after['current_decision'] is None
    assert stored_decisions(t)==history

@pytest.mark.parametrize('legacy_case',[
    'missing_currency_version','missing_scope_hash','missing_fingerprint','missing_scope_attestation',
    'unsupported_currency_version','null','array','malformed'
])
def test_incomplete_or_legacy_decision_metadata_is_historical(client,legacy_case):
    org,t,r,ev=ready_bid(client)
    with sqlite3.connect(main.DB) as db:
        row=db.execute('SELECT id,decision_snapshot FROM decisions WHERE tender_id=?',(t,)).fetchone()
        past=json.loads(row[1])
        if legacy_case.startswith('missing_'):
            past.pop(legacy_case.removeprefix('missing_'),None)
            text=json.dumps(past)
        elif legacy_case=='unsupported_currency_version':
            past['currency_version']=0;text=json.dumps(past)
        else:
            text={'null':'null','array':'[]','malformed':'{not valid json'}[legacy_case]
        db.execute('UPDATE decisions SET decision_snapshot=? WHERE id=?',(text,row[0]))
    history=stored_decisions(t)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['compliance']=='READY_FOR_HUMAN_DECISION'
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert after['decisions'][0]['decision_snapshot']==text
    assert stored_decisions(t)==history

def test_current_bid_requires_current_readiness(client):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE tenders SET source_scope_fingerprint=NULL WHERE id=?',(t,))
    after=client.get(f'/api/tenders/{t}').json()
    assert after['compliance']=='UNRESOLVED' and after['source_scope_verified'] is False
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert verdict(client,t).status_code==409
    assert stored_decisions(t)==history

@pytest.mark.parametrize('revoke',[False,True])
def test_same_scope_reattestation_does_not_restore_old_bid(client,monkeypatch,revoke):
    monkeypatch.setattr(main,'now',lambda:'2030-01-01T00:00:00+00:00')
    org,t,r,ev=ready_bid(client)
    before=client.get(f'/api/tenders/{t}').json();history=stored_decisions(t)
    if revoke:
        with sqlite3.connect(main.DB) as db:
            db.execute('UPDATE tenders SET source_scope_fingerprint=NULL WHERE id=?',(t,))
        assert client.get(f'/api/tenders/{t}').json()['current_decision'] is None
    attest(client,t)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['source_scope_fingerprint']==before['source_scope_fingerprint']
    assert after['source_scope_verified'] is True and after['compliance']=='READY_FOR_HUMAN_DECISION'
    assert after['source_scope_attestation']['at']==before['source_scope_attestation']['at']
    assert after['source_scope_attestation']['event_id']!=before['source_scope_attestation']['event_id']
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert stored_decisions(t)==history
    assert verdict(client,t).status_code==201
    assert client.get(f'/api/tenders/{t}').json()['current_decision']=='BID'
    assert stored_decisions(t)[:len(history)]==history

@pytest.mark.parametrize('field,value',[
    ('source_scope_reviewer','Replacement Human Reviewer'),
    ('source_scope_note','A revised note describing the inspected source set'),
    ('source_scope_at','2030-01-01T00:00:00+00:00')
])
def test_changed_attestation_values_invalidate_bid(client,field,value):
    org,t,r,ev=ready_bid(client);history=stored_decisions(t)
    with sqlite3.connect(main.DB) as db:
        db.execute(f'UPDATE tenders SET {field}=? WHERE id=?',(value,t))
    after=client.get(f'/api/tenders/{t}').json()
    assert after['source_scope_verified'] is True and after['compliance']=='READY_FOR_HUMAN_DECISION'
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert stored_decisions(t)==history

@pytest.mark.parametrize('decision',['HOLD','NO_BID'])
def test_non_bid_decisions_can_remain_current_without_readiness(client,decision):
    org=add_org(client);t=add_tender(client,org);add_req(client,t)
    assert verdict(client,t,decision).status_code==201
    history=stored_decisions(t)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['compliance']=='UNRESOLVED'
    assert after['current_decision']==decision and after['decisions'][0]['is_current'] is True
    assert stored_decisions(t)==history

@pytest.mark.parametrize('literal',[
    '=SUM(1,2)','+SUM(1,2)','-SUM(1,2)','@SUM(1,2)',
    ' \t=SUM(1,2)',' \t+SUM(1,2)',' \t-SUM(1,2)',' \t@SUM(1,2)',
    "'=SUM(1,2)",'Ordinary reviewed text'
])
def test_all_untrusted_spreadsheet_fields_are_literals(client,literal):
    import csv
    from openpyxl import load_workbook
    org=add_org(client)
    result=client.post('/api/tenders',json={'organization_id':org,'title':literal})
    assert result.status_code==201,result.text
    t=result.json()['id']
    source=add_source(client,t,quote=literal.strip())
    result=client.post(f'/api/tenders/{t}/requirements',json={'text':literal,'source_id':source['source_id'],'source_page':2,'source_quote':literal})
    assert result.status_code==201,result.text
    r=result.json()['id']
    assert review_requirement(client,t,r).status_code==200
    ev=evidence(client,org,label=literal)
    assert client.put(f'/api/requirements/{r}/status',json={'status':'VERIFIED','evidence_id':ev,'notes':literal}).status_code==200
    result=client.post(f'/api/tenders/{t}/decisions',json={'decision':'HOLD','reviewer':literal,'rationale':literal+' reviewed by a human'})
    assert result.status_code==201,result.text
    book=load_workbook(io.BytesIO(client.get(f'/api/tenders/{t}/export.xlsx').content),data_only=False)
    def escaped(text):
        return "'"+text if text.lstrip().startswith(('=','+','-','@')) else text
    for cell in ['B2','E8','G8','H8','I8']:
        item=book['Compliance Matrix'][cell]
        assert item.data_type!='f'
        assert item.value==escaped(literal.strip())
    for cell,text in [('B2',literal.strip()),('C2',(literal+' reviewed by a human').strip())]:
        item=book['Decision History'][cell]
        assert item.data_type!='f' and item.value==escaped(text)
    assert book['Compliance Matrix']['A8'].value==r
    assert book['Compliance Matrix']['A8'].data_type=='n'
    assert book['Compliance Matrix']['F8'].value==2
    rows=list(csv.DictReader(io.StringIO(client.get(f'/api/tenders/{t}/export.csv').text)))
    for field in ['Requirement','Exact source quote','Evidence','Notes']:
        assert rows[0][field]==escaped(literal.strip())

def test_spreadsheet_export_escapes_stored_leading_whitespace(client):
    from openpyxl import load_workbook
    org,t,r,ev=ready_bid(client)
    literal=' \t=SUM(1,2)'
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE tenders SET title=? WHERE id=?',(literal,t))
        db.execute('UPDATE requirements SET text=?,source_quote=?,notes=? WHERE id=?',(literal,literal,literal,r))
        db.execute('UPDATE evidence SET label=? WHERE id=?',(literal,ev))
        db.execute('UPDATE decisions SET reviewer=?,rationale=? WHERE tender_id=?',(literal,literal,t))
    book=load_workbook(io.BytesIO(client.get(f'/api/tenders/{t}/export.xlsx').content),data_only=False)
    for cell in ['B2','E8','G8','H8','I8']:
        item=book['Compliance Matrix'][cell]
        assert item.value=="'"+literal and item.data_type!='f'
    for cell in ['B2','C2']:
        item=book['Decision History'][cell]
        assert item.value=="'"+literal and item.data_type!='f'

@pytest.mark.parametrize('metadata_case',[
    'float_event_id','string_event_id','null_event_id','missing_event_id',
    'extra_key','missing_reviewer','missing_note','missing_at','missing_scope_hash',
    'boolean_reviewer','null_note','numeric_at','object_scope_hash','array_attestation'
])
def test_attestation_metadata_requires_exact_shape_and_types(client,metadata_case):
    org,t,r,ev=ready_bid(client)
    with sqlite3.connect(main.DB) as db:
        row=db.execute('SELECT id,decision_snapshot FROM decisions WHERE tender_id=? ORDER BY id DESC',(t,)).fetchone()
        past=json.loads(row[1]);metadata=past['scope_attestation']
        if metadata_case=='float_event_id':
            metadata['event_id']=float(metadata['event_id'])
        elif metadata_case=='string_event_id':
            metadata['event_id']=str(metadata['event_id'])
        elif metadata_case=='null_event_id':
            metadata['event_id']=None
        elif metadata_case.startswith('missing_'):
            metadata.pop(metadata_case.removeprefix('missing_'))
        elif metadata_case=='extra_key':
            metadata['unexpected']=None
        elif metadata_case=='boolean_reviewer':
            metadata['reviewer']=True
        elif metadata_case=='null_note':
            metadata['note']=None
        elif metadata_case=='numeric_at':
            metadata['at']=123
        elif metadata_case=='object_scope_hash':
            metadata['scope_hash']={'hash':metadata['scope_hash']}
        else:
            past['scope_attestation']=list(metadata.values())
        db.execute('UPDATE decisions SET decision_snapshot=? WHERE id=?',(json.dumps(past),row[0]))
    history=stored_decisions(t)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['compliance']=='READY_FOR_HUMAN_DECISION'
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert stored_decisions(t)==history

def test_boolean_attestation_event_id_cannot_match_integer_one(client):
    org,t,r,ev=ready_bid(client)
    with sqlite3.connect(main.DB) as db:
        # Make the fixture attestation's real event ID 1, where True == 1 in Python.
        db.execute('DELETE FROM audit_events WHERE id=1')
        db.execute("UPDATE audit_events SET id=1 WHERE tender_id=? AND action='human_source_scope_attested'",(t,))
    assert verdict(client,t).status_code==201
    with sqlite3.connect(main.DB) as db:
        row=db.execute('SELECT id,decision_snapshot FROM decisions WHERE tender_id=? ORDER BY id DESC',(t,)).fetchone()
        past=json.loads(row[1]);assert past['scope_attestation']['event_id']==1
        past['scope_attestation']['event_id']=True
        db.execute('UPDATE decisions SET decision_snapshot=? WHERE id=?',(json.dumps(past),row[0]))
    history=stored_decisions(t)
    after=client.get(f'/api/tenders/{t}').json()
    assert after['current_decision'] is None and after['decisions'][0]['is_current'] is False
    assert stored_decisions(t)==history

@pytest.mark.parametrize('literal',[*ERROR_CODES,'00123','123.45','1E10'])
def test_spreadsheet_error_codes_and_numeric_looking_text_are_strings(client,literal):
    from openpyxl import load_workbook
    org,t,r,ev=ready_bid(client)
    with sqlite3.connect(main.DB) as db:
        db.execute('UPDATE tenders SET title=? WHERE id=?',(literal,t))
        db.execute('UPDATE requirements SET text=?,source_quote=?,notes=? WHERE id=?',(literal,literal,literal,r))
        db.execute('UPDATE evidence SET label=? WHERE id=?',(literal,ev))
        db.execute('UPDATE decisions SET reviewer=?,rationale=? WHERE tender_id=?',(literal,literal,t))
    book=load_workbook(io.BytesIO(client.get(f'/api/tenders/{t}/export.xlsx').content),data_only=False)
    for cell in ['B2','E8','G8','H8','I8']:
        item=book['Compliance Matrix'][cell]
        assert item.value==literal and item.data_type=='s'
    for cell in ['B2','C2']:
        item=book['Decision History'][cell]
        assert item.value==literal and item.data_type=='s'
    for sheet in book:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value,str):
                    assert cell.data_type=='s'
    assert book['Compliance Matrix']['A8'].value==r
    assert book['Compliance Matrix']['A8'].data_type=='n'
    assert book['Compliance Matrix']['F8'].value==2
    assert book['Compliance Matrix']['F8'].data_type=='n'
