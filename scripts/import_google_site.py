#!/usr/bin/env python3
"""
Minimal importer for Google Sites pages.

Fetches pages from https://sites.google.com/view/msdsoftmatter, cleans HTML,
downloads images, converts to Markdown with YAML front matter, and writes to
pages/<slug>.md. Supports caching, polite delays, and idempotent writes.

Requirements: Python 3.12+, requests, beautifulsoup4, markdownify (optional)
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from markdownify import markdownify as md
except ImportError:
    md = None


# Constants
BASE_URL = "https://sites.google.com/view/msdsoftmatter"
CACHE_DIR = Path(".cache/google_site")
PAGES_DIR = Path("pages")
ASSETS_DIR = Path("assets/img/imported")
DEFAULT_DELAY = 2.0


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def fetch_with_cache(url: str, force: bool = False) -> str:
    """Fetch URL with disk cache. Returns HTML content."""
    cache_key = hashlib.sha256(url.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.html"

    if not force and cache_file.exists():
        print(f"  Cache hit: {url}")
        return cache_file.read_text(encoding="utf-8")

    print(f"  Fetching: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(response.text, encoding="utf-8")

    return response.text


def clean_html(soup: BeautifulSoup) -> None:
    """Remove scripts, styles, and other unwanted elements in-place."""
    for tag in soup.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()


def download_image(img_url: str, page_slug: str) -> Optional[str]:
    """Download image to assets/img/imported/<slug>/ and return relative path."""
    try:
        parsed = urlparse(img_url)
        if not parsed.scheme:
            return None

        # Extract filename from URL
        filename = Path(parsed.path).name
        if not filename:
            filename = f"image_{hashlib.md5(img_url.encode()).hexdigest()[:8]}.jpg"

        # Create directory structure
        img_dir = ASSETS_DIR / page_slug
        img_dir.mkdir(parents=True, exist_ok=True)

        img_path = img_dir / filename

        # Download if not exists
        if not img_path.exists():
            print(f"    Downloading image: {filename}")
            response = requests.get(img_url, timeout=30)
            response.raise_for_status()
            img_path.write_bytes(response.content)

        # Return root-relative path
        return f"/assets/img/imported/{page_slug}/{filename}"

    except Exception as e:
        print(f"    Warning: Failed to download {img_url}: {e}")
        return None


def process_images(soup: BeautifulSoup, page_slug: str, base_url: str) -> None:
    """Download images and update src attributes to root-relative paths."""
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue

        # Make absolute URL
        abs_url = urljoin(base_url, src)

        # Download and update
        local_path = download_image(abs_url, page_slug)
        if local_path:
            img["src"] = local_path


def html_to_markdown(soup: BeautifulSoup) -> str:
    """Convert cleaned HTML to Markdown."""
    if md is None:
        # Fallback: extract text
        return soup.get_text(separator="\n", strip=True)

    # Convert using markdownify
    return md(str(soup), heading_style="ATX", bullets="-")


def extract_title(soup: BeautifulSoup) -> str:
    """Extract page title from HTML."""
    # Try <title> tag
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        # Remove site name suffix if present
        title = re.sub(r"\s*-\s*MSD Soft Matter Lab$", "", title)
        if title:
            return title

    # Try <h1> tag
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return "Untitled Page"


def generate_front_matter(title: str, permalink: str, source_url: str) -> str:
    """Generate YAML front matter."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    front_matter = f"""---
title: "{title}"
permalink: {permalink}
source_url: {source_url}
last_imported: {timestamp}
---

