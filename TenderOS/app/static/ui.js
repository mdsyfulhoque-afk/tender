const $ = sel => document.querySelector(sel);
const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {orgs:[],tenders:[],detail:null,selected:null,tab:'inventory',view:'home',health:null,processors:null,commercial:null,extra:null,loadToken:0,analysisToken:0,analysisBusy:false,analysisMessage:'',workflow:null,workflowId:null};
const hosted=()=>state.health?.mode==='PRIVATE_PILOT';
const api = async (path,options={})=>{
 const headers=new Headers(options.headers||{});
 if(!['GET','HEAD','OPTIONS'].includes((options.method||'GET').toUpperCase())&&hosted()){
  if(!state.health.csrf_token)throw new Error('Refresh the workspace before saving changes');
  headers.set('X-TenderOS-CSRF',state.health.csrf_token);
 }
 const result=await fetch('/api'+path,{...options,headers,credentials:'same-origin'});
 const payload=await result.json().catch(()=>({}));
 if(!result.ok){const msg = typeof payload.detail==='string'?payload.detail:JSON.stringify(payload.detail||payload);throw new Error(msg||'Request failed')}
 return payload;
};
const send=(path,body,method='POST')=>api(path,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
const formValues=(form)=>Object.fromEntries(new FormData(form));
const emptyToNull=(v)=>v===''||v===undefined?null:v;
const yorn=(v)=>v===true?'true':v===false?'false':null;
const documentTypes=['NOTICE','RFP','ANNEX','ADDENDUM','SCHEDULE','FORM','OTHER'];
const nullableNumber=value=>value===''||value===null||value===undefined?null:Number(value);
const maxUploadBytes=()=>state.health?.max_upload_bytes||(hosted()?4:10)*1024*1024;
const uploadLimit=()=>`${maxUploadBytes()/(1024*1024)} MB`;
const classified=value=>value===true||value===1||value===false||value===0;
const mandatoryLabel=value=>value===true||value===1?'Mandatory':value===false||value===0?'Optional':'Classification pending';
const evidenceVerified=e=>e.verification_current===true;
function sourceField(d,value=null,required=true){return `<div class="field"><label>Registered tender PDF</label><select name="source_id" ${required?'required':''}><option value="">Choose the original document</option>${d.sources.map(s=>`<option value="${safe(s.id)}" data-pages="${safe(s.pages)}" ${Number(value)===s.id?'selected':''}>${safe(s.name)} · ${safe(s.pages)} pages</option>`).join('')}</select></div>`;}
function sourcePageField(d,sourceId,page=null){const source=d.sources.find(s=>s.id===Number(sourceId));return `<div class="field"><label>PDF page number (1-based)</label><input type="number" name="source_page" min="1" step="1" ${source?`max="${safe(source.pages)}"`:''} required value="${safe(page??'')}"></div>`;}
function sourceLink(d,s,label='Download original PDF'){return `<a class="btn outline small" href="/api/tenders/${safe(d.tender.id)}/sources/${safe(s.id)}/file" download>${safe(label)}</a>`;}
function hashLine(hash){return hash?`<span class="hash-label">SHA-256</span> <code class="file-hash">${safe(hash)}</code>`:'<span class="fineprint">No document hash recorded</span>';}
function inventoryReady(d){return d.inventory_complete===true&&!!d.inventory?.length&&d.inventory.every(item=>item.availability==='AVAILABLE'&&d.sources.some(s=>s.id===item.source_id));}
function canAttest(d){return inventoryReady(d)&&d.requirements.length>0&&d.requirements.every(r=>r.reviewed&&classified(r.mandatory)&&r.source_id&&r.source_page&&r.source_quote);}
function sourceUploadForm(d){return `<form data-form="pdf-upload"><div class="field"><label>Fill a known missing document (optional)</label><select name="inventory_item_id"><option value="">None — register a new inventory entry</option>${(d.inventory||[]).filter(item=>item.availability==='MISSING').map(item=>`<option value="${safe(item.id)}">${safe(item.title)} · ${safe(item.version_label)}</option>`).join('')}</select></div><div class="field"><label>Original tender PDF (max ${uploadLimit()}, 150 pages)</label><input type="file" name="file" accept="application/pdf,.pdf" required></div><p class="fineprint">A selected missing item becomes available when its original PDF is uploaded. For a new inventory entry, confirm the document type, language and version metadata after upload.</p><button class="btn outline" type="submit">Upload and register PDF</button></form>`;}
function notify(msg,ok=false){const a=$('#alert');a.textContent=msg;a.className=ok?'success':'';window.scrollTo({top:0,behavior:'smooth'});}
function clearAlert(){$('#alert').textContent='';$('#alert').className='';}
async function refresh(){
 pauseAnalysis();
 state.health=await api('/health');
 $('#runtimeMode').textContent=hosted()?'PRIVATE PILOT WORKSPACE':'LOCAL PILOT MODE';
 $('#runtimeStorage').textContent=hosted()?'Managed database · Private file storage':'Local storage · No external model calls';
 const result=await Promise.allSettled([api('/organizations'),api('/tenders'),api('/processors'),api('/commercial/dashboard')]);
 if(result[0].status==='rejected')throw result[0].reason;
 if(result[1].status==='rejected')throw result[1].reason;
 state.orgs=result[0].value;state.tenders=result[1].value;
 state.processors=result[2].status==='fulfilled'?result[2].value:null;
 state.commercial=result[3].status==='fulfilled'?result[3].value:null;
 if(state.selected){try{state.detail=await api('/tenders/'+state.selected);await loadDetailExtras(state.selected)}catch(e){state.selected=null;state.detail=null;state.extra=null}}
 render();
}
function reviewerField(label,placeholder='Reviewer name'){return `<div class="field"><label>${safe(label)}</label><input name="reviewer" required minlength="2" maxlength="100" ${hosted()?`readonly value="${safe(state.health.principal)}"`:`placeholder="${safe(placeholder)}"`}></div>`}
function title(name){$('#pageTitle').textContent=name}
function statBadge(status){return `<span class="pill ${status==='READY_FOR_HUMAN_DECISION'||status==='VERIFIED'?'good':status==='BLOCKED'||status==='NOT_HELD'?'bad':'warn'}">${safe(status.replaceAll('_',' '))}</span>`}
function render(){
 document.querySelectorAll('.nav-item').forEach(n=>n.classList.toggle('active',(n.dataset.action==='home'&&state.view==='home')||(n.dataset.action==='new-tender'&&state.view==='new')));
 if(state.view==='new')renderNew();
 else if(state.view==='detail'&&state.detail)renderDetail();
 else renderHome();
 document.querySelectorAll('form .field').forEach((field,index)=>{const label=field.querySelector('label'),input=field.querySelector('input,select,textarea');if(label&&input&&!label.contains(input)){input.id=`workspace-field-${index}`;label.htmlFor=input.id;}});
}
function renderHome(){
 title('Assessment workspaces');
 const n=state.tenders.length;
 $('#content').innerHTML=`<section class="kpi-row"><div class="kpi"><span>Assessments</span><b>${n}</b></div><div class="kpi"><span>Organizations</span><b>${state.orgs.length}</b></div><div class="kpi"><span>External AI calls</span><b>0</b></div></section>
 ${commercialOverview()}<div class="layout"><div class="card"><div class="sectionhead"><div><h2>Opportunity assessments</h2><p class="sub">Controlled, human-reviewed bid decisions</p></div><button class="btn" data-action="new-tender">＋ New</button></div>
 ${n?state.tenders.map(t=>`<div class="item"><div><span class="eyebrow">${safe(t.notice_id||'NO NOTICE ID')}</span><h3>${safe(t.title)}</h3><p>${safe(t.organization_name)} · ${safe(t.buyer||'Buyer not supplied')} · Deadline ${safe(t.deadline||'unconfirmed')}</p></div><div class="item-actions"><button class="btn outline small" data-action="open-tender" data-id="${t.id}">Open →</button></div></div>`).join(''):
 `<div class="empty"><div class="big">▤</div><h2>Start with one tender</h2><p class="sub">Add the organization, the tender and its documented requirements.</p><button class="btn" data-action="new-tender">Create assessment</button></div>`}</div>
 <div class="stack"><div class="card"><h2>Your delivery workflow</h2><p class="sub">Register documents → run local analysis → review clauses and proof → record the human decision → release a diagnostic → record collections.</p><div class="notice">${hosted()?'Tender sources persist in private cloud storage for this single-owner workspace.':'Tender sources remain in local storage.'} No external model or procurement portal calls are made.</div></div><div class="card"><h2>Try synthetic example</h2><p class="sub">Loads fabricated requirements including a disqualifying mandatory item. For testing only.</p><button class="btn subtle" data-action="demo">Load demonstration</button></div></div></div>${foot()}`;
}
function renderNew(){
 title('New assessment');
 $('#content').innerHTML=`<div class="layout"><div class="stack"><div class="card"><h2>Register a live opportunity</h2><p class="sub">Provide only metadata that you can substantiate.</p><form data-form="new-tender">
 <div class="field"><label>Organization</label><select name="organization_id" required><option value="">Choose organization</option>${state.orgs.map(o=>`<option value="${o.id}">${safe(o.name)}</option>`).join('')}</select></div>
 <div class="field"><label>Tender title</label><input name="title" required minlength="3" placeholder="e.g. Economic feasibility assessment"></div>
 <div class="grid2"><div class="field"><label>Procuring entity</label><input name="buyer" placeholder="Official buyer name"></div><div class="field"><label>Notice / reference ID</label><input name="notice_id" placeholder="Reference from official document"></div></div>
 <div class="grid2"><div class="field"><label>Submission deadline (optional)</label><input name="deadline" type="date"></div><div class="field"><label>Source link (optional)</label><input name="source_url" placeholder="Official notice URL"></div></div><button class="btn" type="submit">Create assessment →</button></form></div></div>
 <div class="stack"><div class="card"><h2>New organization</h2><form data-form="new-org"><div class="field"><label>Legal / trading name</label><input required name="name" minlength="2" placeholder="Your consulting firm"></div><button type="submit" class="btn outline">Add organization</button></form></div><div class="card"><h2>Source-first rule</h2><p class="sub">A manually entered requirement remains unreviewed until its mandatory classification and source wording are checked by a human.</p></div></div></div>${foot()}`;
}
function detailHeader(d){return `<div class="hero-status"><div><span class="eyebrow" style="color:#b7d5df">CURRENT COMPLIANCE STATE</span><h2>${safe(d.compliance.replaceAll('_',' '))}</h2><span class="sub">${safe(d.tender.title)}</span></div><div><div class="metric">${d.coverage_percent===null?'—':d.coverage_percent+'%'}</div><span class="metric-label">MANDATORY EVIDENCE COVERAGE</span></div></div>
 <div class="kpi-row"><div class="kpi"><span>Requirements</span><b>${d.requirements.length}</b></div><div class="kpi"><span>Human-reviewed</span><b>${d.reviewed_count}</b></div><div class="kpi"><span>Hard blockers</span><b>${d.blockers.length}</b></div></div>`}
function renderDetail(){
 const d=state.detail;
 title('Tender assessment #'+d.tender.id);
 const tabs=['inventory','analysis','requirements','evidence','decision','delivery','export','pilot','audit'];
 const tabLabels={analysis:'Analysis work',delivery:'Delivery',pilot:'Pilot observations'};
 $('#content').innerHTML=`<div class="spread" style="margin-bottom:14px"><div class="sub">${safe(d.tender.buyer||'Buyer not specified')} · Deadline: ${safe(d.tender.deadline||'unconfirmed')} · ${safe(d.tender.notice_id||'No reference')}</div><button class="btn outline small" data-action="home">← All assessments</button></div>
 ${detailHeader(d)}${nextActions(d)}<div class="card"><div class="tabs" role="tablist" aria-label="Assessment workflow">${tabs.map(t=>`<button type="button" role="tab" id="workflow-tab-${t}" tabindex="${t===state.tab?0:-1}" aria-selected="${t===state.tab}" aria-controls="tabContent" class="tab ${t===state.tab?'active':''}" data-action="tab" data-tab="${t}">${tabLabels[t]||t.charAt(0).toUpperCase()+t.slice(1)}</button>`).join('')}</div><div id="tabContent" role="tabpanel" aria-labelledby="workflow-tab-${safe(state.tab)}">${renderTab(d)}</div></div>${foot()}`;
}
function renderTab(d){return ({inventory:()=>inventoryTab(d),analysis:()=>analysisTab(d),requirements:()=>reqTab(d),evidence:()=>evidenceTab(d),decision:()=>decisionTab(d),delivery:()=>deliveryTab(d),export:()=>exportTab(d),pilot:()=>pilotTab(d),audit:()=>auditTab(d)})[state.tab]?.()||inventoryTab(d);}
function inventoryFields(d,item={}){
 const missing=item.availability==='MISSING';
 return `<div class="field"><label>Document title</label><input name="title" required minlength="2" maxlength="300" value="${safe(item.title||'')}" placeholder="Official RFP, annex, schedule or amendment title"></div>
 <div class="grid2"><div class="field"><label>Document type</label><select name="document_type" required>${documentTypes.map(type=>`<option value="${type}" ${type===(item.document_type||'OTHER')?'selected':''}>${type.replaceAll('_',' ')}</option>`).join('')}</select></div><div class="field"><label>Publication date (optional)</label><input type="date" name="publication_date" value="${safe(item.publication_date||'')}"></div></div>
 <div class="grid2"><div class="field"><label>Language</label><input name="language" required minlength="2" maxlength="80" value="${safe(item.language||'English')}"></div><div class="field"><label>Version / amendment identifier</label><input name="version_label" required maxlength="120" value="${safe(item.version_label||'Original')}"></div></div>
 <div class="field"><label>Supersedes document (required for an addendum)</label><select name="supersedes_item_id" ${item.document_type==='ADDENDUM'?'required':''}><option value="">None — original / independent document</option>${(d.inventory||[]).filter(other=>other.id!==item.id).map(other=>`<option value="${safe(other.id)}" ${other.id===item.supersedes_item_id?'selected':''}>${safe(other.title)} · ${safe(other.version_label)}</option>`).join('')}</select></div>
 <div class="grid2"><div class="field"><label>Document availability</label><select name="availability"><option value="AVAILABLE" ${!missing?'selected':''}>Available — original PDF uploaded</option><option value="MISSING" ${missing?'selected':''}>Missing — needed before source attestation</option></select></div><div class="field"><label>Original PDF assigned to this record</label><select name="source_id" ${missing?'disabled':'required'}><option value="">${missing?'No uploaded PDF':'Choose a registered PDF'}</option>${d.sources.map(source=>`<option value="${safe(source.id)}" ${source.id===item.source_id?'selected':''}>${safe(source.name)}</option>`).join('')}</select></div></div>
 <div class="field"><label>Inventory notes / missing document follow-up</label><textarea name="notes" maxlength="3000" placeholder="Record known annexes, clarifications, exclusions and what must be obtained">${safe(item.notes||'')}</textarea></div>`;
}
function inventoryTab(d){
 const inventory=d.inventory||[],missing=inventory.filter(item=>item.availability!=='AVAILABLE'||!d.sources.some(source=>source.id===item.source_id));
 return `<div class="sectionhead tab-heading"><div><h2>Tender document inventory</h2><p class="sub">List every known notice, RFP, annex, schedule, form and addendum. Missing items keep source review unresolved.</p></div><span class="pill ${inventoryReady(d)?'good':'warn'}">${inventory.length} records · ${missing.length} incomplete</span></div>
 ${d.inventory_issues?.length?`<div class="notice critical"><strong>Inventory checks to resolve</strong><ul>${d.inventory_issues.map(issue=>`<li>${safe(typeof issue==='string'?issue:JSON.stringify(issue))}</li>`).join('')}</ul></div>`:''}
 <div class="notice">Adding, changing or removing inventory or source records revokes source attestation and makes earlier BID approvals stale. Uploads register an original PDF and an inventory entry; review its metadata below.</div>
 ${inventory.length?inventory.map(item=>{const source=d.sources.find(s=>s.id===item.source_id),superseded=inventory.find(other=>other.id===item.supersedes_item_id);return `<article class="req" id="inventory-${safe(item.id)}"><div class="req-top"><div><span class="eyebrow">DOCUMENT ${safe(item.id)} · ${safe(item.document_type)}</span><h3>${safe(item.title)}</h3><p class="sub">${safe(item.version_label)} · ${safe(item.language)} · Published ${safe(item.publication_date||'date unconfirmed')}</p></div><span class="pill ${item.availability==='AVAILABLE'&&source?'good':'warn'}">${item.availability==='AVAILABLE'&&source?'Available':'Missing / unassigned'}</span></div>
 ${superseded?`<p class="sub">Supersedes: <strong>${safe(superseded.title)}</strong> (${safe(superseded.version_label)})</p>`:''}${item.notes?`<p class="record-notes">${safe(item.notes)}</p>`:''}
 ${source?`<div class="file-card"><div class="spread"><div><strong>${safe(source.name)}</strong><p class="sub">${safe(source.pages)} pages · ${safe(source.bytes)} bytes</p></div>${sourceLink(d,source)}</div><div>${hashLine(source.sha256)}</div></div>`:'<div class="notice critical">Obtain and upload the original PDF, then assign it to this record. This item prevents source completeness attestation.</div>'}
 <details><summary>Edit document metadata or assignment</summary><form data-form="inventory-edit" data-id="${safe(item.id)}">${inventoryFields(d,item)}<button class="btn small" type="submit">Save inventory record</button></form><div class="divider"></div><button class="btn outline small danger-text" type="button" data-action="delete-inventory" data-id="${safe(item.id)}">Remove inventory record</button></details></article>`}).join(''):'<div class="notice critical">No document inventory is registered. Upload the original tender PDF and record any known missing documents.</div>'}
 <div class="divider"></div><div class="grid2"><section><h3>Add known document or missing item</h3><form data-form="inventory-new">${inventoryFields(d)}<button class="btn" type="submit">Add inventory record</button></form></section><section><h3>Upload original tender PDF</h3><p class="sub">${hosted()?'The PDF persists in private storage.':'The PDF is stored in this local workspace.'} Text extraction is a local rules-based aid; every candidate requires human review.</p>${sourceUploadForm(d)}<div class="notice">PDF page numbers refer to the uploaded file, starting at 1. Scanned images, encrypted files and complex tables may require a readable original or careful manual transcription.</div>
 ${d.sources.length?`<details class="source-library"><summary>All registered original PDFs (${d.sources.length})</summary>${d.sources.map(source=>`<div class="file-card"><div class="spread"><strong>${safe(source.name)}</strong>${sourceLink(d,source)}</div><p class="sub">${safe(source.pages)} pages · ${safe(source.bytes)} bytes</p>${hashLine(source.sha256)}</div>`).join('')}</details>`:''}</section></div>`;
}
function reqTab(d){return `<div class="sectionhead tab-heading"><div><h2>Requirement register</h2><p class="sub">Check the exact clause against the original PDF. Candidate extraction never confirms eligibility.</p></div>${statBadge(d.compliance)}</div>
 ${d.blockers.length?`<div class="notice critical"><strong>${d.blockers.length} mandatory blocker(s).</strong> BID is disabled until resolved with verified evidence.</div>`:''}
 ${!d.sources.length?'<div class="notice critical">Upload the original tender PDF in Inventory before registering or reviewing requirements. A typed reference alone cannot verify a clause.</div>':''}
 ${d.requirements.length?d.requirements.map(r=>{const source=d.sources.find(s=>s.id===r.source_id);return `<article class="req" id="requirement-${safe(r.id)}"><div class="req-top"><div><span class="eyebrow">R-${safe(r.id)} · PDF PAGE ${safe(r.source_page||'NOT SUPPLIED')} · ${r.reviewed?'REVIEWED':'NOT REVIEWED'}</span><h3>${safe(r.text)}</h3><p class="sub">${mandatoryLabel(r.mandatory)} · ${r.evidence_label?'Evidence: '+safe(r.evidence_label):'No mapped evidence'}<br>Original: ${source?safe(source.name):'No valid registered PDF assigned'}</p></div>${statBadge(r.effective_status)}</div>
 ${r.source_quote?`<blockquote class="source-quote">${safe(r.source_quote)}</blockquote>`:''}${source?sourceLink(d,source,'Download original for review'):''}
 ${r.evidence_issue?`<div class="notice critical">${safe(r.evidence_issue)}</div>`:''}
 <details><summary>Review source clause and map evidence</summary><form data-form="review-req" data-id="${safe(r.id)}"><div class="field"><label>Requirement text (correct using the original)</label><textarea required minlength="5" maxlength="5000" name="text">${safe(r.text)}</textarea></div>${sourceField(d,r.source_id)}<div class="grid2"><div class="field"><label>Mandatory classification</label><select required name="mandatory"><option value="">Select from official source</option><option value="true" ${r.mandatory===true||r.mandatory===1?'selected':''}>Mandatory</option><option value="false" ${r.mandatory===false||r.mandatory===0?'selected':''}>Optional</option></select></div>${sourcePageField(d,r.source_id,r.source_page)}</div><div class="field"><label>Verbatim quote from the selected PDF page</label><textarea name="source_quote" required maxlength="4000">${safe(r.source_quote||'')}</textarea></div><p class="fineprint">The page must exist and the quote must match its extracted text. Wording and mandatory classification remain your human review. Changing the clause, classification or citation resets its mapped status to UNKNOWN; map evidence again afterward.</p><button class="btn small" type="submit" ${!d.sources.length?'disabled':''}>Confirm human review</button></form>
 <div class="divider"></div><form data-form="status" data-id="${safe(r.id)}"><h3>Evidence-based status</h3><div class="grid2"><div class="field"><label>Status</label><select name="status">${['UNKNOWN','VERIFIED','PARTIAL','NOT_HELD'].map(status=>`<option value="${status}" ${status===r.status?'selected':''}>${status.replaceAll('_',' ')}</option>`).join('')}</select></div><div class="field"><label>Evidence reference</label><select name="evidence_id"><option value="">None</option>${d.evidence.map(e=>`<option value="${safe(e.id)}" ${r.evidence_id===e.id?'selected':''}>${safe(e.label)} ${evidenceVerified(e)?'(current human verification)':'(unverified / stale)'}</option>`).join('')}</select></div></div><div class="field"><label>Reviewer note / missing items</label><textarea name="notes" maxlength="3000">${safe(r.notes)}</textarea></div><p class="fineprint">VERIFIED requires an attached, human-verified, unexpired organization document. Mark unknown or partial when proof is insufficient.</p><button class="btn outline small" type="submit">Save reviewed status</button></form></details></article>`}).join(''):'<div class="notice">No requirements registered. Upload an original PDF in Inventory to extract candidates, or add a source-linked clause below.</div>'}
 <div class="divider"></div><h3>Add requirement manually</h3><form data-form="new-req"><div class="field"><label>Exact condition or required item</label><textarea name="text" required minlength="5" maxlength="5000" placeholder="Write the exact tender condition"></textarea></div><div class="grid2">${sourceField(d)}${sourcePageField(d)}</div><div class="field"><label>Verbatim quote from this PDF page</label><textarea name="source_quote" required maxlength="4000" placeholder="Copy the exact clause from the registered original"></textarea></div><div class="field"><label>Initial mandatory classification</label><select name="mandatory"><option value="">Pending human classification</option><option value="true">Mandatory</option><option value="false">Optional</option></select></div><p class="fineprint">Registration does not approve the requirement. Confirm its wording and mandatory classification through human review.</p><button class="btn" type="submit" ${!d.sources.length?'disabled':''}>Register for review</button></form>`;}
function evidenceMetadataFields(e={}){return `<div class="field"><label>Evidence title</label><input name="label" required minlength="2" maxlength="200" value="${safe(e.label||'')}" placeholder="Similar contract completion certificate"></div><div class="field"><label>Document reference / certificate ID</label><input name="reference" required minlength="2" maxlength="500" value="${safe(e.reference||'')}" placeholder="Signed document ID or official reference"></div><div class="field"><label>Expiry date (if applicable)</label><input type="date" name="expires_on" value="${safe(e.expires_on||'')}"></div>`;}
function evidenceTab(d){return `<div class="sectionhead tab-heading"><div><h2>Organization evidence</h2><p class="sub">${safe(d.tender.organization_name||state.orgs.find(o=>o.id===d.tender.organization_id)?.name||'This organization')} · A typed reference cannot count as verified proof.</p></div></div><div class="notice">Register evidence as unverified, upload its original PDF, then inspect and verify the exact document hash. New files and metadata changes revoke prior verification and make linked decisions stale.</div>
 <div class="grid2"><section>${d.evidence.length?d.evidence.map(e=>{const files=e.files||[],currentHash=e.document_hash||files[0]?.sha256||'',verified=evidenceVerified(e);return `<article class="req" id="evidence-${safe(e.id)}"><div class="spread"><h3>${safe(e.label)}</h3><span class="pill ${verified?'good':'warn'}">${verified?'Current human verification':'Unverified / stale'}</span></div><p class="sub">Reference: ${safe(e.reference)}<br>Expires: ${safe(e.expires_on||'Not specified')}<br>Verification note: ${safe(e.verification_note||'None recorded')}</p>
 ${files.length?`<div class="file-list">${files.map((file,index)=>`<div class="file-card"><div class="spread"><div><strong>${safe(file.filename)}</strong><p class="sub">${index===0?'Latest original':'Earlier original'} · ${safe(file.bytes)} bytes · ${safe(file.uploaded_at)}</p></div><a class="btn outline small" href="/api/organizations/${safe(d.tender.organization_id)}/evidence/${safe(e.id)}/files/${safe(file.id)}" download>Download PDF</a></div>${hashLine(file.sha256)}</div>`).join('')}</div>`:'<div class="notice critical">No original PDF uploaded. This evidence cannot support VERIFIED status.</div>'}
 <details><summary>Upload original and verify evidence</summary><form data-form="evidence-upload" data-id="${safe(e.id)}"><div class="field"><label>Original evidence PDF (max ${uploadLimit()})</label><input name="file" type="file" accept="application/pdf,.pdf" required></div><button class="btn outline small" type="submit">Upload private PDF</button><p class="fineprint">Every upload preserves its original hash and revokes earlier verification.</p></form><div class="divider"></div><form data-form="verify-evidence" data-id="${safe(e.id)}"><h3>Human document verification</h3><input type="hidden" name="document_hash" value="${safe(currentHash)}"><div class="field"><label>Verification note</label><textarea required minlength="10" maxlength="2000" name="verification_note" placeholder="Record issuer, authenticity, validity and relevance checks"></textarea></div><div class="field"><label class="checkbox-label"><input name="inspected_original" type="checkbox" required ${!currentHash||!files.length?'disabled':''}> I downloaded and inspected the latest original, including issuer, dates and relevance</label></div><div class="verification-hash">Document to verify: ${hashLine(currentHash)}</div><button class="btn small" type="submit" ${!currentHash||!files.length?'disabled':''}>Record human verification</button></form>
 ${verified?`<form data-form="withdraw-evidence" data-id="${safe(e.id)}"><input name="document_hash" type="hidden" value="${safe(currentHash)}"><div class="divider"></div><div class="field"><label>Reason to withdraw verification</label><textarea required minlength="10" maxlength="2000" name="verification_note" placeholder="Record the concern or changed circumstance"></textarea></div><button class="btn outline small danger-text" type="submit">Withdraw verification</button></form>`:''}</details>
 <details><summary>Edit evidence metadata</summary><form data-form="edit-evidence" data-id="${safe(e.id)}">${evidenceMetadataFields(e)}<p class="fineprint">Saving metadata returns this evidence to unverified. Verify its original again before using it as proof.</p><button class="btn outline small" type="submit">Save metadata and revoke verification</button></form></details></article>`}).join(''):'<div class="notice">No evidence registered for this organization.</div>'}</section>
 <section><h3>Register new evidence</h3><form data-form="new-evidence">${evidenceMetadataFields()}<div class="notice">New evidence is always unverified. After registration, upload and inspect its original PDF before recording human verification.</div><button class="btn" type="submit">Register unverified evidence</button></form><p class="fineprint">${hosted()?'Original evidence files persist in private cloud storage and downloads require workspace authentication.':'Original evidence files are stored in this local workspace.'} No file is sent to a model or procurement portal.</p></section></div>`;}
function decisionTab(d){const readyToAttest=canAttest(d);return `<div class="grid2 tab-heading"><section><h2>Human decision gate</h2><p class="sub">A named reviewer makes the commercial decision after checking current source requirements and evidence.</p><div class="notice ${d.compliance==='BLOCKED'?'critical':''}">Compliance: <strong>${safe(d.compliance)}</strong><br>Mandatory verified: ${safe(d.mandatory_verified)} of ${safe(d.mandatory_total)}<br>Open issues: ${d.unresolved.length}; blockers: ${d.blockers.length}<br>Complete source inventory attested: <strong>${d.source_scope_verified?'Yes':'No'}</strong></div>
 <form data-form="source-attest"><h3>Attest complete tender source review</h3><p class="fineprint">Inspect every known RFP, schedule, form, annex and amendment. Confirm all inventory documents are available and the source-linked requirement list is complete. Any change requires renewed review.</p>${!readyToAttest?'<div class="notice critical">Before attesting, register a nonempty inventory with an original PDF for every item, include every uploaded source, then review every requirement and its source citation. Missing or unregistered documents prevent attestation.</div>':''}${reviewerField(hosted()?'Authenticated reviewer':'Reviewer name')}<div class="field"><label>Document inventory / completeness review notes</label><textarea name="note" required minlength="15" maxlength="3000" placeholder="Identify documents, versions, annexes and amendments checked and explain completeness"></textarea></div><div class="field"><label class="checkbox-label"><input name="checked_full_document_set" type="checkbox" required ${!readyToAttest?'disabled':''}> I inspected the complete original document set, checked the inventory and confirmed all requirements are registered</label></div><button class="btn outline small" type="submit" ${!readyToAttest?'disabled':''}>Attest source completeness</button></form><div class="divider"></div>
 <form data-form="decision"><div class="field"><label>Decision</label><select name="decision"><option value="HOLD">HOLD — request evidence / clarification</option><option value="NO_BID">NO-BID — do not pursue</option><option value="BID" ${d.compliance!=='READY_FOR_HUMAN_DECISION'?'disabled':''}>BID — authorize bid preparation</option></select></div>${reviewerField(hosted()?'Authenticated human reviewer':'Human reviewer','Reviewer name (local prototype: unverified identity)')}<div class="field"><label>Decision rationale (minimum 10 characters)</label><textarea name="rationale" required minlength="10" maxlength="3000"></textarea></div><button class="btn" type="submit">Record human decision</button></form></section>
 <section><h2>Decision history</h2><p class="sub">History is retained. Source, inventory and linked evidence changes can make an earlier approval stale.</p>${d.decisions.length?d.decisions.map(x=>`<article class="req"><div class="spread"><strong>${safe(x.decision.replace('_','-'))} ${x.is_current?'(current)':'(historical / stale)'}</strong><span class="sub">${safe(x.created_at)}</span></div><p class="sub">By ${safe(x.reviewer)}</p><p class="record-notes">${safe(x.rationale)}</p></article>`).join(''):'<div class="notice">No final human decision has been recorded.</div>'}</section></div>`;}
function exportTab(d){return `<div class="tab-heading"><h2>Editable assessment outputs</h2><p class="sub">Exports reflect the current reviewed state and retain source citations and evidence references. Decision history is recorded separately.</p><div class="links"><a href="/api/tenders/${safe(d.tender.id)}/export.docx">↓ Word (.docx)</a><a href="/api/tenders/${safe(d.tender.id)}/export.xlsx">↓ Excel (.xlsx)</a><a href="/api/tenders/${safe(d.tender.id)}/export.csv">↓ CSV</a></div><div class="divider"></div><h3>Registered original PDFs</h3>${d.sources.length?d.sources.map(source=>`<div class="file-card"><div class="spread"><div><strong>${safe(source.name)}</strong><p class="sub">${safe(source.pages)} pages · ${safe(source.bytes)} bytes</p></div>${sourceLink(d,source)}</div>${hashLine(source.sha256)}</div>`).join(''):'<p class="sub">No original PDF registered. Upload documents and review their inventory before source attestation.</p>'}<div class="notice">${hosted()?'Exports download to your browser; tender and evidence PDFs persist in managed private storage.':'Exports download to your browser; original PDFs remain in this local workspace.'} No e-GP submission or external model call occurs.</div></div>`;}
function pilotTab(d){const m=d.metrics||{};return `<div class="grid2" style="margin-top:23px"><div><h2>Pilot observations</h2><p class="sub">Historical owner-entered observations. These amounts do not enter the collections ledger; record receipts and costs in Delivery.</p><form data-form="metrics"><div class="grid2"><div class="field"><label>Legacy observed quote (BDT)</label><input type="number" min="0" step="0.01" name="quoted_bdt" value="${safe(m.quoted_bdt??'')}"></div><div class="field"><label>Legacy observed payment (BDT)</label><input type="number" min="0" step="0.01" name="paid_bdt" value="${safe(m.paid_bdt??'')}"></div><div class="field"><label>Prior assessment time (min)</label><input type="number" min="0" name="baseline_minutes" value="${safe(m.baseline_minutes??'')}"></div><div class="field"><label>Our total delivery time (min)</label><input type="number" min="0" name="actual_minutes" value="${safe(m.actual_minutes??'')}"></div><div class="field"><label>Generic AI + Excel benchmark (min)</label><input type="number" min="0" name="benchmark_minutes" value="${safe(m.benchmark_minutes??'')}"></div></div>
 <div class="grid2"><div class="field"><label>Changed or protected client's decision?</label><select name="decision_changed"><option value="">Unknown</option><option value="true" ${m.decision_changed===1?'selected':''}>Yes</option><option value="false" ${m.decision_changed===0?'selected':''}>No</option></select></div><div class="field"><label>Client purchased again?</label><select name="repeat_customer"><option value="">Unknown</option><option value="true" ${m.repeat_customer===1?'selected':''}>Yes</option><option value="false" ${m.repeat_customer===0?'selected':''}>No</option></select></div></div><div class="field"><label>Commercial validation notes</label><textarea name="notes">${safe(m.notes||'')}</textarea></div><button class="btn" type="submit">Save observed results</button></form></div><div><div class="notice">Commercial gate: do not fund a self-serve SaaS until paid repeat use, valuable decisions, reasonable review time and advantages over generic AI + Excel are demonstrated.</div><h3>Evaluation fields</h3><p class="sub">Payment evidence; change in bid decision; material risks detected; time to deliver; second paid assessment; confidentiality concerns; cost of onboarding.</p></div></div>`}
function auditTab(d){return `<div style="padding-top:22px"><h2>Append-only activity log</h2><p class="sub">${hosted()?'Records actions under the authenticated workspace owner and timestamps.':'Records actions and timestamps. Local pilot names are not authenticated identities.'}</p>${d.audit.length?d.audit.map(a=>`<div class="audit"><strong>${safe(a.action)}</strong> · ${safe(a.created_at)}<br><span class="muted">${safe(a.actor)} · ${safe(a.payload.slice(0,450))}</span></div>`).join(''):'<p class="sub">No audit entries.</p>'}</div>`}
const terminalWorkflowStates=new Set(['WAITING_HUMAN','COMPLETED','FAILED','STALE','CANCELLED','BUDGET_EXHAUSTED','WAITING_INPUT']);
const checklistLabels={intake_complete:'Scope, exclusions and agreed documents recorded',source_scope_reviewed:'Source completeness and missing documents reviewed',evidence_gaps_reviewed:'Evidence gaps and blockers reviewed',decision_limitations_reviewed:'Decision, uncertainty and diagnostic limitations reviewed'};
const money=minor=>minor===null||minor===undefined?'Unquoted':`BDT ${(Number(minor)/100).toLocaleString('en-BD',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
const moneyInput=minor=>minor===null||minor===undefined?'':(Number(minor)/100).toFixed(2);
const readableStatus=value=>String(value||'PENDING').replaceAll('_',' ');
const workflowBadge=run=>`<span class="pill ${run.state==='COMPLETED'?'good':['FAILED','BUDGET_EXHAUSTED'].includes(run.state)?'bad':'warn'}">${safe(readableStatus(run.state))}</span>`;
const newKey=()=>crypto.randomUUID();
function parseMinor(value,allowBlank=false){
 const text=String(value??'').trim();if(!text&&allowBlank)return null;
 if(!/^\d+(?:\.\d{1,2})?$/.test(text))throw new Error('Enter a BDT amount with at most two decimal places');
 const [whole,fraction='']=text.split('.'),minor=Number(whole)*100+Number(fraction.padEnd(2,'0'));
 if(!Number.isSafeInteger(minor)||minor>9_000_000_000_000)throw new Error('The maximum supported amount is BDT 90,000,000,000.00');return minor;
}
function pauseAnalysis(){
 state.analysisToken++;
 if(state.analysisBusy)state.analysisMessage='Progress is saved. Resume from Analysis work when you are ready.';
 state.analysisBusy=false;
}
async function loadDetailExtras(tenderId){
 const paths=['workflows','service-intake','ledger','diagnostic-releases'];
 const results=await Promise.allSettled(paths.map(path=>api(`/tenders/${tenderId}/${path}`)));
 if(state.selected!==tenderId)return;
 const extra={tenderId,workflows:[],intake:null,ledger:null,releases:null,errors:{}};
 for(let i=0;i<results.length;i++){
  if(results[i].status==='fulfilled')extra[['workflows','intake','ledger','releases'][i]]=results[i].value;
  else extra.errors[paths[i]]=results[i].reason.message;
 }
 state.extra=extra;
 const run=extra.workflows.find(job=>job.id===state.workflowId)||extra.workflows[0];
 if(run){
  try{const detail=await api(`/tenders/${tenderId}/workflows/${run.id}`);if(state.selected===tenderId){state.workflowId=detail.id;state.workflow=detail}}
  catch(e){if(state.selected===tenderId){state.workflow=null;extra.errors.workflows=e.message}}
 }else{state.workflowId=null;state.workflow=null}
}
function featureError(path){const error=state.extra?.errors?.[path];return error?`<div class="notice critical">Unable to load this section: ${safe(error)}. Use Refresh to reconnect before making changes.</div>`:'';}
function commercialOverview(){
 const d=state.commercial;if(!d)return '<div class="notice">The collections register is unavailable. Refresh to load recorded cash and costs.</div>';
 const t=d.totals||{};
 return `<section class="commercial-overview" aria-label="Observed collections"><div class="sectionhead"><div><h2>Observed business results</h2><p class="sub">Manual collections and recorded direct costs · BDT · ${safe(d.paid_assessment_count||0)} assessments with positive net receipts</p></div><span class="pill muted">Overhead unknown</span></div><div class="business-kpis"><div><span>Net cash collected</span><strong>${safe(money(t.net_cash_minor??0))}</strong></div><div><span>Recorded direct costs</span><strong>${safe(money(t.recorded_direct_costs_minor??0))}</strong></div><div><span>Contribution after recorded costs</span><strong>${safe(money(t.contribution_after_recorded_costs_minor??0))}</strong></div><div><span>Repeat paid organizations</span><strong>${safe(d.repeat_paid_organization_count||0)}</strong></div></div><p class="fineprint">Quotes and legacy pilot observations are excluded. Refunds and corrections reduce collections. These are operator-recorded figures; unknown overhead prevents a profit claim.</p></section>`;
}
function nextActions(d){
 const actions=[];
 for(const b of d.blockers||[])actions.push({priority:'Blocker',tab:'requirements',anchor:`requirement-${b.requirement_id}`,label:`Resolve mandatory NOT HELD · R-${b.requirement_id}`,note:b.text});
 for(const issue of d.inventory_issues||[])actions.push({priority:'Source gap',tab:'inventory',anchor:issue.inventory_item_id?`inventory-${issue.inventory_item_id}`:'',label:issue.reason||'Complete the source inventory',note:issue.inventory_item_id?`Document ${issue.inventory_item_id}`:'Every original must be represented'});
 for(const r of d.requirements||[]){
  if(!r.reviewed||!classified(r.mandatory)||!r.source_provenance_valid)actions.push({priority:'Review',tab:'requirements',anchor:`requirement-${r.id}`,label:`Review wording, classification and citation · R-${r.id}`,note:r.text});
  else if(r.mandatory&&(r.effective_status==='UNKNOWN'||r.effective_status==='PARTIAL'))actions.push({priority:'Proof gap',tab:'requirements',anchor:`requirement-${r.id}`,label:`Resolve ${readableStatus(r.effective_status).toLowerCase()} mandatory proof · R-${r.id}`,note:r.evidence_issue||r.text});
 }
 const relevantEvidence=new Set(d.requirements.filter(r=>r.evidence_id).map(r=>r.evidence_id));
 for(const e of d.evidence||[])if(!evidenceVerified(e))actions.push({priority:relevantEvidence.has(e.id)?'Linked proof':'Evidence',tab:'evidence',anchor:`evidence-${e.id}`,label:`Inspect expired, unverified or changed proof · ${e.label}`,note:'Only human verification of the current original can support VERIFIED status'});
 if(!d.source_scope_verified)actions.push({priority:'Human gate',tab:'decision',label:'Attest the complete source set after review',note:'Inventory, every requirement and original versions must be current'});
 if(!d.decisions.length||!d.decisions[0].is_current)actions.push({priority:'Human gate',tab:'decision',label:d.decisions.length?'Review the stale decision against current inputs':'Record BID, NO-BID or HOLD',note:'A historical approval does not authorize a current BID'});
 const quality=(state.workflow?.issues||[]).filter(issue=>['NEEDS_OCR','NEEDS_MANUAL_REVIEW','EXTRACTION_FAILED','UNREADABLE','INCOMPLETE_BOUND','PARSE_FAILED'].includes(issue.code));
 for(const issue of quality)actions.push({priority:'Coverage',tab:'analysis',label:issue.message||readableStatus(issue.code),note:`Source ${issue.source_id||'unspecified'}${issue.page?` · PDF page ${issue.page}`:''}`});
 const visible=actions.slice(0,5),rest=actions.slice(5);
 const rows=items=>items.map(a=>`<li><span class="action-priority">${safe(a.priority)}</span><div><button class="text-button" data-action="resolve" data-tab="${a.tab}" data-anchor="${safe(a.anchor||'')}">${safe(a.label)}</button><p class="sub">${safe(a.note)}</p></div><span aria-hidden="true">→</span></li>`).join('');
 return `<section class="next-actions"><div class="sectionhead"><div><h2>Next actions</h2><p class="sub">Current source, proof and decision gates · suggestions never clear a gate</p></div><span class="pill ${actions.length?'warn':'good'}">${actions.length} open actions</span></div>${actions.length?`<ol class="action-list">${rows(visible)}</ol>${rest.length?`<details><summary>Show ${rest.length} more actions</summary><ol class="action-list">${rows(rest)}</ol></details>`:''}`:'<p class="sub">Current review gates have recorded approval. Confirm delivery scope and release the diagnostic in Delivery.</p>'}</section>`;
}
function analysisTab(d){
 const run=state.workflow,processors=state.processors?.processors||[],model=processors.find(p=>p.kind==='LOCAL_MODEL');
 const running=state.analysisBusy&&state.view==='detail'&&state.tab==='analysis',busy=!!state.analysisFlight;
 return `<div class="sectionhead tab-heading"><div><h2>Analysis work</h2><p class="sub">Source inspection → clause candidates → evidence relevance → citation check → your review</p></div><span class="pill">Local rules</span></div>
 <div class="processor-banner"><div><strong>No model usage charges</strong><p>Fixed local processing prepares source-linked suggestions. It cannot verify evidence, attest completeness or approve a bid.</p></div><span class="pill muted">${safe(model?.label||'Local model')}: ${safe(model?.status||'UNCONFIGURED')}</span></div>
 <p class="fineprint">Model inference is disabled. Analysis advances in saved batches while this view is open. Closing the view or losing connection stops further requests; saved work can be resumed.</p>
 ${featureError('workflows')}${!state.processors?'<div class="notice critical">Processor policy is unavailable. Refresh before starting analysis.</div>':''}
 <div class="workflow-toolbar"><button class="btn" data-action="workflow-create" ${busy||!d.sources.length||!state.processors||state.extra?.errors?.workflows?'disabled':''}>Analyze registered documents</button><span class="sub">${d.sources.length} registered originals · no OCR or model is downloaded</span></div>
 ${state.analysisMessage?`<div class="notice" role="status">${safe(state.analysisMessage)}</div>`:''}
 ${run?workflowPanel(d,run,running,busy):'<div class="empty compact"><h3>No saved analysis yet</h3><p class="sub">Register the original PDFs in Inventory, then start a bounded analysis.</p></div>'}
 ${(state.extra?.workflows||[]).length?`<details class="run-history"><summary>Saved analysis history (${state.extra.workflows.length})</summary>${state.extra.workflows.map(job=>`<div class="item"><div><strong>Analysis #${safe(job.id)}</strong><p>${safe(job.processor_label||'Local rules')} · ${safe(job.created_at||'')}${job.currency?.full_current===false?' · Historical inputs':''}</p></div><div class="item-actions">${workflowBadge(job)}<button class="btn outline small" data-action="workflow-select" data-id="${safe(job.id)}" ${busy?'disabled':''}>${job.id===run?.id?'Selected':'Open'}</button></div></div>`).join('')}</details>`:''}`;
}
function workflowPanel(d,run,running,busy){
 const p=run.progress||{},terminal=terminalWorkflowStates.has(run.state),sourceCurrent=run.currency?.source_current===true;
 const candidates=run.candidates||[],pending=candidates.filter(c=>!c.review);
 return `<section class="workflow-run"><div class="sectionhead"><div><h3>Analysis #${safe(run.id)}</h3><p class="sub">${safe(run.processor_label||'Local rules')} · ${safe(run.contract_version||'')} · ${safe(run.created_at||'')}</p></div>${workflowBadge(run)}</div>
 <div class="progress-copy" role="status" aria-live="polite"><strong>${safe(p.pages_processed||0)} / ${safe(p.pages_total||0)} source pages processed</strong><span>${running?'Advancing one saved batch at a time…':terminal?'Processing stopped at this recorded state':'Saved; continue analysis to advance'}</span></div>
 <div class="stage-list">${(run.steps||[]).map(step=>`<div class="stage ${step.state==='COMPLETED'||step.state==='SUCCEEDED'?'done':''}"><span class="stage-marker" aria-hidden="true">${step.state==='COMPLETED'||step.state==='SUCCEEDED'?'✓':'•'}</span><div><strong>${safe(readableStatus(step.task_kind))}</strong><small>${safe(readableStatus(step.state))}</small></div></div>`).join('')}</div>
 ${run.currency?.full_current===false?`<div class="notice critical">This analysis used earlier inputs. ${sourceCurrent?'Its source citations are still current; a valid candidate can only be added as an unreviewed requirement. Evidence suggestions must be rechecked.':'Sources or their inventory changed. Start a fresh analysis before accepting candidates.'}</div>`:''}
 <div class="flex">${!terminal?`<button class="btn" data-action="workflow-continue" ${busy?'disabled':''}>${running?'Analyzing…':'Continue analysis'}</button><button class="btn outline small" data-action="workflow-cancel">Cancel analysis</button>`:''}<button class="btn outline small" data-action="workflow-restart" ${busy?'disabled':''}>Restart with current documents</button><a class="btn subtle small" href="/api/tenders/${safe(d.tender.id)}/workflows/${safe(run.id)}/receipt.json" download>Download run receipt</a></div>
 ${run.state==='WAITING_INPUT'?'<div class="notice critical">More input or a readable original is needed. Check the findings below, update Inventory, then start a fresh analysis.</div>':''}
 ${(run.issues||[]).length?`<div class="notice critical"><strong>Coverage and provenance findings</strong><ul>${run.issues.map(issue=>{const source=d.sources.find(s=>s.id===issue.source_id);return `<li><strong>${safe(readableStatus(issue.code))}</strong> · ${safe(source?.name||`Source ${issue.source_id||'unspecified'}`)}${issue.page?` · PDF page ${safe(issue.page)}`:''}<br>${safe(issue.message||'Review the original and processing limits.')}${source?` <a class="link" href="/api/tenders/${safe(d.tender.id)}/sources/${safe(source.id)}/file#page=${safe(issue.page||1)}">Open original</a>`:''}</li>`}).join('')}</ul></div>`:''}
 <div class="sectionhead queue-heading"><div><h3>Clause review queue</h3><p class="sub">${pending.length} awaiting disposition · extraction counts do not prove complete coverage</p></div><button class="btn outline small" data-action="resolve" data-tab="requirements">Requirement register →</button></div>
 ${candidates.length?candidates.map(c=>candidateCard(d,run,c,sourceCurrent,busy)).join(''):'<p class="sub">No clause candidates are available in this run. Inspect the source findings and the existing requirement register; absence of candidates never establishes eligibility.</p>'}
 ${evidenceSuggestions(d,run,(run.evidence_suggestions||[]).filter(s=>String(s.requirement_or_candidate_key||'').startsWith('requirement:')))}
 <details class="run-details"><summary>Processing limits and technical receipt</summary><p class="sub">Fixed SYSTEM workflow; autonomous AI agent: No. Training use and external model calls: disabled. No opaque AI runtime identity is claimed.</p><dl class="receipt-grid"><dt>Task batches</dt><dd>${safe(p.task_batches||0)} / ${safe(p.max_task_batches||'—')}</dd><dt>External model calls</dt><dd>${safe(run.usage?.external_model_calls??0)}</dd><dt>Model spend</dt><dd>${safe(money(run.usage?.model_spend_minor??0))}</dd><dt>Processing time</dt><dd>${safe(((run.usage?.elapsed_ms||0)/1000).toFixed(1))} seconds</dd><dt>Infrastructure cost</dt><dd>Unknown</dd></dl>${(run.artifacts||[]).map(a=>`<div class="file-card"><strong>${safe(readableStatus(a.artifact_kind))}</strong><br>${hashLine(a.output_sha256)}</div>`).join('')}</details></section>`;
}
function candidateCard(d,run,c,sourceCurrent,busy){
 const source=d.sources.find(s=>s.id===c.source_id),valid=c.citation_status==='CITATION_VALID',review=c.review;
 return `<article class="candidate-card"><div class="req-top"><div><span class="eyebrow">${safe(source?.name||`Source ${c.source_id}`)} · PDF PAGE ${safe(c.page)}</span><h3>${safe(c.proposed_text)}</h3></div><span class="pill ${valid?'good':'warn'}">${safe(readableStatus(c.citation_status||'PENDING CHECK'))}</span></div><blockquote class="source-quote">${safe(c.verbatim_quote)}</blockquote><div class="flex">${source?`<a class="btn outline small" href="/api/tenders/${safe(d.tender.id)}/sources/${safe(c.source_id)}/file#page=${safe(c.page)}" target="_blank" rel="noopener">Inspect original at page ${safe(c.page)}</a>`:''}<span class="fineprint">Mandatory classification remains unassigned</span></div>
 ${evidenceSuggestions(d,run,(run.evidence_suggestions||[]).filter(s=>s.requirement_or_candidate_key===c.candidate_key))}
 ${review?`<div class="notice ${review.disposition==='ACCEPTED'||review.disposition==='DUPLICATE'?'ok':''}"><strong>${safe(readableStatus(review.disposition))}</strong>${review.requirement_id?` · <button class="text-button" data-action="resolve" data-tab="requirements" data-anchor="requirement-${safe(review.requirement_id)}">Review R-${safe(review.requirement_id)}</button>`:''}<p class="record-notes">${safe(review.note||'')}</p></div>`:`<form data-form="candidate-review" data-key="${safe(c.candidate_key)}" data-job="${safe(run.id)}"><div class="grid2"><div class="field"><label>Your disposition</label><select name="disposition"><option value="ACCEPT" ${!valid||!sourceCurrent?'disabled':''}>Add to requirement register</option><option value="REJECT" ${!valid||!sourceCurrent?'selected':''}>Reject this suggestion</option></select></div><div class="field"><label>Review note</label><input name="note" required minlength="5" maxlength="2000" placeholder="Record your source check or rejection reason"></div></div><p class="fineprint">Adding a candidate creates UNKNOWN, unreviewed content or identifies an existing duplicate. You still review wording, mandatory classification and evidence in the requirement register.</p><button class="btn outline small" type="submit" ${busy?'disabled':''}>Save candidate disposition</button></form>`}</article>`;
}
function evidenceSuggestions(d,run,suggestions){
 if(!suggestions.length)return '';
 return `<details class="evidence-suggestions"><summary>${suggestions.length} evidence relevance suggestion(s) · not verified proof</summary>${suggestions.map(s=>{const evidence=d.evidence.find(e=>e.id===s.evidence_id);return `<div class="file-card"><button class="text-button" data-action="resolve" data-tab="evidence" data-anchor="evidence-${safe(s.evidence_id)}">${safe(evidence?.label||`Evidence ${s.evidence_id}`)}</button><p class="sub">${safe(s.rationale||'Metadata words overlap')} · ${safe(readableStatus(s.expiry_state))}</p><p class="fineprint">Overlapping terms: ${safe((s.overlap_terms||[]).join(', '))}. ${safe((s.unresolved_conditions||[]).join('; '))}</p>${String(s.requirement_or_candidate_key).startsWith('requirement:')?`<button class="text-button" data-action="resolve" data-tab="requirements" data-anchor="requirement-${safe(String(s.requirement_or_candidate_key).split(':')[1])}">Inspect mapped requirement</button>`:''}</div>`}).join('')}</details>`;
}
function dateTimeInput(value){if(!value)return '';const d=new Date(value);if(Number.isNaN(d.getTime()))return '';return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
function deliveryTab(d){
 const e=state.extra,intake=e?.intake?.intake||{},ledger=e?.ledger,releaseData=e?.releases;
 const keys=e?.intake?.checklist_keys||Object.keys(checklistLabels),agreed=new Set(intake.agreed_inventory_ids||[]),totals=ledger?.totals||{};
 return `<div class="sectionhead tab-heading"><div><h2>Diagnostic delivery</h2><p class="sub">Agree the scope, release a frozen report, and record actual collections and costs</p></div><span class="pill muted">Manual service operations</span></div>
 <div class="notice">A useful diagnostic can conclude HOLD or NO-BID and disclose incomplete sources or evidence. Delivery never approves eligibility. No payment is charged and no report is emailed automatically.</div>
 <div class="grid2 delivery-grid"><section><h3>Agreed service scope</h3>${featureError('service-intake')}
 <form data-form="service-intake"><div class="field"><label>Diagnostic scope</label><textarea name="scope" required minlength="10" maxlength="6000" placeholder="Describe the tender assessment and outputs the client agreed to receive">${safe(intake.scope||'')}</textarea></div><div class="field"><label>Exclusions and limitations</label><textarea name="exclusions" maxlength="4000" placeholder="Record what is outside this diagnostic and any access or source limitations">${safe(intake.exclusions||'')}</textarea></div>
 <fieldset class="document-selection"><legend>Agreed source inventory</legend>${d.inventory.length?d.inventory.map(item=>`<label class="checkbox-label"><input type="checkbox" name="agreed_inventory_id" value="${safe(item.id)}" ${agreed.has(item.id)?'checked':''}><span>${safe(item.title)} · ${safe(item.version_label)}${item.availability!=='AVAILABLE'?' · MISSING':''}</span></label>`).join(''):'<p class="sub">No source inventory is registered. Add the known documents in Inventory.</p>'}</fieldset>
 <div class="grid2"><div class="field"><label>Agreed fee (BDT, blank if unquoted)</label><input name="quoted_fee" inputmode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" value="${safe(moneyInput(intake.quoted_fee_minor))}" placeholder="e.g. 1500.00"></div><div class="field"><label>Promised delivery date and time (your timezone)</label><input type="datetime-local" name="due_at" value="${safe(dateTimeInput(intake.due_at))}"></div></div>
 <fieldset class="delivery-checklist"><legend>Your diagnostic review checklist</legend><p class="fineprint">Acknowledging a reviewed gap does not resolve it or attest source completeness.</p>${keys.map(key=>`<label class="checkbox-label"><input type="checkbox" name="${safe(key)}" ${intake.checklist?.[key]?'checked':''}><span>${safe(checklistLabels[key]||readableStatus(key))}</span></label>`).join('')}</fieldset>${reviewerField(hosted()?'Authenticated reviewer':'Scope reviewer')}<button class="btn" type="submit" ${e?.errors?.['service-intake']?'disabled':''}>Save service intake</button></form></section>
 <section><h3>Collections and direct costs</h3>${featureError('ledger')}<div class="cash-summary"><div><span>Quoted fee</span><strong>${safe(money(intake.quoted_fee_minor))}</strong></div><div><span>Net recorded cash</span><strong>${safe(money(totals.net_cash_minor??0))}</strong></div><div><span>Recorded direct costs</span><strong>${safe(money(totals.recorded_direct_costs_minor??0))}</strong></div><div><span>Contribution after recorded costs</span><strong>${safe(money(totals.contribution_after_recorded_costs_minor??0))}</strong></div></div><p class="fineprint">Operator-recorded amounts, not bank reconciliation. Overhead is unknown; contribution is not profit. Quotes do not count as receipts.</p>
 <form data-form="ledger-entry"><div class="grid2"><div class="field"><label>Entry type</label><select name="kind"><option value="RECEIPT">Cash receipt</option><option value="DIRECT_COST">Direct delivery cost</option><option value="REFUND">Refund of a receipt</option><option value="REVERSAL">Correct a receipt or cost</option></select></div><div class="field"><label>Amount (BDT)</label><input name="amount" required inputmode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" placeholder="e.g. 1000.00"></div></div><div class="field ledger-parent" hidden><label>Original entry to correct</label><select name="reverses_entry_id" disabled><option value="">Choose the recorded original</option>${(ledger?.entries||[]).filter(entry=>['RECEIPT','DIRECT_COST'].includes(entry.kind)&&entry.remaining_correctable_minor>0).map(entry=>`<option value="${safe(entry.id)}" data-kind="${safe(entry.kind)}">#${safe(entry.id)} · ${safe(readableStatus(entry.kind))} · ${safe(entry.reference)} · ${safe(money(entry.remaining_correctable_minor))} remaining</option>`).join('')}</select></div><div class="field"><label>Receipt / cost / correction reference</label><input name="reference" required minlength="2" maxlength="200" placeholder="Offline receipt, transaction or invoice reference"></div><div class="field"><label>Entry note</label><textarea name="note" maxlength="2000" placeholder="Describe the collection, direct cost or correction"></textarea></div><button class="btn outline" type="submit" ${e?.errors?.ledger?'disabled':''}>Record ledger entry</button></form>
 <details class="ledger-history"><summary>Append-only ledger (${ledger?.entries?.length||0} entries)</summary>${(ledger?.entries||[]).map(entry=>`<div class="ledger-row"><div><strong>#${safe(entry.id)} ${safe(readableStatus(entry.kind))}</strong><p class="sub">${safe(entry.reference)} · ${safe(entry.created_at)}<br>Recorded by ${safe(entry.actor)}${entry.reverses_entry_id?` · corrects #${safe(entry.reverses_entry_id)}`:''}</p>${entry.note?`<p class="record-notes fineprint">${safe(entry.note)}</p>`:''}</div><strong>${safe(money(entry.amount_minor))}</strong></div>`).join('')||'<p class="sub">No receipts or costs recorded.</p>'}</details>
 </section></div>
 <div class="divider"></div><div class="grid2 delivery-grid"><section><h3>Release an immutable diagnostic</h3>${featureError('diagnostic-releases')}<p class="sub">Capture the current assessment, known gaps, source versions, scope and ledger in a versioned report. Earlier releases stay downloadable when inputs change.</p><form data-form="diagnostic-release">${reviewerField(hosted()?'Authenticated release reviewer':'Release reviewer')}<div class="field"><label>Diagnostic release note</label><textarea name="delivery_note" required minlength="10" maxlength="4000" placeholder="Record the findings, limitations and why this diagnostic is ready to release"></textarea></div><div class="field"><label class="checkbox-label"><input type="checkbox" name="delivery_confirmed_manually"> I have already delivered this report outside TenderOS</label></div><div class="field"><label>Manual delivery reference (required if delivered)</label><input name="delivery_reference" maxlength="200" placeholder="Record the external delivery reference without bank or card details"></div><p class="fineprint">Save all four intake review acknowledgements before release. This creates a frozen report; the optional confirmation only records your stated delivery.</p><button class="btn" type="submit" ${!e?.intake?.exists||keys.some(key=>!intake.checklist?.[key])||e?.errors?.['diagnostic-releases']?'disabled':''}>Create diagnostic release</button></form></section>
 <section><h3>Report releases</h3>${(releaseData?.releases||[]).map(release=>`<article class="release-card"><div class="spread"><strong>Diagnostic v${safe(release.release_version)}</strong><span class="pill ${release.is_current?'good':'warn'}">${release.is_current?'Current snapshot':'Historical / stale'}</span></div><p class="sub">${safe(release.created_at)} · ${safe(release.reviewer)}<br>${safe(readableStatus(release.compliance))} · ${safe(release.current_decision||'No recorded decision')}</p>${release.is_superseded?'<p class="fineprint">A later version is available.</p>':''}<p class="fineprint">${release.delivery_confirmed_manually?`Delivery manually recorded: ${safe(release.delivery_reference)}`:'No external delivery confirmation recorded.'}</p>${release.warnings?.length?`<details><summary>Captured diagnostic warnings (${release.warnings.length})</summary><ul>${release.warnings.map(w=>`<li>${safe(typeof w==='string'?w:w.message||w.reason||JSON.stringify(w))}</li>`).join('')}</ul></details>`:''}<div class="links">${['docx','csv','json'].map(format=>`<a href="/api/tenders/${safe(d.tender.id)}/diagnostic-releases/${safe(release.id)}/export.${format}" download>↓ ${format==='docx'?'Word':format.toUpperCase()}</a>`).join('')}</div><details class="release-hash"><summary>Frozen snapshot hash</summary>${hashLine(release.snapshot_sha256)}</details></article>`).join('')||'<div class="notice">No report released yet. Agree the service scope and review the diagnostic limitations first.</div>'}</section></div>`;
}
async function selectWorkflow(id){
 pauseAnalysis();const tenderId=state.selected;const run=await api(`/tenders/${tenderId}/workflows/${id}`);
 if(state.selected!==tenderId)return;state.workflow=run;state.workflowId=run.id;state.analysisMessage='';render();
}
function saveRun(run){state.workflow=run;state.workflowId=run.id;if(state.extra){const index=state.extra.workflows.findIndex(r=>r.id===run.id);if(index<0)state.extra.workflows.unshift(run);else state.extra.workflows[index]=run}}
async function advanceAnalysis(){
 if(state.analysisFlight||!state.workflow)return;
 const tenderId=state.selected,jobId=state.workflow.id,token=++state.analysisToken;
 const flight={token,tenderId,jobId};state.analysisFlight=flight;state.analysisBusy=true;state.analysisMessage='';render();
 try{
  while(token===state.analysisToken&&state.selected===tenderId&&state.view==='detail'&&state.tab==='analysis'&&!terminalWorkflowStates.has(state.workflow.state)){
   const run=await send(`/tenders/${tenderId}/workflows/${jobId}/advance`,{});
   if(state.selected===tenderId&&state.workflowId===jobId)saveRun(run);
   if(token!==state.analysisToken||state.selected!==tenderId||state.tab!=='analysis')break;
   if(terminalWorkflowStates.has(run.state))state.analysisMessage=run.state==='WAITING_HUMAN'?'Analysis is saved. Review the suggestions and the original documents; human gates still apply.':`Analysis stopped: ${readableStatus(run.state)}. Review its findings before continuing.`;
   render();
   if(!terminalWorkflowStates.has(run.state))await new Promise(resolve=>setTimeout(resolve,180));
  }
 }catch(e){if(state.selected===tenderId)state.analysisMessage=`Connection or processing stopped: ${e.message}. Progress is saved. Refresh the run before resuming.`}
 finally{if(state.analysisFlight===flight)state.analysisFlight=null;if(token===state.analysisToken)state.analysisBusy=false;if(state.selected===tenderId&&state.view==='detail'&&state.tab==='analysis')render()}
}
async function createWorkflow(restart=false){
 if(state.analysisFlight||state.workflowActionBusy)return;
 state.workflowActionBusy=true;
 const tenderId=state.selected,oldId=state.workflow?.id;
 if(!state.createAttempt||state.createAttempt.tenderId!==tenderId||state.createAttempt.restart!==restart||state.createAttempt.oldId!==oldId)state.createAttempt={tenderId,restart,oldId,key:newKey()};
 const path=`/tenders/${tenderId}/workflows${restart?`/${oldId}/restart`:''}`;
 try{
 const run=await api(path,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':state.createAttempt.key},body:JSON.stringify(restart?{}:{processor_kind:'RULES'})});
 state.createAttempt=null;if(state.selected!==tenderId)return;saveRun(run);state.analysisMessage='';render();await advanceAnalysis();
 }finally{state.workflowActionBusy=false}
}

function foot(){return `<div class="footer-note">TenderOS ${hosted()?'private pilot · Single owner · Managed private storage':'local pilot'} · Not a legal qualification certificate · Human sign-off required · No external model calls</div>`}
async function openTender(id){
 pauseAnalysis();const token=++state.loadToken;
 const d=await api('/tenders/'+id);if(token!==state.loadToken)return;
 state.selected=id;state.detail=d;state.view='detail';state.tab='inventory';state.workflowId=null;state.workflow=null;state.extra=null;
 await loadDetailExtras(id);if(token===state.loadToken)render();
}
function inventoryPayload(v){return {...v,publication_date:emptyToNull(v.publication_date),source_id:nullableNumber(v.source_id),supersedes_item_id:nullableNumber(v.supersedes_item_id)};}
async function uploadPdf(path,form){
 const file=form.elements.namedItem('file')?.files?.[0];
 if(!file)throw new Error('Choose the original PDF before uploading');
 if(file.size>maxUploadBytes())throw new Error(`This PDF exceeds the ${uploadLimit()} upload limit`);
 if(!file.size)throw new Error('The selected PDF is empty');
 const body=new FormData(form);if(body.get('inventory_item_id')==='')body.delete('inventory_item_id');
 return api(path,{method:'POST',body});
}
document.addEventListener('change',ev=>{
 const input=ev.target,form=input.closest('form[data-form]');if(!form)return;
 if(form.dataset.form==='ledger-entry'&&input.name==='kind'){
  const correction=['REFUND','REVERSAL'].includes(input.value),parent=form.elements.namedItem('reverses_entry_id');
  form.querySelector('.ledger-parent').hidden=!correction;parent.disabled=!correction;parent.required=correction;parent.value='';
  [...parent.options].forEach(option=>{const invalid=input.value==='REFUND'&&option.dataset.kind==='DIRECT_COST';option.disabled=invalid;option.hidden=invalid});
 }
 if(form.dataset.form==='diagnostic-release'&&input.name==='delivery_confirmed_manually')form.elements.namedItem('delivery_reference').required=input.checked;
 if(input.name==='source_id'&&['new-req','review-req'].includes(form.dataset.form)){
  const page=form.elements.namedItem('source_page'),quote=form.elements.namedItem('source_quote'),pages=input.selectedOptions[0]?.dataset.pages;
  if(page){page.value='';if(pages)page.max=pages;else page.removeAttribute('max');}
  if(quote)quote.value='';
 }
 if(['inventory-new','inventory-edit'].includes(form.dataset.form)){
  const availability=form.elements.namedItem('availability'),source=form.elements.namedItem('source_id'),type=form.elements.namedItem('document_type'),supersedes=form.elements.namedItem('supersedes_item_id');
  if(input.name==='availability'&&source){const missing=availability.value==='MISSING';source.required=!missing;source.disabled=missing;if(missing)source.value='';}
  if(input.name==='document_type'&&supersedes)supersedes.required=type.value==='ADDENDUM';
 }
});

document.addEventListener('input',ev=>{
 const form=ev.target.closest('form[data-form]');if(form)delete form.dataset.idempotency;
});

document.addEventListener('keydown',ev=>{
 const tab=ev.target.closest('[role=tab]');if(!tab||!['ArrowLeft','ArrowRight','Home','End'].includes(ev.key))return;
 const tabs=[...document.querySelectorAll('[role=tab]')],index=tabs.indexOf(tab);
 const next=ev.key==='Home'?0:ev.key==='End'?tabs.length-1:(index+(ev.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
 ev.preventDefault();tabs[next].click();
});

document.addEventListener('click',async ev=>{
 const btn=ev.target.closest('[data-action]');if(!btn)return;
 try{clearAlert();const action=btn.dataset.action;
  if(action==='home'){pauseAnalysis();state.loadToken++;state.view='home';state.selected=null;state.detail=null;state.extra=null;render()}
  if(action==='new-tender'){pauseAnalysis();state.loadToken++;state.view='new';render()}
  if(action==='refresh'){await refresh();notify('Workspace refreshed',true)}
  if(action==='open-tender'){await openTender(Number(btn.dataset.id))}
  if(action==='tab'){if(btn.dataset.tab!==state.tab)pauseAnalysis();state.tab=btn.dataset.tab;render();document.getElementById('workflow-tab-'+state.tab)?.focus()}
  if(action==='resolve'){
   pauseAnalysis();state.tab=btn.dataset.tab;render();
   const target=btn.dataset.anchor?document.getElementById(btn.dataset.anchor):document.getElementById('tabContent');
   if(target){target.querySelector('details')?.setAttribute('open','');target.tabIndex=-1;target.focus();target.scrollIntoView({behavior:'smooth',block:'start'})}
  }
  if(action==='workflow-select'){btn.disabled=true;await selectWorkflow(Number(btn.dataset.id))}
  if(action==='workflow-create'||action==='workflow-restart'){btn.disabled=true;await createWorkflow(action==='workflow-restart')}
  if(action==='workflow-continue'){btn.disabled=true;await advanceAnalysis()}
  if(action==='workflow-cancel'){
   pauseAnalysis();btn.disabled=true;const tenderId=state.selected,jobId=state.workflow.id;
   const run=await send(`/tenders/${tenderId}/workflows/${jobId}/cancel`,{});
   if(state.selected===tenderId){saveRun(run);state.analysisMessage='Analysis cancelled. Original documents and saved outputs are preserved.';render()}
  }
  if(action==='delete-inventory'){
   if(!window.confirm('Remove this inventory record? Source completeness must be reviewed again, and earlier BID approvals will become stale.'))return;
   btn.disabled=true;
   try{await api(`/inventory/${btn.dataset.id}`,{method:'DELETE'});await refresh();notify('Inventory record removed; source review and decision currency updated',true)}finally{btn.disabled=false}
  }
  if(action==='demo'){const x=await api('/demo',{method:'POST'});await refresh();await openTender(x.tender_id);notify('Loaded synthetic demo only. No real tender or organization data.',true)}
 }catch(e){notify(e.message);if(btn.isConnected)btn.disabled=false}
});
document.addEventListener('submit',async ev=>{
 const form=ev.target.closest('form[data-form]');if(!form)return;ev.preventDefault();
 if(form.dataset.busy==='true')return;form.dataset.busy='true';
 const submit=form.querySelector('button[type=submit]');if(submit)submit.disabled=true;
 try{clearAlert();const v=formValues(form),typ=form.dataset.form,d=state.detail;
  if(typ==='candidate-review'){
   const tenderId=state.selected;
   const run=await send(`/tenders/${tenderId}/workflows/${form.dataset.job}/candidates/${encodeURIComponent(form.dataset.key)}/review`,{disposition:v.disposition,note:v.note});
   if(state.selected===tenderId){saveRun(run);state.detail=await api(`/tenders/${tenderId}`);render();notify('Candidate disposition saved. Added requirements remain unreviewed and UNKNOWN until your source and evidence review.',true)}
  }
  if(typ==='service-intake'){
   const checklist=Object.fromEntries(Object.keys(checklistLabels).map(key=>[key,!!form.elements.namedItem(key)?.checked]));
   const due=v.due_at?new Date(v.due_at):null;if(due&&Number.isNaN(due.getTime()))throw new Error('Choose a valid delivery date and time');
   await send(`/tenders/${state.selected}/service-intake`,{scope:v.scope,exclusions:v.exclusions,agreed_inventory_ids:new FormData(form).getAll('agreed_inventory_id').map(Number),due_at:due?.toISOString()||null,quoted_fee_minor:parseMinor(v.quoted_fee,true),currency:'BDT',reviewer:v.reviewer,checklist},'PUT');
   await refresh();notify('Service scope and review checklist saved. Quotes are separate from cash receipts.',true);
  }
  if(typ==='ledger-entry'){
   const amount=parseMinor(v.amount);if(amount<=0)throw new Error('The ledger amount must be greater than zero');
   const correction=['REFUND','REVERSAL'].includes(v.kind);if(correction&&!v.reverses_entry_id)throw new Error('Choose the original receipt or cost for this correction');
   form.dataset.idempotency||=newKey();
   const out=await send(`/tenders/${state.selected}/ledger`,{kind:v.kind,amount_minor:amount,currency:'BDT',reverses_entry_id:correction?Number(v.reverses_entry_id):null,idempotency_key:form.dataset.idempotency,reference:v.reference,note:v.note});
   await refresh();notify(out.replayed?'This entry was already recorded; no duplicate was added.':'Append-only ledger entry recorded. Collections and direct costs updated.',true);
  }
  if(typ==='diagnostic-release'){
   const manual=!!v.delivery_confirmed_manually;if(manual&&!v.delivery_reference?.trim())throw new Error('Record a delivery reference when confirming external delivery');
   form.dataset.idempotency||=newKey();
   const out=await send(`/tenders/${state.selected}/diagnostic-releases`,{reviewer:v.reviewer,delivery_note:v.delivery_note,idempotency_key:form.dataset.idempotency,delivery_confirmed_manually:manual,delivery_reference:v.delivery_reference||''});
   await refresh();notify(out.replayed?'This frozen diagnostic was already released; no duplicate was created.':'Versioned diagnostic released. Download its frozen report from Report releases.',true);
  }
  if(typ==='new-org'){await send('/organizations',{name:v.name});await refresh();state.view='new';render();notify('Organization registered',true)}
  if(typ==='new-tender'){const x=await send('/tenders',{...v,organization_id:Number(v.organization_id),deadline:emptyToNull(v.deadline)});await refresh();await openTender(x.id);notify('Assessment created',true)}
  if(typ==='inventory-new'){await send(`/tenders/${state.selected}/inventory`,inventoryPayload(v));await refresh();notify('Document inventory record added; source completeness needs human review',true)}
  if(typ==='inventory-edit'){await send(`/inventory/${form.dataset.id}`,inventoryPayload(v),'PUT');await refresh();notify('Inventory updated; review source completeness and decision currency',true)}
  if(typ==='new-req'){await send(`/tenders/${state.selected}/requirements`,{text:v.text,source_id:nullableNumber(v.source_id),source_quote:v.source_quote,source_page:nullableNumber(v.source_page),mandatory:v.mandatory===''?null:v.mandatory==='true',reviewed:false});await refresh();notify('Source-linked requirement registered as unreviewed',true)}
  if(typ==='review-req'){await send(`/requirements/${form.dataset.id}/review`,{text:v.text,mandatory:v.mandatory==='true',source_id:nullableNumber(v.source_id),source_page:nullableNumber(v.source_page),source_quote:v.source_quote},'PUT');await refresh();notify('Requirement reviewed. If the clause, classification or citation changed, its evidence mapping must be renewed.',true)}
  if(typ==='new-evidence'){await send('/evidence',{organization_id:d.tender.organization_id,label:v.label,reference:v.reference,expires_on:emptyToNull(v.expires_on),verified:false,verification_note:''});await refresh();notify('Unverified evidence registered. Upload its original PDF before verification.',true)}
  if(typ==='edit-evidence'){await send(`/evidence/${form.dataset.id}`,{organization_id:d.tender.organization_id,label:v.label,reference:v.reference,expires_on:emptyToNull(v.expires_on),verified:false,verification_note:''},'PUT');await refresh();notify('Evidence metadata updated and prior verification revoked',true)}
  if(typ==='evidence-upload'){await uploadPdf(`/evidence/${form.dataset.id}/upload-pdf`,form);await refresh();notify('Private evidence PDF uploaded. Inspect the latest original and verify its document hash.',true)}
  if(typ==='verify-evidence'){
   if(!v.inspected_original||!v.document_hash)throw new Error('Upload and inspect the latest original PDF before verification');
   await send(`/evidence/${form.dataset.id}/verify`,{verified:true,verification_note:v.verification_note,document_hash:v.document_hash});await refresh();notify('Human verification recorded for the exact uploaded document hash',true)}
  if(typ==='withdraw-evidence'){await send(`/evidence/${form.dataset.id}/verify`,{verified:false,verification_note:v.verification_note,document_hash:v.document_hash});await refresh();notify('Evidence verification withdrawn; linked requirements and decisions must be reviewed',true)}
  if(typ==='status'){await send(`/requirements/${form.dataset.id}/status`,{status:v.status,evidence_id:emptyToNull(v.evidence_id)?Number(v.evidence_id):null,notes:v.notes},'PUT');await refresh();notify('Requirement status updated',true)}
  if(typ==='source-attest'){if(!canAttest(d))throw new Error('Complete the document inventory and source-linked requirement review before attesting');await send(`/tenders/${state.selected}/attest-source-scope`,{reviewer:v.reviewer,note:v.note,checked_full_document_set:!!v.checked_full_document_set});await refresh();notify('Complete source inventory review recorded',true)}
  if(typ==='decision'){await send(`/tenders/${state.selected}/decisions`,v);await refresh();notify('Human decision appended to immutable decision history',true)}
  if(typ==='pdf-upload'){const out=await uploadPdf(`/tenders/${state.selected}/upload-pdf`,form);await refresh();notify(`Original PDF registered in inventory. ${out.candidates} candidate requirements need human review. Check the document metadata and known missing items.`,true)}
  if(typ==='metrics'){
   const values={...v};for(const key of ['quoted_bdt','paid_bdt','baseline_minutes','actual_minutes','benchmark_minutes'])values[key]=v[key]===''?null:Number(v[key]);
   for(const key of ['decision_changed','repeat_customer'])values[key]=v[key]===''?null:v[key]==='true';
   await send(`/tenders/${state.selected}/metrics`,values);await refresh();notify('Actual pilot data saved',true)}
 }catch(e){notify(e.message)}finally{form.dataset.busy='false';if(submit)submit.disabled=false}
});
refresh().catch(e=>{$('#runtimeMode').textContent='WORKSPACE UNAVAILABLE';$('#runtimeStorage').textContent='Authentication or configuration needs attention';$('#content').textContent='Unable to load the workspace. Resolve the connection issue, then refresh.';notify('Unable to connect to TenderOS: '+e.message)});
