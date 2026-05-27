"""Centralised logging setup for the HCM Self-Service Assistant.

Call `setup_logging()` once at process start (main.py / streamlit_app.py).
Every module then does:

    import logging
    _log = logging.getLogger("hcm_agent.<module_name>")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Log file location ──────────────────────────────────────────────
_LOG_DIR  = Path(__file__).resolve().parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "hcm_assistant.log"

_FMT = "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO, console: bool = True) -> logging.Logger:
    """Configure root logger with a rotating file handler and optional console handler.

    Args:
        level:   Logging level (default INFO). Use logging.DEBUG for maximum detail.
        console: If True, also stream to stdout.

    Returns:
        The root ``hcm_agent`` logger.
    """
    _LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger("hcm_agent")
    if root.handlers:
        # Already configured — don't add duplicate handlers (Streamlit hot-reload)
        return root

    root.setLevel(level)
    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # ── Rotating file handler (10 MB × 3 backups) ──────────────────
    fh = RotatingFileHandler(
        _LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    # ── Console handler ────────────────────────────────────────────
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        root.addHandler(ch)

    # ── Silence noisy third-party libraries ───────────────────────
    for noisy in ("httpx", "httpcore", "openai", "urllib3", "watchdog"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root.info("=" * 60)
    root.info("HCM Self-Service Assistant — logging initialised")
    root.info(f"Log file : {_LOG_FILE}")
    root.info("=" * 60)

    return root
