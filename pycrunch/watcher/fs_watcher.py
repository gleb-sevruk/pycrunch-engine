import asyncio
import logging
from pathlib import Path
from typing import Set

from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.file_removed_task import FileRemovedTask
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..constants import CONFIG_FILE_NAME
from ._abstract_watcher import Watcher

logger = logging.getLogger(__name__)


def create_handler(files_to_watch: "Set[str]", event_loop):
    from ..pipeline.file_modification_task import FileModifiedNotificationTask

    class CustomFSWatchHandler(FileSystemEventHandler):
        """Logs all the events captured."""

        def __init__(self):
            super().__init__()
            self.files_to_watch = files_to_watch
            self.event_loop = event_loop

        def should_watch_file(self, entry: 'str') -> bool:
            return entry.endswith(('.py', '.pyx', '.pyd', CONFIG_FILE_NAME))

        def known_file(self, file):
            return file in self.files_to_watch

        def on_moved(self, event):
            super().on_moved(event)

            if self.known_file(event.src_path):
                self.add_task_in_queue(FileRemovedTask(file=event.src_path))

            if not self.should_watch_file(event.src_path):
                return


            what = 'directory' if event.is_directory else 'file'
            logger.debug(
                "Moved %s: from %s to %s", what, event.src_path, event.dest_path
            )
            self.send_modification_message(event.dest_path, 'moved')

        def on_created(self, event):
            super().on_created(event)
            if not self.should_watch_file(event.src_path):
                return

            self.send_modification_message(event.src_path, 'created')

        def on_deleted(self, event):
            super().on_deleted(event)
            if not self.known_file(event.src_path):
                return

            if not self.should_watch_file(event.src_path):
                return

            self.add_task_in_queue(FileRemovedTask(file=event.src_path))
            logger.info('Added file removal for pipeline ' + event.src_path)

        def add_task_in_queue(self, t: "AbstractTask"):
            # Hack included: it is not possible to submit into asyncio queue from another thread, therefore:
            # https://stackoverflow.com/questions/59083275/simplest-way-to-put-an-item-in-an-asyncio-queue-from-sync-code-running-in-a-sepa
            # main event loop doesn't know about action made in thread
            fut = asyncio.run_coroutine_threadsafe(
                execution_pipeline.put_raw(t), self.event_loop
            )
            fut.result()

        def on_modified(self, event):
            super().on_modified(event)

            if not self.known_file(event.src_path):
                return

            if not self.should_watch_file(event.src_path):
                return

            self.send_modification_message(event.src_path, 'modified')

            what = 'directory' if event.is_directory else 'file'
            logger.debug("Modified %s: %s", what, event.src_path)

        def send_modification_message(self, filename, context):
            logger.debug('Adding file modification for processing ' + filename)

            self.add_task_in_queue(FileModifiedNotificationTask(file=filename, context=context))
            logger.debug(' -- done Added ' + filename)

    return CustomFSWatchHandler()


class FSWatcher(Watcher):
    def __init__(self):
        self._started = False
        self.files = set()
        self.event_loop = asyncio.get_event_loop()

    def watch(self, files):
        logger.debug('watch...')
        self.files.update(files)
        logger.debug(f"Total files to watch: {len(self.files)}")

        self.start_thread_if_not_running()

    def start_thread_if_not_running(self):
        if self._started:
            return

        logger.debug('start_thread_if_not_running->Creating fs_observer')
        path = str(Path('.').absolute())
        logger.debug('watch root path: ', path)
        observer = Observer()
        observer.schedule(
            create_handler(self.files, event_loop=self.event_loop),
            path=path,
            recursive=True,
        )
        observer.start()
        logger.info('Started watch thread...')
        self._started = True
