import time
import os
import time
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


COOLDOWN = 10 # seconds


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable) -> None:
        self.callback = callback
        self.cooldown_finish: float = 0
        super().__init__()

    def on_modified(self, event: FileSystemEvent):
        if self.cooldown_finish > time.time():
            print('Ignore update trigger (cooldown)')
            return
        
        self.cooldown_finish = time.time() + COOLDOWN

        if not event.is_directory:
            time.sleep(1) # to avoid Zlib error 5
            os.system('clear')
            print(f"Modified file: {event.src_path}")
            self.callback(event.src_path)

    # def on_created(self, event: FileSystemEvent):
    #     if not event.is_directory:
    #         print(f"New file created: {event.src_path}")
    #         self.callback(event.src_path)


def monitor_directory(path, callback: Callable[[str], None]):
    event_handler = FileChangeHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    print('Monitoring', path)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Check every 1 second
    finally:
        observer.stop()
        observer.join()
