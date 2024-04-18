import asyncio
from time import time, sleep
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
# import schedule


class Planner:
    def __init__(self, interval: float, callback: Callable[..., any], *params):
        self.interval: float = interval
        self.callback: Callable[..., None] = callback
        self.last_call_result: any = None
        self.params: list|tuple = params
        self.is_running: bool = False
        self.started_at: int = None
        self.scheduler: BackgroundScheduler = BackgroundScheduler()
        self.scheduler.add_job(self._run_callback, 'interval', seconds=interval*60)

    async def maintain_event_loop(self):
        print("starting event loop.")
        while True:
            await asyncio.sleep(1)

    def start(self):
        if not self.is_running:
            self.scheduler.start()
            self.started_at: int = time() // 60
            self.is_running = True
            print("Planner started.")
            asyncio.run(self.maintain_event_loop())

    def stop(self):
        if self.is_running:
            self.scheduler.cancel()
            # self.scheduler.shutdown()
            self.is_running = False
            print("Planner stopped.")

    def _run_callback(self):
        # self.last_call_result = await self.callback()
        asyncio.run(self.callback())


    def minutes_running(self) -> int:
        return (time() // 60) - self.started_at
