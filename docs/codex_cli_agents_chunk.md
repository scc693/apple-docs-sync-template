# Codex CLI Agent Instructions for Apple Docs Sync

Add the following text to the `AGENTS.md` file in your Codex CLI project to help the agent
understand how to work with the Apple Docs Sync template:

```markdown
## Apple Docs Sync Research Instructions

1. Before making changes, review these resources:
   - `scripts/sync_apple_docs.sh` for the download-and-convert workflow.
   - `scripts/generate_docs_config.py` for sitemap crawling and URL list generation.
   - `docs-config/apple_urls.txt` (or its regenerated output) for the list of tracked pages.
   - Markdown snapshots inside `Docs/Apple/` for previously synchronized content.

2. When a task requires Apple developer reference material:
   - Start with the most relevant entry in `docs-config/apple_urls.txt`. Use keyword overlap
     between the task description and the URL or filename to make an initial guess.
   - If the exact term is unclear, prefer pages that align with the framework or platform
     mentioned in the request (for example, "swiftui" or "cloudkit").

3. After selecting a candidate page:
   - Open the matching Markdown file in `Docs/Apple/` if it exists. If it has not been
     synchronized yet, run `make docs-sync` (or `bash scripts/sync_apple_docs.sh`) to fetch
     it locally before inspecting the content.
   - Extract the relevant sections needed to answer the question or implement the feature.

4. Verification rubric for gathering sufficient context:
   - If the first page does not include the API, class, or guide referenced in the task,
     mark it as insufficient and check the next best candidate from `docs-config/apple_urls.txt`.
   - Continue cycling through likely pages until you either locate the necessary reference or
     exhaust the relevant subset of URLs. Each time you switch pages, document why the previous
     one was insufficient.
   - When the correct information is found, confirm that the extracted context answers the
     original question or supports the requested change. Only then proceed with implementation.

5. If no local snapshot covers the needed topic, update `docs-config/apple_urls.txt` with a
   promising Apple developer URL, run `make docs-sync`, and re-run the rubric above.
```
