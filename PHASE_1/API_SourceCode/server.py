'''
Server file that contains the flask implementation.
'''
import re
import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_restx import Resource, Api, reqparse
from flask_cors import CORS
from json import dumps
import geocoder
import locationtagger


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

# class Manager(object):
#     def __init__(self, data):
#         self.articles = data
#         self.n = len(data)

#     def findArticle(self, n):
#         for article in self.articles:
#             if article['ID'] == n:
#                 return article
#         return None

parser = reqparse.RequestParser()

# PARSER DOCUMENTATION 

'''
    Arguments for filtering reports
'''
parser_report = parser.copy()
parser_report.add_argument('n', type=int, help='Max number of results', location='args')
parser_report.add_argument('location', type=str, help='Location', location='args')
parser_report.add_argument('key_terms', type=str, help='List of key terms', location='args')
parser_report.add_argument('start_date', type=str, help='Start date of date range (yyyy-mm-ddThh:mm:ss)', location='args')
parser_report.add_argument('end_date', type=str, help='End date of date range (yyyy-mm-ddThh:mm:ss)', location='args')

'''
    Arguments for creating reports
'''
parser_create = parser.copy()
parser_create.add_argument('url', type=str, required=True, help='Url of the event', location='args')
parser_create.add_argument('date_of_publication', type=str, required=True, help='Date of publication (yyyy-mm-ddThh:mm:ss)', location='args')
parser_create.add_argument('headline', type=str, required=True, help='Headline for the report', location='args')
parser_create.add_argument('main_text', type=str, required=True, help='Main text of the event', location='args')
parser_create.add_argument('disease', type=str, required=True, help='Comma separated list of diseases', location='args')
parser_create.add_argument('syndrome', type=str, required=False, help='Comma separated list of syndromes', location='args')
parser_create.add_argument('type', type=str, required=True, help='Type of event e.g death, infected', location='args')
parser_create.add_argument('location', type=str, required=True, help='location', location='args')
parser_create.add_argument('date', type=str, required=True, help='Date of the event (yyyy-mm-ddThh:mm:ss)', location='args')

'''
    Arguments for updating reports
'''
parser_update = parser.copy()
parser_update.add_argument('url', type=str, help='URL of report', location='args', required=False)
parser_update.add_argument('date_of_publication', type=str, help='Date of report publication', location='args', required=False)
parser_update.add_argument('headline', type=str, help='Headline of report', location='args', required=False)
parser_update.add_argument('main_text', type=str, help='Main text of report', location='args', required=False)
parser_update.add_argument('disease', type=str, help='Disease contained within report', location='args', required=False)
parser_update.add_argument('syndrome', type=str, help='Syndrome within report', location='args', required=False)
parser_update.add_argument('type', type=str, help='Type of report', location='args', required=False)
parser_update.add_argument('location', type=str, help='location in report', location='args', required=False)
parser_update.add_argument('date', type=str, help='Date of report', location='args', required=False)

data = []
with open('final.json',"r") as f:
    data = eval(f.read())
    f.close()

# articleList = Manager(data)


APP = Flask(__name__)
api = Api(APP, title = 'OUTBREAK', description = 'This API extracts disease reports from the Global Outbreak website')
CORS(APP)
APP.register_error_handler(Exception, defaultHandler)
parser = reqparse.RequestParser()
# app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
# Routes
@api.doc(parser=parser_report)
@api.response(200, "Sucess")
@api.response(400, "Invalid search")
@api.response(404, "Invalid date param")
@APP.route('/search', methods=['GET'])
def get_results():
    '''Fetch the reports from the database'''
    newResponse = []
    args = parser_report.parse_args()
    reportList = []
    LocationList = []
    if args['start_date'] is None or args['end_date'] is None:
        return "No Date Param", 400

    if re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', args['start_date']) is None:
            return "Invalid start-date", 404

    if re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', args['end_date']) is None:
        return "Invalid end-date", 404

    for report in data:
        keys = []
        LocationList = []
        if args['key_terms'] is not None:
            if ',' not in args['key_terms']:
                if args['key_terms'] in str(report['main_text']):     
                    pass
                else:
                    continue
            else:
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
                    # return country.geojson
                    if len(country.geojson['features']) == 0:
                        continue

                    if args['location'] == country.geojson['features'][0]['properties']['country']:
                        LocationList.append(args['location'])
                        pass
                    else:
                        for state in country.geojson['features']:
                            if args['location'] == state['properties']['address']:
                                LocationList.append(args['location'])

            if len(LocationList) == 0:
                continue
                # if args['location'] in str(report['main_text']):     
                #     pass
                # else:
                #     continue
        
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

            if datetime_event_date < datetime_start_date and datetime_event_date > datetime_end_date:
                continue
        reportList.append(report)                
    
    return json.dumps(reportList, indent=2)
# http://127.0.0.1:8080/search?start_date=2015-10-01T08:45:10&end_date=2015-11-01T19:37:12
@APP.route('/results/<int:article_id>', methods=['GET'])
def get_result(article_id):
    '''Fetch the report of the given id from the database'''
    return json.dumps(data[article_id], indent=2)


@APP.route('/update/result', methods=['POST'])
def update_result():
    
    '''A report with the given parameters'''
    return "Updated Report"


@APP.route('/add/result', methods=['POST'])
def add_result():
    '''Add a new report with the given parameters'''
    return "Added Report"

@APP.route('/results/<int:article_id>', methods=['DELETE'])
def remove_result(article_id):

    return 'Deleted Report'



if __name__ == "__main__":
    APP.run(port=8080)