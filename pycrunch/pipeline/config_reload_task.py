from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.session import config


class ConfigReloadTask(AbstractTask):
    async def run(self):
        config.load_runtime_configuration()
