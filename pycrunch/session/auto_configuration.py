import io
from pathlib import Path

class AutoConfiguration:
    def __init__(self, configuration_file):
        """
        :type configuration_file: Path
        """
        self.configuration_file = configuration_file

    def ensure_configuration_exist(self):
        if self.configuration_file.exists():
            return
        
        self.create_default_configuration_file()

    def create_default_configuration_file(self):
        default_config_file = '''# documentation https://pycrunch.com/docs/configuration-file
engine:
    runtime: pytest'''
        with io.open(self.configuration_file, encoding='utf-8', mode='w') as f:
            f.write(default_config_file)

        print(f'Created default configuration file.')
