#!/usr/bin/env python3
"""Dependency-free static checks for every public KinderCore HTML page."""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_PREFIXES = ("https://", "http://", "data:", "mailto:", "tel:", "//")


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.references = []
        self.title = []
        self.in_title = False
        self.lang = None
        self.description = None
        self.h1_count = 0
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                self.errors.append(f"duplicate id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content", "")
        if tag in {"link", "script", "img"}:
            value = attrs.get("href") if tag == "link" else attrs.get("src")
            if value:
                self.references.append((tag, value))
        if tag == "a":
            href = attrs.get("href", "")
            if href:
                self.references.append(("anchor", href))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data.strip())


def resolve_local(source, value):
    clean = value.split("?", 1)[0].split("#", 1)[0]
    if not clean:
        return source
    target = ROOT / clean.lstrip("/") if clean.startswith("/") else (source.parent / clean)
    if target.is_dir():
        target = target / "index.html"
    return target.resolve()


def main():
    errors = []
    pages = sorted(ROOT.rglob("*.html"))
    if not pages:
        print("FAIL: no HTML pages found")
        return 1

    parsed_pages = {}
    for page in pages:
        parser = SiteParser()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{page.relative_to(ROOT)}: cannot parse HTML: {exc}")
            continue
        parsed_pages[page.resolve()] = parser
        relative = page.relative_to(ROOT).as_posix()
        if not parser.lang:
            errors.append(f"{relative}: html lang is missing")
        if not "".join(parser.title).strip():
            errors.append(f"{relative}: title is missing")
        if not parser.description or len(parser.description.strip()) < 40:
            errors.append(f"{relative}: meta description is missing or too short")
        if parser.h1_count != 1:
            errors.append(f"{relative}: expected exactly one h1, found {parser.h1_count}")
        errors.extend(f"{relative}: {item}" for item in parser.errors)

    for page, parser in parsed_pages.items():
        relative = page.relative_to(ROOT).as_posix()
        for kind, value in parser.references:
            if value.startswith(EXTERNAL_PREFIXES):
                continue
            target = resolve_local(page, value)
            if not target.exists():
                errors.append(f"{relative}: broken local {kind} reference: {value}")
                continue
            if kind == "anchor" and "#" in value:
                fragment = value.split("#", 1)[1]
                target_parser = parsed_pages.get(target)
                if target_parser and fragment and fragment not in target_parser.ids:
                    errors.append(f"{relative}: missing anchor target {value}")

    for required in ("styles.css", "script.js", "favicon.svg", "robots.txt", "sitemap.xml"):
        if not (ROOT / required).is_file():
            errors.append(f"required file is missing: {required}")

    if errors:
        print("Static website checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Static website checks passed.")
    print(f"- HTML pages: {len(parsed_pages)}")
    print("- Every page has a language, title, description and exactly one H1")
    print("- Local assets, navigation links and in-page anchors checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
