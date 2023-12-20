import logging

from pycrunch.pipeline import execution_pipeline

logger = logging.getLogger(__name__)

"""
  responsible for handling tasks for
    
    - Test run
    - File tracking
"""


async def dispather_thread():
    logger.info('Dispatcher thread -- Start')
    while True:
        logger.debug('Dispatcher thread -- inside event loop, waiting for task...')
        task = await execution_pipeline.get_task()
        logger.debug('Dispatcher thread -- received task:')
        logger.debug(f'   {task}')
        try:
            await task.run()
        except Exception as e:
            logger.exception(
                'Exception in dispatcher_thread, execution will begin from the next task',
                exc_info=e,
            )

    logger.debug('Dispatcher thread -- End')
