import setuptools
from distutils.core import setup

setup(name='pycrunch-engine',
      version='1.2.2',
      description='Automatic Test Runner Engine',
      url='http://github.com/gleb-sevruk/pycrunch-engine',
      author='Gleb Sevruk',
      author_email='support@pycrunch.com',
      license='libpng',
      keywords="tdd unit-testing test runner",
      packages=setuptools.find_packages(),
      download_url='https://github.com/gleb-sevruk/pycrunch-engine/archive/v1.2.2.tar.gz',
      setup_requires=['wheel'],
      entry_points={
          'console_scripts': ['pycrunch-engine=pycrunch.main:run'],
      },
      install_requires=[
          'pytest',
          'coverage==4.5.3',
          'PyYAML',
          'watchgod',
          'python-socketio>=4,<5',
          'aiohttp',
      ],
      include_package_data=True,
      zip_safe=False)
