"""
utils.py — Shared utilities for the ingestion module.

Provides:
- retry()       — decorator for retrying failed API calls with exponential backoff
- rate_limit()  — decorator for enforcing a minimum gap between API calls
- setup_logger() — factory for consistently configured loggers
"""

import functools
import logging
import time
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

def setup_logger(name: str) -> logging.Logger:
    """Return a logger that emits timestamp, level, and message to stdout.

    Parameters
    ----------
    name:
        Name for the logger — typically ``__name__`` of the calling module.

    Returns
    -------
    logging.Logger
        A configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)
    return logger


_utils_logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# retry decorator
# ---------------------------------------------------------------------------

def retry(max_attempts: int = 3, delay: float = 2.0) -> Callable[[F], F]:
    """Decorator that retries *func* on any exception with exponential backoff.

    The wait time doubles after each failed attempt:
    ``delay``, ``delay * 2``, ``delay * 4``, …

    Parameters
    ----------
    max_attempts:
        Maximum number of times to attempt the function (including the first
        call).  Must be >= 1.
    delay:
        Initial delay in seconds between attempts.  Doubles on each retry.

    Returns
    -------
    Callable
        The decorated function.

    Raises
    ------
    Exception
        Re-raises the last exception if all attempts are exhausted.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            wait = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt < max_attempts:
                        _utils_logger.warning(
                            "Attempt %d/%d failed for '%s': %s — retrying in %.1fs",
                            attempt,
                            max_attempts,
                            func.__qualname__,
                            exc,
                            wait,
                        )
                        time.sleep(wait)
                        wait *= 2
                    else:
                        _utils_logger.error(
                            "All %d attempts failed for '%s': %s",
                            max_attempts,
                            func.__qualname__,
                            exc,
                        )
            raise last_exc  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# rate_limit decorator
# ---------------------------------------------------------------------------

# Module-level state: maps function id → timestamp of last call.
_last_call_times: dict[int, float] = {}


def rate_limit(calls_per_minute: int = 25) -> Callable[[F], F]:
    """Decorator that enforces a minimum interval between successive calls.

    The minimum gap is ``60 / calls_per_minute`` seconds.  If the decorated
    function is called before the gap has elapsed the call blocks (sleeps)
    until the gap is satisfied.

    Parameters
    ----------
    calls_per_minute:
        Maximum number of calls per minute allowed.

    Returns
    -------
    Callable
        The decorated function.
    """
    min_interval = 60.0 / calls_per_minute

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_id = id(func)
            now = time.monotonic()
            last = _last_call_times.get(func_id, 0.0)
            elapsed = now - last
            if elapsed < min_interval:
                sleep_for = min_interval - elapsed
                _utils_logger.debug(
                    "Rate limiting '%s': sleeping %.2fs", func.__qualname__, sleep_for
                )
                time.sleep(sleep_for)
            _last_call_times[func_id] = time.monotonic()
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
