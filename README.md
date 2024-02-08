# Quick start

`pip install pycrunch-engine`

_This engine depends on `aiohttp`, you may need to check cross-dependencies if your project also uses `aiohttp`_

PyCrunch is written and supports Python 3.6+.

![What Covers What](https://i.stack.imgur.com/w7wQM.png)

## How to run:
### Using PyCharm Connector extension

 Install extension from JetBrains marketplace
 https://plugins.jetbrains.com/plugin/13264-pycrunch--live-testing
 
 Open your project in PyCharm, and select "Run/Restart PyCrunch Engine"

 Engine will be started automatically, and you will be able to see your tests in PyCrunch plugin window

### Manual (Without PyCharm)

In python project root, inside correct virtual environment, after installation via `pip install pycrunch-engine`, run: 

`pycrunch-engine`


Optionally, port can be specified, in order to run more than one instance of engine:

`pycrunch-engine --port=31234`

From the PyCrunch menu in PyCharm, select "Connect to Custom PyCrunch Engine", and enter port number


### Configuration file

Configuration file will be created automatically on the first use of pycrunch-engine

Configuration file `.pycrunch-config.yaml` will be created and placed at project root (which is current working directory where engine is started)

Minimum configuration 
```yaml
engine:
  runtime: pytest
```

Most of the parameters listed:
```yaml
discovery:
  # Paths, that will be excluded during test discovery.
  # The file will be excluded from discovery, if either starts_with or ends_with condition is true on filename. File path is relative to project root folder.
  # On Windows, use `\` separator when excluding paths
  exclusions:
  - front/
  - venv/
  - test_runner.py
engine:
  # default - `pytest` [django, pytest]
  runtime: pytest
  # execution timeout in seconds (60 seconds by default, 0 - no timeout)
  timeout: 60

  # maximum number of concurrent test runners
  cpu-cores: 4

  # minimum number of tests to schedule per core (5 by default)
  multiprocessing-threshold: 4

  # When this is on, pytest plugins will be loaded
  # By default this option is off, to speed-up individual test execution
  load-pytest-plugins: true

  # Use runtime analysis to find TestCase class inheritors
  deep-inheritance: false

  # Useful if you work in monorepo with multiple python projects (Default - `.`)
  change-detection-root: .

  # Enable web UI (Default - `false`)
  enable-web-ui: true
  
  # Customize pytest.ini  [spec_file.py -> def should_be_true()]
  # python_files = test_*.py tests_*.py spec*.py moduletest*.py
  module-prefixes: test spec moduletest
  # python_functions = *_test should* must*
  function-prefixes: should must

# Environment variables to forward to pytest executors
env:
  DJANGO_SETTINGS_MODULE: django_app.settings.local
  DB_HOST: 0.0.0.0
```

Django configuration

```yaml
discovery:
  exclusions:
  - front/
  - build/
  - test_discovery_specs_demo.py
engine:
  runtime: django
env:
  DJANGO_SETTINGS_MODULE: djangoapp.settings.local
```

Configuration file may be checked-in the to source control, to allow other developers to use engine.

See more examples and detailed description of each parameter available
https://pycrunch.com/docs/configuration-file/

## Debugging tests
It is possible to run tests with debugger from PyCrunch extension. 

First, you need to install correct version of `pydevd-pycharm` package, depending on your PyCharm version.

You can find out the required version of pydevd-pycharm by going into run configuration, creating new `Python Debug Server`, and copy-paste command like: 

`pip install pydevd-pycharm~=223.8617.48`

After that you can run tests with debugger from PyCrunch extension.

> **Warning**
> Coverage will not be collected when test is executed under debugger.

See here for more details: 
https://pycrunch.com/docs/debugging-support

## Django Support Details

 Primary goal of extension is to run as fast as possible.
 
 Default Django Test Runner creates new database each time when tests are run.
 
This leads to multiple problems:

 - Inability to run tests in parallel
 - Sometimes database got stale, and you need to type `yes` in terminal in order to destroy it
 - Each test run consumes more resources than it should, by creating database and applying migrations each time
 - Tests are not really *unit-tests*, sometimes you do not need database at all
 - Cannot run tests (or some code from unit-test) upon data stored in local database 
 
 As a result, pycrunch will use same database for running tests as `manage.py runserver`, without initializing temporary database. 
 
 Be careful when you run your suite for the first time, as it may corrupt data. 
 
 If your insist on using separate database, please create new `django.setting` module and pass it as environment variable to pycrunch-engine using `.pycrunch-config.yaml` file in env section, something like
 
 ```yaml
engine:
  runtime: django
env:
  DJANGO_SETTINGS_MODULE: djangoapp.settings.pycrunch_local
```
 
 ## Running in Docker 
 
Some developers are using docker or docker-compose to set up environment and run development server in docker container

pycrunch-engine and extension support this use case.

All you need, is to map some port from docker to your local machine (ex. 5000) and put additional `path-mapping` configuration inside `.pycrunch-config.yaml`:

```yaml
engine:
  runtime: django
env:
  DJANGO_SETTINGS_MODULE: djangoapp.settings.pycrunch_local
path-mapping:
    /code: /Users/neo/code/matrix-django-api
```

You will probably need to rebuild containers using `docker-compose up --build` in order for exposed port to appear

 Then, enter inside docker container (ex:)
 ```commandline
 docker-compose exec web bash
 # inside container:
 pycrunch-engine
 # will run on 5000 port by default
```

From PyCharm extension menu, select "Connect to Custom PyCrunch Engine"

### Troubleshooting

If you see the error like:

 `engineio.server - ERROR - The client is using an unsupported version of the Socket.IO or Engine.IO protocols`
   
Please update the engine via `pip install --upgrade pycrunch-engine`

Make sure both engine and plugin are 1.6.0 version or higher.

This was major dependency change, so please report any issues you may have. 

### Contacts:
 
 https://pycrunch.com
 
 support@pycrunch.com
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
