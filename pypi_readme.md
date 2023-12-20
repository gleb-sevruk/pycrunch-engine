https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56

`bump-my-version bump patch --verbose --dry-run --no-tag --allow-dirty`

`python setup.py sdist`

`twine upload dist/*`