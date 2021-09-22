import asyncio
import threading
from pathlib import Path

from watchgod import watch, Change, PythonWatcher, awatch

from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.file_removed_task import FileRemovedTask
from ._abstract_watcher import Watcher

import logging

logger = logging.getLogger(__name__)


class FSWatcher(Watcher):
    def __init__(self):
        self.thread_lock = threading.Lock()
        self.thread = None
        self.files = set()

    async def thread_proc(self):
        from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask

        logger.debug('thread_proc')
        logger.debug(f'files {self.files}')

        logger.debug(f'files {self.files}')

        path = Path('.').absolute()
        print('watching this:...')
        print(path)
        async for changes in awatch(path, watcher_cls=PythonWatcher):
            for c in changes:
                change_type = c[0]

                force = False
                if change_type == Change.added:
                    force = True

                file = c[1]
                logger.info(f'File watcher alarm: file: `{file}` type `{change_type}` ')

                if force or self.should_watch(file):
                    if change_type == Change.deleted:
                        execution_pipeline.add_task(FileRemovedTask(file=file))
                        logger.info('Added file removal for pipeline ' + file)
                    else:
                        execution_pipeline.add_task(FileModifiedNotificationTask(file=file))
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

