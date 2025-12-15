#!/usr/bin/env python3
"""
Image extraction and download utility for Google Sites mirror.

Extracts all image URLs from cached HTML files, audits existing downloads,
and downloads any missing images at highest resolution.

Requirements: Python 3.12+, requests, beautifulsoup4
"""

import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# Constants
CACHE_DIR = Path(".cache/google_site")
ASSETS_DIR = Path("assets/img/imported")
REPORT_DIR = Path("agent-os/specs/2025-12-15-mirror-google-sites-content/planning")

# Google Sites image URL patterns
GOOGLEUSERCONTENT_PATTERN = re.compile(r"https://lh\d+\.googleusercontent\.com/")

# Page mapping from Task Group 1
PAGE_MAPPING = {
    "726dc4aed019ddfe8d4aec84beb2a58e094239610ef20397472266c525c9f9d5.html": {
        "url": "https://sites.google.com/view/msdsoftmatter",
        "page": "base",
    },
    "db0960b28cd11087d539789cdc901bd515d45c0a638561ed5b52131e376010fb.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/home",
        "page": "home",
    },
    "7c44d6002797ed4e16888a8e51cfa9cd3584371c4278971ef54cf76828586dd8.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/wei-chen",
        "page": "wei-chen",
    },
    "48dc46bb5ac6f1605b8f428e06475cd1cbae047dd751fe44f93c547e67fc3173.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/our-team",
        "page": "our-team",
    },
    "9b3e538070721b79b927bb10c747462358aad4fef8b2b1983c78396175cfc19a.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/research",
        "page": "research",
    },
    "a113c8020ff098c659bfbb2fe65ec1dd97dba9f68ecc3493cd870f06d1a794e7.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/publications",
        "page": "publications",
    },
    "1774d69b9a9f50b6f6b5fc94c2ba1e2c8d4bb86ec99240e01b7ab28d84213a00.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/facilities",
        "page": "facilities",
    },
    "80bf5a1708d72eb5e193a8e97fa8950695a585259582498376eca0d6c1867db5.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/links",
        "page": "links",
    },
    "4d7cc1730f37e5f9977b709cadd0672bd01df22860fa533766448266a5230574.html": {
        "url": "https://sites.google.com/view/msdsoftmatter/contact",
        "page": "contact",
    },
}


