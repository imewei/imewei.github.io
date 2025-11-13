import json
import time
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin

import requests
from bs4 import BeautifulSoup


START_URL = "https://sites.google.com/view/msdsoftmatter/"
OUTPUT_DIR = Path("docs")


from typing import Optional


def normalize_internal(url: str) -> Optional[str]:
    """Keep only URLs that belong to the site and strip fragments/query."""
    clean, _ = urldefrag(url)
    if not clean.startswith(START_URL):
        return None
    if clean.endswith("#"):
        clean = clean[:-1]
    return clean


def crawl_site() -> tuple[list[dict], set[str]]:
    session = requests.Session()
    visited: set[str] = set()
    queue: deque[str] = deque([START_URL])
    pages: list[dict] = []
    assets: set[str] = set()

    while queue:
        current = queue.popleft()
        if current in visited:
            continue

        try:
            resp = session.get(current, timeout=30)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED {current}: {exc}")
            visited.add(current)
            continue

        visited.add(current)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        sections = [sec.get("id") for sec in soup.select("section[id]")]
        excerpt = " ".join(sec.get_text(" ", strip=True) for sec in soup.select("section"))[:400]
        pages.append({
            "url": current,
            "title": title,
            "sections": [s for s in sections if s],
            "excerpt": excerpt,
        })

        for img in soup.select("img[src]"):
            assets.add(urldefrag(img["src"])[0])

        for el in soup.select('[style*="background-image"]'):
            style = el.get("style", "")
            if "url(" in style:
                fragment = style.split("url(", 1)[1].split(")", 1)[0].strip("\"' ")
                if fragment:
                    assets.add(urldefrag(fragment)[0])

        for link in soup.select("a[href]"):
            href = link["href"].strip()
            if not href:
                continue
            if href.startswith("http"):
                if href.startswith(START_URL):
                    internal = normalize_internal(href)
                    if internal and internal not in visited:
                        queue.append(internal)
                else:
                    assets.add(urldefrag(href)[0])
            elif href.startswith("/"):
                internal = normalize_internal(urljoin(current, href))
                if internal and internal not in visited:
                    queue.append(internal)

        time.sleep(0.4)

    pages.sort(key=lambda item: item["url"])
    return pages, assets


def write_outputs(pages: list[dict], assets: set[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    site_map = OUTPUT_DIR / "site-map.json"
    inventory_md = OUTPUT_DIR / "inventory.md"

    with site_map.open("w", encoding="utf-8") as fh:
        json.dump({"pages": pages, "assets": sorted(assets)}, fh, indent=2)

    with inventory_md.open("w", encoding="utf-8") as fh:
        fh.write("# MSD Soft Matter Lab Inventory\n\n")
        for idx, page in enumerate(pages, start=1):
            fh.write(f"## {idx}. {page['title'] or page['url']}\n")
            fh.write(f"- URL: {page['url']}\n")
            if page["sections"]:
                fh.write(f"- Sections: {', '.join(page['sections'])}\n")
            if page["excerpt"]:
                fh.write(f"- Excerpt: {page['excerpt']}\n")
            fh.write("\n")
        fh.write("## Assets\n")
        for asset in sorted(assets):
            fh.write(f"- {asset}\n")


def main() -> None:
    pages, assets = crawl_site()
    print(f"Crawled {len(pages)} pages and discovered {len(assets)} unique assets")
    write_outputs(pages, assets)


if __name__ == "__main__":
    main()
