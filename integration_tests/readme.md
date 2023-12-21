# Integration test suite

This are basic test scenarios that uses `integration_tests/test_folder` as a test folder.

Then test suite communicates via web-sockets as a real client.

It checks that tests are discovered.

Also checks for combined and individual coverage (information that would be drawn in PyCharm Plugin) 

## Running via docker:

```bash
cd integration_tests
docker-compose up --build
```

## How to develop/run tests locally

You will need multiple terminals to run all the components.

1. Starting engine manually 
cd to folder `integration_tests/test_folder`
```
cd integration_tests/test_folder
pycrunch-engine --port 11016
```

In another terminal:

Create new environment (if not created yet) (ie: pycrunch_integration_tests310)
Install requirements:
```
pip install requirements.txt
```

2. Either run pycruch-engine again in `integration_tests` or use `pytest`

Option 1
```bash
# Using pycrunch-engine
cd integration_tests
pycrunch-engine --port 20111

# now connect to it via PyCharm menu (20111); You can use any port you want
```

Option 2
```
cd integration_tests
pytest pycrunch_integration_tests/pycrunch_engine_int_test.py

# Or run using PyCharm menu
```

Note: You will need to set PYCRUNCH_API_URL to http://localhost:11016

(this already hard-coded into .pycrunch-config.yaml configuration; so no need to do anything when using first option)

Or just hard-code it in `integration_tests/pycrunch_integration_tests/pycrunch_engine_int_test.py` `PYCRUNCH_API_URL` variable

