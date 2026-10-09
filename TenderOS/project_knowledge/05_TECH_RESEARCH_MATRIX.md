# ART-050 — Candidate Technology and Reuse Matrix
**Status:** Desktop/repository review + general technical knowledge; **not** current web/GitHub/license audit. This session has no live web search. Verify versions, licenses, pricing and security alerts before engineering selection.

| Task | Candidate | Why consider | Reuse recommendation | Verification required |
|---|---|---|---|---|
| Current app and API | FastAPI | Already in repository, tested | RETAIN for pilot | Pin versions/security advisories |
| Deterministic data | SQLite | Already working locally | RETAIN during isolated pilot | Concurrency and backup drills |
| Multi-tenant data | PostgreSQL | RLS and relational constraints | DEFER to multi-user SaaS | Tenant isolation tests, hosting cost |
| Text PDF | pypdf | Already in repo | RETAIN with warnings | Table loss, font/layout limitations |
| Structured parsing | pdfplumber / Docling | Layout-friendly extraction candidates | BENCHMARK, do not auto-adopt | License, installation footprint, scanned results |
| Scanned PDFs | Tesseract / OCRmyPDF | Local OCR candidate | BENCHMARK only after data rights review | Bangla accuracy, page mapping, subprocess isolation |
| Model interface | typed Python adapter / approved local runtime | Provider-independent task calls and explicit egress | SMALL adapter first | Available local compute, model runtime, measured quality |
| Agent orchestration | LangGraph | Bounded stateful agent flows | EVALUATE after minimal agent baseline | Installation/license/maintenance/live docs |
| Agent orchestration | PydanticAI | Typed tools/outputs | EVALUATE | Current APIs and integration effort |
| Agent orchestration | CrewAI | Multi-role orchestration | COMPARE; avoid persona-only demos | Actual tool support, cost/latency |
| Durable execution | Temporal | Workflow retries and durable state | DEFER until job loss observed | Ops burden, maintenance |
| Low-code operations | n8n | Useful for authorized business triggers | DEFER beyond core pilot | Access control and secure secret lifecycle |
| Evidence search | PostgreSQL FTS/pgvector | Hybrid retrieval when evidence volume grows | Start scoped lexical/local index; benchmark vector | Recall, tenant filters, embedding egress |
| Outputs | python-docx, openpyxl | Both already used | RETAIN and enhance tests | Version pinning, large docs, injection testing |
| Observability | OpenTelemetry / Langfuse | Agent tracing and eval | Start local structured audit events | Privacy policies, sensitive trace redaction |
| Development agents | Codex or other autonomous repo coding runtime | Necessary founder gate | REQUIRED but NOT AVAILABLE IN EXPOSED SESSION | Real child-run receipts, tool logs, independent review |
| Hosted autonomous builder | Replit AI Agent | Offered connector in earlier discussion | OPTIONAL alternative, not yet connected | Does it support independently delegated agents and private local artifacts? |
| Model cloud gateway | OpenAI/Anthropic APIs | Real model calls if approved | OPT-IN ONLY | API key, pricing, data policy, processor agreement |
| Containerization | Docker/Compose | Isolates service + controlled dependencies | SHOULD, after approved architecture | Image CVEs, secrets, resource caps |

## Build-vs-reuse decision
Preserve current rule engine/API/tests, improve targeted weaknesses, and create only the minimum agent orchestration needed for real model-backed extraction and scoped evidence retrieval. Resist building a full AI operating company before first repeat paid customer behavior. Freeze technology decisions until version/license/source verification can be completed.
