# Quick start

`pip install pycrunch-engine`

_This engine depends on `aiohttp`, you may need to check cross-dependencies if your project also uses `aiohttp`_

PyCrunch is written and supports Python 3.6+.

![What Covers What](https://i.stack.imgur.com/w7wQM.png)

## How to run:
### Using PyCharm Connector extension

 Download extension and install it from disk using PyCharm
 https://pycrunch-dist.s3.eu-central-1.amazonaws.com/pycrunch-intellij-connector-latest.zip
 
 Open your project in PyCharm, and select "Run/Restart PyCrunch Engine"

Engine will be started automatically, and you will be able to see your test in PyCrunch plugin window

### Manual (Without PyCharm)

In python project root, run: 

`pycrunch-engine`


Optionally, port can be specified, in order to run more than one instance of engine:

`pycrunch-engine --port=31234`


### Configuration file

Configuration file should be created prior to the first use of pycrunch-engine


Configuration file `.pycrunch-config.yaml` should be created and placed at project root

Minimum configuration 
```yaml
engine:
  runtime: pytest
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

Configuration File may be checked-in the to source control, to allow other developers to use engine.

###### Beta restriction
For Django, you probably need to disable logging, pasting following line in your settings file:
```python
LOGGING_CONFIG = None

```
This issue is already on roadmap and will be addressed soon. 

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


### Contacts:
 
 https://pycrunch.com
 
 support@pycrunch.com
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
