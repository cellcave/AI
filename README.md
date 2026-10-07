# SAVE SUPPLIERS — original brief implementation

Original SAVE SUPPLIERS branding and a premium dark blue/gold interface, inspired by the reference site's navigation, spacing and app-oriented layout. The reference's branding, source and product descriptions are not used as this site's content.

## Included

- Home, Apps, About, Contact, Privacy, Terms and 404.
- Sticky header, animated accessible mobile navigation, shared footer and keyboard focus styles.
- Central app data with reusable cards, grid, buttons, headings and app detail template.
- Responsive three/two/one-column grid, app search/categories and optional screenshots.
- Detail pages, features, product CTA, related apps and clean lowercase routes generated from app records.
- Unique metadata, Open Graph/X titles/descriptions, organization schema, favicon, production sitemap and robots.
- GitHub Pages workflow with automatic domain and repository-path detection.
- Plain HTML/CSS/JavaScript output with no browser dependencies, cookies or analytics.

## Important current catalog state

The original brief does not provide actual app names, descriptions, features or product URLs. `src/apps.json` therefore contains an empty catalog, and the site presents a polished empty state. No reference apps or invented SAVE SUPPLIERS products are advertised. Actual detail pages are generated as soon as real app records are added and the site is rebuilt.

`fixtures/qa-apps.json` is strictly verification data and is never used by the normal build or deployment. It proves that three apps generate automatically, with one draft excluded. It is not a product catalog or a public demo.

The requested temporary email `test@gmail.com` is used throughout and is centralized in `src/site.json`.

## Upload to GitHub Pages

The ZIP puts `index.html` and all website folders directly at its root, together with editable source and `.github` deployment configuration. Upload the ZIP's contents to the repository root, including `.github`; do not upload the ZIP itself or an extra enclosing folder. Use Settings → Pages → Source: GitHub Actions. Push to main or run the workflow manually. The workflow builds the actual production URL, canonical tags, sitemap and repository base path automatically.

The root HTML files have relative links for ordinary page navigation and assets. The workflow is the recommended GitHub Pages deployment so production SEO and the 404 page use the correct public URL. A public URL has not been supplied, so the bundled preview intentionally uses noindex and does not invent canonical/sitemap domains.

## Build and preview

Python 3.10+ is required for authoring; published visitors need only a browser.

```sh
python build.py --portable
python verify.py
python serve.py
```

Open http://127.0.0.1:4173/. Preview through a web server, rather than double-clicking HTML files, to use clean directory URLs.

## Add an actual app

Edit `src/apps.json` and rebuild. Example record shape:

```json
[
  {
    "slug": "your-app-slug",
    "name": "Actual app name",
    "description": "A concise description of your actual product.",
    "intro": "A longer overview of what this app does.",
    "category": "Utilities",
    "platform": "Android",
    "status": "available",
    "icon": "document",
    "color": "blue",
    "url": "https://your-actual-product-url.example",
    "features": [
      {"title": "Actual feature", "text": "Explain a confirmed app capability."}
    ]
  }
]
```

Replace all example values with real product information. Do not paste unconfirmed URLs into the catalog.

- `slug`: unique lowercase words separated by hyphens; creates `/apps/your-app-slug/`.
- `status`: `available`, `coming-soon`, or `draft`. Drafts do not generate public cards, routes or sitemap entries.
- `url`: actual HTTPS Open App link. `storeUrl` can instead supply a Google Play listing.
- `privacyUrl`: optional actual HTTPS app-specific privacy policy. Website privacy is not a substitute.
- `icon`: simple `document` or `leaf` line icon; `color`: `blue`, `gold`, `purple` or `lime`.
- `iconPath`: optional local path such as `assets/icons/my-app.png`; put the file in `src/assets/icons/`.
- `screenshots`: optional list of objects with local `path`, descriptive `alt` and optional `caption`. Save originals in `src/assets/`.
- `formats` and `note`: optional support details.

A coming-soon or unlinked app has an honest contact action. Real links create real CTAs; no fabricated download buttons are shown.

## Contact and policies

Contact prepares an encoded email draft, with validation and direct-email fallback. It does not send email on your behalf or store submitted messages. Website policies describe the static site and must be updated if you add tracking, payments or a backend. App-specific policies depend on actual app behavior.

## Verification

See `QA-REPORT.md` and `qa/production/browser-report.json`. The optional `browser-checks.cjs` requires Playwright and a browser installed locally. Standard build and internal-link checks require no Python packages. The separate architecture verification build can be reproduced with:

```sh
python build.py --qa --apps-data fixtures/qa-apps.json --base /save-suppliers/ --site-url https://example.github.io/save-suppliers
python verify.py --qa
python serve.py --qa --port 4181
```

This writes `.qa-dist/`, never `dist/`. The test domain is used only to verify correct URL generation. No live deployment was performed.