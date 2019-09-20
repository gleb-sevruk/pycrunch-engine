import setuptools
from distutils.core import setup

setup(name='pycrunch-engine',
      version='0.6',
      description='Automatic Test Runner Engine',
      url='http://github.com/gleb-sevruk/pycrunch-engine',
      author='Gleb Sevruk',
      author_email='support@pycrunch.com',
      license='libpng',
      packages=setuptools.find_packages(),
      download_url='https://github.com/gleb-sevruk/pycrunch-engine/archive/v0.6.tar.gz',
      setup_requires=['wheel'],
      entry_points={
          'console_scripts': ['pycrunch-engine=pycrunch.main:run'],
      },
      install_requires=[
          'pytest==4.6.3',
          'coverage==4.5.3',
          'PyYAML',
          'watchgod',
          'python-socketio',
          'aiohttp',
      ],
      include_package_data=True,
      zip_safe=False)
