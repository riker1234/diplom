"""
Remove accessory products (detachable mics, headset mics, etc.) from the microphone table.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.microphone import Microphone

EXCLUDE_KEYWORDS = ["съёмный", "сменный", "для гарнитур", "для наушник"]

def main():
    db = SessionLocal()
    to_delete = db.query(Microphone).all()
    deleted = 0
    for mic in to_delete:
        name_lower = (mic.name or "").lower()
        if any(kw.lower() in name_lower for kw in EXCLUDE_KEYWORDS):
            print(f"  deleting [{mic.id}] {mic.name}")
            db.delete(mic)
            deleted += 1
    db.commit()
    db.close()
    print(f"\nDone. Deleted {deleted} records.")

if __name__ == "__main__":
    main()
