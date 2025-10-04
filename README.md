# Apple Docs Sync Template

[![Apple Docs Sync](https://github.com/${{REPO_OWNER}}/${{REPO_NAME}}/actions/workflows/sync_apple_docs.yml/badge.svg)](https://github.com/${{REPO_OWNER}}/${{REPO_NAME}}/actions/workflows/sync_apple_docs.yml)
![Latest Tag](https://img.shields.io/github/v/tag/${{REPO_OWNER}}/${{REPO_NAME}}?label=latest%20tag&sort=semver)

Syncs a curated set of Apple developer docs into Markdown snapshots for offline/reference use in other projects.

## How it works
- URLs are defined in `docs-config/apple_urls.txt` (one line per: `<URL> <output.md>`).
- Regenerate the list at any time with `python scripts/generate_docs_config.py` (defaults to the live developer.apple.com sitemap; see below for offline usage).
- `scripts/sync_apple_docs.sh` fetches pages (curl) and converts HTML→Markdown (pandoc) into `Docs/Apple/`.
- A nightly GitHub Action opens a PR with changes.

## Use in any project
1. Copy `docs-config/`, `scripts/`, `.github/workflows/sync_apple_docs.yml`, and the `Docs/Apple/` folder (empty is fine).
2. Generate a fresh list of Apple documentation pages:
   ```bash
   python scripts/generate_docs_config.py
   ```
   Use `--source <file-or-url>` to point at cached sitemap XML when offline (the fixtures in `tests/fixtures/sitemaps/` offer a small sample set for testing).
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

## Plug it into an Xcode project with Codex CLI (no-stress steps)
These directions assume you vibe-code more than you spelunk through Xcode internals. Follow them literally and you’ll be ready to trigger the doc sync from the [Codex CLI](https://github.com/nanogiants/codex-cli) without guessing where anything lives.

1. **Install Codex CLI once** (macOS):
   ```bash
   brew install codex-cli
   ```
   This gives you the `codex` command the rest of the steps use.
2. **Locate your Xcode project folder the easy way:** open your app in Xcode, click the blue project name at the very top of the Project Navigator (left sidebar), then choose **File ▸ Show in Finder**. The Finder window that appears is the folder you want to work inside; it contains `YourApp.xcodeproj` (that blue icon is the project bundle).
3. **Drop the docs + scripts into the project folder:** copy this repo’s `Docs/Apple`, `docs-config`, and `scripts` folders into the same Finder window from step 2. Keep them side-by-side with your `.xcodeproj`—no need to open the project bundle or dig through hidden files.
4. **Tell Codex how to run the sync:** in that same folder, create a file named `codex.yml` (right-click ▸ New Document if you’re in Finder, or use your favorite editor) with the following contents:
   ```yaml
   workflows:
     apple-docs-sync:
       description: Fetch Apple docs into Docs/Apple for Xcode browsing
       steps:
         - run: bash scripts/sync_apple_docs.sh
   ```
   > Tip: if the file already exists, just add the `apple-docs-sync` block under your existing `workflows:` key instead of duplicating it.
5. **Make Xcode aware of the Markdown:** back in Xcode, drag the `Docs/Apple` folder from Finder straight into the Project Navigator. When the dialog pops up, choose **Create folder references** (the blue folder option) so Xcode automatically picks up new Markdown files whenever the sync runs.
6. **Run it whenever you need fresh docs:** open Terminal, `cd` into the same folder as your `.xcodeproj`, and run:
   ```bash
   codex run apple-docs-sync
   ```
   Codex will execute the workflow and call the sync script for you. When it finishes, flip back to Xcode and the updated docs appear under `Docs/Apple`.
7. *(Optional but nice)* Add a Codex build step in Xcode so you can refresh docs without leaving the IDE: select your app target ▸ **Build Phases** ▸ **+ ▸ New Run Script Phase**, drag it near the top, and paste `codex run apple-docs-sync`. Now the docs refresh any time you trigger that build phase.
