"""Dependency-free static website generator. Python 3.10+."""
import argparse
import html
import json
import re
import shutil
import posixpath
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
parser = argparse.ArgumentParser()
parser.add_argument("--base", default="/", help="/ for user sites; /repo-name/ for project sites")
parser.add_argument("--site-url", default=None, help="Full public site URL, including repo path")
parser.add_argument("--apps-data", default=None, help="Alternate catalog for verification")
parser.add_argument("--qa", action="store_true", help="Write a separate .qa-dist verification build")
parser.add_argument("--portable", action="store_true", help="Relative links for root or repository uploads")
args = parser.parse_args()
base = "/" + args.base.strip("/") + "/" if args.base.strip("/") else "/"
if not re.fullmatch(r"/(?:[A-Za-z0-9._-]+/)*", base):
    raise SystemExit("Base path must consist of URL-safe path segments")
site = json.loads((SRC / "site.json").read_text(encoding="utf-8-sig"))
catalog_file = Path(args.apps_data).resolve() if args.apps_data else SRC / "apps.json"
apps = json.loads(catalog_file.read_text(encoding="utf-8-sig"))
for app in apps:
    app['id'] = app.get('slug', app.get('id'))
    app.setdefault('status', 'available')
    app.setdefault('icon', 'document')
    app.setdefault('color', 'blue')
    app.setdefault('platform', 'App')
    app.setdefault('formats', [])
    app.setdefault('note', '')
    app.setdefault('screenshots', [])
    app.setdefault('intro', app.get('description', ''))
    app.setdefault('features', [])
    if app['status'] not in ('available', 'coming-soon', 'draft'):
        raise SystemExit('App status must be available, coming-soon or draft')
apps = [app for app in apps if app['status'] != 'draft']
origin = (args.site_url if args.site_url is not None else site["siteUrl"]).rstrip("/")
if origin:
    parsed = urlparse(origin)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment:
        raise SystemExit("site URL must be an absolute HTTP(S) URL without query or fragment")
    if parsed.path.rstrip("/") != base.rstrip("/"):
        raise SystemExit("site URL path must match --base (include your repository name in both)")
ids = [app["id"] for app in apps]
if len(set(ids)) != len(ids) or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", id) for id in ids):
    raise SystemExit("App IDs must be unique lowercase URL slugs")
for app in apps:
    for field in ("storeUrl", "privacyUrl", "url"):
        if app.get(field) and urlparse(app[field]).scheme != "https":
            raise SystemExit(f"{app['id']}: {field} must be an HTTPS URL")
dist = ROOT / (".qa-dist" if args.qa else "dist")
# This generator owns only its own dist directory.
if dist.exists():
    shutil.rmtree(dist)
dist.mkdir()
shutil.copytree(SRC / "assets", dist / "assets")
(dist / ".nojekyll").write_text("", encoding="utf-8")
routes = []
E = lambda value: html.escape(str(value), quote=True)
U = lambda path="": E(base + path.lstrip("/"))
EMAIL = E(site["email"])
NAME = E(site["name"])

def icon(kind):
    paths = {
        "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
        "leaf": '<path d="M20 3C10 2 3 6 3 13a7 7 0 0 0 12 5c4-4 5-10 5-15Z"/><path d="M4 21 15 10"/>',
        "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
        "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>'
    }
    return '<svg viewBox="0 0 24 24" aria-hidden="true">' + paths.get(kind, paths["document"]) + '</svg>'

def button(label, path, secondary=False, external=False):
    href = E(path) if external else U(path)
    cls = 'btn secondary' if secondary else 'btn'
    attrs = ' target="_blank" rel="noopener noreferrer"' if external else ''
    suffix = '<span class="sr-only"> (opens in a new tab)</span>' if external else ''
    return f'<a class="{cls}" href="{href}"{attrs}>{E(label)}{suffix}</a>'

def section_heading(label, title):
    return f'<div class="section-head"><div><span class="eyebrow">{E(label)}</span><h2>{E(title)}</h2></div></div>'

