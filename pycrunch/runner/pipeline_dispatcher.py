import logging

from pycrunch.api import shared
from pycrunch.pipeline import execution_pipeline

logger = logging.getLogger(__name__)

"""
  responsible for handling tasks for
    
    - Test run
    - File tracking
"""

async def dispather_thread():
    logger.debug('Dispatcher thread -- Start')
    count = 1
    while True:
        print('inside event loop')
        task = await execution_pipeline.get_task()
        print('received task...')
        try:
            await task.run()
        except Exception as e:
            logger.exception('Exception in dispatcher_thread, ', exc_info=e)



        count += 1


    logger.debug('Dispatcher thread -- End')
