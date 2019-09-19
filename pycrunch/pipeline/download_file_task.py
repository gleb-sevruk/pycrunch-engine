import io

from pycrunch.api import shared
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.session import config

import logging

logger = logging.getLogger(__name__)

class DownloadFileTask(AbstractTask):
    def __init__(self, filename):
        self.filename = filename

    async def run(self):
        target_file = config.path_mapping.map_local_to_remote(self.filename)
        my_file = io.FileIO(target_file, 'r')
        content = my_file.read()
        logger.debug(f'sending file {self.filename}')
        await shared.pipe.push(event_type='file_did_load',
                         filename=self.filename,
                         file_contents=content,
                         )
        # return Response(content, mimetype='application/x-python-code')