from asyncio import get_event_loop, iscoroutinefunction
from functools import partial


async def await_func(func_or_coro, loop, *args, **kwargs):
    if iscoroutinefunction(func_or_coro):
        return await func_or_coro(*args, **kwargs)
    loop = loop or get_event_loop()
    return await loop.run_in_executor(
        None, partial(func_or_coro, *args, **kwargs)
    )
