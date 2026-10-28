#!/usr/bin/env python3
"""Dependency-free static checks for the KinderCore landing page."""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "index.html"


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
        self.errors = []

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
        if tag in {"link", "script", "img"}:
            value = attrs.get("href") if tag == "link" else attrs.get("src")
            if value:
                self.references.append((tag, value))
        if tag == "a":
            href = attrs.get("href", "")
            if href.startswith("#") and len(href) > 1:
                self.references.append(("anchor", href[1:]))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text.append(data.strip())


def main():
    errors = []
    if not HTML_FILE.exists():
        print("FAIL: index.html is missing")
        return 1

    parser = SiteParser()
    parser.feed(HTML_FILE.read_text(encoding="utf-8"))

    if parser.lang != "ru":
        errors.append("html lang should be ru")
    if not "".join(parser.title_text).strip():
        errors.append("page title is missing")
    if not parser.description or len(parser.description.strip()) < 50:
        errors.append("meta description is missing or too short")
    if parser.h1_count != 1:
        errors.append(f"expected exactly one h1, found {parser.h1_count}")

    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        errors.append("duplicate id values: " + ", ".join(duplicates))

    for kind, value in parser.references:
        if kind == "anchor":
            if value not in parser.ids:
                errors.append(f"anchor target #{value} does not exist")
            continue
        if value.startswith(("https://", "http://", "data:", "mailto:", "tel:", "//")):
            continue
        local_path = value.split("?", 1)[0].split("#", 1)[0]
        if not local_path:
            continue
        if local_path.startswith("/"):
            target = ROOT / local_path.lstrip("/")
        else:
            target = ROOT / local_path
        if not target.exists():
            errors.append(f"local {kind} reference does not exist: {value}")

    for required in ("styles.css", "script.js", "favicon.svg", "robots.txt"):
        if not (ROOT / required).is_file():
            errors.append(f"required file is missing: {required}")

    if errors:
        print("Static website checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Static website checks passed.")
    print(f"- HTML language: {parser.lang}")
    print(f"- H1 count: {parser.h1_count}")
    print(f"- Unique IDs: {len(set(parser.ids))}")
    print(f"- Local references checked: {len(parser.references)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
