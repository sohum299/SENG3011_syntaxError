'''
Helper functions
'''
from datetime import datetime
import re

def handle_date_parameter(args):
  # Date error handling
  if args['start_date'] is None or args['end_date'] is None:
    return False

  if re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', args['start_date']) is None:
    return False

  if re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', args['end_date']) is None:
    return False
  return True

def is_date_valid(start, end):
  currDate = datetime.now()
  if start > currDate or end > currDate:
    return False
  
  if start > end:
    return False
  return True

def is_date_valid2(date):
  if re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', date) is None:
    return False
  return True

def list_handling(string):
    returnList = string.split(',')
    return returnList