def extract_image_urls_from_html(html_content: str) -> list[str]:
    """Extract all image URLs from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    image_urls = []

    for img in soup.find_all("img"):
        src = img.get("src")
        if src and GOOGLEUSERCONTENT_PATTERN.match(src):
            image_urls.append(src)

    # Also check for background images in style attributes
    for element in soup.find_all(style=True):
        style = element.get("style", "")
        urls = re.findall(r'url\(["\']?(https://lh\d+\.googleusercontent\.com/[^"\')\s]+)["\']?\)', style)
        image_urls.extend(urls)

    return image_urls


def normalize_image_url(url: str) -> str:
    """Normalize image URL by extracting the base part without size parameter."""
    # Remove size parameter (=w1280, =w16383, etc.)
    match = re.match(r"(.*?)(=w\d+)?$", url)
    if match:
        return match.group(1)
    return url


def get_high_res_url(url: str) -> str:
    """Get the highest resolution version of the image URL."""
    base_url = normalize_image_url(url)
    return f"{base_url}=w16383"


def extract_filename_from_url(url: str) -> str:
    """Extract filename from Google Sites image URL."""
    # Parse URL and get path
    parsed = urlparse(url)
    path = parsed.path

    # Google Sites URLs look like:
    # /sitesv/AAzXCkfT2Sxyo0HSmMefO14TqB_vaDWHPfcK5dS3qI9N...=w1280
    # Extract the AAzXCk... part
    if "/sitesv/" in path:
        filename = path.split("/sitesv/")[-1]
    else:
        filename = path.split("/")[-1]

    # Remove size parameter for consistent filenames
    filename = re.sub(r"=w\d+$", "", filename)

    return filename


def scan_cache_for_images() -> dict[str, list[dict[str, Any]]]:
    """Scan all cached HTML files and extract image URLs with page context."""
    results: dict[str, list[dict[str, Any]]] = {}

    if not CACHE_DIR.exists():
        print(f"Error: Cache directory not found: {CACHE_DIR}")
        sys.exit(1)

    for cache_file in CACHE_DIR.glob("*.html"):
        filename = cache_file.name

        if filename not in PAGE_MAPPING:
            print(f"Warning: Unknown cache file: {filename}")
            continue

        page_info = PAGE_MAPPING[filename]
        page_name = page_info["page"]
        source_url = page_info["url"]

        print(f"Scanning: {page_name} ({filename[:20]}...)")

        html_content = cache_file.read_text(encoding="utf-8")
        image_urls = extract_image_urls_from_html(html_content)

        for url in image_urls:
            normalized = normalize_image_url(url)

            if normalized not in results:
                results[normalized] = []

            # Check if this page is already recorded for this image
            existing_pages = [r["page"] for r in results[normalized]]
            if page_name not in existing_pages:
                results[normalized].append({
                    "page": page_name,
                    "original_url": url,
                    "filename": extract_filename_from_url(url),
                })

    return results


def audit_existing_images() -> dict[str, list[Path]]:
    """Audit existing downloaded images in assets/img/imported/."""
    existing: dict[str, list[Path]] = {}

    if not ASSETS_DIR.exists():
        return existing

    for page_dir in ASSETS_DIR.iterdir():
        if not page_dir.is_dir():
            continue

        for image_file in page_dir.iterdir():
            if image_file.is_file() and not image_file.name.startswith("."):
                # Extract base filename (remove extension and size params)
                base_name = image_file.stem
                base_name = re.sub(r"=w\d+$", "", base_name)

                if base_name not in existing:
                    existing[base_name] = []
                existing[base_name].append(image_file)

    return existing


def download_image(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    """Download image from URL to destination path with retry logic."""
    for attempt in range(max_retries):
        try:
            print(f"  Downloading: {dest_path.name}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(response.content)

            return True

        except requests.RequestException as e:
            print(f"  Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return False


def main() -> None:
    """Main entry point for image extraction and download."""
    print("=" * 60)
    print("MSD Soft Matter Lab - Image Extraction and Download")
    print("=" * 60)
    print()

    # Task 2.1: Extract all image URLs from cached HTML files
    print("TASK 2.1: Extracting image URLs from cached HTML files...")
    print("-" * 60)

    image_data = scan_cache_for_images()

    print()
    print(f"Found {len(image_data)} unique images across all pages")
    print()

    # Build detailed inventory
    all_images: list[dict[str, Any]] = []
    for normalized_url, page_refs in image_data.items():
        filename = page_refs[0]["filename"]
        pages = [ref["page"] for ref in page_refs]

        all_images.append({
            "normalized_url": normalized_url,
            "filename": filename,
            "pages": pages,
            "original_urls": [ref["original_url"] for ref in page_refs],
        })

    # Print summary by page
    print("Images found per page:")
    page_counts: dict[str, int] = {}
    for img in all_images:
        for page in img["pages"]:
            page_counts[page] = page_counts.get(page, 0) + 1

    for page, count in sorted(page_counts.items()):
        print(f"  {page}: {count} images")

    print()

    # Task 2.2: Audit existing downloaded images
    print("TASK 2.2: Auditing existing downloaded images...")
    print("-" * 60)

    existing_images = audit_existing_images()

    print(f"Found {len(existing_images)} unique filenames in assets/img/imported/")
    print()

    # Count files per folder
    print("Images per folder:")
    for page_dir in sorted(ASSETS_DIR.iterdir()):
        if page_dir.is_dir():
            count = len(list(page_dir.glob("*")))
            print(f"  {page_dir.name}/: {count} files")

    print()

    # Compare extracted URLs with existing files
    print("Comparing extracted URLs with existing files...")

    missing_images: list[dict[str, Any]] = []
    matched_images: list[dict[str, Any]] = []

    for img in all_images:
        filename = img["filename"]

        # Check if this filename exists in any form
        if filename in existing_images:
            matched_images.append(img)
        else:
            missing_images.append(img)

    print(f"  Matched: {len(matched_images)} images")
    print(f"  Missing: {len(missing_images)} images")
    print()

    # Task 2.3: Download missing images at highest resolution
    print("TASK 2.3: Downloading missing images...")
    print("-" * 60)

    download_results: list[dict[str, Any]] = []

    if not missing_images:
        print("No missing images to download!")
    else:
        for img in missing_images:
            high_res_url = get_high_res_url(img["normalized_url"])
            filename = img["filename"]
            primary_page = img["pages"][0]

            # Determine extension based on URL or default to jpg
            extension = ".jpg"

            dest_path = ASSETS_DIR / primary_page / f"{filename}=w16383"

            if dest_path.exists():
                print(f"  Already exists: {dest_path.name}")
                download_results.append({
                    "filename": filename,
                    "status": "skipped",
                    "path": str(dest_path),
                    "pages": img["pages"],
                })
                continue

            success = download_image(high_res_url, dest_path)
            download_results.append({
                "filename": filename,
                "status": "success" if success else "failed",
                "path": str(dest_path) if success else None,
                "url": high_res_url,
                "pages": img["pages"],
            })

            if success:
                time.sleep(0.5)  # Polite delay

    print()

    # Task 2.4: Verify download completeness
    print("TASK 2.4: Verifying download completeness...")
    print("-" * 60)

    # Re-audit after downloads
    final_existing = audit_existing_images()
    final_missing: list[dict[str, Any]] = []

    for img in all_images:
        filename = img["filename"]
        if filename not in final_existing:
            final_missing.append(img)

    print(f"Total unique images in cache: {len(all_images)}")
    print(f"Total unique filenames downloaded: {len(final_existing)}")
    print(f"Still missing: {len(final_missing)}")

    if final_missing:
        print()
        print("Missing images (require manual review):")
        for img in final_missing:
            print(f"  - {img['filename']} (pages: {', '.join(img['pages'])})")

    print()

    # Generate report
    print("Generating image extraction report...")
    print("-" * 60)

    report: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_unique_images_in_cache": len(all_images),
            "images_matched_to_existing_files": len(matched_images),
            "missing_images_identified": len(missing_images),
            "images_still_missing": len(final_missing),
        },
        "images_by_page": {page: count for page, count in sorted(page_counts.items())},
        "all_images": [
            {
                "filename": img["filename"],
                "pages": img["pages"],
                "normalized_url": img["normalized_url"],
            }
            for img in all_images
        ],
        "download_results": download_results,
        "still_missing": [
            {
                "filename": img["filename"],
                "pages": img["pages"],
                "url": img["normalized_url"],
            }
            for img in final_missing
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "image-extraction-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report saved to: {report_path}")

    # Also generate a markdown summary
    md_report = generate_markdown_report(report, all_images, existing_images)
    md_path = REPORT_DIR / "image-extraction-report.md"
    md_path.write_text(md_report, encoding="utf-8")
    print(f"Markdown report saved to: {md_path}")

    print()
    print("=" * 60)
    print("Image extraction complete!")
    print("=" * 60)

    # Exit with error if images are missing
    if final_missing:
        sys.exit(1)


def generate_markdown_report(
    report: dict[str, Any],
    all_images: list[dict[str, Any]],
    existing_images: dict[str, list[Path]],
) -> str:
    """Generate a markdown summary report."""
    lines = [
        "# Image Extraction Report",
        "",
        f"**Generated:** {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- **Total unique images in cache:** {report['summary']['total_unique_images_in_cache']}",
        f"- **Images matched to existing files:** {report['summary']['images_matched_to_existing_files']}",
        f"- **Missing images identified:** {report['summary']['missing_images_identified']}",
        f"- **Images still missing:** {report['summary']['images_still_missing']}",
        "",
        "## Images by Page",
        "",
        "| Page | Image Count |",
        "|------|-------------|",
    ]

    for page, count in sorted(report["images_by_page"].items()):
        lines.append(f"| {page} | {count} |")

    lines.extend([
        "",
        "## Image Inventory",
        "",
        "The following tables list all images found in the cached HTML files.",
        "",
    ])

    # Group by page
    pages_images: dict[str, list[dict[str, Any]]] = {}
    for img in all_images:
        for page in img["pages"]:
            if page not in pages_images:
                pages_images[page] = []
            pages_images[page].append(img)

    for page in sorted(pages_images.keys()):
        images = pages_images[page]
        lines.extend([
            f"### {page.replace('-', ' ').title()}",
            "",
            "| Filename | Status |",
            "|----------|--------|",
        ])

        for img in images:
            filename = img["filename"]
            status = "Downloaded" if filename in existing_images else "Missing"
            lines.append(f"| `{filename[:50]}...` | {status} |")

        lines.append("")

    if report["still_missing"]:
        lines.extend([
            "## Still Missing (Requires Manual Review)",
            "",
        ])
        for img in report["still_missing"]:
            lines.append(f"- `{img['filename']}` (pages: {', '.join(img['pages'])})")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
