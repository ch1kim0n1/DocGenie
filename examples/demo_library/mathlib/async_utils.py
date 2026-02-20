"""Async utilities demonstrating async def function capture by DocGenie."""

from __future__ import annotations

import asyncio


async def async_compute(value: int, delay: float = 0.0) -> int:
    """Simulate an async computation with an optional delay.

    Args:
        value: The integer to double.
        delay: Seconds to sleep before returning (default 0).

    Returns:
        value multiplied by 2.
    """
    await asyncio.sleep(delay)
    return value * 2


async def batch_compute(values: list[int]) -> list[int]:
    """Compute values concurrently using asyncio.gather.

    Args:
        values: A list of integers to process.

    Returns:
        A list of results, each element doubled.
    """
    tasks = [async_compute(v) for v in values]
    results = await asyncio.gather(*tasks)
    return list(results)


async def retry(coro_fn: object, retries: int = 3, delay: float = 0.1) -> object:
    """Retry an async coroutine function up to ``retries`` times.

    Args:
        coro_fn: A zero-argument async callable.
        retries: Maximum number of attempts.
        delay: Seconds between attempts.

    Returns:
        The result of the first successful invocation.

    Raises:
        Exception: The last exception if all attempts fail.
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return await coro_fn()  # type: ignore[operator]
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
