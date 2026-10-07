"""Dependency-free static website generator. Python 3.10+."""
import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
parser = argparse.ArgumentParser()
parser.add_argument("--base", default="/", help="/ for user sites; /repo-name/ for project sites")
parser.add_argument("--site-url", default=None, help="Full public site URL, including repo path")
args = parser.parse_args()
base = "/" + args.base.strip("/") + "/" if args.base.strip("/") else "/"
if not re.fullmatch(r"/(?:[A-Za-z0-9._-]+/)*", base):
    raise SystemExit("Base path must consist of URL-safe path segments")
site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
apps = json.loads((SRC / "apps.json").read_text(encoding="utf-8"))
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
    for field in ("storeUrl", "privacyUrl"):
        if app.get(field) and urlparse(app[field]).scheme != "https":
            raise SystemExit(f"{app['id']}: {field} must be an HTTPS URL")
dist = ROOT / "dist"
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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(fulltitle)}</title><meta name="description" content="{E(description)}"><meta name="robots" content="{robots}"><meta name="theme-color" content="#101311"><meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}"><meta property="og:title" content="{E(fulltitle)}"><meta property="og:description" content="{E(description)}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{E(fulltitle)}"><meta name="twitter:description" content="{E(description)}">{canonical}<link rel="icon" type="image/svg+xml" href="{U('assets/favicon.svg')}"><link rel="stylesheet" href="{U('assets/site.css')}"><script src="{U('assets/site.js')}" defer></script><script type="application/ld+json">{structured}</script></head><body>{header(active if active is not None else route)}<main id="main" tabindex="-1">{body}</main>{footer()}</body></html>'''
    path = dist / route / "index.html" if route else dist / "index.html"
    if route == "404.html":
        path = dist / route
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if not noindex:
        routes.append(route)

def app_icon(app):
    return f'<span class="app-icon {E(app["color"])}">{icon(app["icon"])}</span>'

def card(app):
    search = E((app["name"] + " " + app["description"] + " " + app["category"]).lower())
    return f'''<article class="app-card" data-app="{E(app['id'])}" data-category="{E(app['category'])}" data-search="{search}"><div class="card-top">{app_icon(app)}<span class="tag">{E(app['category'])}</span></div><h3><a href="{U('apps/' + app['id'] + '/')}">{E(app['name'])}</a></h3><p>{E(app['description'])}</p><div class="card-bottom"><span>{E(app['platform'])}</span><a href="{U('apps/' + app['id'] + '/')}">Explore app<span class="sr-only">: {E(app['name'])}</span></a></div></article>'''

def page_top(label, title, description):
    return f'<section class="page-top"><div class="wrap"><span class="eyebrow">{label}</span><h1>{title}</h1><p>{description}</p></div></section>'

def cta():
    return f'<section class="section"><div class="wrap"><div class="cta"><div><h2>Let’s make the everyday easier.</h2><p>Questions about an app? We’re here to help.</p></div><a class="btn" href="{U("contact/")}">Contact us</a></div></div></section>'

featured = apps[0] if apps else None
panel = ""
if featured:
    panel = f'''<article class="product-panel" aria-label="Featured app: {E(featured['name'])}"><div class="panel-top"><span>In the spotlight</span><span>{E(featured['platform'])}</span></div><div class="panel-icon">{icon(featured['icon'])}</div><h2 class="panel-title">{E(featured['name'])}.</h2><p>{E(featured['description'])}</p><div class="formats">{''.join(f'<span class="format">{E(x)}</span>' for x in featured['formats'][:4])}</div><div class="panel-bottom"><span>{E(featured['category'])}</span><a href="{U('apps/' + featured['id'] + '/')}">Meet the app</a></div></article>'''
