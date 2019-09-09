import threading
from pathlib import Path

from watchgod import watch, Change, PythonWatcher

from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.pipeline import execution_pipeline
from ._abstract_watcher import Watcher

import logging

logger = logging.getLogger(__name__)


class FSWatcher(Watcher):
    def __init__(self):
        self.thread_lock = threading.Lock()
        self.thread = None
        self.files = []

    def thread_proc(self):
        from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask

        logger.debug('thread_proc')
        logger.debug(f'files {self.files}')

        logger.debug(f'files {self.files}')

        path = Path('.').absolute()
        print('watching this:...')
        print(path)
        for changes in watch(path, watcher_cls=PythonWatcher):
            for c in changes:
                change_type = c[0]
                force = False
                if change_type == Change.added:
                    force = True

                file = c[1]
                if force or self.should_watch(file):
                    execution_pipeline.add_task(FileModifiedNotificationTask(file=file))
                    logger.info('Added file for pipeline ' + file)
                else:
                    logger.debug('non-significant file changed ' + file)

        logger.debug('END thread_proc')



    def watch(self, files):
        logger.debug('watch...')
        self.files = files
        with self.thread_lock:
            if self.thread is None:
                logger.info('Starting watch thread...')
                # logger.info('NOT')
                self.thread = threading.Thread(target=self.thread_proc)
                self.thread.start()

    def should_watch(self, file):
        return file in self.files

