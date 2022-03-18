'''
Server file that contains the flask implementation.
'''

# import os
# import sys
import re
import json
from flask import Flask
from flask_cors import CORS
from flask_restx import Resource, Api, reqparse
import geocoder
import validators
from helper import *
from datetime import datetime
import logging

# from flask_cors import CORS
# from json import dumps

class Manager(object):
    def __init__(self, data):
        self.articles = data
        self.n = len(data)

    def findArticle(self, n):
        for article in self.articles:
            if article['ID'] == n:
                return article
        return None

data = []
with open('final.json',"r") as f:
    data = eval(f.read())
    f.close()

articleList = Manager(data)
APP = Flask(__name__)
api = Api(APP, title = 'OUTBREAK', description = 'This API extracts disease reports from the Global Outbreak website')
CORS(APP)
parser = reqparse.RequestParser()

parser_get = parser.copy()
parser_get.add_argument('n', type=int, help='Max number of results', location='args')
parser_get.add_argument('location', type=str, help='Location', location='args')
parser_get.add_argument('key_terms', type=str, help='List of key terms', location='args')
parser_get.add_argument('start_date', type=str, help='Start date of date range (yyyy-mm-ddThh:mm:ss)', location='args')
parser_get.add_argument('end_date', type=str, help='End date of date range (yyyy-mm-ddThh:mm:ss)', location='args')


parser_create = parser.copy()
parser_create.add_argument('url', type=str, required=True, help='Url of the event', location='args')
parser_create.add_argument('date_of_publication', type=str, required=True, help='Date of publication (yyyy-mm-ddThh:mm:ss)', location='args')
parser_create.add_argument('headline', type=str, required=True, help='Headline for the report', location='args')
parser_create.add_argument('main_text', type=str, required=True, help='Main text of the event', location='args')
parser_create.add_argument('description', type=str, required=False, help='Descriptive text of the event', location='args')
parser_create.add_argument('disease', type=str, required=True, help='Comma separated list of diseases', location='args')
parser_create.add_argument('syndrome', type=str, required=False, help='Comma separated list of syndromes', location='args')
parser_create.add_argument('type', type=str, required=True, help='Type of event e.g death, infected', location='args')
parser_create.add_argument('location', type=str, required=True, help='location', location='args')
parser_create.add_argument('date', type=str, required=True, help='Date of the event (yyyy-mm-ddThh:mm:ss)', location='args')


parser_update = parser.copy()
parser_update.add_argument('url', type=str, help='URL of report', location='args', required=False)
parser_update.add_argument('date_of_publication', type=str, help='Date of report publication', location='args', required=False)
parser_update.add_argument('headline', type=str, help='Headline of report', location='args', required=False)
parser_update.add_argument('main_text', type=str, help='Main text of report', location='args', required=False)
parser_update.add_argument('rep_n', type=int, help='Report Number', location='args', required=False)
parser_update.add_argument('disease', type=str, help='Disease contained within report', location='args', required=False)
parser_update.add_argument('syndrome', type=str, help='Syndrome within report', location='args', required=False)
parser_update.add_argument('type', type=str, help='Event type of report', location='args', required=False)
parser_update.add_argument('location', type=str, help='Location in report', location='args', required=False)
parser_update.add_argument('date', type=str, help='Event date', location='args', required=False)

parser_log = parser.copy()
parser_log.add_argument('password', type=str, help='Password to obtain log file for API', required=True, location='args')

# Routes
@api.doc(parser=parser_get)
@api.response(200, "Sucess")
@api.response(400, "Invalid search")
@api.response(404, "Invalid date param")
@APP.route('/search', methods=['GET'])
def get_results():
  '''Fetch the reports from the database'''
  newResponse = []
  args = parser_get.parse_args()
  reportList = []
  LocationList = []

  if args["start_date"] is None or args["end_date"] is None:
      return "No date Param", 400

  for report in data:
    keys = []
    LocationList = []
    if args['key_terms'] is not None:
      key_term_list = args['key_terms'].split(',')
      for key_term in key_term_list:
        if key_term in str(report['main_text']):
          keys.append(key_term)  
      if (len(keys) == 0):
        continue

    if args['location'] is not None:
      LocationList = []
      if len(report['reports']['Locations']) != 0:
        for location in report['reports']['Locations']:
          country = geocoder.geonames(location['geonames_id'], key='syntaxerror', method='children')
          if len(country.geojson['features']) == 0:
            continue
        
          if args['location'] == country.geojson['features'][0]['properties']['country']:
            LocationList.append(args['location'])
          else:
            for state in country.geojson['features']:
              if args['location'] == state['properties']['address']:
                LocationList.append(args['location'])

      if len(LocationList) == 0:
        continue

    if args['start_date'] is not None and args['end_date'] is not None:
      event_date = report['date_of_publication']
      date_event, time_event = event_date.split('T')[0], event_date.split('T')[1]
      date_event, time_event = list(map(int, date_event.split('-'))), list(map(int, time_event.split(':')))
      datetime_event_date = datetime(*(date_event + time_event))

      date_start, time_start = args['start_date'].split('T')[0], args['start_date'].split('T')[1]
      date_start, time_start = list(map(int, date_start.split('-'))), list(map(int, time_start.split(':')))
      datetime_start_date = datetime(*(date_start + time_start))  

      date_end, time_end = args['end_date'].split('T')[0], args['end_date'].split('T')[1]
      date_end, time_end = list(map(int, date_end.split('-'))), list(map(int, time_end.split(':')))
      datetime_end_date = datetime(*(date_end + time_end))
      if not handle_date_parameter(args):
        return "Invalid date param", 404

      if not is_date_valid(datetime_start_date, datetime_end_date):
        return "Invalid date", 404
  
      if datetime_event_date < datetime_start_date or datetime_event_date > datetime_end_date:
        continue
    reportList.append(report) 

  with open('output.json', "w+") as f:
    f.write(json.dumps(reportList, indent = 2))
  return json.dumps(reportList, indent=2)