def brand():
    return f'<a class="brand" href="{U()}" aria-label="{NAME} home"><span class="brand-mark" aria-hidden="true">S</span>{NAME}</a>'

def header(active):
    nav = ""
    for slug, label in [("", "Home"), ("apps/", "Apps"), ("about/", "About"), ("contact/", "Contact us")]:
        current = ' aria-current="page"' if active == slug else ""
        cls = ' class="nav-contact"' if slug == "contact/" else ""
        nav += f'<a href="{U(slug)}"{current}{cls}>{label}</a>'
    return f'<a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="wrap header-inner">{brand()}<button class="menu-toggle" type="button" aria-controls="primary-nav" aria-expanded="false" aria-label="Open menu">{icon("menu")}</button><nav class="primary-nav" id="primary-nav" aria-label="Primary navigation">{nav}</nav></div></header>'

def footer():
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-grid"><div class="footer-intro">{brand()}<p>Practical apps. Clear information.<br>A simpler way through the everyday.</p><a class="email" href="mailto:{EMAIL}">{EMAIL}</a></div><nav class="footer-nav" aria-label="Company"><strong>Explore</strong><a href="{U('apps/')}">Our apps</a><a href="{U('about/')}">About us</a><a href="{U('contact/')}">Contact &amp; support</a></nav><nav class="footer-nav" aria-label="Legal"><strong>The details</strong><a href="{U('privacy/')}">Website privacy</a><a href="{U('terms/')}">Terms of use</a></nav></div><div class="footer-bottom"><span>© 2026 {NAME}. All rights reserved.</span><span>Built around everyday life.</span></div></div></footer>'''

def write_page(route, title, description, body, active=None, noindex=False):
    fulltitle = f"{title} | {site['name']}"
    canonical = f'<link rel="canonical" href="{E(origin + "/" + route)}"><meta property="og:url" content="{E(origin + "/" + route)}">' if origin else ""
    robots = "noindex,follow" if noindex or not origin else "index,follow"
    schema = {"@context": "https://schema.org", "@type": "Organization", "name": site["name"], "email": site["email"]}
    if origin:
        schema["url"] = origin + "/"
    structured = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    content = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(fulltitle)}</title><meta name="description" content="{E(description)}"><meta name="robots" content="{robots}"><meta name="theme-color" content="#0c1019"><meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}"><meta property="og:title" content="{E(fulltitle)}"><meta property="og:description" content="{E(description)}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{E(fulltitle)}"><meta name="twitter:description" content="{E(description)}">{canonical}<link rel="icon" type="image/svg+xml" href="{U('assets/favicon.svg')}"><link rel="stylesheet" href="{U('assets/site.css')}"><script src="{U('assets/site.js')}" defer></script><script type="application/ld+json">{structured}</script></head><body>{header(active if active is not None else route)}<main id="main" tabindex="-1">{body}</main>{footer()}</body></html>'''
    if args.portable and route != '404.html':
        directory = route.rstrip('/') or '.'
        def relative_link(match):
            attr, url = match.groups()
            if not url.startswith(base): return match.group(0)
            local = url[len(base):]
            relative = posixpath.relpath(local or '.', directory)
            if url.endswith('/'):
                relative = './' if relative == '.' else relative + '/'
            return f'{attr}="{relative}"'
        content = re.sub(r'(href|src)="([^"]+)"', relative_link, content)
    path = dist / route / "index.html" if route else dist / "index.html"
    if route == "404.html":
        path = dist / route
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if not noindex:
        routes.append(route)

def app_icon(app):
    if app.get('iconPath'):
        return f'<span class="app-icon"><img src="{U(app["iconPath"])}" alt="{E(app["name"])} app icon" width="62" height="62"></span>'
    return f'<span class="app-icon {E(app["color"])}">{icon(app["icon"])}</span>'

