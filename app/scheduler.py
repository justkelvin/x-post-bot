from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    def add_interval_job(self, job_id: str, interval_minutes: int, func, *args, **kwargs) -> None:
        self._scheduler.add_job(
            func,
            "interval",
            minutes=interval_minutes,
            id=job_id,
            replace_existing=True,
            args=args,
            kwargs=kwargs,
            max_instances=1,
            coalesce=True,
        )


scheduler = Scheduler()
