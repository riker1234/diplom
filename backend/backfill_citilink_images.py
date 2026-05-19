"""
Backfill image_url for products that have citilink_url but no image_url.
Uses simple HTTP requests to extract og:image from product pages.
"""
import time
import random
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import httpx
from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_og_image(url: str, client: httpx.Client) -> str | None:
    try:
        r = client.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            return None
        html = r.text
        # og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1)
        # content first (some pages swap attribute order)
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"  error: {e}")
    return None


def main():
    db = SessionLocal()
    total_updated = 0

    with httpx.Client() as client:
        for model in MODELS:
            name = model.__tablename__
            candidates = (
                db.query(model)
                .filter(model.citilink_url.isnot(None), model.image_url.is_(None))
                .all()
            )
            print(f"\n{name}: {len(candidates)} without image")

            for item in candidates:
                img = fetch_og_image(item.citilink_url, client)
                if img:
                    item.image_url = img
                    db.commit()
                    total_updated += 1
                    print(f"  ✓ [{item.id}] {item.name[:50]}")
                else:
                    print(f"  - [{item.id}] no image found")
                time.sleep(random.uniform(0.4, 0.9))

    db.close()
    print(f"\nDone. Updated {total_updated} records.")


if __name__ == "__main__":
    main()
