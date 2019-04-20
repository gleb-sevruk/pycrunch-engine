import logging

from pycrunch.api import shared
from pycrunch.pipeline import execution_pipeline

logger = logging.getLogger(__name__)

def dispather_thread(arg):
    logger.debug('OPA THGREAD!')
    count = 1
    while True:
        task = execution_pipeline.get_task()
        try:
            task.run()
        except Exception as e:
            logger.exception('Exception in dispather_thread, ', exc_info=e)



        count += 1



    logger.debug('OPA THGREAD --- done!')