home = f'''<section class="hero"><div class="wrap hero-grid"><div><span class="eyebrow">Everyday software, thoughtfully simple</span><h1>Small tools.<br><span>Better days.</span></h1><p class="lead">From reading a document to keeping a personal routine, discover apps built around the things you do every day.</p><div class="actions"><a class="btn" href="{U('apps/')}">Explore our apps</a><a class="text-link" href="{U('about/')}">Meet SAVE SUPPLIERS</a></div><p class="micro">Practical Android apps. A clear purpose.</p></div>{panel}</div></section><div class="wrap strip"><div><span>01 /</span> Useful by design</div><div><span>02 /</span> Made for everyday moments</div><div><span>03 /</span> Support within reach</div></div><section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Our apps</span><h2>A little less effort.<br>A little more done.</h2></div><a class="text-link" href="{U('apps/')}">View all apps</a></div><div class="app-grid">{''.join(card(app) for app in apps[:2])}</div></div></section><section class="section band"><div class="wrap split"><div><span class="eyebrow">The SAVE SUPPLIERS approach</span><h2>Keep the purpose clear.<br>Keep life moving.</h2><p>Useful software starts with an ordinary task. We focus on making that task easier to understand, easier to start and easier to return to.</p><a class="text-link" href="{U('about/')}">More about us</a></div><ul class="rule-list"><li><strong>Everyday usefulness</strong>Tools for reading, organizing and personal routines.</li><li><strong>Information you can find</strong>Product details and support, without the search.</li><li><strong>A direct conversation</strong>A clear route to contact us when you need help.</li></ul></div></section>{cta()}'''
write_page("", "Practical apps for everyday life", site["description"], home)

categories = list(dict.fromkeys(app["category"] for app in apps))
filters = ''.join(f'<button type="button" data-filter="{E(cat)}" aria-pressed="{str(cat == "All").lower()}">{E(cat)}</button>' for cat in ["All"] + categories)
catalog = page_top("Our app collection", "Find your everyday companion.", "Explore practical apps for documents, daily routines and the moments in between.") + f'''<section class="catalog"><div class="wrap"><div class="catalog-tools"><label class="search-field" for="app-search">{icon('search')}<span class="sr-only">Search apps</span><input id="app-search" type="search" placeholder="Search apps" autocomplete="off"></label><div class="filters" role="group" aria-label="Filter apps by category">{filters}</div></div><p class="result-count" id="app-count" aria-live="polite">{len(apps)} apps</p><div class="app-grid">{''.join(card(app) for app in apps)}</div><div class="empty" id="empty-apps" hidden><h2>No apps found</h2><p>Try a different search or select All.</p></div></div></section>'''
write_page("apps/", "Our apps", "Browse the SAVE SUPPLIERS Android app catalog and explore product features.", catalog)

for app in apps:
    detail_url = 'apps/' + app['id'] + '/'
    primary = f'<a class="btn" href="{E(app["storeUrl"])}" rel="noopener noreferrer" target="_blank">View on Google Play<span class="sr-only"> (opens in a new tab)</span></a>' if app.get("storeUrl") else f'<a class="btn" href="{U("contact/")}">Ask about this app</a>'
    privacy = f'<a class="text-link" href="{E(app["privacyUrl"])}">App privacy policy</a>' if app.get("privacyUrl") else ""
    features = ''.join(f'<article class="feature"><span class="number">0{i+1}</span><h3>{E(f["title"])}</h3><p>{E(f["text"])}</p></article>' for i, f in enumerate(app["features"]))
    format_tags = ''.join('<span class="format">' + E(fmt) + '</span>' for fmt in app["formats"])
    formats = f'<section class="section band"><div class="wrap split"><div><span class="eyebrow">Supported formats</span><h2>More files.<br>One reading routine.</h2></div><div class="formats">{format_tags}</div></div></section>' if app["formats"] else ""
    body = f'''<section class="page-top"><div class="wrap"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{U()}">Home</a><span aria-hidden="true">/</span><a href="{U('apps/')}">Apps</a><span aria-hidden="true">/</span><span aria-current="page">{E(app['name'])}</span></nav><div class="detail-hero"><div><span class="eyebrow">{E(app['category'])} · {E(app['platform'])}</span><h1>{E(app['name'])}</h1><p>{E(app['intro'])}</p><div class="actions">{primary}{privacy}</div></div><aside class="detail-summary" aria-label="App overview">{app_icon(app)}<h2>{E(app['name'])}</h2><dl><div><dt>Platform</dt><dd>{E(app['platform'])}</dd></div><div><dt>Category</dt><dd>{E(app['category'])}</dd></div><div><dt>Questions?</dt><dd><a href="{U('contact/')}">Contact us</a></dd></div></dl></aside></div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">What you can do</span><h2>Built around your routine.</h2></div></div><div class="grid3">{features}</div><div class="notice"><p>{E(app['note'])}</p></div></div></section>{formats}{cta()}'''
    write_page(detail_url, app['name'], app['description'], body, active="apps/")

