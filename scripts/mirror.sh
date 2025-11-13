#!/usr/bin/env bash
# mirror.sh - Web crawler using wget for site mirroring
#
# Usage: ./scripts/mirror.sh <URL> [OPTIONS]
#
# This script crawls a target URL using wget with appropriate throttling
# and retry logic, stores raw HTML in timestamped directories, then calls
# postprocess_mirror.py to rewrite links and relocate assets.

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TMP_DIR="${REPO_ROOT}/tmp/site-mirror/runs"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RAW_DIR="${TMP_DIR}/${TIMESTAMP}/raw"
STAGING_DIR="${TMP_DIR}/${TIMESTAMP}/staging"

# wget defaults
WAIT_SECONDS=1
RETRY_COUNT=3
USER_AGENT="Mozilla/5.0 (compatible; MirrorBot/1.0)"

# --- Helper Functions ---
show_help() {
    cat << EOF
Usage: ${0##*/} <URL> [OPTIONS]

Crawl a target URL into tmp/site-mirror/runs/<timestamp>/raw, then
postprocess links and assets into a staging tree.

ARGUMENTS:
  URL                   Target URL to mirror (required)

OPTIONS:
  -h, --help            Show this help message and exit
  -w, --wait SECONDS    Wait time between requests (default: ${WAIT_SECONDS})
  -r, --retries COUNT   Number of retries on failure (default: ${RETRY_COUNT})
  -d, --depth LEVEL     Maximum recursion depth (default: infinite)
  --user-agent STRING   Custom User-Agent header (default: "${USER_AGENT}")
  --no-postprocess      Skip postprocessing step

EXAMPLES:
  # Basic mirror with defaults
  ${0##*/} https://example.com

  # Custom wait time and retry count
  ${0##*/} https://example.com --wait 2 --retries 5

  # Limit recursion depth
  ${0##*/} https://example.com --depth 2

  # Skip postprocessing (just wget)
  ${0##*/} https://example.com --no-postprocess

NOTES:
  - Raw mirror stored in: ${TMP_DIR}/<timestamp>/raw
  - Processed output in:  ${TMP_DIR}/<timestamp>/staging
  - Requires: wget, python3, beautifulsoup4
  - macOS/BSD compatible (uses BSD sed syntax)

EOF
}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

# --- Argument Parsing ---
TARGET_URL=""
MAX_DEPTH=""
NO_POSTPROCESS=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -w|--wait)
            WAIT_SECONDS="${2:-}"
            [[ -z "$WAIT_SECONDS" ]] && error "--wait requires a value"
            shift 2
            ;;
        -r|--retries)
            RETRY_COUNT="${2:-}"
            [[ -z "$RETRY_COUNT" ]] && error "--retries requires a value"
            shift 2
            ;;
        -d|--depth)
            MAX_DEPTH="${2:-}"
            [[ -z "$MAX_DEPTH" ]] && error "--depth requires a value"
            shift 2
            ;;
        --user-agent)
            USER_AGENT="${2:-}"
            [[ -z "$USER_AGENT" ]] && error "--user-agent requires a value"
            shift 2
            ;;
        --no-postprocess)
            NO_POSTPROCESS=true
            shift
            ;;
        -*)
            error "Unknown option: $1 (try --help)"
            ;;
        *)
            [[ -n "$TARGET_URL" ]] && error "Only one URL allowed"
            TARGET_URL="$1"
            shift
            ;;
    esac
done

[[ -z "$TARGET_URL" ]] && error "URL required (try --help)"

# --- Preflight Checks ---
command -v wget >/dev/null 2>&1 || error "wget not found (install via: brew install wget)"
command -v python3 >/dev/null 2>&1 || error "python3 not found"

if [[ "$NO_POSTPROCESS" == false ]]; then
    python3 -c "import bs4" 2>/dev/null || error "beautifulsoup4 not found (install via: pip3 install beautifulsoup4)"
fi

# --- Main Execution ---
log "Starting mirror of ${TARGET_URL}"
log "Output directory: ${RAW_DIR}"

mkdir -p "${RAW_DIR}"

# Build wget command
WGET_ARGS=(
    --recursive
    --page-requisites
    --html-extension
    --convert-links
    --no-parent
    --wait="${WAIT_SECONDS}"
    --tries="${RETRY_COUNT}"
    --user-agent="${USER_AGENT}"
    --adjust-extension
    --execute robots=off
    --directory-prefix="${RAW_DIR}"
)

[[ -n "$MAX_DEPTH" ]] && WGET_ARGS+=(--level="${MAX_DEPTH}")

log "Running wget with wait=${WAIT_SECONDS}s, retries=${RETRY_COUNT}"
if ! wget "${WGET_ARGS[@]}" "${TARGET_URL}"; then
    error "wget failed"
fi

log "wget completed successfully"
log "Raw files stored in: ${RAW_DIR}"

# --- Postprocessing ---
if [[ "$NO_POSTPROCESS" == true ]]; then
    log "Skipping postprocessing (--no-postprocess flag)"
    exit 0
fi

POSTPROCESS_SCRIPT="${SCRIPT_DIR}/postprocess_mirror.py"
[[ ! -f "$POSTPROCESS_SCRIPT" ]] && error "postprocess_mirror.py not found at ${POSTPROCESS_SCRIPT}"

log "Running postprocessing..."
mkdir -p "${STAGING_DIR}"

if ! python3 "${POSTPROCESS_SCRIPT}" "${RAW_DIR}" "${STAGING_DIR}"; then
    error "postprocess_mirror.py failed"
fi

log "Postprocessing completed"
log "Staging tree: ${STAGING_DIR}"
log "Mirror complete!"
