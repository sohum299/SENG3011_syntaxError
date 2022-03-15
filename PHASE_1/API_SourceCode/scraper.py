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
from newspaper import Article 
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

def generateReport(text): 
  #print(text)
  """
  diseases: [<string::disease>],
  syndromes: [<string::syndrome>],
  event_date: <string::date>,
  locations: [<object::location>],
  """

  # tokenise by sentence
  sentences = sent_tokenize(text)

  # tokenise the words
  # remove stop_words such as "a", "in", "as", "the", etc
  stop_words = set(stopwords.words("english"))
  filtered_words = []
  for words in word_tokenize(text):
    if words.casefold() not in stop_words:
      filtered_words.append(words)


  # reduce words to their stem. E.g. "helper" and "helping" becomes "help"
  lemmatizer = WordNetLemmatizer()
  lemmatize_words = []
  for word in filtered_words:
    lemmatize_words.append(lemmatizer.lemmatize(word))

  tagged_words = nltk.pos_tag(lemmatize_words)
  tree = nltk.ne_chunk(tagged_words)
  #tree.draw()
  #print(lemmatize_words)

  #print(tagged_words)
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
        entities = locationtagger.find_locations(text = sentence.lower())
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
            
  eventDate = ""   
  matches = datefinder.find_dates(text)
  Times = []
  for match in matches:
    Times.append(match)
  if len(Times) != 0:
    eventDate = Times[0].strftime("%m/%d/%Y, %H:%M:%S")
    
    
  if len(DiseaseList) == 0:
    DiseaseList.append("other")
  f.close()

  f = open("syndrome_list.json","r") 
  syndromes = json.load(f)
  for word in syndromes:
    #print(word)
    for sentence in sentences:
      if word['name'].lower() in sentence.lower() and word['name'] not in SyndromeList:
        SyndromeList.append(word['name'])

  eventType = []
  for word in lemmatize_words:
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

  # print(SyndromeList)
  # use lat/long for location
  # use disease/syndrome list for diseases/syndromes
  # look for an ordinal for a case number 
  # look for event-type things 
  #print(LocationList.country_regions)
  return {"diseases": DiseaseList, "syndromes": SyndromeList, "event_date": eventDate, "EventType": eventType, "Locations": LocationList}
"""
  for t in tree:
    for c in t:
      if hasattr(t, 'label') and t.label() == "GPE":
        LocationList.append(c[0])
        for sentence in sentences:
          if c[0] in sentence:
            locationSentences.append(sentence)
            print(f"{sentence}")

""" 


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

with open('rawData.html',"r",encoding = "ISO-8859-1") as f:
    linkdata = re.search(r'var incidents = \[(.*)\]', f.read(), re.MULTILINE|re.DOTALL)
    finaldata = open('rawData.txt', 'w',encoding="utf-8")
    finaldata.write(linkdata[1])
    finaldata.close()
    f.close

with open('rawData.txt') as f:
  dataStore = eval(f.read())
f.close()

for article in dataStore:
  soup = BeautifulSoup(article['Description'], "html.parser")
  
  text = soup.get_text()
  text = text.split('] ')[1]
  text = text.split('Read')[0]
  
  main_string = ""
  valid=validators.url(article["URL"])
  if valid:
    req = requests.get(article["URL"])
  if req.status_code == 200:
    soup = BeautifulSoup(req.content, 'html.parser')


  currArticle = Article(article["URL"])
  currArticle.download()
  currArticle.parse()
  currArticle.nlp()
  main_string = currArticle.text
  main_string = re.sub('\n', ' ', main_string)
  main_string = unidecode(main_string)
  
  if main_string != "":
    report = generateReport(main_string)
  else:
    report = generateReport(text)

  
  FinalDict = {"URL": article['URL'], "date_of_publication":article['DateTime'], "headline": article['TipText'],"main_text":main_string, "Description": text, "reports":report}
  with open("final.json", "a+") as f:
    json.dump(FinalDict,f, indent=2)
    f.write('\n')

