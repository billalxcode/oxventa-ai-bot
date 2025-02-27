import queue
import threading
from typing import Callable
from src.core.logger import console

class WorkerThreadQueue(threading.Thread):
    count = 0
    def __init__(self, name: str, queue: queue.Queue = None):
        if not name:
            name = f"Worker-{self.__class__.count}"
            self.__class__.count += 1
        if not queue:
            queue = queue
        
        super().__init__(name=name)
        self.queue = queue
        self.daemon = True

        self.done_event = threading.Event()

        self.running = True

        self.start()

    def run(self):
        while self.running:
            try:
                task, args, kwargs = self.queue.get(block=True, timeout=0.5)
                
                task(*args, **kwargs)
                console.info(f"Worker {self.name}: task completed")
                self.done_event.set()
            except queue.Empty: pass
            except Exception as e:
                console.error(f"Worker error: {e}")
                self.stop()

    def stop(self):
        self.running = False

class WorkerThread(threading.Thread):
    count = 0

    def __init__(self, name: str, target: Callable, args: tuple):
        if not name:
            name = f"Worker-{self.__class__.count}"
            self.__class__.count += 1

        super().__init__(name=name, target=target, args=args)
        self.target = target
        self.args = args
        self.daemon = True
        self.running = True

    def stop(self):
        self.running = False
        