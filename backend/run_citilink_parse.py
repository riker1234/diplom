"""Run full Citilink parse for all categories directly (no HTTP timeout)."""
import sys
import logging
sys.path.insert(0, r"C:\Users\User\Desktop\diplom\backend")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("citilink_parse.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("run_citilink_parse")

from app.database import SessionLocal
from app.parsers.citilink import (
    parse_mice,
    parse_keyboards,
    parse_monitors,
    parse_headphones,
    parse_microphones,
    parse_mousepads,
)

CATEGORIES = [
    ("mice", parse_mice),
    ("keyboards", parse_keyboards),
    ("monitors", parse_monitors),
    ("headphones", parse_headphones),
    ("microphones", parse_microphones),
    ("mousepads", parse_mousepads),
]

db = SessionLocal()
try:
    for name, fn in CATEGORIES:
        logger.info("=== Parsing %s ===", name)
        result = fn(db)
        logger.info("=== %s done: %s ===", name, result)
finally:
    db.close()

logger.info("All done.")
