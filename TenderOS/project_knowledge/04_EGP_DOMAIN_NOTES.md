# ART-040 — e-GP Domain Source Notes for TenderOS
**Scope:** Selected visible pages of *e-GP টেন্ডার এর আদ্যোপান্ত* (attached scanned explanatory guide). These are **secondary instructional material**, not authenticated official current rules or legal advice.

## Observations from supplied book
| Printed page / source file | Observed subject | TenderOS design implication |
|---|---|---|
| 163–166, `E-GP_163-205.pdf` | Tenderer/applicant/consultant registration, credential documents, tenderer records and claimed experience verification | Keep company credentials, issuer, experience proof, verified vs attested status distinct |
| 175–177, `E-GP_163-205.pdf` | e-Tender document preparation, tender/application/proposal completeness, forms/templates, mandatory questions and selection criteria | Support specific templates/categories; don't reduce all requirements to one paragraph; completeness human review |
| 176–177, same | Clause 3.4.2: applicant responsibility to read and address all tender selection criteria and amendments | Requirements must include amendments and actual tender-specific text; secondary book cannot substitute the RFP |
| 180–182, same | Online uploading, strict closing time, pre-tender meeting and clarifications | Record deadlines and clarification windows; no autonomous submission; clear "assessment does not submit" warning |
| 183–184, same | Tender/Application/Proposal amendment publication and e-lodgment; electronic document integrity | Every addendum triggers a new source-set version and revokes previous BID currentness |
| 188–189, same | e-evaluation follows published criteria; working sheets and review | Build source-linked compliance matrix and clear human review states |
| 206–211, `E-GP_205-245.pdf` | Guideline appendices on payment systems | Payment instruments matter for future tender-specific requirements, not for MVP payment automation |
| 229+ and 249+, `E-GP_205-245.pdf` / `E-GP_245-287.pdf` | BPR and PPR 2025/Schedule-II comparisons | Version-specific procurement regimes and official rule verification matter; do not hardcode secondary thresholds |
| 262–274, `E-GP_245-287.pdf` | e-GP user agreement, confidentiality, time reference and tender submission | Project design needs confidentiality, time zone (BST), e-GP boundary and record integrity |
| 206, `E-GP_205-245.pdf` | Section 3.12 translation/publication refers to prior government approval | Treat scanned book as reference; do not redistribute/translate it wholesale in the product without checking rights |

## Required domain data fields
- Procurement regime (Bangladesh BPPA/PPR, donor-specific, other), **source of applicable rule**, effective date, tender method where specified, jurisdiction and document version.
- Opportunity reference, buyer, deadlines with timezone `Asia/Dhaka` or documented source timezone, clarification meeting and addendum issue dates.
- Source file SHA-256, original filename, language, PDF printed-page-vs-viewer-page mapping, source section, exact quote, layout/page bounds where available.
- Requirement type (`mandatory_eligibility`, `experience`, `turnover`, `financial_capacity`, `key_personnel`, `joint_venture`, `documentation`, `security`, `methodology`, `submission_process`, `other`) as candidate labels until confirmed.
- Named evidence records with owner, issuer, contract value/currency, dates/period, relevance span, verified-by and expiry.

## Quality risk specifically exposed by these materials
The supplied guide is partly Bangla, partly English, contains facing-page two-up scans, tables and page mappings. The existing regex/pypdf pipeline cannot process it reliably. A future OCR/layout parser should be benchmarked on actual scanned RFPs and document tables; unclear text must be flagged rather than fabricated. Avoid using the guide as current legal authority; compare source-specific obligations to current official BPPA documents when public research becomes available.

## Do not implement
No e-GP credentials, portal login, CAPTCHA handling, auto-submission, financial transactions or tender amendment posting as MVP work. TenderOS complements official electronic procurement infrastructure.
