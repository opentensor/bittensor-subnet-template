import asyncio


def get_async_result(cor_func, *args, **kwargs):
    """Sync wrapper to call async coroutine and returns the result."""

    # To avoid the `cannot reuse already awaited coroutine` error, I need to create a new coroutine every time.
    def create_coroutine(cor_func_, *args_, **kwargs_):
        return cor_func_(*args_, **kwargs_)

    return asyncio.run(create_coroutine(cor_func, *args, **kwargs))
