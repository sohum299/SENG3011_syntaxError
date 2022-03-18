from multiprocessing.dummy import Process
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

# def UniqueDisease(data,sentence, word):
#   DiseaseList = []
#   for disease in data: 
#     if disease["name"].lower() in sentence.lower() and disease["name"].lower() != word.lower():
#       DiseaseList.append(disease["name"])
#   return DiseaseList


# def HowManyReports(text):
#   sentences = sent_tokenize(text)
#   DiseaseList = {}
#   Uncertainty = ["or", "to be confirmed", "uncertain", "possibly",]
#   ExclusionList = ["similar to", "like", "same as", "identical", "parallel", "the same as", "alike", "resembling"]
#   ProcessedDiseases = []
#   f = open("disease_list.json","r") 
#   data = json.load(f)
#   for word in data:
#     if word in ProcessedDiseases:
#         continue
#     for sentence in sentences:
#       for similarity in ExclusionList:
#         sentence = sentence.lower()
#         if similarity in sentence:
#           safe, ignore = sentence.split(similarity)
#           if word["name"].lower() in ignore:
#             continue
#           elif word["name"] in safe and word['name'] not in ProcessedDiseases:
#             DiseaseList[word["name"]] = [word['name']]
#             ProcessedDiseases.append(word["name"])
#             break
          

#       if word['name'].lower() in sentence.lower() and word['name'] not in ProcessedDiseases:
#         if len(UniqueDisease(data, sentence, word['name'])) == 0:
#             DiseaseList[word["name"]] = [word["name"]]
#             ProcessedDiseases.append(word["name"])
#             break
#         else: 
#           for disease in UniqueDisease(data, sentence, word['name']):
#             if disease in ProcessedDiseases and disease in DiseaseList.keys() and word["name"] not in DiseaseList[disease]:
#               DiseaseList[disease].append(word['name'])
#               ProcessedDiseases.append(word['name'])
#               break
            
#           if any(word in sentence.lower() for word in Uncertainty):
#             DiseaseList[word["name"]] = UniqueDisease(data, sentence, word['name'])
#             DiseaseList[word["name"]].append(word["name"])
#             for disease in DiseaseList[word["name"]]:
#                 ProcessedDiseases.append(disease)
#             break
#           else:
#             DiseaseList[word["name"]] = [word['name']]
#             ProcessedDiseases.append(word["name"])
#             break
#   return DiseaseList

# def DiseaseFrequency(text):
#   f = open("disease.json","r") 
#   data = json.load(f)
#   words = getStemWords(text.lower())
#   dist = nltk.FreqDist(words)
#   dict = {}
  
#   for disease in data:
#     for word, frequency in dist.most_common(50):
#       if word.lower() == disease['name'].lower():
#         dict[word] = frequency

#   return dict
      



def getEventType(stem_words):
  eventType = []
  for word in stem_words:
    word.lower()
    if word in ["death", "lose","fatality", "pass away"] and "Death" not in eventType:
      eventType.append("Death")
    elif word in ["outbreak", "detect"] and "Presence" not in eventType:
      eventType.append("Presence")
    elif word in ["report", "spread", "infect", "symptoms"] and "Infected" not in eventType:
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
  matches = list(datefinder.find_dates(text))
  Times = []
  # for match in matches:
  #   Times.append(match)
  while True:
    try:
      match = next(matches)
    except TypeError as e:
      print(f"TypeError {e}")
      continue
    except StopIteration as e:
      print(f"StopIteration {e}")
      break
    except Exception as e:
      raise e
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
  

# def generateReport(text, description): 
#   # tokenise by sentence
#   sentences = sent_tokenize(text)

#   DiseaseList = []
#   SyndromeDict = {}
#   LocationList = []
#   LocationDict = {}
#   eventDate = {}
#   eventType = {}
#   ReportList = []

#   #finds disease, finds location associated with disease
#   # if location already exists in report list, append disease to that report
#   # if Disease mentioned again but new location not in location list, then append new location to existing disease
#   DiseaseDict = HowManyReports(text)
#   f = open("syndrome_list.json","r") 
#   syndromes = json.load(f)

#   data = DiseaseDict.keys()
#   for word in data:
#     LocationDict[word] = []
#     SyndromeDict[word] = []
#     eventType[word] = []
#     for sentence in sentences:
#       if word.lower() in sentence.lower():
#         LocationList = getLocations(sentence, LocationList)
#         for Location in LocationList:
#           if Location not in LocationDict[word]:
#            LocationDict[word].append(Location)
#         for syndrome in syndromes:
#           if syndrome["name"].lower() in sentence.lower() and syndrome["name"] not in SyndromeDict[word]:
#             SyndromeDict[word].append(syndrome["name"])
#         eventDate[word]= getEventDate(text)
#         EventList = getEventType(sentence)
#         for event in EventList:
#           if eventType not in eventType[word]:
#             eventType[word].append(event)
  

#   if len(DiseaseDict.keys()) == 0:
#     DiseaseDict["other"] = ["other"]
#     LocationDict["other"] = getLocations(description, LocationList)
#     SyndromeDict["other"] = []
#     for word in syndromes:
#       for sentence in sentences:
#         if word['name'].lower() in sentence.lower() and word['name'] not in SyndromeDict["other"]:
#           SyndromeDict["other"].append(word['name'])
#     eventDate["other"] = getEventDate(text)
#     eventType["other"] = getEventType(getStemWords(text))
  
#   for key in DiseaseDict.keys():
    
#     ReportList.append({"diseases":DiseaseDict[key], "syndromes": SyndromeDict[key], "event_date": eventDate[key], "event_type":eventType[key], "location": LocationDict[key]})

  # print(SyndromeList)
  # use lat/long for location
  # use disease/syndrome list for diseases/syndromes
  # look for an ordinal for a case number 
  # look for event-type things 
  #print(LocationList.country_regions)


    # return ReportList



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
    try:
      req = requests.get(article["URL"])
    except:
      pass
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

