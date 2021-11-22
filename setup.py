import setuptools
from distutils.core import setup

setup(name='pycrunch-engine',
      version='1.3.1',
      description='Automatic Test Runner Engine',
      url='http://github.com/gleb-sevruk/pycrunch-engine',
      author='Gleb Sevruk',
      author_email='support@pycrunch.com',
      license='libpng',
      keywords="tdd unit-testing test runner",
      packages=setuptools.find_packages(),
      project_urls={
              'Documentation': 'https://pycrunch.com/docs',
              'Funding': 'https://pycrunch.com/donate',
              'PyCharm Plugin': 'https://plugins.jetbrains.com/plugin/13264-pycrunch--live-testing',
              'Source': 'https://github.com/gleb-sevruk/pycrunch-engine',
              'Tracker': 'https://github.com/gleb-sevruk/pycrunch-engine/issues',
      },
      setup_requires=['wheel'],
      entry_points={
              'console_scripts': ['pycrunch-engine=pycrunch.main:run'],
      },
      install_requires=[
              'pytest',
              'coverage>4',
              'PyYAML',
              'watchgod',
              'python-socketio>=4,<5',
              'aiohttp',
      ],
      include_package_data=True,
      zip_safe=False)
