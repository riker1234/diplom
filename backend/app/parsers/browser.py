import atexit
import logging
import threading
from playwright.sync_api import sync_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_pw = None
_browser: Browser | None = None

_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = {runtime: {}};
"""

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _get_browser() -> Browser:
    global _pw, _browser
    with _lock:
        if _browser is None:
            logger.info("browser.py: starting sync_playwright...")
            _pw = sync_playwright().start()
            logger.info("browser.py: launching chromium...")
            _browser = _pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            logger.info("browser.py: chromium launched OK")
            atexit.register(_shutdown)
    return _browser


def _shutdown():
    global _pw, _browser
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
        _browser = None
    if _pw:
        try:
            _pw.stop()
        except Exception:
            pass
        _pw = None


def new_context() -> BrowserContext:
    ctx = _get_browser().new_context(
        user_agent=_UA,
        locale="ru-RU",
        viewport={"width": 1920, "height": 1080},
    )
    ctx.add_init_script(_STEALTH_JS)
    return ctx
