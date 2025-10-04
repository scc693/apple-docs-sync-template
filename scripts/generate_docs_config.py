"""Utilities for building docs-config/apple_urls.txt from sitemaps.

This module provides helpers for crawling sitemap indexes produced by
https://developer.apple.com.  The logic is intentionally written so it can run
in simple execution environments (like GitHub Actions) without requiring any
additional dependencies beyond the Python standard library.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Set
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import gzip
import xml.etree.ElementTree as ET

__all__ = ["SitemapError", "gather_urls"]


@dataclass
class SitemapError(Exception):
    """Raised when a sitemap cannot be retrieved or parsed."""

    message: str
    url: str | None = None

    def __str__(self) -> str:  # pragma: no cover - delegating to base.
        if self.url:
            return f"{self.message} ({self.url})"
        return self.message


def _read_bytes(source: str | Path, *, timeout: int | float = 10) -> bytes:
    """Return the raw bytes for *source*.

    The helper accepts both HTTP(S) URLs and local file system paths.  When the
    payload is compressed with gzip (detected via response headers, the file
    suffix, or the gzip magic number) the bytes are inflated before being
    returned.  Errors are wrapped in :class:`SitemapError` with a helpful URL
    for debugging purposes.
    """

    def _decompress_if_needed(raw: bytes, *, headers: dict[str, str] | None = None) -> bytes:
        if not raw:
            return raw

        is_gzip = False
        lower_source = str(source).lower()
        if lower_source.endswith(".gz"):
            is_gzip = True
        if headers:
            encoding = headers.get("Content-Encoding", "").lower()
            if "gzip" in encoding:
                is_gzip = True
            content_type = headers.get("Content-Type", "").lower()
            if "gzip" in content_type or "application/x-gzip" in content_type:
                is_gzip = True
        if raw.startswith(b"\x1f\x8b"):
            is_gzip = True

        if not is_gzip:
            return raw

        try:
            return gzip.decompress(raw)
        except OSError as exc:  # pragma: no cover - defensive guard.
            raise SitemapError("Failed to decompress gzip payload", str(source)) from exc

    parsed = urlparse(str(source))
    try:
        if parsed.scheme in ("", "file"):
            path = Path(parsed.path if parsed.scheme else source)
            data = path.read_bytes()
            return _decompress_if_needed(data)

        request = Request(str(source), headers={"User-Agent": "apple-docs-sync/1.0"})
        with urlopen(request, timeout=timeout) as response:  # type: ignore[call-arg]
            raw = response.read()
            headers = {k: v for k, v in response.headers.items()}  # type: ignore[attr-defined]
            return _decompress_if_needed(raw, headers=headers)
    except FileNotFoundError as exc:
        raise SitemapError("Unable to locate sitemap", str(source)) from exc
    except Exception as exc:  # pragma: no cover - network errors vary.
        raise SitemapError("Unable to download sitemap", str(source)) from exc


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_sitemap(data: bytes, *, base_url: str | None = None) -> tuple[str, List[str]]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:  # pragma: no cover - defensive guard.
        raise SitemapError("Unable to parse sitemap XML", base_url) from exc

    tag = _strip_namespace(root.tag)

    if tag == "sitemapindex":
        locs: List[str] = []
        for sitemap in root.findall(".//{*}loc"):
            if sitemap.text:
                loc = sitemap.text.strip()
                if base_url:
                    loc = urljoin(base_url, loc)
                locs.append(loc)
        return "index", locs

    if tag == "urlset":
        urls: List[str] = []
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                text = loc.text.strip()
                if base_url:
                    text = urljoin(base_url, text)
                urls.append(text)
        return "urlset", urls

    raise SitemapError("Unsupported sitemap format", base_url)


def gather_urls(start: str | Path) -> List[str]:
    """Return all URLs reachable from a sitemap or sitemap index."""

    to_visit: List[str | Path] = [start]
    visited: Set[str | Path] = set()
    discovered: Set[str] = set()

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)

        data = _read_bytes(current)
        base_url = str(current)
        sitemap_type, items = _parse_sitemap(data, base_url=base_url)
        if sitemap_type == "index":
            to_visit.extend(items)
        else:
            discovered.update(items)

    return sorted(discovered)
