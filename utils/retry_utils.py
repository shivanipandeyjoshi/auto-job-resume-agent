from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def retry(max_attempts: int = 3, delay_seconds: float = 0.5):
    """Retry a function a limited number of times when it raises."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - exercised indirectly
                    last_error = exc
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay_seconds)
            if last_error is not None:
                raise last_error
            raise RuntimeError("retry failed")

        return wrapper  # type: ignore[return-value]

    return decorator
