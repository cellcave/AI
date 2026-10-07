# Deploy on GitHub Pages

1. Create a GitHub repository. Upload the contents of this project folder to the repository root, including the hidden `.github` folder. Do not upload only the outer folder or ZIP.
2. Use the `main` branch (or update the workflow branch if you use another).
3. Open repository **Settings → Pages → Build and deployment → Source**, then select **GitHub Actions**.
4. Open **Actions → Deploy SAVE SUPPLIERS to GitHub Pages → Run workflow**, or push to `main`.
5. The deployment job provides the live website URL. Check the homepage, app detail pages and mobile menu at that address.

The workflow builds from source, validates internal links, and uploads `dist/`. It reads the Pages base path and public URL from GitHub. User/organization sites use `/`; repository sites use `/repository-name/`. Custom domains also use the URL reported by Pages.

## Manual build examples

User site:

```sh
python build.py --base / --site-url https://YOUR-USERNAME.github.io
```

Repository site:

```sh
python build.py --base /YOUR-REPOSITORY/ --site-url https://YOUR-USERNAME.github.io/YOUR-REPOSITORY
```

Replace the uppercase example values with your real details, then run `python verify.py`. Every internal navigation link and asset URL receives the base path, including the 404 page. URL and base must match; the build rejects mismatched settings. The included preview server serves the current build at its configured base.

The output is static HTML with actual directories for routes; no SPA rewrite is required. GitHub Pages automatically serves `404.html` for unknown routes. `.nojekyll` prevents unwanted processing.

## Before launch

Confirm the app catalog and support email, provide real store and app privacy links where applicable, and review the website policies against your practices. There are no fabricated ratings, downloads, customer quotes, payment features or live-store links.
