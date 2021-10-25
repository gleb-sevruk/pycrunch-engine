import asyncio
import logging
from pathlib import Path

from pycrunch.pipeline import execution_pipeline

from ..constants import CONFIG_FILE_NAME
from ._abstract_watcher import Watcher

logger = logging.getLogger(__name__)

def create_handler(files_to_watch: "set[str]", event_loop):
    # todo: fix recursive imports
    from pycrunch.pipeline.file_removed_task import FileRemovedTask
    from watchdog.events import FileSystemEventHandler

    from ..pipeline.file_modification_task import FileModifiedNotificationTask

    class Handler(FileSystemEventHandler):
        """Logs all the events captured."""

        def __init__(self, logger=None):
            super().__init__()
            self.files_to_watch = files_to_watch
            self.logger = logger or logging.root
            self.event_loop = event_loop

        def should_watch_file(self, entry: 'str') -> bool:
            return entry.endswith(('.py', '.pyx', '.pyd', CONFIG_FILE_NAME))

        def known_file(self, file):
            return file in self.files_to_watch

        def on_moved(self, event):
            super().on_moved(event)

            if self.known_file(event.src_path):
                self.add_task_in_queue_threading_hack(FileRemovedTask(file=event.src_path))

            # todo test dirs move
            if not self.should_watch_file(event.src_path):
                return


            # will also emit `created`
            # self.send_modification_message(event.dest_path)

            what = 'directory' if event.is_directory else 'file'
            self.logger.info(
                "Moved %s: from %s to %s", what, event.src_path, event.dest_path
            )

        def on_created(self, event):
            super().on_created(event)
            if not self.should_watch_file(event.src_path):
                return

            self.send_modification_message(event.src_path)

        def on_deleted(self, event):
            super().on_deleted(event)
            if not self.known_file(event.src_path):
                return

            if not self.should_watch_file(event.src_path):
                return

            self.add_task_in_queue_threading_hack(FileRemovedTask(file=event.src_path))
            logger.info('Added file removal for pipeline ' + event.src_path)

        def add_task_in_queue_threading_hack(self, t: "AbstractTask"):
            # https://stackoverflow.com/questions/59083275/simplest-way-to-put-an-item-in-an-asyncio-queue-from-sync-code-running-in-a-sepa
            # main event loop doesn't know about action made in thread
            fut = asyncio.run_coroutine_threadsafe(
                execution_pipeline.q.put(t),
                self.event_loop)
            fut.result()
            pass

        def on_modified(self, event):
            super().on_modified(event)

            if not self.known_file(event.src_path):
                return

            if not self.should_watch_file(event.src_path):
                return

            self.send_modification_message(event.src_path)

            what = 'directory' if event.is_directory else 'file'
            self.logger.info("Modified %s: %s", what, event.src_path)

        def send_modification_message(self, filename):
            logger.info('Adding file modification for pipeline ' + filename)

            self.add_task_in_queue_threading_hack(
                FileModifiedNotificationTask(file=filename)
            )

            logger.info(' -- done Added ' + filename)

    return Handler()

class FSWatcher(Watcher):
    def __init__(self):
        self._started = False
        self.files = set()
        self.event_loop = asyncio.get_event_loop()

    # async def thread_proc(self):
    #
    #     logger.debug('thread_proc')
    #     logger.debug(f'files {self.files}')
    #
    #     logger.debug(f'files {self.files}')
    #
    #     path = Path('.').absolute()
    #     print('watching this:...')
    #     print(path)
    #     async for changes in awatch(path, watcher_cls=CustomPythonWatcher):
    #         for c in changes:
    #             change_type = c[0]
    #
    #             force = False
    #             if change_type == Change.added:
    #                 force = True
    #
    #             file = c[1]
    #             logger.info(f'File watcher alarm: file: `{file}` type `{change_type}` ')
    #
    #             # TODO: Debounce
    #             if force or self.known_file(file):
    #                 if change_type == Change.deleted:
    #                     execution_pipeline.add_task(FileRemovedTask(file=file))
    #                     logger.info('Added file removal for pipeline ' + file)
    #                 else:
    #                     execution_pipeline.add_task(
    #                         FileModifiedNotificationTask(file=file)
    #                     )
    #                     logger.info('Added file modification for pipeline ' + file)
    #             else:
    #                 logger.debug('non-significant file changed ' + file)
    #
    #     logger.debug('END thread_proc')

    def watch(self, files):
        logger.debug('watch...')
        self.files.update(files)
        logger.debug(f"Total files to watch: {len(self.files)}")

        self.start_thread_if_not_running()

    def start_thread_if_not_running(self):
        from watchdog.observers import Observer
        if self._started:
            return

        path = str(Path('.').absolute())
        print('watching this:...')
        print(path)
        observer = Observer()
        observer.schedule(create_handler(self.files, event_loop=self.event_loop), path=path, recursive=True)
        observer.start()
        logger.info('Starting watch thread...')
        self._started = True

