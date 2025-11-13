# MSD Soft Matter Lab (imewei.github.io)

This repository hosts the next-generation Jekyll site for the MSD Soft Matter Lab led by Dr. Wei Chen at Argonne National Laboratory. It contains:

- A GitHub Pages–compatible Jekyll scaffold (`_config.yml`, `_layouts/`, `_includes/`, `_data/`, `pages/`, `assets/`).
- Reference artifacts gathered from the legacy Google Site (`docs/reference-shots`, `docs/inventory.md`).
- Automation tooling for content migration (`scripts/import_google_site.py`) and mirroring (`scripts/mirror.sh`).

## Quick Start

### Serve locally

```bash
bundle install           # installs github-pages + deps
bundle exec jekyll serve --livereload
# visit http://127.0.0.1:4000
```

### Production build

```bash
JEKYLL_ENV=production bundle exec jekyll build
```

### Deploy on GitHub Pages

1. Push to the `main` branch.
2. In GitHub ➜ Settings ➜ Pages, set **Source** to `GitHub Actions` (or `main / (root)` if you prefer the legacy workflow).
3. The default GitHub Pages workflow provided by `github-pages` will publish `_site/` automatically.

## Editing Content

- Author primary pages under `pages/` (Markdown + YAML front matter) and let `_data/navigation.yml` define the navigation order/title.
- Use `_layouts/page.html` for most content; `_layouts/default.html` already wires in header/nav/footer includes.
- Store shared structured data in `_data/*.yml` (e.g., future `people.yml`, `publications.yml`).
- Add images to `assets/img/` and reference them with absolute paths such as `/assets/img/lab/beamline.jpg`.
- Run `bundle exec jekyll build` before committing to catch Liquid/front-matter issues.

## Importer Workflow (Google Site ➜ Jekyll)

`scripts/import_google_site.py` fetches the eight public Google Site pages, converts them to Markdown, and downloads images locally.

```bash
python3 -m venv .venv && source .venv/bin/activate    # optional
pip install -r scripts/requirements.txt

# dry-run specific page (cached where possible)
python scripts/import_google_site.py --pages research

# refresh everything (re-download HTML + assets)
python scripts/import_google_site.py --force-refresh
```

Key features:
- Caches raw HTML under `.cache/google_site/` so re-runs are fast.
- Saves Markdown output to `pages/<slug>.md` with clean front matter.
- Downloads images into `assets/img/imported/<slug>/` and rewrites `img` tags to local paths; falls back to remote URLs if a download fails.
- Sleeps between requests (`--delay` flag, default 1.0 s) to stay polite.

## Mirror Workflow (snapshot `_site/`)

Use `scripts/mirror.sh` to capture a fully linked snapshot of the staged Google Site (or any target) into `tmp/site-mirror`. It combines a throttled `wget` crawl with the Python post-processor `scripts/postprocess_mirror.py`.

```bash
./scripts/mirror.sh \
  --source https://sites.google.com/view/msdsoftmatter \
  --output tmp/site-mirror \
  --depth 5 \
  --retries 3

# Inspect normalized output
npx serve tmp/site-mirror/staging
```

Highlights:
- Stores immutable runs under `tmp/site-mirror/runs/<timestamp>/` and symlinks `latest`, `raw`, `staging` for convenience.
- Rewrites all internal links to root-relative paths and relocates non-HTML assets under `/assets/`.
- Upgrades `lh3.googleusercontent.com` images to their high-resolution `=s0` variants when available.

## Documentation

- `docs/architecture.md` – deep dive into layouts/includes/data, CSS variable strategy, nav config, authoring guidance, and workflow diagrams.
- `docs/inventory.md` + `docs/site-map.json` – crawl output from the legacy Google Site.

## Contributing

1. Create a feature branch.
2. Run `bundle exec jekyll build` and (optionally) `python scripts/import_google_site.py --pages home` to ensure tooling still works.
3. Commit with descriptive messages referencing files touched.
4. Open a pull request; include before/after screenshots for visual changes.

## License

Content and code © {{ 'now' | date: '%Y' }} MSD Soft Matter Lab, Argonne National Laboratory. Unless otherwise stated, source files are released under the MIT License.
