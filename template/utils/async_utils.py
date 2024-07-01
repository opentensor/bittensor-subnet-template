import asyncio


def get_async_result(coroutine):
    """Sync wrapper to call async coroutine and returns the result."""
    return asyncio.run(coroutine)