@api.response(200, "Sucess")
@api.response(400, "Invalid search")
@api.response(404, "Article not found")
@api.doc(params={'article_id':'ID of report to get'})
@APP.route('/results/<int:article_id>', methods=['GET'])
def get_result(article_id):
  '''Fetch the report of the given id from the database'''
  if article_id < 0 or article_id > len(data):
    return 'Not a valid ID', 400
  elif data[article_id] == None:
    return 'Article with ID does not exist', 404
  else:
    return json.dumps(data[article_id], indent=2), 200

@api.response(200, "Sucess")
@api.response(400, "Invalid search")
@api.response(404, "Article not found")
@api.doc(params={'article_id':'ID of report to update'})
@api.doc(parser=parser_update)
@APP.route('/update/result/<int:article_id>', methods=['PUT'])
def update_result(article_id):
  '''A report with the given parameters'''
  args = parser_update.parse_args()
  art = data[article_id]

  if args['url'] is not None:
    valid = validators.url(args['url'])
    if not valid:
      return 'Invalid URL', 400
    else:
      art['URL'] = args['url']

  if args['date_of_publication'] is not None:
    if is_date_valid2(args['date_of_publication']):
      art['date_of_publication'] = args['date_of_publication']
  
  if args['headline'] is not None:
    art['headline'] = args['headline'].replace('_', ' ')

  if args['main_text'] is not None:
    art['main_text'] = args['main_text'].replace('_', ' ')

  if args['rep_n'] is not None:
    rep_num = args['rep_n']
    if args['disease'] is not None:
        diseaseList = list_handling(args['disease'])
        art['reports'][rep_num]['diseases'] = diseaseList

    if args['syndrome'] is not None:
        syndromeList = list_handling(args['syndrome'])
        art['reports'][rep_num]['syndromes'] = syndromeList

    if args['type'] is not None:
        typeList = list_handling(args['type'])
        art['reports'][rep_num]['event_type'] = typeList
    
    if args['date'] is not None:
        if is_date_valid2(args['date']):
        art['reports'][rep_num]['event_date'] = args['date']
        else:
        return 'Invalid Event Date', 400

    if args['location'] is not None:
        locationList = list_handling(args['location'])
        returnList = []
        for location in locationList:
        loc = validate_location(location)
        if loc is None:
            return "Invalid Location", 400
        else:
            returnList.append(loc)
        art['reports'][0]['location'] = returnList

  with open('output.json', "w+") as f:
    f.write(json.dumps(art, indent = 2))
  return art, 200

@api.response(200, "Sucess")
@api.response(400, "Invalid arguements")
@api.doc(parser=parser_create)
@APP.route('/add/result', methods=['POST'])
def add_result():
    '''Add a new report with the given parameters'''
    args = parser_create.parse_args()
    newObj = {}

    if validators.url(args['url']):
        newObj['URL'] = args['url']
    else:
        return "Invalid URL", 400
        
    if is_date_valid2(args['date_of_publication']):
        newObj['date_of_publication'] = args['date_of_publication']
    else:
        return "Invalid Date", 400

    newObj['headline'] = args['headline']
    newObj['main_text'] = args['main_text']

    if args['description'] is not None:
        newObj['Description'] = args['description']
    else:
        newObj['Description'] = ""

    newObj['reports'] = []

    reportObj = {}

    reportObj['diseases'] = list_handling(args['disease'])
    
    if args['syndrome'] is not None:
        reportObj['syndromes'] = list_handling(args['syndrome'])

    if is_date_valid2(args['date']):
        reportObj['event_date'] = args['date']
    else:
        return "Invalid Date", 400

    reportObj['event_type'] = list_handling(args['type'])

    locationList = list_handling(args['location'])
    reportObj['location'] = []
    for location in locationList:
        code = geocoder.geonames(location, key='syntaxerror')
        locationObj = {"geonames_id": code.geonames_id}
        reportObj['location'].append(locationObj)
    
    newObj['reports'].append(reportObj)

    data.append(newObj)

    with open('output.json', "w+") as f:
        f.write(json.dumps(newObj, indent = 2))
        f.close()

    with open('final.json', "w+") as f:
        f.write(json.dumps(data, indent = 2))
        f.close()
    return newObj, 200

@api.response(200, "Sucess")
@api.response(400, "Invalid ID")
@APP.route('/delete/<int:article_id>', methods=['DELETE'])
def remove_result(article_id):
    if article_id >= len(data):
        return "Invalid ID", 200

    deleted = data[article_id]
    del data[article_id]
    with open('output.json', "w+") as f:
        f.write(json.dumps(deleted, indent=2))
        f.close()

    with open('final.json', "w+") as f:
        f.write(json.dumps(data, indent=2))
        f.close()
        
    return deleted, 200

@api.response(200,"Success")
@APP.route('/user/log', methods=['GET'])
def getUserLog():    
    return {"time":datetime.now(), "team_name": "SyntaxError", "data_source": 'http://outbreaks.globalincidentmap.com/'}



@api.response(200, 'Success')
@api.response(404, 'Log file not found')
@api.response(499, 'Invalid password provided')
@api.doc(parser=parser_log)
@APP.route('/admin/log', methods=['GET'])
def getAdminlog():
    args = parser_log.parse_args()
    if args['password'] != 'Syntax3rror':
        return "Invalid password", 499
    
    with open('admin.log') as log:
        return log.read()

if __name__ == "__main__":
    APP.run(debug = True,port = 8000)
    logging.basicConfig(filename='admin.log', level=logging.DEBUG)
    