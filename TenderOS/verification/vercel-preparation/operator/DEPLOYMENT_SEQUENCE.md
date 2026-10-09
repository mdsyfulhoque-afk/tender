# TenderOS Vercel deployment preparation

Agent: `/root/tenderos_vercel_operator`. Opaque runtime run ID: unavailable (`null`).

## Current state

Official Vercel CLI 63.1.0 is installed outside source. `whoami --format json --non-interactive` reports `loggedIn: false` and exits 1. There are no configured Vercel secret bindings, runtime variables, outbound identities, or linked project. No Vercel account tools are callable in this child catalog. The managed environment is current and its restricted package-manager network policy is enforced. An unauthenticated HEAD request to `https://api.vercel.com/v2/user` through the inherited proxy receives CONNECT 403; no credential was sent. No account resource or deployment was created.

## Required setup

Use the supported cloud environment configuration workflow to grant the Vercel API/authentication hosts and bind `VERCEL_TOKEN` securely, or complete a deliberate official CLI login once authentication networking is available. Never paste a token into chat, source, CLI arguments, or receipts. Preserve proxy variables and CA trust; do not disable TLS or attempt an alternate egress path. Provisioned database/blob and deployment verification hosts must be allowed once their actual names are known.

## Ordered execution after candidate freeze

1. Run `vercel whoami --format json --non-interactive`. Inspect actual teams and projects; do not invent account/team/project IDs or create a duplicate project.
2. Freeze the independently reviewed source commit. Operate from the exact deployment directory provided by the packaging agent. Explicitly link the intended existing or newly authorized project, then run `vercel project inspect --non-interactive` and confirm owner and project.
3. Use Vercel Marketplace storage discovery and the live Neon integration guide to inspect available products/plans/regions. Prefer an existing appropriate database or a verified free resource. Do not select a paid/default billing plan without established authorization. If Marketplace terms or account claim requires a human browser action, report that exact server requirement without inventing approval.
4. Provision/connect Neon Postgres to the intended environments only. Inspect required env variable names against the frozen template; never print values.
5. Create/connect a Blob store with `--access private`, explicit intended region and environments. The current CLI supports `vercel blob create-store <name> --access private --environment production --environment preview`; use its installed help for exact confirmation flags. Use a separate preview data scope when validation would mutate data.
6. Verify server authentication bindings and all required datastore/private Blob env keys. The storage adapter supports a private-store read/write token or runtime OIDC token plus `BLOB_STORE_ID`; do not save short-lived OIDC values for reuse.
7. Pull secrets only to an excluded local file when necessary. Bootstrap instructions require linking and complete env verification before database migrations or dev. Run only documented schema initialization/migration commands against the intended resource. Do not import an unknown customer SQLite DB or uploaded PDFs.
8. Deploy the frozen application, verify build/runtime status and the complete authenticated browser/API/data/private-PDF flow, and promote to production under the existing user deployment authorization. Keep final BID approval human.
9. Record the returned deployment URL and actual project ID, verify persistence after a new request/function instance, verify unauthenticated access is rejected, and ensure private Blob URLs cannot be anonymously downloaded.

## Successful skill reads

`bootstrap`, `vercel-cli`, `vercel-storage`, `marketplace`, CLI storage/integrations references, and cloud environment runtime/networking references.

The catalog lists `deployments-cicd`, `env-vars`, and `access-protected-vercel-deployment`, but `skills.read` for their exact listed packages/resources returned `failed to read skill resource`. No content or requirement from these unreadable resources has been fabricated. Use installed CLI help or repair resource access before relying on those skills.
