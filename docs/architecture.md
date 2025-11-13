# MSD Soft Matter Lab Website - Architecture

This document describes the structure, styling, navigation, and workflows for the lab website.

## Site Structure

This is a **static HTML site** with no build system or templating engine. All pages are standalone HTML files.

### Pages

- `index.html` - Home page with research highlights
- `wei-chen.html` - PI profile
- `team.html` - Lab members
- `research.html` - Research projects
- `publications.html` - Publications list
- `facilities.html` - Equipment and resources
- `links.html` - External resources
- `contact.html` - Contact information

### No Layouts or Includes

Unlike Jekyll or other static site generators, this site **does not use**:
- `_layouts/` directory
- `_includes/` directory
- Template inheritance
- Partial components

Each HTML file is self-contained with its own `<header>`, `<nav>`, and `<footer>`.

## Styling

### CSS Architecture

Single stylesheet: `styles.css`

**CSS Variables** (defined in `:root`):
- `--primary-color: #003366` - Header background, primary theme
- `--primary-light: #0066cc` - Gradients, hover states
- `--accent-color: #66b3ff` - Link hover color
- `--text-color: #333` - Body text
- `--background-color: #f5f5f5` - Page background
- `--card-background: white` - Content cards

### Key Selectors

- `.container` - Max-width 1200px content wrapper
- `.hero` - Full-width blue gradient section
- `.research-card` - Content card with shadow
- `header` - Navy blue sticky navigation bar
- `nav ul` - Flexbox horizontal menu

### Responsive Design

- Mobile-first approach with `@media` queries
- Navigation collapses on small screens
- Flexible grid layouts for research cards

## Navigation

### Structure

Navigation is **repeated in every HTML file** (no shared template):

```html
<nav>
    <ul>
        <li><a href="index.html">Home</a></li>
        <li><a href="wei-chen.html">Wei Chen</a></li>
        <li><a href="team.html">Our Team</a></li>
        <li><a href="research.html">Research</a></li>
        <li><a href="publications.html">Publications</a></li>
        <li><a href="facilities.html">Facilities</a></li>
        <li><a href="links.html">Links</a></li>
        <li><a href="contact.html">Contact</a></li>
    </ul>
</nav>
```

### Adding a New Page

To add a new page (e.g., `news.html`):

1. Create `news.html` by copying an existing page
2. Update `<title>` and content
3. **Manually update navigation** in ALL HTML files:
   ```html
   <li><a href="news.html">News</a></li>
   ```

This is the main drawback of static HTML without templating.

## Authoring Workflow

### Manual Authoring (Primary)

1. Edit HTML files directly in a text editor
2. Preview locally: `open index.html` or use a local server
3. Commit changes to git
4. Push to GitHub (deploys via GitHub Pages)

### Content Updates

- **Text changes**: Edit HTML directly
- **Styling changes**: Edit `styles.css`
- **New pages**: Copy existing page structure, update navigation everywhere

### Local Development

No build step required. Options for local preview:

```bash
# Python simple server
python3 -m http.server 8000

# Open directly in browser
open index.html
```

## Workflows

### Workflow 1: Importer (Future)

**Purpose**: Import content from external sources (e.g., lab management systems)

**Process**:
1. Fetch data via API or export file
2. Generate HTML from template
3. Update navigation if needed
4. Commit and deploy

**Status**: Not implemented. Would require custom scripts.

### Workflow 2: Mirror (Site Crawler)

**Purpose**: Mirror external websites for integration or archival

**Tools**: `scripts/mirror.sh` and `scripts/postprocess_mirror.py`

**Process**:

1. **Crawl target site**:
   ```bash
   ./scripts/mirror.sh https://example.com
   ```
   - Uses `wget` with throttling and retries
   - Stores raw HTML in `tmp/site-mirror/runs/<timestamp>/raw/`

2. **Postprocess content** (automatic):
   - Rewrites links to root-relative (`/images/foo.png`)
   - Organizes assets by type (images, CSS, JS)
   - Output in `tmp/site-mirror/runs/<timestamp>/staging/`

