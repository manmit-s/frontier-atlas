import logging
import sys
from typing import Any, Dict

def setup_logger(name: str = "pipeline", level: int = logging.INFO) -> logging.Logger:
    """Configures a compact, structured console logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger

logger = setup_logger()

def log_task_metric(
    category: str,
    action: str,
    url: str,
    status: str,
    latency_ms: float = 0.0,
    details: str = ""
) -> None:
    """Logs compact telemetry for a crawling/extraction event without raw data dumping."""
    msg = f"[{category.upper()}] {action.upper()} | status={status} | latency={latency_ms:.1f}ms | url={url}"
    if details:
        # Enforce strict character boundary to keep log output compact
        bounded_details = details[:120] + ("..." if len(details) > 120 else "")
        msg += f" | {bounded_details}"
    logger.info(msg)
