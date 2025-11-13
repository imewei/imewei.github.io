# Google Sites Importer

Minimal importer for the MSD Soft Matter Lab Google Sites page.

## Requirements

- Python 3.12+
- Dependencies (install via `pip install -r requirements.txt`):
  - `requests` - HTTP client
  - `beautifulsoup4` - HTML parsing
  - `markdownify` - HTML to Markdown conversion (optional, falls back to text extraction)

## Installation

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Import all discovered pages (with 2s delay between requests)
python3 scripts/import_google_site.py

# Import specific pages by slug
python3 scripts/import_google_site.py --pages home about contact

# Force re-import even if cached
python3 scripts/import_google_site.py --force

# Custom delay between requests
python3 scripts/import_google_site.py --delay 1.0

# Show help
python3 scripts/import_google_site.py --help
```

## Features

- **Per-page fetch with caching**: Downloads are cached in `.cache/google_site/` to avoid repeated requests
- **Polite delays**: Configurable delay between requests (default: 2 seconds)
- **HTML cleaning**: Strips scripts, styles, and unwanted elements
- **Image downloads**: Images are downloaded to `assets/img/imported/<slug>/` with root-relative links
- **Markdown conversion**: Converts HTML to Markdown using markdownify (or plain text fallback)
- **YAML front matter**: Each page includes title, permalink, source_url, and last_imported timestamp
- **Idempotent writes**: Only updates files if content has changed
- **Page filtering**: Import specific pages using `--pages` flag
- **Force mode**: Re-fetch and re-write with `--force` flag

## Output Structure

```
pages/
  home.md
  about.md
  contact.md
  ...

assets/img/imported/
  home/
    image1.jpg
    image2.png
  about/
    photo.jpg
  ...
```

## Example Output

```markdown
---
title: "Research"
permalink: /research/
source_url: https://sites.google.com/view/msdsoftmatter/research
last_imported: 2025-11-12T10:30:00Z
---

# Research

Our research focuses on...
```

## Notes

- Google Sites uses JavaScript for navigation, so automatic page discovery may not find all pages
- Manually specify pages with `--pages` if needed
- The script is macOS-friendly and uses `pathlib` for cross-platform compatibility
- Network requests only occur at runtime (no external calls in test environment)
- Root-relative links ensure images work from any URL path
