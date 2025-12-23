from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

NEWS_URL = "https://www.wherewindsmeetgame.com/m/news/"
BASE_URL = "https://www.wherewindsmeetgame.com/"

# simple in-memory cache (good enough)
_cache_data: List[dict] | None = None
_cache_until: float = 0.0

def fetch_wwm_news(limit: int = 6, ttl_seconds: int = 900) -> List[dict]:
    global _cache_data, _cache_until

    now = time.time()
    if _cache_data is not None and now < _cache_until:
        return _cache_data[:limit]

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        r = client.get(NEWS_URL)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Grab links that look like news items.
    # The page lists multiple news entries as links; we filter by typical news URL patterns.
    items: List[dict] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = " ".join(a.get_text(" ", strip=True).split())

        if not text:
            continue

        # Heuristic: news links usually contain "/news/" or go to a news detail page
        if "/news/" not in href and "/m/news/" not in href:
            continue

        url = urljoin(BASE_URL, href)
        items.append({"title": text, "url": url})

    # de-dup by url, preserve order
    seen = set()
    deduped = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        deduped.append(it)

    _cache_data = deduped
    _cache_until = now + ttl_seconds
    return deduped[:limit]
