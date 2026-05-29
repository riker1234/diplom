import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def _run_all_parsers():
    from app.database import SessionLocal
    from app.parsers.ozon import (
        parse_mice, parse_keyboards, parse_monitors,
        parse_headphones, parse_microphones, parse_mousepads,
    )

    db = SessionLocal()
    jobs = [
        ("mice",        parse_mice),
        ("keyboards",   parse_keyboards),
        ("monitors",    parse_monitors),
        ("headphones",  parse_headphones),
        ("microphones", parse_microphones),
        ("mousepads",   parse_mousepads),
    ]
    try:
        for name, fn in jobs:
            try:
                result = fn(db)
                logger.info("Scheduled parse %s: %s", name, result)
            except Exception as exc:
                logger.error("Scheduled parse %s failed: %s", name, exc)
    finally:
        db.close()


scheduler = BackgroundScheduler(timezone="Europe/Moscow")
scheduler.add_job(
    _run_all_parsers,
    trigger=IntervalTrigger(weeks=1),
    id="weekly_full_parse",
    name="Weekly full re-parse (Ozon)",
    replace_existing=True,
)
