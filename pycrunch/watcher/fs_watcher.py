import asyncio
import logging
import threading
from pathlib import Path

from watchgod import DefaultDirWatcher

from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.file_removed_task import FileRemovedTask

from ..constants import CONFIG_FILE_NAME
from ._abstract_watcher import Watcher

logger = logging.getLogger(__name__)


# Todo: switch to watchdog with kernel-level notification support

class CustomPythonWatcher(DefaultDirWatcher):
    def should_watch_file(self, entry: 'DirEntry') -> bool:
        return entry.name.endswith(
            ('.py', '.pyx', '.pyd', CONFIG_FILE_NAME)
        )


class FSWatcher(Watcher):
    def __init__(self):
        self.thread_lock = threading.Lock()
        self.thread = None
        self.files = set()

    async def thread_proc(self):
        from watchgod import Change, awatch

        from pycrunch.pipeline.file_modification_task import \
            FileModifiedNotificationTask

        logger.debug('thread_proc')
        logger.debug(f'files {self.files}')

        logger.debug(f'files {self.files}')

        path = Path('.').absolute()
        print('watching this:...')
        print(path)
        async for changes in awatch(path, watcher_cls=CustomPythonWatcher):
            for c in changes:
                change_type = c[0]

                force = False
                if change_type == Change.added:
                    force = True

                file = c[1]
                logger.info(f'File watcher alarm: file: `{file}` type `{change_type}` ')

                # TODO: Debounce
                if force or self.should_watch(file):
                    if change_type == Change.deleted:
                        execution_pipeline.add_task(FileRemovedTask(file=file))
                        logger.info('Added file removal for pipeline ' + file)
                    else:
                        execution_pipeline.add_task(
                            FileModifiedNotificationTask(file=file)
                        )
                        logger.info('Added file modification for pipeline ' + file)
                else:
                    logger.debug('non-significant file changed ' + file)

        logger.debug('END thread_proc')

    def watch(self, files):
        logger.debug('watch...')
        self.files.update(files)
        logger.debug(f"Total files to watch: {len(self.files)}")

        self.start_thread_if_not_running()

    def start_thread_if_not_running(self):
        with self.thread_lock:
            if self.thread is None:
                logger.info('Starting watch thread...')
                # logger.info('NOT')

                # self.thread = threading.Thread(target=self.thread_proc)
                # self.thread.start()
                self.thread = True
                loop = asyncio.get_event_loop()
                loop.create_task(self.thread_proc())

    def should_watch(self, file):
        return file in self.files