def card(app):
    search = E((app["name"] + " " + app["description"] + " " + app["category"]).lower())
    status = '<span class="app-status">Coming soon</span>' if app['status'] == 'coming-soon' else ''
    return f'''<article class="app-card" data-app="{E(app['id'])}" data-category="{E(app['category'])}" data-search="{search}"><div class="card-top">{app_icon(app)}<span class="tag">{E(app['category'])}</span></div>{status}<h3><a href="{U('apps/' + app['id'] + '/')}">{E(app['name'])}</a></h3><p>{E(app['description'])}</p><div class="card-bottom"><span>{E(app['platform'])}</span><a href="{U('apps/' + app['id'] + '/')}">View app<span class="sr-only">: {E(app['name'])}</span></a></div></article>'''

def app_grid(records):
    return '<div class="app-grid">' + ''.join(card(app) for app in records) + '</div>'

def empty_catalog():
    return f'<div class="catalog-empty"><span class="eyebrow">The app collection</span><h2>A place for what’s next.</h2><p>App details will appear here as they are published. For product inquiries or support, get in touch with SAVE SUPPLIERS.</p><div class="actions">{button("Contact us", "contact/")}</div></div>'

def related_apps(app):
    related = [other for other in apps if other['id'] != app['id']][:3]
    if not related: return ''
    return '<section class="section band"><div class="wrap">' + section_heading('Keep exploring', 'More from SAVE SUPPLIERS') + app_grid(related) + '</div></section>'

def page_top(label, title, description):
    return f'<section class="page-top"><div class="wrap"><span class="eyebrow">{label}</span><h1>{title}</h1><p>{description}</p></div></section>'

def cta():
    return f'<section class="section"><div class="wrap"><div class="cta"><div><h2>Let’s make the everyday easier.</h2><p>Questions about an app? We’re here to help.</p></div><a class="btn" href="{U("contact/")}">Contact us</a></div></div></section>'

featured = apps[0] if apps else None
panel = f'<aside class="product-panel brand-panel" aria-label="SAVE SUPPLIERS platform"><div class="panel-top"><span>SAVE SUPPLIERS</span><span>Apps &amp; tools</span></div><h2 class="panel-title">Simple tools.<br>Clear possibilities.</h2><p>A home for our applications, their features and the information you need to get started.</p><ul class="panel-capabilities"><li><strong>Explore</strong><span>Find your next app</span></li><li><strong>Understand</strong><span>Clear product details</span></li><li><strong>Connect</strong><span>Support within reach</span></li></ul><div class="panel-bottom"><span>One platform. Room to grow.</span><a href="{U("apps/")}">Explore apps</a></div></aside>' 
if featured:
    panel = f'''<article class="product-panel" aria-label="Featured app: {E(featured['name'])}"><div class="panel-top"><span>In the spotlight</span><span>{E(featured['platform'])}</span></div><div class="panel-icon">{icon(featured['icon'])}</div><h2 class="panel-title">{E(featured['name'])}.</h2><p>{E(featured['description'])}</p><div class="formats">{''.join(f'<span class="format">{E(x)}</span>' for x in featured['formats'][:4])}</div><div class="panel-bottom"><span>{E(featured['category'])}</span><a href="{U('apps/' + featured['id'] + '/')}">Meet the app</a></div></article>'''
