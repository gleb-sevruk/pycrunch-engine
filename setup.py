from distutils.core import setup

import setuptools

setup(
    name='pycrunch-engine',
    version='1.6.4',
    description='PyCrunch Engine - Connector for PyCharm plugin, providing real-time test feedback and precise test '
    'coverage tracking for Python projects. ',
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
        'watchdog',
        'python-socketio>=5',
        'aiohttp',
        'nest-asyncio',
    ],
    include_package_data=True,
    zip_safe=False,
)
