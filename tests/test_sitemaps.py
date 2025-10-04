from __future__ import annotations

import gzip
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_docs_config import SitemapError, gather_urls


def test_gather_urls_accepts_compressed_sitemap(tmp_path):
    source = ROOT / "tests" / "fixtures" / "sitemaps" / "urlset.xml"
    target = tmp_path / "compressed-urlset.xml.gz"
    target.write_bytes(gzip.compress(source.read_bytes(), mtime=0))

    try:
        urls = gather_urls(target)
    except SitemapError as exc:  # pragma: no cover - the regression guard
        pytest.fail(f"gather_urls raised SitemapError: {exc}")

    assert "https://example.com/docs/intro" in urls