"""
    return front_matter


def write_page(page_slug: str, content: str, force: bool = False) -> None:
    """Write page to pages/<slug>.md with idempotent behavior."""
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PAGES_DIR / f"{page_slug}.md"

    # Check if content changed
    if not force and output_file.exists():
        existing = output_file.read_text(encoding="utf-8")
        if existing == content:
            print(f"  No changes: {output_file}")
            return

    output_file.write_text(content, encoding="utf-8")
    print(f"  Written: {output_file}")


def import_page(url: str, page_filter: Optional[Sequence[str]], force: bool, delay: float) -> None:
    """Import a single page from Google Sites."""
    # Extract page identifier from URL
    parsed = urlparse(url)
    page_path = parsed.path.strip("/")

    # Create slug
    if page_path and page_path != "view/msdsoftmatter":
        page_slug = slugify(page_path.split("/")[-1])
    else:
        page_slug = "home"

    # Apply filter
    if page_filter and page_slug not in page_filter:
        return

    print(f"\nProcessing: {page_slug}")

    # Fetch HTML
    html = fetch_with_cache(url, force=force)
    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = extract_title(soup)

    # Find main content (Google Sites structure varies)
    # Try to find the main content area
    content_div = soup.find("div", class_=re.compile(r"sites-canvas-main")) or soup.body

    if content_div:
        # Clean HTML
        clean_html(content_div)

        # Process images
        process_images(content_div, page_slug, url)

        # Convert to Markdown
        markdown = html_to_markdown(content_div)
    else:
        markdown = "Content not found."

    # Generate front matter
    permalink = f"/{page_slug}/" if page_slug != "home" else "/"
    front_matter = generate_front_matter(title, permalink, url)

    # Combine
    full_content = front_matter + markdown

    # Write to disk
    write_page(page_slug, full_content, force=force)

    # Polite delay
    if delay > 0:
        time.sleep(delay)


def discover_pages(base_url: str, force: bool) -> list[str]:
    """
    Discover pages from the Google Site.

    Note: Google Sites relies on client-side navigation. This function therefore
    returns at least the base page and any directly linked siblings discovered.
    Additional slugs provided via --pages are appended later.
    """
    print("Discovering pages...")
    html = fetch_with_cache(base_url, force=force)
    soup = BeautifulSoup(html, "html.parser")

    pages = [base_url]

    # Look for navigation links
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "sites.google.com/view/msdsoftmatter" in href:
            full_url = urljoin(base_url, href)
            if full_url not in pages:
                pages.append(full_url)

    return pages


def ensure_slug_pages(pages: list[str], requested: Sequence[str], *, base_url: str) -> dict[str, str]:
    """Return mapping of slug -> URL ensuring requested slugs exist."""
    result = {}
    normalized_base = base_url.rstrip("/") + "/"
    for url in pages:
        slug = slugify(url.split("/")[-1]) or "home"
        result[slug] = url
    for slug in requested:
        if slug not in result:
            result[slug] = urljoin(normalized_base, slug)
    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import pages from Google Sites to Markdown with YAML front matter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Import all discovered pages
  %(prog)s --pages home about contact   # Import specific pages by slug
  %(prog)s --force --delay 1            # Force re-import with 1s delay
  %(prog)s --help                       # Show this help message
""",
    )

    parser.add_argument(
        "--pages",
        nargs="+",
        metavar="SLUG",
        help="Filter to specific page slugs (e.g., home about contact)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-fetch and re-write even if cached/unchanged",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        metavar="SECONDS",
        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})",
    )

    args = parser.parse_args()

    print(f"MSD Soft Matter Lab - Google Sites Importer")
    print(f"Source: {BASE_URL}")
    print(f"Delay: {args.delay}s, Force: {args.force}")

    if args.pages:
        print(f"Filter: {', '.join(args.pages)}")

    try:
        # Discover pages
        discovered = discover_pages(BASE_URL, force=args.force)
        print(f"\nDiscovered {len(discovered)} page(s)")

        url_map = ensure_slug_pages(discovered, args.pages or [], base_url=BASE_URL)
        target_slugs = args.pages if args.pages else list(url_map.keys())

        # Import each page
        for slug in target_slugs:
            url = url_map.get(slug)
            if not url:
                print(f"[warn] No URL for slug '{slug}', skipping")
                continue
            import_page(url, [slug], args.force, args.delay)

        print("\n✓ Import complete!")
        print(f"  Pages written to: {PAGES_DIR.absolute()}")
        print(f"  Images saved to: {ASSETS_DIR.absolute()}")

    except KeyboardInterrupt:
        print("\n\n✗ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
