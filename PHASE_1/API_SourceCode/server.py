'''
Server file that contains the flask implementation.
'''

import os
import sys
from flask import Flask, request
from flask_cors import CORS
from json import dumps


def defaultHandler(err):
    '''Default handler for server.py'''
    response = err.get_response()
    print('response', err, err.get_response())
    response.data = dumps({
        'code': err.code,
        'name': 'System Error',
        'message': err.get_description(),
    })
    response.content_type = 'application/json'
    return response

APP = Flask(__name__)

CORS(APP)
APP.register_error_handler(Exception, defaultHandler)

# Routes
@APP.route('/results', methods=['GET'])
def get_results():
    '''Fetch the reports from the database'''

@APP.route('/result/{id}', methods=['GET'])
def get_result():
    '''Fetch the report of the given id from the database'''

@APP.route('/add/result', method=['POST'])
def add_result():
    '''Add a new report with the given parameters'''
    parameters = request.get_json()

@APP.route('/results', method=['DELETE'])
def remove_result():
    '''Deletes a report of given id'''

if __name__ == "__main__":
    APP.run(port=8080)