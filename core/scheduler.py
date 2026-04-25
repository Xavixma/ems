import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class EmsScheduler:
    def __init__(self, energy_manager, poll_interval_s: int):
        self._energy_manager = energy_manager
        self._poll_interval_s = poll_interval_s
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.add_job(
            self._energy_manager.tick,
            trigger=IntervalTrigger(seconds=self._poll_interval_s),
            id="ems_tick",
            name="EMS polling tick",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("EMS scheduler started — polling every %ds", self._poll_interval_s)

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("EMS scheduler stopped")
