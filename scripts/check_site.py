#!/usr/bin/env python3
"""Dependency-free static checks for all KinderCore website pages."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ("styles.css", "script.js", "favicon.svg", "robots.txt", "sitemap.xml", "functions/api/analytics.js")
REQUIRED_PAGES = ("index.html", "partners/index.html", "en/index.html", "en/partners/index.html", "privacy.html")


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.references = []
        self.title_text = []
        self.in_title = False
        self.lang = None
        self.description = None
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content", "")
        if tag in {"link", "script", "img", "a"}:
            value = attrs.get("href") if tag in {"link", "a"} else attrs.get("src")
            if value:
                self.references.append((tag, value))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text.append(data.strip())


def page_file(path):
    if not path or path == "/":
        return ROOT / "index.html"
    target = ROOT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    return target


def main():
    errors = []
    for required in REQUIRED_FILES:
        if not (ROOT / required).is_file():
            errors.append(f"required file is missing: {required}")
    analytics_source = (ROOT / "functions/api/analytics.js").read_text(encoding="utf-8") if (ROOT / "functions/api/analytics.js").is_file() else ""
    if 'env.ANALYTICS_ENABLED !== "true"' not in analytics_source:
        errors.append("analytics endpoint must remain disabled unless ANALYTICS_ENABLED=true")
    for required in REQUIRED_PAGES:
        if not (ROOT / required).is_file():
            errors.append(f"required page is missing: {required}")

    pages = sorted(ROOT.rglob("*.html"))
    parsed = {}
    for file_path in pages:
        relative = file_path.relative_to(ROOT).as_posix()
        parser = SiteParser()
        parser.feed(file_path.read_text(encoding="utf-8"))
        parsed[relative] = parser
        expected_lang = "en" if relative.startswith("en/") else "ru"
        if parser.lang != expected_lang:
            errors.append(f"{relative}: html lang should be {expected_lang}")
        if not "".join(parser.title_text).strip():
            errors.append(f"{relative}: page title is missing")
        if not parser.description or len(parser.description.strip()) < 40:
            errors.append(f"{relative}: meta description is missing or too short")
        if parser.h1_count != 1:
            errors.append(f"{relative}: expected exactly one h1, found {parser.h1_count}")
        duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if duplicates:
            errors.append(f"{relative}: duplicate id values: " + ", ".join(duplicates))

    for relative, parser in parsed.items():
        for kind, value in parser.references:
            if value.startswith(("https://", "http://", "mailto:", "tel:", "data:", "//")):
                continue
            parts = urlsplit(value)
            target = (page_file(parts.path) if parts.path else ROOT / relative) if kind == "a" else (ROOT / parts.path.lstrip("/"))
            if parts.path and not target.exists():
                errors.append(f"{relative}: local {kind} reference does not exist: {value}")
                continue
            if parts.fragment:
                if kind == "a":
                    target_rel = target.relative_to(ROOT).as_posix()
                    target_parser = parsed.get(target_rel)
                else:
                    target_parser = parser if not parts.path else None
                if target_parser and parts.fragment not in target_parser.ids:
                    errors.append(f"{relative}: anchor target #{parts.fragment} does not exist in {target_rel if kind == 'a' else relative}")

    if errors:
        print("Static website checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Static website checks passed.")
    print(f"- HTML pages checked: {len(parsed)}")
    print(f"- Required pages present: {len(REQUIRED_PAGES)}")
    print(f"- Local references checked: {sum(len(p.references) for p in parsed.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
