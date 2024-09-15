from argparse import ArgumentParser
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

import stats_tool


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback) -> None:
        self.callback = callback
        super().__init__()

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            print(f"Modified file: {event.src_path}")
            self.callback(event.src_path)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            print(f"New file created: {event.src_path}")
            self.callback(event.src_path)


def monitor_directory(path):
    callback = stats_tool.main

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

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('directory_to_monitor')
    args = parser.parse_args()


    monitor_directory(args.directory_to_monitor)
