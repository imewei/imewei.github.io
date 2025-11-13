#!/usr/bin/env python3
"""
postprocess_mirror.py - Rewrite HTML links and relocate assets

Takes a raw wget mirror directory and produces a staging tree with:
- Root-relative links (e.g., /images/foo.png instead of ../../images/foo.png)
- Assets organized into logical directories
- Clean directory structure suitable for deployment

Usage:
    python3 postprocess_mirror.py <raw_dir> <staging_dir>

Arguments:
    raw_dir     Directory containing raw wget output
    staging_dir Output directory for processed files

Requirements:
    - Python >= 3.12
    - beautifulsoup4 (pip3 install beautifulsoup4)
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class MirrorPostprocessor:
    """Process raw wget mirror into clean staging tree."""

    def __init__(self, raw_dir: Path, staging_dir: Path) -> None:
        self.raw_dir = raw_dir.resolve()
        self.staging_dir = staging_dir.resolve()
        self.asset_map: dict[str, str] = {}  # old_path -> new_path

    def run(self) -> None:
        """Execute full postprocessing workflow."""
        logger.info(f"Processing mirror from {self.raw_dir}")
        logger.info(f"Output to {self.staging_dir}")

        if not self.raw_dir.exists():
            raise FileNotFoundError(f"Raw directory not found: {self.raw_dir}")

        self.staging_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Copy and organize files
        self._organize_files()

        # Phase 2: Rewrite HTML links
        self._rewrite_html_files()

        logger.info("Postprocessing complete")

    def _organize_files(self) -> None:
        """Copy files from raw to staging with logical organization."""
        logger.info("Organizing files...")

        for src_path in self.raw_dir.rglob("*"):
            if not src_path.is_file():
                continue

            rel_path = src_path.relative_to(self.raw_dir)
            dest_path = self._map_destination(rel_path)

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)

            # Track mapping for link rewriting
            self.asset_map[str(rel_path)] = str(dest_path.relative_to(self.staging_dir))

        logger.info(f"Organized {len(self.asset_map)} files")

    def _map_destination(self, rel_path: Path) -> Path:
        """Determine staging destination for a file."""
        # Asset type detection by extension
        suffix = rel_path.suffix.lower()

        # Images
        if suffix in {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico"}:
            return self.staging_dir / "images" / rel_path.name

        # Stylesheets
        if suffix == ".css":
            return self.staging_dir / "css" / rel_path.name

        # JavaScript
        if suffix == ".js":
            return self.staging_dir / "js" / rel_path.name

        # Fonts
        if suffix in {".woff", ".woff2", ".ttf", ".otf", ".eot"}:
            return self.staging_dir / "fonts" / rel_path.name

        # HTML files - preserve structure but flatten excessive nesting
        if suffix in {".html", ".htm"}:
            # If deeply nested, flatten to root
            if len(rel_path.parts) > 2:
                return self.staging_dir / rel_path.name
            return self.staging_dir / rel_path

        # Other files - preserve structure
        return self.staging_dir / rel_path

    def _rewrite_html_files(self) -> None:
        """Rewrite links in all HTML files to root-relative paths."""
        logger.info("Rewriting HTML links...")

        html_files = list(self.staging_dir.rglob("*.html"))
        html_files.extend(self.staging_dir.rglob("*.htm"))

        for html_path in html_files:
            self._process_html_file(html_path)

        logger.info(f"Processed {len(html_files)} HTML files")

    def _process_html_file(self, html_path: Path) -> None:
        """Rewrite links in a single HTML file."""
        try:
            with html_path.open("r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception as e:
            logger.warning(f"Failed to parse {html_path}: {e}")
            return

        modified = False

        # Rewrite <a href="...">
        for tag in soup.find_all("a", href=True):
            if self._rewrite_link(tag, "href"):
                modified = True

        # Rewrite <link href="..."> (stylesheets)
        for tag in soup.find_all("link", href=True):
            if self._rewrite_link(tag, "href"):
                modified = True

        # Rewrite <script src="...">
        for tag in soup.find_all("script", src=True):
            if self._rewrite_link(tag, "src"):
                modified = True

        # Rewrite <img src="...">
        for tag in soup.find_all("img", src=True):
            if self._rewrite_link(tag, "src"):
                modified = True

        # Rewrite <source src="..."> (audio/video)
        for tag in soup.find_all("source", src=True):
            if self._rewrite_link(tag, "src"):
                modified = True

        # Rewrite CSS url() references
        for tag in soup.find_all("style"):
            if tag.string:
                new_css = self._rewrite_css_urls(tag.string)
                if new_css != tag.string:
                    tag.string = new_css
                    modified = True

        # Save if modified
        if modified:
            with html_path.open("w", encoding="utf-8") as f:
                f.write(str(soup))
            logger.debug(f"Rewrote links in {html_path.name}")

    def _rewrite_link(self, tag, attr: str) -> bool:
        """Rewrite a single link attribute to root-relative."""
        original = tag[attr]

        # Skip external URLs and anchors
        if original.startswith(("http://", "https://", "//", "#", "mailto:", "tel:")):
            return False

        # Parse and normalize
        parsed = urlparse(original)
        if parsed.scheme or parsed.netloc:
            return False

        # Extract path component
        path = parsed.path

        # Try to map to new location
        new_path = self._resolve_new_path(path)
        if new_path is None:
            return False

        # Make root-relative
        root_relative = f"/{new_path}"

        # Preserve query and fragment
        if parsed.query:
            root_relative += f"?{parsed.query}"
        if parsed.fragment:
            root_relative += f"#{parsed.fragment}"

        tag[attr] = root_relative
        return True

    def _resolve_new_path(self, original_path: str) -> str | None:
        """Find new staging path for an original path."""
        # Normalize path
        original_path = original_path.lstrip("/")

        # Direct lookup in asset map
        if original_path in self.asset_map:
            return self.asset_map[original_path]

        # Try matching by filename
        filename = Path(original_path).name
        for old_path, new_path in self.asset_map.items():
            if Path(old_path).name == filename:
                return new_path

        # Fallback: return as-is
        return original_path

    def _rewrite_css_urls(self, css_content: str) -> str:
        """Rewrite url() references in CSS."""
        import re

        def replace_url(match):
            url = match.group(1).strip('\'"')
            if url.startswith(("http://", "https://", "//", "#", "data:")):
                return match.group(0)

            new_path = self._resolve_new_path(url)
            if new_path:
                return f'url("/{new_path}")'
            return match.group(0)

        return re.sub(r'url\(["\']?([^"\')]+)["\']?\)', replace_url, css_content)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Postprocess wget mirror to clean staging tree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("raw_dir", type=Path, help="Raw wget output directory")
    parser.add_argument("staging_dir", type=Path, help="Staging output directory")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        processor = MirrorPostprocessor(args.raw_dir, args.staging_dir)
        processor.run()
        return 0
    except Exception as e:
        logger.error(f"Postprocessing failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
