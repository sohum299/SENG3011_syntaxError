from time import sleep
from tkinter import EventType
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from unidecode import unidecode
from datetime import datetime
import re
import geocoder
import json
import validators
import requests
import locationtagger
from newspaper import Article, Config 
import nltk
import ssl
import unicodedata
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import datefinder
from datetime import datetime

#extract a list of locations, match it to the original text 
#split the string so that its just that sentence
# look for number of cases/Disease/Syndrome + conjunction/disjunction

def getEventType(stem_words):
  eventType = []
  for word in stem_words:
    word.lower()
    if word in ["death", "lose","fatality", "pass away"] and "Death" not in eventType:
      eventType.append("Death")
    elif word in ["outbreak", "detect"] and "Presence" not in eventType:
      eventType.append("Presence")
    elif word in ["report", "spread", "infect"] and "Infected" not in eventType:
      eventType.append("Infected")
    elif word in ["hospitalize"] and "Hospitalised" not in eventType:
      eventType.append("Hospitalised")
    elif word in ["recover"] and "Recovered" not in eventType:
      eventType.append("Recovered")

  return eventType

# tokenise the words
# remove stop_words such as "a", "in", "as", "the", etc
# reduce words to their stem. E.g. "helper" and "helping" becomes "help"
def getStemWords(text):
  stop_words = set(stopwords.words("english"))
  stems = []
  stemmer = WordNetLemmatizer()
  for words in word_tokenize(text):
    if words.casefold() not in stop_words:
      stems.append(stemmer.lemmatize(words))

  return stems

def getEventDate(text):
  eventDate = datetime.today().strftime('%Y-%m-%d')
  matches = datefinder.find_dates(text)
  Times = []
  for match in matches:
    Times.append(match)
  if len(Times) != 0:
    eventDate = Times[0].strftime("%m/%d/%Y %H:%M:%S")
    eventDate = eventDate.replace(" ", "T")
    eventDate = eventDate.replace("/", "-")
    

  return eventDate


def getLocations(text, LocationList):
  entities = locationtagger.find_locations(text = text.lower())
  cityList = entities.cities
  regionList = entities.regions
  countryList = entities.countries
  if len(cityList) == 0 and len(regionList) == 0:
    for country in countryList:
      g = geocoder.geonames(country, key='syntaxerror')
      LocationList.append({"geonames_id":g.geonames_id})
    
  elif len(cityList) == 0 and len(regionList) != 0:
    for region in regionList:
      g = geocoder.geonames(region, key='syntaxerror')
      LocationList.append({"geonames_id":g.geonames_id})
  else: 
    for city in cityList:
      g = geocoder.geonames(city, key='syntaxerror')
      LocationList.append({"geonames_id":g.geonames_id})

  return LocationList
  

def generateReport(text, description): 

  # tokenise by sentence
  sentences = sent_tokenize(text)

  DiseaseList = []
  SyndromeList = []
  LocationList = []
  ReportList = []
  PosConjunctions = ['or', '']
  #finds disease, finds location associated with disease
  # if location already exists in report list, append disease to that report
  # if Disease mentioned again but new location not in location list, then append new location to existing disease

  f = open("disease_list.json","r") 
  data = json.load(f)
  for word in data:
    for sentence in sentences:
      if word['name'].lower() in sentence.lower() and word['name'] not in DiseaseList:
        DiseaseList.append(word['name'])
        LocationList = getLocations(sentence, LocationList)
            
  
  if len(DiseaseList) == 0:
    DiseaseList.append("other")
    LocationList = getLocations(description, LocationList)
  f.close()

  f = open("syndrome_list.json","r") 
  syndromes = json.load(f)
  for word in syndromes:
    #print(word)
    for sentence in sentences:
      if word['name'].lower() in sentence.lower() and word['name'] not in SyndromeList:
        SyndromeList.append(word['name'])
        LocationList = getLocations(sentence, LocationList)

  
  eventDate = getEventDate(text)
  eventType = getEventType(getStemWords(text))

  # print(SyndromeList)
  # use lat/long for location
  # use disease/syndrome list for diseases/syndromes
  # look for an ordinal for a case number 
  # look for event-type things 
  #print(LocationList.country_regions)
  return {"diseases": DiseaseList, "syndromes": SyndromeList, "event_date": eventDate, "EventType": eventType, "Locations": LocationList}



"""
URL = "http://outbreaks.globalincidentmap.com/"  
browser = webdriver.Chrome(ChromeDriverManager().install())
browser.get(URL)
keys = Select(browser.find_element_by_name("TimeScale"))
keys.select_by_value("All")
browser.find_element_by_name("Submit").click()
with open('rawData.html', 'w', encoding="utf-8") as w:
  w.write(browser.page_source)
"""

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
config = Config()
config.browser_user_agent = user_agent

with open('rawData.html',"r",encoding = "ISO-8859-1") as f:
    linkdata = re.search(r'var incidents = \[(.*)\]', f.read(), re.MULTILINE|re.DOTALL)
    finaldata = open('rawData.txt', 'w',encoding="utf-8")
    finaldata.write(linkdata[1])
    finaldata.close()
    f.close

with open('rawData.txt') as f:
  dataStore = eval(f.read())
f.close()

FinalList = []
for article in dataStore:
  soup = BeautifulSoup(article['Description'], "html.parser")
  
  text = soup.get_text()
  text = text.split('] ')[1]
  text = text.split('Read')[0]
  
  main_string = ""
  valid = False
  try:
    valid=validators.url(article["URL"])
  except:
    pass
  if valid:
    req = requests.get(article["URL"])
  if req.status_code == 200:
    try:
      currArticle = Article(article["URL"], config = config)
      currArticle.download()
      currArticle.parse()
      currArticle.nlp()
      main_string = currArticle.text
      main_string = re.sub('\n', ' ', main_string)
      main_string = unidecode(main_string)
    except:
      main_string = "Invalid"
      pass
  if main_string != "":
    report = generateReport(main_string, text)
  else:
    report = generateReport(text, text)
  
  # 1. Try print out one report per article 
  FinalDict = {"URL": article['URL'], "date_of_publication":article['DateTime'].replace(" ","T"), "headline": article['TipText'],"main_text":main_string, "Description": text, "reports":report}
  FinalList.append(FinalDict)
  with open("final.json", "w+") as f:
    json.dump(FinalList,f, indent=2)