about = page_top("About SAVE SUPPLIERS", "Useful software.<br>A clear purpose.", "We build our app collection around everyday tasks, with product information and support close at hand.") + f'''<section class="section band"><div class="wrap split"><div><p class="about-statement">A document to read.<br>A routine to keep.<br>One less thing in your way.</p></div><div><h2>Start with the everyday.</h2><p>Our collection brings together document tools and personal tracking apps. Each app has its own purpose, explained on its product page so you can decide whether it fits your needs.</p><p>We believe the information around an app matters too. That’s why this website keeps product details, contact information and website policies easy to find.</p><a class="text-link" href="{U('apps/')}">Explore the collection</a></div></div></section>{cta()}'''
write_page("about/", "About us", "Learn about SAVE SUPPLIERS and our approach to practical everyday apps.", about)

contact = page_top("Contact &amp; support", "Let’s talk.", "Have a question, feedback or a support request? Tell us which app you’re using and how we can help.") + f'''<div class="wrap contact-layout"><div><div class="contact-card"><h2>A direct line to us.</h2><p>Email our team with your question.</p><a class="email" href="mailto:{EMAIL}">{EMAIL}</a></div><div class="contact-card"><h2>Help us help you.</h2><p>For app support, include the app name, your device model and a short description of the issue.</p><p>Please leave out passwords, payment details and private documents.</p></div></div><form class="contact-form" id="contact-form" data-email="{EMAIL}"><div class="form-row"><div class="field"><label for="contact-name">Your name</label><input id="contact-name" name="name" required maxlength="120" autocomplete="name"></div><div class="field"><label for="contact-email">Your email</label><input id="contact-email" name="email" type="email" required maxlength="254" autocomplete="email"></div></div><div class="field"><label for="contact-subject">What’s this about?</label><select id="contact-subject" name="subject"><option>General question</option>App support</option>Feedback</option><option>Privacy question</option></select></div><div class="field"><label for="contact-message">Your message</label><textarea id="contact-message" name="message" required minlength="10" maxlength="4000" placeholder="Tell us a little about your question…"></textarea></div><button class="btn" type="submit">Create email draft</button><p class="form-help">This opens a draft in your email app. Nothing is sent until you send the email.</p><p class="form-status" id="contact-status" role="status"></p><a class="text-link" id="email-draft" hidden>Open your email draft</a><noscript><p>To contact us, email <a href="mailto:{EMAIL}">{EMAIL}</a> directly.</p></noscript></form></div>'''
contact = contact.replace('<option>App support</option>Feedback</option>', '<option>App support</option><option>Feedback</option>')
write_page("contact/", "Contact & support", "Contact SAVE SUPPLIERS with app questions, feedback or privacy inquiries.", contact)

