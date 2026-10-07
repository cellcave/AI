# SAVE SUPPLIERS

Complete static website, inspired by the supplied FT reference. Original SAVE SUPPLIERS UI and shared page generator. No framework, external fonts, install step or runtime dependencies. Python 3.10+ is used only to build and preview. The published site is plain HTML, CSS, JavaScript and SVG.

## Preview

```sh
python build.py
python verify.py
python serve.py
```

Open http://127.0.0.1:4173/. Use the local server instead of double-clicking HTML because the navigation uses website paths.

## Edit

- `src/site.json`: company name, email and optional public site URL.
- `src/apps.json`: reusable app catalog. An entry generates a listing card and its own detail route. IDs must be unique lowercase URL slugs. Provide at least one app for the featured homepage panel.
- `src/assets/site.css`: responsive theme, layout and interactions.
- `src/assets/site.js`: mobile menu, catalog search/filter and contact email draft.
- `build.py`: shared header, footer, app cards, page templates and content.

Rebuild after editing. `dist/` is generated output; edits there will be overwritten by the next build.

## Initial content to confirm

The two initial app records are adapted from the supplied reference ZIP: All Document Reader and Quit Vape & Pouches. They are not independently verified SAVE SUPPLIERS products. Confirm their names, features and ownership or replace the records with your actual apps before publishing.

`test@gmail.com` is the contact address carried forward from the earlier project context. Replace it with your actual support address before publishing. Empty `storeUrl` and `privacyUrl` fields are intentional: the site shows a support action instead of a fabricated download link, and never presents website privacy as an app policy. Add actual HTTPS store and app policy URLs when available; their buttons will appear automatically.

The contact form opens a correctly encoded email draft. It does not claim to send messages and has no server or database. Without an email client, visitors can use the displayed email address. With JavaScript disabled, all navigation and app content remain available, with a direct email fallback.

Website policies describe this static implementation. They must be updated if you add tracking, cookies, a submission backend or payments. App-specific policies need to reflect the actual apps.

## Production SEO

The bundled build is a local preview and intentionally uses noindex until a real public URL is supplied. Canonicals, Open Graph URLs, sitemap URLs and robots are generated from that URL; no domain is invented. The workflow supplies the GitHub Pages URL automatically. Social metadata includes titles and descriptions; no social image is claimed.

See `DEPLOY-GITHUB-PAGES.md` for deployment. No website has been published by preparing this ZIP.
