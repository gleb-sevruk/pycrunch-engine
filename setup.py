import setuptools
from distutils.core import setup

setup(name='pycrunch-engine',
      version='0.5.1',
      description='Automatic Test Runner Engine',
      url='http://github.com/gleb-sevruk/pycrunch-engine',
      author='Gleb Sevruk',
      author_email='support@pycrunch.com',
      license='libpng',
      packages=setuptools.find_packages(),
      download_url='https://github.com/gleb-sevruk/pycrunch-engine/archive/v0.5.1.tar.gz',
      setup_requires=['wheel'],
      entry_points={
          'console_scripts': ['pycrunch-engine=pycrunch.main:run'],
      },
      install_requires=[
          'PyYAML==5.1',
          'pytest==4.6.3',
          'watchdog==0.9.0',
          'watchgod==0.4',
          'python-socketio',
          'coverage==4.5.3',
      ],
      include_package_data=True,
      zip_safe=False)
