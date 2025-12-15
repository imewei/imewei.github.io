# MSD Soft Matter Lab – Parity Audit (2025-11-13)

## Executive Summary
- **Result:** ❌ *Fail* – the GitHub Pages preview (`http://127.0.0.1:4000`) does not yet resemble the Google Site in layout, navigation polish, media coverage, or link fidelity.
- **Scope:** 8 top-level pages enumerated in `docs/site-map.json` (Home, Wei Chen, Our Team, Research, Publications, Facilities, Links, Contact). Reference screenshots from `docs/reference-shots/` supplied ground truth.
- **Method:** Served `_site/` via `python3 -m http.server 4000`; opened each page locally and cross-compared copy, sections, and media with their Google Site counterparts plus the crawl metadata.

## Page-by-Page Findings
### Home (`/`)
- **Nav/title:** Text-only nav matches ordering, but styling diverges (Google hero, dropdown “More” icon, Argonne branding missing). Title matches.
- **Sections:** Local page is a single block of raw harvested text (Google nav boilerplate + hero headings duplicated). Google Site has hero image, 3 research cards, CTA buttons.
- **Images:** 0 rendered locally vs. hero + research imagery on source; assets downloaded exist under `assets/img/imported/home/` but never referenced.
- **Downloads/Embeds:** None wired locally; Google page has “Learn more” buttons linking deeper in-site sections.
- **Copy/layout issues:** All boilerplate (“Search this site”, “Report abuse”) and navigation duplicates remain inline, breaking UX.

### Wei Chen (`/wei-chen/`)
- **Nav/title:** Matches routing; still text-only nav.
- **Sections:** Local file is a raw transcript of CV bullets without typography, subheadings, or cards. Google Site uses structured biography sections and downloadable CV link.
- **Images:** 0 (Google page has portrait + background hero).
- **Downloads:** CV link (`https://drive.google.com/file/d/1-ijC9KQlzSmAkoX9VKgI8JA7sMMJ-NNf/view?usp=drive_link`) requires Google login (302 → accounts.google.com); cannot embed on GitHub Pages without rehosting.
- **Embeds:** None locally; source uses Drive embed for CV preview.

### Our Team (`/our-team/`)
- **Nav/title:** Matches.
- **Sections:** Local content is a plain list of names/emails in paragraph form with duplicated nav boilerplate. Google Site displays responsive cards for each member plus former team listing with headshots.
- **Images:** 0 vs. 5 current member photos + group imagery.
- **Downloads/Embeds:** Source contains mailto links only; parity acceptable but layout missing.

### Research (`/research/`)
- **Nav/title:** Matches.
- **Sections:** Local page contains full text paragraphs but lacks headings, cards, and toggles present on Google Site. Section count (5 major research themes) present in text but unstyled.
- **Images:** 0 vs. hero banners + inline figures.
- **Embeds:** Source uses subtle icon cards; not ported.

### Publications (`/publications/`)
- **Nav/title:** Matches.
- **Sections:** Local page lists only the first few publications captured at crawl time and still includes “Google Sites / Report abuse”. Google Site page includes dozens of publications with DOI links and highlight cards.
- **Images:** 0 vs. header imagery.
- **Downloads:** DOI/outbound links exist but are plain text; not validated because they appear intact.

### Facilities (`/facilities/`)
- **Nav/title:** Matches.
- **Sections:** Local copy is an immense text blob containing repeated “Manuals / Operations Procedures” strings, no tables, no accordions. Google Site organizes facilities into cards with download buttons and Box/Drive embeds.
- **Images:** 0 vs. multiple facility photos.
- **Downloads:** Numerous Box, DOC, and schedule links listed in source inventory but not hyperlinked locally (text only). Users cannot click manuals.
- **Embeds:** Outlook calendars and Box file widgets absent locally; source uses at least 4 Google Script modules.

### Links (`/links/`)
- **Nav/title:** Matches.
- **Sections:** Local page is plain text; Google version has categorized link lists with clickable anchors.
- **Images:** None, parity acceptable.
- **Downloads/Embeds:** Many critical resources (Team Box Folder, MyArgonne, etc.) are plain text; they need markdown hyperlinks.

### Contact (`/contact/`)
- **Nav/title:** Matches.
- **Sections:** Local version is text-only, repeating nav boilerplate and lacking map/office photo. Google page embeds Google Maps and contact cards.
- **Images:** 0 vs. hero photo/building image.
- **Embeds:** No map or forms locally. Source uses Google Map widget + multiple script embeds.

## Risky Link Validation
| Link | HTTP Result | Notes |
| --- | --- | --- |
| `https://drive.google.com/file/d/1-ijC9KQlzSmAkoX9VKgI8JA7sMMJ-NNf/view?usp=drive_link` | `302` to Google Accounts login | Requires authentication; cannot be directly linked without auth or rehosting. |
| `https://www.google.com/url?q=https://outlook.office365.com/.../calendar.html` | `200` for Google interstitial, but actual Outlook calendar requires Argonne login | Embed relies on authenticated Outlook Web calendar, so it will not render on GitHub Pages. |

(Headers captured via `curl -I`; see command log for details.)

## Annotated Screenshots
1. `docs/parity/home-local.png` – local Home page shows only text, missing hero/imagery (compare to `docs/reference-shots/home.png`).
2. `docs/parity-shots/local-facilities.png` vs `docs/reference-shots/facilities.png` – Facilities page lacks cards, links, and any styling.
3. `docs/parity-shots/local-contact.png` vs `docs/reference-shots/contact.png` – Contact page missing map widget and photo.

## Pass/Fail
- **Status:** ❌ **Fail** – The current GitHub Pages content is merely raw scraped text with duplicated Google boilerplate, zero images, missing embeds, and non-functional downloads. Substantial templating and asset embedding are required before the site can be considered a faithful duplicate.

## Recommended Remediation Steps (High-Level)
1. Update the importer/post-processor to strip Google chrome strings and convert headings, lists, and links into clean Markdown.
2. Wire downloaded images (`assets/img/imported/<slug>/`) into the Markdown with descriptive alt text; add hero metadata per page.
3. Recreate embedded features: host CV PDF locally, replace Outlook calendar with static schedule or link, and convert Box/Drive assets into accessible downloads.
4. Reconstruct structured layouts (cards, accordions) using Markdown + custom includes or data files.
