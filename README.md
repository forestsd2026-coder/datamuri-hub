# Datamuri source and deployment

The production site remains on the existing `datamuri-hub` Cloudflare Pages
direct-upload project. Pushing `main` now runs `.github/workflows/deploy.yml`;
GitHub's **Actions → Deploy complete Datamuri site → Run workflow** also deploys
the full current source. No new hosting project or paid service is required.

The workflow stages **every tracked public asset** into `.site/`, excluding only
deployment infrastructure and `functions/`. Cloudflare's maintained Wrangler
Action uploads that complete directory and compiles `functions/[[path]].js`
from the repository root. It must never deploy only an edited page. Add all
new assets to Git. Do not commit credentials or local build directories.

The existing function keeps the `datamuri-hub.pages.dev` and apex host redirect
to `www.datamuri.us.com`, preserving path and query. Compatibility settings and
custom domains remain managed by the existing Cloudflare project; the workflow
does not replace them.

Repository Actions configuration:

- Secret `CLOUDFLARE_API_TOKEN`: Cloudflare **Pages Write**, scoped to the existing
  account. Cloudflare's available Pages token scope is account-wide, not one
  project; this token has no DNS, Workers, or general account permissions.
- Variable `CLOUDFLARE_ACCOUNT_ID`: existing Cloudflare account ID.
- Public repository Actions runner, pinned official checkout/Node/Wrangler actions,
  pinned Wrangler version, read-only GitHub permissions, serialized production deploys.

After deployment, `scripts/verify.py` fetches every public asset from the unique
deployment URL and compares its SHA-256 with the source. It also checks both
existing production redirects and the custom-domain homepage. The unique URL
avoids zone-level HTML email/analytics transformations affecting byte comparison.

For a local read-only verification, run `python3 scripts/stage.py` from a fresh
checkout, then `python3 scripts/verify.py https://DEPLOYMENT.datamuri-hub.pages.dev`.
For rollback, use Cloudflare Pages' existing previous successful deployment or
revert a source commit and push `main`; do not replace the site with a partial tree.