home_apps = app_grid(apps[:3]) if apps else empty_catalog()
home = f"""<section class="hero"><div class="wrap hero-grid"><div><span class="eyebrow">SAVE SUPPLIERS · Apps &amp; tools</span><h1>Useful apps.<br><span>Everyday ease.</span></h1><p class="lead">Explore our apps and tools, find the details that matter, and get support when you need it. All in one place.</p><div class="actions">{button('Explore Apps', 'apps/')}<a class="text-link" href="{U('about/')}">About SAVE SUPPLIERS</a></div><p class="micro">A clear purpose. A simple experience.</p></div>{panel}</div></section><div class="wrap strip"><div><span>01 /</span> Apps with a purpose</div><div><span>02 /</span> Details at a glance</div><div><span>03 /</span> A direct route to support</div></div><section class="section" id="our-apps"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Explore the collection</span><h2>Your next useful tool.</h2></div><a class="text-link" href="{U('apps/')}">View all apps</a></div>{home_apps}</div></section><section class="section band"><div class="wrap split"><div><span class="eyebrow">Why SAVE SUPPLIERS</span><h2>Less friction.<br>More possibility.</h2><p>Choosing an app should be straightforward. Our platform brings product information and a direct route to support together, so you can focus on what you need to do.</p><a class="text-link" href="{U('about/')}">Get to know us</a></div><ul class="rule-list"><li><strong>A clear starting point</strong>Browse the collection and explore each app’s purpose.</li><li><strong>The details that matter</strong>Find features, product links and app information in one place.</li><li><strong>Support within reach</strong>Get in touch with questions, feedback or requests for help.</li></ul></div></section><section class="section"><div class="wrap"><div class="cta"><div><h2>Find what works for you.</h2><p>Explore the SAVE SUPPLIERS app collection.</p></div>{button('Explore Apps', 'apps/')}</div></div></section>"""

write_page("", "Apps & tools for everyday life", site["description"], home)

categories = list(dict.fromkeys(app["category"] for app in apps))
filters = ''.join(f'<button type="button" data-filter="{E(cat)}" aria-pressed="{str(cat == "All").lower()}">{E(cat)}</button>' for cat in ["All"] + categories)
catalog_content = empty_catalog()
if apps:
    catalog_content = f'<div class="catalog-tools"><label class="search-field" for="app-search">{icon("search")}<span class="sr-only">Search apps</span><input id="app-search" type="search" placeholder="Search apps" autocomplete="off"></label><div class="filters" role="group" aria-label="Filter apps by category">{filters}</div></div><p class="result-count" id="app-count" aria-live="polite">{len(apps)} apps</p>{app_grid(apps)}<div class="empty" id="empty-apps" hidden><h2>No apps found</h2><p>Try a different search or select All.</p></div>'
catalog = page_top('The app collection', 'Explore. Discover.<br>Make it yours.', 'Find app information, features and product links from SAVE SUPPLIERS.') + f'<section class="catalog"><div class="wrap">{catalog_content}</div></section>'

write_page("apps/", "Our apps", "Explore SAVE SUPPLIERS apps and tools, product features and support information.", catalog)

def app_detail_page(app):
    detail_url = 'apps/' + app['id'] + '/'
    app_url = app.get('url') or app.get('storeUrl')
    primary = button('Open App' if app.get('url') else 'View on Google Play', app_url, external=True) if app_url and app['status'] == 'available' else button('Ask about this app', 'contact/')
    privacy = f'<a class="text-link" href="{E(app["privacyUrl"])}">App privacy policy</a>' if app.get("privacyUrl") else ""
    features = ''.join(f'<article class="feature"><span class="number">0{i+1}</span><h3>{E(f["title"])}</h3><p>{E(f["text"])}</p></article>' for i, f in enumerate(app["features"]))
    format_tags = ''.join('<span class="format">' + E(fmt) + '</span>' for fmt in app["formats"])
    formats = f'<section class="section band"><div class="wrap split"><div><span class="eyebrow">Supported formats</span><h2>More files.<br>One reading routine.</h2></div><div class="formats">{format_tags}</div></div></section>' if app["formats"] else ""
    note = '<div class="notice"><p>' + E(app['note']) + '</p></div>' if app['note'] else ''
    screenshots = ''
    if app['screenshots']:
        screenshots = '<section class="section"><div class="wrap">' + section_heading('A closer look', 'See the app in action') + '<div class="screenshot-grid">'
        for shot in app['screenshots']:
            screenshots += f'<figure><img src="{U(shot["path"])}" alt="{E(shot["alt"])}" loading="lazy"><figcaption>{E(shot.get("caption", ""))}</figcaption></figure>'
        screenshots += '</div></div></section>'
    body = f'''<section class="page-top"><div class="wrap"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{U()}">Home</a><span aria-hidden="true">/</span><a href="{U('apps/')}">Apps</a><span aria-hidden="true">/</span><span aria-current="page">{E(app['name'])}</span></nav><div class="detail-hero"><div><span class="eyebrow">{E(app['category'])} · {E(app['platform'])}</span><h1>{E(app['name'])}</h1><p>{E(app['intro'])}</p><div class="actions">{primary}{privacy}</div></div><aside class="detail-summary" aria-label="App overview">{app_icon(app)}<h2>{E(app['name'])}</h2><dl><div><dt>Platform</dt><dd>{E(app['platform'])}</dd></div><div><dt>Category</dt><dd>{E(app['category'])}</dd></div><div><dt>Questions?</dt><dd><a href="{U('contact/')}">Contact us</a></dd></div></dl></aside></div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">What you can do</span><h2>Built around your routine.</h2></div></div><div class="grid3">{features}</div>{note}</div></section>{formats}{screenshots}{related_apps(app)}{cta()}'''
    return body