3. **Review staging output**:
   ```bash
   open tmp/site-mirror/runs/<timestamp>/staging/index.html
   ```

4. **Integrate content**:
   - Copy desired files to repository root
   - Update navigation and styling
   - Test all links and assets
   - Commit and deploy

**Use Cases**:
- Migrating legacy lab websites
- Archiving conference proceedings
- Importing documentation from external sources

**Caveats**:
- Requires manual integration (no automatic merge)
- JavaScript-heavy sites may not mirror correctly
- Always obtain permission before crawling

See `scripts/README.md` for detailed usage and options.

## Data Management

### No Data Layer

This site does not use:
- YAML front matter
- `_data/` directory
- JSON/YAML configuration files
- Automated data rendering

All content is embedded directly in HTML.

### Future Enhancements

Consider migrating to a static site generator (Jekyll, Hugo, Eleventy) if:
- Navigation becomes unmanageable
- Content is frequently updated by non-technical users
- Data-driven pages are needed (e.g., publications database)

## Deployment

### GitHub Pages

1. Push changes to `main` branch
2. GitHub Pages automatically serves from root directory
3. Site available at `https://imewei.github.io`

### Custom Domain (Optional)

1. Add `CNAME` file with domain name
2. Configure DNS records
3. Enable HTTPS in repository settings

## Directory Structure

```
imewei.github.io/
├── index.html              # Home page
├── wei-chen.html           # PI profile
├── team.html               # Team page
├── research.html           # Research page
├── publications.html       # Publications page
├── facilities.html         # Facilities page
├── links.html              # Links page
├── contact.html            # Contact page
├── styles.css              # Global stylesheet
├── images/                 # (future) Image assets
├── scripts/                # Maintenance scripts
│   ├── mirror.sh          # Site crawler
│   ├── postprocess_mirror.py  # Link rewriter
│   └── README.md          # Scripts documentation
├── docs/                   # Documentation
│   └── architecture.md    # This file
└── tmp/                    # Temporary/generated files (gitignored)
    └── site-mirror/       # Mirror output
```

## Best Practices

### Navigation Consistency

- Use find/replace when updating navigation across all files
- Consider a script to update nav if changes are frequent

### CSS Organization

- Group related styles with comments
- Use CSS variables for theme colors
- Keep media queries at the end of file

### HTML Semantics

- Use semantic tags (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`)
- Include ARIA labels for accessibility
- Validate HTML with W3C validator

### Asset Management

- Use relative paths for local assets
- Organize images in `images/` directory (when needed)
- Optimize images before committing (use ImageOptim or similar)

### Version Control

- Commit logical changes separately
- Write descriptive commit messages
- Don't commit `tmp/` directory (add to `.gitignore`)

## Maintenance Notes

### Updating All Pages

To update header/footer/navigation across all pages:

```bash
# Example: Update copyright year
sed -i '' 's/© 2025/© 2026/g' *.html
```

(Note: `-i ''` is BSD sed syntax for macOS)

### Link Validation

Periodically check for broken links:

```bash
# Using wget
wget --spider --recursive --no-directories --no-verbose http://localhost:8000
```

### Accessibility

- Test with screen readers (VoiceOver on macOS)
- Validate with axe DevTools browser extension
- Ensure sufficient color contrast (WCAG AA minimum)

## Migration Path

If the site grows significantly, consider migrating to:

1. **Jekyll** (GitHub Pages native)
   - Minimal learning curve
   - Built-in templating and data files
   - Automatic deployment on GitHub Pages

2. **Hugo** (fast, powerful)
   - Very fast build times
   - Requires separate deployment step

3. **Eleventy** (flexible, modern)
   - JavaScript-based
   - Multiple template languages
   - Good for gradual migration

Migration would convert:
- Repeated navigation → `_includes/nav.html`
- Page structure → `_layouts/default.html`
- Styles → partials or component CSS
- Content → Markdown + front matter

## Further Reading

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [HTML5 Semantic Elements](https://developer.mozilla.org/en-US/docs/Web/HTML/Element)
- [CSS Variables Guide](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
