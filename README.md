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

### Step-by-step usage for new projects

The instructions below assume you are starting from the root folder of the app
or documentation project where you want the Apple docs snapshots to live (for
example `~/projects/my-app`).

1. **Create the required folders.** In your project root, create the following
   directories so the sync scripts have predictable locations:

   ```bash
   mkdir -p Docs/Apple
   mkdir -p docs-config
   mkdir -p scripts
   ```

   `Docs/Apple/` will hold the Markdown output, `docs-config/` stores the URL
   list, and `scripts/` keeps helper scripts such as
   `generate_docs_config.py`.

2. **Copy the template files into place.** Drop `scripts/generate_docs_config.py`
   into the `scripts/` directory you just created.  Copy any starter URL list
   (for example the provided `docs-config/apple_urls.txt`) into `docs-config/`.
   Your tree should now look similar to:

   ```text
   my-app/
     Docs/
       Apple/
     docs-config/
       apple_urls.txt
     scripts/
       generate_docs_config.py
   ```

3. **Run the sitemap crawler.** The script only uses the Python standard
   library, so the system Python 3 that ships with macOS or most Linux
   distributions is sufficient.  From the root of your project run:

   ```bash
   python3 - <<'PY'
from pathlib import Path
from scripts.generate_docs_config import gather_urls

# Replace this URL with the sitemap or sitemap index you want to crawl.
START_SITEMAP = "https://developer.apple.com/tutorials/sitemap.xml.gz"

urls = gather_urls(START_SITEMAP)

output_path = Path("docs-config/apple_urls.txt")
output_path.write_text(
    "\n".join(f"{url} {url.rsplit('/', 1)[-1] or 'index'}.md" for url in urls),
    encoding="utf-8",
)

print(f"Wrote {output_path} with {len(urls)} entries")
PY
   ```

   The `gather_urls` helper automatically inflates compressed sitemap indexes
   (`.xml.gz` files) and follows nested indexes until every document URL is
   discovered.

4. **Review and customize the output file.** Open
   `docs-config/apple_urls.txt`, adjust any Markdown filenames to match your
   preferred naming scheme, and remove URLs you do not need.  The `make
   docs-sync` command (documented above) will use this file to download and
   convert the listed pages into Markdown files under `Docs/Apple/`.

## Guiding Codex CLI with Apple Docs context

Teams that drive this workflow through [Codex CLI](https://github.com/openai/codex-cli)
can provide tailored agent instructions so that the assistant knows how to
inspect the Apple documentation snapshots.  The file
`docs/codex_cli_agents_chunk.md` contains a ready-to-copy Markdown block that
you can paste into your project's `AGENTS.md` file.

The instruction chunk walks Codex through:

- Where to find the sync scripts and URL configuration (`scripts/` and
  `docs-config/`).
- How to make an initial guess at the most relevant Apple developer page.
- A rubric for checking additional Markdown snapshots in `Docs/Apple/` until
  the agent locates the correct reference material or decides to fetch a new
  page with `make docs-sync`.

Copy the fenced block into your `AGENTS.md`, commit the change in your Codex
CLI project, and the assistant will consistently reference the synced Apple
documentation before attempting new tasks.
