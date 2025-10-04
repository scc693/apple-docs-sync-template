#!/usr/bin/env bash
# Sync a curated set of Apple docs into Docs/Apple as Markdown for repository reference.
# Requires: curl, pandoc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${ROOT}/Docs/Apple"
LIST="${ROOT}/docs-config/apple_urls.txt"
FETCH_MODE="${APPLE_DOCS_FETCH_MODE:-network}"
FIXTURE_DIR="${APPLE_DOCS_FIXTURE_DIR:-${ROOT}/tests/fixtures/apple_docs}"
USER_AGENT="${APPLE_DOCS_USER_AGENT:-Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15}"
MAX_RETRIES="${APPLE_DOCS_MAX_RETRIES:-3}"
RETRY_DELAY="${APPLE_DOCS_RETRY_DELAY:-5}"

if [[ "${FETCH_MODE}" == "network" && -n "${ACT:-}" ]]; then
  FETCH_MODE="fixtures"
fi

mkdir -p "${DEST}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }; }
need curl
need pandoc

log() { printf '%s\n' "$*" >&2; }

fetch_html() {
  local url="$1"
  local out="$2"
  local attempt=1
  local html=""

  case "${FETCH_MODE}" in
    network)
      while (( attempt <= MAX_RETRIES )); do
        log "→ Fetching ${url} (attempt ${attempt}/${MAX_RETRIES})"
        if html="$(curl --fail --show-error --silent --location --compressed -A "${USER_AGENT}" "${url}")"; then
          printf '%s' "${html}"
          return 0
        fi
        local status=$?
        if (( attempt == MAX_RETRIES )); then
          log "✗ Failed after ${MAX_RETRIES} attempts: curl exit ${status}"
          return "${status}"
        fi
        log "… retrying in ${RETRY_DELAY}s (curl exit ${status})"
        sleep "${RETRY_DELAY}"
        (( attempt++ ))
      done
      ;;
    fixtures)
      local stem
      stem="$(basename "${out}" .md)"
      local fixture_path="${FIXTURE_DIR}/${stem}.html"
      if [[ ! -f "${fixture_path}" ]]; then
        log "✗ Fixture not found for ${out}: ${fixture_path}"
        return 1
      fi
      log "→ Using fixture ${fixture_path}"
      cat "${fixture_path}"
      return 0
      ;;
    *)
      log "Unknown APPLE_DOCS_FETCH_MODE: ${FETCH_MODE}" >&2
      return 2
      ;;
  esac
}

write_markdown() {
  local html="$1"
  local url="$2"
  local out="$3"

  # Convert HTML -> GitHub Flavored Markdown
  printf '%s' "${html}" | pandoc -f html -t gfm -o "${DEST}/${out}"
  {
    echo
    echo "> Source: ${url}"
    echo "> Snapshot: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  } >> "${DEST}/${out}"
  log "✓ Wrote ${DEST}/${out}"
}

main() {
  if [[ ! -f "${LIST}" ]]; then
    echo "Config list not found: ${LIST}" >&2
    exit 1
  fi

  while read -r url out; do
    [[ -z "${url:-}" || -z "${out:-}" ]] && continue
    local html_content=""
    html_content="$(fetch_html "${url}" "${out}")" || {
      local status=$?
      exit "${status}"
    }
    write_markdown "${html_content}" "${url}" "${out}"
  done < "${LIST}"

  log "✅ Synced Apple docs to ${DEST}/"
}

main "$@"
