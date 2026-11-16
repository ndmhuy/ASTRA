"""Bounded independent jobs with stable output ordering and cancellation cleanup."""

import asyncio


async def run_bounded(items, work, limit):
    if limit == 1:
        return [await work(item) for item in items]
    semaphore = asyncio.Semaphore(limit)

    async def invoke(item):
        async with semaphore:
            return await work(item)

    tasks = [asyncio.create_task(invoke(item)) for item in items]
    try:
        return await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
