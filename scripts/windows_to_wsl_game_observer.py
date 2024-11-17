"""
Run this script in Windows to observe changes in the Satisfactory game
save directory. This is required as the windows file system can not be
watched from within the WSL2.
"""

from argparse import ArgumentParser
import os
import shutil
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, dest_dir: str) -> None:
        self.dest_dir = dest_dir
        super().__init__()

    def _copy_file(self, event):
        src_path = event.src_path
        file_name = os.path.basename(src_path)
        dest_path = os.path.join(self.dest_dir, file_name)
        try:
            shutil.copy2(src_path, dest_path)
            print(f"Copied: {src_path} -> {dest_path}")
        except Exception as e:
            print(f"Failed to copy {src_path} to {dest_path}: {e}")
        
    # def on_modified(self, event: FileSystemEvent):
    #     if not event.is_directory and event.src_path.endswith('.sav') and not 'BACK000' in event.src_path:
    #         print(f"Modified file: {event.src_path}")
    #         self._copy_file(event)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and event.src_path.endswith('.sav') and not 'BACK000' in event.src_path:
            print(f"New file created: {event.src_path}")
            self._copy_file(event)


def monitor_directory(monitor_path, destination_path):
    event_handler = FileChangeHandler(destination_path)
    observer = Observer()
    observer.schedule(event_handler, monitor_path, recursive=False)
    print('Monitoring', monitor_path)
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
    parser.add_argument('output_dir')
    args = parser.parse_args()

    monitor_directory(args.directory_to_monitor, args.output_dir)
