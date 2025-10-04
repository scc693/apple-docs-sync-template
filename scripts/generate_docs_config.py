#!/usr/bin/env python3
"""Generate the Apple documentation sync configuration file.

This helper walks the public Apple Developer sitemaps and emits
`docs-config/apple_urls.txt` entries in the `<url> <output.md>` format used by
`scripts/sync_apple_docs.sh`.

The script defaults to the public sitemap index at
`https://developer.apple.com/sitemap.xml`.  Network access to the Apple domain
is required when pulling the live sitemap.  For offline testing the
`--source` argument (or the `APPLE_DOCS_SITEMAP_SOURCE` environment variable)
can point at a local XML file.

Usage examples::

    # Regenerate the configuration from the live sitemap
    python scripts/generate_docs_config.py

    # Use a cached sitemap bundle for offline testing
    python scripts/generate_docs_config.py --source tests/fixtures/sitemaps/root.xml

"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DEFAULT_SITEMAP = "https://developer.apple.com/sitemap.xml"
DEFAULT_ALLOWED_PREFIXES = (
    "https://developer.apple.com/documentation/",
    "https://developer.apple.com/tutorials/",
    "https://developer.apple.com/design/human-interface-guidelines/",
)
DEFAULT_OUTPUT = Path("docs-config/apple_urls.txt")


class SitemapError(RuntimeError):
    """Raised when the sitemap cannot be parsed or fetched."""


def _is_url(location: str) -> bool:
    return location.startswith("http://") or location.startswith("https://")


def _read_bytes(location: str) -> bytes:
    if _is_url(location):
        req = Request(
            location,
            headers={
                "User-Agent": "apple-docs-sync-config-generator/1.0 (+https://github.com/)"
            },
        )
        with urlopen(req) as response:  # nosec: B310 - URL controlled via CLI/env
            return response.read()
    path = Path(location)
    if not path.exists():
        raise SitemapError(f"Sitemap source not found: {location}")
    return path.read_bytes()


def _iter_xml_text(root: ET.Element, tag_suffix: str) -> Iterator[str]:
    for elem in root.iter():
        if elem.tag.lower().endswith(tag_suffix) and elem.text:
            text = elem.text.strip()
            if text:
                yield text


def _parse_sitemap(location: str) -> Tuple[str, List[str]]:
    try:
        raw = _read_bytes(location)
    except Exception as exc:  # pragma: no cover - surfaced to CLI
        raise SitemapError(f"Failed to fetch {location}: {exc}") from exc

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SitemapError(f"Invalid XML in {location}: {exc}") from exc

    tag = root.tag.lower()
    if tag.endswith("sitemapindex"):
        return "index", list(_iter_xml_text(root, "loc"))
    if tag.endswith("urlset"):
        return "urlset", list(_iter_xml_text(root, "loc"))
    raise SitemapError(f"Unsupported sitemap tag in {location}: {root.tag}")


def _slugify_segment(segment: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", segment.lower()).strip("-")
    return slug or "section"


def _url_to_filename(url: str, existing: Dict[str, int]) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    segments = [_slugify_segment(part) for part in path.split("/") if part]
    if not segments:
        segments = ["index"]
    if parsed.fragment:
        segments.append(_slugify_segment(parsed.fragment))
    stem = "__".join(segments)
    candidate = f"{stem}.md"
    counter = existing.get(candidate, 0)
    if counter:
        while True:
            counter += 1
            candidate = f"{stem}_{counter}.md"
            if candidate not in existing:
                break
    existing[candidate] = counter or 1
    return candidate


def gather_urls(
    source: str,
    allowed_prefixes: Sequence[str],
    visited: set[str] | None = None,
) -> List[str]:
    visited = visited or set()
    if source in visited:
        return []
    visited.add(source)

    kind, entries = _parse_sitemap(source)
    urls: List[str] = []
    if kind == "index":
        for entry in entries:
            urls.extend(gather_urls(entry, allowed_prefixes, visited))
    else:
        for entry in entries:
            if any(entry.startswith(prefix) for prefix in allowed_prefixes):
                urls.append(entry)
    return urls


def build_mapping(urls: Iterable[str]) -> "OrderedDict[str, str]":
    filenames: Dict[str, int] = {}
    mapping: "OrderedDict[str, str]" = OrderedDict()
    for url in sorted(set(urls)):
        mapping[url] = _url_to_filename(url, filenames)
    return mapping


def write_mapping(mapping: "OrderedDict[str, str]", destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for url, filename in mapping.items():
            handle.write(f"{url} {filename}\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=os.environ.get("APPLE_DOCS_SITEMAP_SOURCE", DEFAULT_SITEMAP),
        help="Sitemap index URL or file path (defaults to the live Apple sitemap)",
    )
    parser.add_argument(
        "--allow-prefix",
        action="append",
        dest="allowed_prefixes",
        help="Allow URLs that start with this prefix (can be repeated).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write the docs configuration file",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    prefixes = (
        tuple(args.allowed_prefixes)
        if args.allowed_prefixes
        else DEFAULT_ALLOWED_PREFIXES
    )

    urls = gather_urls(args.source, prefixes)
    if not urls:
        raise SitemapError(
            "No URLs discovered. Check the sitemap source or allowed prefixes."
        )

    mapping = build_mapping(urls)
    write_mapping(mapping, args.output)

    print(
        f"Wrote {len(mapping)} entries to {args.output}",  # noqa: T201 - CLI output
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    try:
        raise SystemExit(main())
    except SitemapError as exc:
        print(f"error: {exc}", file=sys.stderr)  # noqa: T201 - CLI output
        raise SystemExit(1) from exc
