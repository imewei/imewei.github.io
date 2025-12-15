# Reference Screenshots Directory

This directory should contain full-page screenshots of all top-level pages from the original Google Site for reference during migration.

## Required Screenshots

Capture full-page screenshots (not just viewport) of the following 8 pages:

1. **home.png**
   - URL: https://sites.google.com/view/msdsoftmatter/home
   - Content: Landing page with 3 research focus areas

2. **wei-chen.png**
   - URL: https://sites.google.com/view/msdsoftmatter/wei-chen
   - Content: PI profile, education, research focus

3. **our-team.png**
   - URL: https://sites.google.com/view/msdsoftmatter/our-team
   - Content: Current and former lab members

4. **research.png**
   - URL: https://sites.google.com/view/msdsoftmatter/research
   - Content: Five research focus areas with illustrations

5. **publications.png**
   - URL: https://sites.google.com/view/msdsoftmatter/publications
   - Content: Recent publications and patents

6. **facilities.png**
   - URL: https://sites.google.com/view/msdsoftmatter/facilities
   - Content: Equipment list and shared resources

7. **links.png**
   - URL: https://sites.google.com/view/msdsoftmatter/links
   - Content: External resources and partner institutions

8. **contact.png**
   - URL: https://sites.google.com/view/msdsoftmatter/contact
   - Content: Contact information and address

## Capture Methods

### Method 1: Browser Extension (Easiest)
Use a full-page screenshot extension like:
- Chrome: "Full Page Screen Capture", "GoFullPage", or "Awesome Screenshot"
- Firefox: "Fireshot" or "Nimbus Screenshot"

### Method 2: Browser DevTools (Built-in)
1. Open page in Chrome/Edge
2. Press F12 to open DevTools
3. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)
4. Type "screenshot" and select "Capture full size screenshot"
5. Save with the appropriate filename

### Method 3: Automated Script (Most Consistent)
Use Playwright or Puppeteer for consistent captures:

```bash
# Install Playwright
npm install -D @playwright/test

# Create screenshot script (save as capture-screenshots.js)
```

```javascript
const { chromium } = require('playwright');

const pages = [
  { name: 'home', url: 'https://sites.google.com/view/msdsoftmatter/home' },
  { name: 'wei-chen', url: 'https://sites.google.com/view/msdsoftmatter/wei-chen' },
  { name: 'our-team', url: 'https://sites.google.com/view/msdsoftmatter/our-team' },
  { name: 'research', url: 'https://sites.google.com/view/msdsoftmatter/research' },
  { name: 'publications', url: 'https://sites.google.com/view/msdsoftmatter/publications' },
  { name: 'facilities', url: 'https://sites.google.com/view/msdsoftmatter/facilities' },
  { name: 'links', url: 'https://sites.google.com/view/msdsoftmatter/links' },
  { name: 'contact', url: 'https://sites.google.com/view/msdsoftmatter/contact' }
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

  for (const p of pages) {
    console.log(`Capturing ${p.name}...`);
    await page.goto(p.url, { waitUntil: 'networkidle' });
    await page.screenshot({
      path: `reference-shots/${p.name}.png`,
      fullPage: true
    });
  }

  await browser.close();
  console.log('All screenshots captured!');
})();
```

```bash
# Run the script
node capture-screenshots.js
```

## Screenshot Specifications

- **Format:** PNG
- **Width:** 1920px viewport (or wider if content requires)
- **Type:** Full-page (entire scrollable content, not just viewport)
- **Quality:** High resolution for reference purposes
- **Naming:** Use exact filenames listed above (lowercase, hyphenated)

## Purpose

These screenshots serve as:
1. **Visual reference** during HTML/CSS conversion
2. **Layout verification** to ensure migrated pages match original
3. **Archive** of original Google Site design before migration
4. **Comparison tool** for QA after GitHub Pages deployment

## Status

✅ **All screenshots captured on 2025-11-13 using Playwright**

- [x] home.png (676 KB)
- [x] wei-chen.png (881 KB)
- [x] our-team.png (1.1 MB)
- [x] research.png (1.9 MB)
- [x] publications.png (746 KB)
- [x] facilities.png (4.2 MB)
- [x] links.png (562 KB)
- [x] contact.png (803 KB)

**Total:** 8 screenshots, ~10.8 MB

## Notes

- Capture both desktop and mobile views if responsive design testing is needed
- Consider capturing screenshots at multiple viewport sizes if layout changes significantly
- Store original high-resolution versions; can be downscaled later if needed
- Recommended to capture all screenshots in a single session to ensure consistent appearance
