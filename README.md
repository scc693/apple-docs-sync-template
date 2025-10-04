# Apple Docs Sync Template

[![Apple Docs Sync](https://github.com/${{REPO_OWNER}}/${{REPO_NAME}}/actions/workflows/sync_apple_docs.yml/badge.svg)](https://github.com/${{REPO_OWNER}}/${{REPO_NAME}}/actions/workflows/sync_apple_docs.yml)
![Latest Tag](https://img.shields.io/github/v/tag/${{REPO_OWNER}}/${{REPO_NAME}}?label=latest%20tag&sort=semver)

Syncs a curated set of Apple developer docs into Markdown snapshots for offline/reference use in other projects.

## How it works
- URLs are defined in `docs-config/apple_urls.txt` (one line per: `<URL> <output.md>`).
- `scripts/sync_apple_docs.sh` fetches pages (curl) and converts HTML→Markdown (pandoc) into `Docs/Apple/`.
- A nightly GitHub Action opens a PR with changes.

## Use in any project
1. Copy `docs-config/`, `scripts/`, `.github/workflows/sync_apple_docs.yml`, and the `Docs/Apple/` folder (empty is fine).
2. Add or edit URLs in `docs-config/apple_urls.txt`.
3. Run locally:
   ```bash
   brew install pandoc   # macOS
   make docs-sync        # or: bash scripts/sync_apple_docs.sh
   ```

## Local testing without network access
The sync script can run against lightweight fixtures when outbound network access is unavailable (for example, when using `act` or other CI sandboxes).

```bash
APPLE_DOCS_FETCH_MODE=fixtures make docs-sync
```

When running the GitHub Actions workflow locally with [`act`](https://github.com/nektos/act), the script automatically falls back to fixtures because `act` sets the `ACT` environment variable.

You can provide custom fixtures by setting `APPLE_DOCS_FIXTURE_DIR` to a directory containing `<output>.html` files that match entries in `docs-config/apple_urls.txt`.

## Regenerating the sitemap configuration

The helper script `scripts/generate_docs_config.py` can crawl Apple developer
sitemaps and rebuild `docs-config/apple_urls.txt` as your source of truth
changes.  The crawler understands nested sitemap indexes and now also supports
compressed sitemap indexes (`.xml.gz`), inflating them automatically while it
discovers URLs.