for app in apps:
    write_page('apps/' + app['id'] + '/', app['name'], app['description'], app_detail_page(app), active='apps/')

about = page_top('About SAVE SUPPLIERS', 'Simple experiences.<br>Room for possibility.', 'SAVE SUPPLIERS is a home for apps, tools and the information that helps you choose and use them.') + f'<section class="section band"><div class="wrap split"><div><p class="about-statement">Explore an app.<br>Understand its purpose.<br>Take your next step.</p></div><div><h2>Keep the essentials close.</h2><p>This platform brings our app collection, product details and support together. Each application has its own page, with a clear overview and a direct route to the next step.</p><p>As our collection grows, you’ll find new apps here. For questions, feedback or help, our contact page keeps the conversation within reach.</p><a class="text-link" href="{U("apps/")}">Explore our apps</a></div></div></section>{cta()}'

write_page("about/", "About us", "Learn about SAVE SUPPLIERS and our approach to practical everyday apps.", about)

contact = page_top("Contact &amp; support", "Let’s talk.", "Have a question, feedback or a support request? Tell us which app you’re using and how we can help.") + f'''<div class="wrap contact-layout"><div><div class="contact-card"><h2>A direct line to us.</h2><p>Email our team with your question.</p><a class="email" href="mailto:{EMAIL}">{EMAIL}</a></div><div class="contact-card"><h2>Help us help you.</h2><p>For app support, include the app name, your device model and a short description of the issue.</p><p>Please leave out passwords, payment details and private documents.</p></div></div><form class="contact-form" id="contact-form" data-email="{EMAIL}"><div class="form-row"><div class="field"><label for="contact-name">Your name</label><input id="contact-name" name="name" required maxlength="120" autocomplete="name"></div><div class="field"><label for="contact-email">Your email</label><input id="contact-email" name="email" type="email" required maxlength="254" autocomplete="email"></div></div><div class="field"><label for="contact-subject">What’s this about?</label><select id="contact-subject" name="subject"><option>General question</option><option>App support</option><option>Feedback</option><option>Privacy question</option></select></div><div class="field"><label for="contact-message">Your message</label><textarea id="contact-message" name="message" required minlength="10" maxlength="4000" placeholder="Tell us a little about your question…"></textarea></div><button class="btn" type="submit">Create email draft</button><p class="form-help">This opens a draft in your email app. Nothing is sent until you send the email.</p><p class="form-status" id="contact-status" role="status"></p><a class="text-link" id="email-draft" hidden>Open your email draft</a><noscript><p>To contact us, email <a href="mailto:{EMAIL}">{EMAIL}</a> directly.</p></noscript></form></div>'''
write_page("contact/", "Contact & support", "Contact SAVE SUPPLIERS with app questions, feedback or privacy inquiries.", contact)