privacy = page_top("Website policy", "Privacy, explained.", "This policy describes this website. Individual mobile apps may have their own privacy policies.") + f'''<article class="wrap prose"><p>Last updated: 6 October 2026</p><h2>Information on this website</h2><p>This is a static informational website. It does not require an account, accept payments, store contact-form entries, or include advertising or analytics scripts.</p><h2>When you contact us</h2><p>The contact form prepares an email draft on your device. The website does not submit your message to a server. If you send the email, we receive the information you include, such as your name, email address and message, and use it to handle your inquiry.</p><h2>Hosting and technical information</h2><p>The hosting provider may process technical information such as IP addresses and request logs to deliver the website, maintain security and operate its service. These activities are subject to the provider’s own policies.</p><h2>Cookies and local storage</h2><p>The website code does not set cookies or use browser storage. External websites and services you choose to visit may follow different practices.</p><h2>External links and mobile apps</h2><p>App stores and other linked services operate under their own privacy terms. This website policy does not describe how a mobile app processes data. Review the relevant app’s privacy information before using it; contact us if you need help locating it.</p><h2>Your requests</h2><p>To ask about personal information you shared by email, request a correction or deletion, or raise a privacy question, contact <a href="mailto:{EMAIL}">{EMAIL}</a>.</p><h2>Updates</h2><p>We may update this policy when website features or practices change. The date above identifies the current version.</p></article>'''
write_page("privacy/", "Website privacy", "Read how the SAVE SUPPLIERS website handles contact inquiries and technical information.", privacy)

terms = page_top("Website terms", "A few clear essentials.", "These terms apply to use of the SAVE SUPPLIERS website and its informational content.") + f'''<article class="wrap prose"><p>Last updated: 6 October 2026</p><h2>Using the website</h2><p>You may browse this website and use its contact information for legitimate inquiries. Do not interfere with its operation, attempt unauthorized access or use its content to mislead others.</p><h2>Product information</h2><p>App descriptions are provided to help you understand the collection. Availability, features and compatibility can change between app versions and devices. Confirm current details with the applicable app store or our support team.</p><h2>Separate app terms</h2><p>These terms cover the website. They do not replace app-specific terms, privacy policies, store terms, subscription conditions or purchase agreements.</p><h2>Content and ownership</h2><p>Website branding and original content belong to their respective owners. Browsing this website does not transfer intellectual property rights. Third-party names and formats identify their respective products.</p><h2>External services</h2><p>Links to app stores or other services lead to independent providers. Their content, availability and terms are controlled by those providers.</p><h2>Availability and limitations</h2><p>We aim to keep information useful and the website accessible, but cannot guarantee uninterrupted availability or compatibility with every device. Nothing in these terms removes rights or protections provided by applicable law.</p><h2>Contact and changes</h2><p>Questions about these terms can be sent to <a href="mailto:{EMAIL}">{EMAIL}</a>. We may update these terms as the website changes.</p></article>'''
write_page("terms/", "Terms of use", "Read the terms for browsing and using the SAVE SUPPLIERS website.", terms)

write_page("404.html", "Page not found", "The page you requested could not be found.", f'<section class="error-page wrap"><span class="eyebrow">A small detour</span><h1>404</h1><h2>This page isn’t here.</h2><p>The link may have changed. Explore our apps or head back to the homepage.</p><div class="actions"><a class="btn" href="{U()}">Back to home</a><a class="btn secondary" href="{U("apps/")}">Explore apps</a></div></section>', active="none", noindex=True)
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
if origin:
    sitemap += '\n'.join(f'<url><loc>{E(origin + "/" + route)}</loc></url>' for route in routes)
sitemap += '\n</urlset>\n'
(dist / "sitemap.xml").write_text(sitemap, encoding="utf-8")
robots = f'User-agent: *\nDisallow: {base}\n' if not origin else f'User-agent: *\nAllow: {base}\nSitemap: {origin}/sitemap.xml\n'
(dist / "robots.txt").write_text(robots, encoding="utf-8")
(dist / "build-info.json").write_text(json.dumps({"base": base, "siteUrl": origin, "routes": routes, "appCount": len(apps)}, indent=2), encoding="utf-8")
print(f"Built {len(routes)} pages + 404, {len(apps)} apps, base {base}")
if not origin:
    print("Local preview build: noindex enabled. Provide --site-url for production SEO.")
