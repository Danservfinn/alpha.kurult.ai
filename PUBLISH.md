# Publish step

Arghun drops one markdown file per day. The builder turns that folder into the static site. Live DNS for alpha.kurult.ai waits on Temujin. Do not touch kurult.ai MX or mail records.

## Where the markdown goes

Canonical drop folder, in this repo:

```
articles/YYYY-MM-DD-slug.md
```

- Date is the filename date. Slug is lowercase letters, digits, and single hyphens.
- Required frontmatter: `title`, `date` (must match the filename date), `summary`, and a non-empty `sources` list of `label` plus `http` or `https` `url`.
- The builder rejects any other filename, a date mismatch, or missing sources. A sourceless note cannot ship.
- The research-only disclaimer is injected by the builder. Do not rely on the note to include it.
- Drafts on the box stay in `/workspace/state/arghun/drafts/` until Arghun copies a compliant file into `articles/`. This repo does not pull that folder.

Fixture already on the desk: `articles/2026-10-02-desk-open.md`. It is a format sample, not a market call.

## What triggers the rebuild

From the repo root:

```sh
python3 scripts/build.py
```

That writes `dist/`. Exit line is `BUILD_OK` or `BUILD_FAIL`.

Preview (not the live hostname):

```sh
CLOUDFLARE_API_TOKEN=$(cat ~/.kublai/secrets/cloudflare-pages-api-token) \
CLOUDFLARE_ACCOUNT_ID=1c1f920b044b2841be2e0f3021dad061 \
npx wrangler@4.59.1 pages deploy dist \
  --project-name alpha-kurult-ai \
  --branch feat/alpha-site
```

`--branch` other than the production branch (`main`) is a preview URL. Do not omit `--branch`. Omitting it publishes production. Do not attach the custom domain `alpha.kurult.ai` until Temujin says deploy. Do not pass `--commit-hash`.

After Temujin approves the live cutover, and only then: deploy the production branch and attach `alpha.kurult.ai` in Pages custom domains. Confirm `dig +short kurult.ai MX` is still `smtp.google.com` before and after. Never edit MX.

## What this host is not

No analytics. No wallet connect. No comments. No production `.env`. First-party scripts only, served from this host. No third-party script host. Pages Functions in `functions/` cache the Treasury yield XML and the chain RPC calls. They are not copied into `dist/`.

## Chart library

`lightweight-charts` 5.2.1 standalone production build.
sha256: e21cc5caa0226ef30bd8549c50b9ef926615f2a4ee6b4e486353477a55f598cf
Path: `static/vendor/lightweight-charts-5.2.1.js`
License: Apache-2.0, file `static/vendor/LICENSE-lightweight-charts`.
Notice: `static/vendor/NOTICE-lightweight-charts`.
The builder rejects a sha mismatch.
