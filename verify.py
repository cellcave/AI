"""Check the generated pages and all internal links without external dependencies."""
import json
import argparse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--qa', action='store_true')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parent / (".qa-dist" if args.qa else "dist")
info = json.loads((ROOT / "build-info.json").read_text(encoding="utf-8"))
BASE = info["base"]
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []
        self.ids = []
        self.h1 = 0
        self.title = False
        self.description = False
        self.viewport = False
        self.canonical = ""
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1": self.h1 += 1
        if tag == "title": self.title = True
        if tag == "meta":
            if attrs.get("name") == "description": self.description = bool(attrs.get("content"))
            if attrs.get("name") == "viewport": self.viewport = True
        if tag == "link" and attrs.get("rel") == "canonical": self.canonical = attrs["href"]
        for attr in ("href", "src"):
            if attrs.get(attr): self.urls.append(attrs[attr])

pages = list(ROOT.rglob("*.html"))
for file in pages:
    p = Page()
    p.feed(file.read_text(encoding="utf-8"))
    label = str(file.relative_to(ROOT))
    if p.h1 != 1: errors.append(f"{label}: expected one h1")
    if not all((p.title, p.description, p.viewport)): errors.append(f"{label}: incomplete head metadata")
    if len(set(p.ids)) != len(p.ids): errors.append(f"{label}: duplicate IDs")
    if info['siteUrl'] and not p.canonical: errors.append(f"{label}: missing canonical")
    for value in p.urls:
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc: continue
        if not parsed.path:
            if parsed.fragment and parsed.fragment not in p.ids: errors.append(f"{label}: missing anchor {value}")
            continue
        if not parsed.path.startswith('/') and info.get('portable'):
            target = (file.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT.resolve()):
                errors.append(f'{label}: relative link leaves output directory: {value}')
                continue
            if parsed.path.endswith('/') or target.is_dir(): target = target / 'index.html'
            if not target.is_file(): errors.append(f'{label}: missing relative link: {value}')
            continue
        if not parsed.path.startswith(BASE):
            errors.append(f"{label}: URL escapes base path: {value}")
            continue
        rel = unquote(parsed.path[len(BASE):])
        target = ROOT / rel
        if parsed.path.endswith("/") or target.is_dir(): target = target / "index.html"
        if not target.is_file(): errors.append(f"{label}: missing file {value}")
tree = ET.parse(ROOT / "sitemap.xml")
locs = tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
if info["siteUrl"] and len(locs) != len(info["routes"]): errors.append("Sitemap page count mismatch")
if not (ROOT / ".nojekyll").exists(): errors.append("Missing .nojekyll")
if errors:
    raise SystemExit("\n".join(errors))
print(f"PASS: {len(pages)} pages; internal links, assets, headings, metadata, anchors and sitemap. Base: {BASE}")