privacy = page_top("Website policy", "Privacy, explained.", "This policy describes this website. Individual mobile apps may have their own privacy policies.") + f'''<article class="wrap prose"><p>Last updated: 7 October 2026</p><h2>Information on this website</h2><p>This is a static informational website. It does not require an account, accept payments, store contact-form entries, or include advertising or analytics scripts.</p><h2>When you contact us</h2><p>The contact form prepares an email draft on your device. The website does not submit your message to a server. If you send the email, we receive the information you include, such as your name, email address and message, and use it to handle your inquiry.</p><h2>Hosting and technical information</h2><p>The hosting provider may process technical information such as IP addresses and request logs to deliver the website, maintain security and operate its service. These activities are subject to the provider’s own policies.</p><h2>Cookies and local storage</h2><p>The website code does not set cookies or use browser storage. External websites and services you choose to visit may follow different practices.</p><h2>External links and mobile apps</h2><p>App stores and other linked services operate under their own privacy terms. This website policy does not describe how a mobile app processes data. Review the relevant app’s privacy information before using it; contact us if you need help locating it.</p><h2>Your requests</h2><p>To ask about personal information you shared by email, request a correction or deletion, or raise a privacy question, contact <a href="mailto:{EMAIL}">{EMAIL}</a>.</p><h2>Updates</h2><p>We may update this policy when website features or practices change. The date above identifies the current version.</p></article>'''
write_page("privacy/", "Website privacy", "Read how the SAVE SUPPLIERS website handles contact inquiries and technical information.", privacy)

terms = page_top("Website terms", "A few clear essentials.", "These terms apply to use of the SAVE SUPPLIERS website and its informational content.") + f'''<article class="wrap prose"><p>Last updated: 7 October 2026</p><h2>Using the website</h2><p>You may browse this website and use its contact information for legitimate inquiries. Do not interfere with its operation, attempt unauthorized access or use its content to mislead others.</p><h2>Product information</h2><p>App descriptions are provided to help you understand the collection. Availability, features and compatibility can change between app versions and devices. Confirm current details with the applicable app store or our support team.</p><h2>Separate app terms</h2><p>These terms cover the website. They do not replace app-specific terms, privacy policies, store terms, subscription conditions or purchase agreements.</p><h2>Content and ownership</h2><p>Website branding and original content belong to their respective owners. Browsing this website does not transfer intellectual property rights. Third-party names and formats identify their respective products.</p><h2>External services</h2><p>Links to app stores or other services lead to independent providers. Their content, availability and terms are controlled by those providers.</p><h2>Availability and limitations</h2><p>We aim to keep information useful and the website accessible, but cannot guarantee uninterrupted availability or compatibility with every device. Nothing in these terms removes rights or protections provided by applicable law.</p><h2>Contact and changes</h2><p>Questions about these terms can be sent to <a href="mailto:{EMAIL}">{EMAIL}</a>. We may update these terms as the website changes.</p></article>'''
write_page("terms/", "Terms of use", "Read the terms for browsing and using the SAVE SUPPLIERS website.", terms)

write_page("404.html", "Page not found", "The page you requested could not be found.", f'<section class="error-page wrap"><span class="eyebrow">A small detour</span><h1>404</h1><h2>This page isn’t here.</h2><p>The link may have changed. Explore our apps or head back to the homepage.</p><div class="actions"><a class="btn" href="{U()}">Back to home</a><a class="btn secondary" href="{U("apps/")}">Explore apps</a></div></section>', active="none", noindex=True)
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
if origin:
    sitemap += '\n'.join(f'<url><loc>{E(origin + "/" + route)}</loc></url>' for route in routes)
sitemap += '\n</urlset>\n'
(dist / "sitemap.xml").write_text(sitemap, encoding="utf-8")
robots = f'User-agent: *\nDisallow: {base}\n' if not origin else f'User-agent: *\nAllow: {base}\nSitemap: {origin}/sitemap.xml\n'
(dist / "robots.txt").write_text(robots, encoding="utf-8")
(dist / "build-info.json").write_text(json.dumps({"base": base, "portable": args.portable, "siteUrl": origin, "routes": routes, "appCount": len(apps)}, indent=2), encoding="utf-8")
print(f"Built {len(routes)} pages + 404, {len(apps)} apps, base {base}")
if not origin:
    print("Local preview build: noindex enabled. Provide --site-url for production SEO.")
