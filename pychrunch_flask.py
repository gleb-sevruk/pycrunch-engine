import io
from collections import OrderedDict
from decimal import Decimal

from coverage import CoverageData, Coverage
from flask import Flask, render_template, url_for, jsonify, Response
from flask_cors import CORS

import tests
from api.serializers import serialize_coverage
from diagnostics import print_coverage

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return "Nothing here"

def get_file():
 return '/Users/gleb/code/PyCrunch/tests.py'

@app.route("/entry-file")
def entry_file():
    return jsonify({'entry_file': get_file()})



@app.route("/coverage", methods=['POST'])
def run_coverage():
    cov = tests.run()
    serialized = serialize_coverage(cov, get_file())
    return jsonify(dict(entry_file=get_file(), results=serialized))


@app.route("/file", methods=['GET'])
def download_file():
    my_file = io.FileIO(get_file(), 'r')
    content = my_file.read()
    return Response(content, mimetype='application/x-python-code')

