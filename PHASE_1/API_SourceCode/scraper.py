from time import sleep
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
import re
import json
import validators
import requests
import locationtagger
import nltk
import ssl
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer




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
  f = open("disease_list.json","r") 
  data = json.load(f)
  for word in data:
    #print(word)
    for sentence in sentences:
      if word['name'].lower() in sentence.lower() and word['name'] not in DiseaseList:
        DiseaseList.append(word['name'])
  print(DiseaseList)

  # use lat/long for location
  # use disease/syndrome list for diseases/syndromes
  # look for an ordinal for a case number 
  # look for event-type things 
  LocationList = locationtagger.find_locations(text = text.lower())
  print(LocationList.regions, LocationList.country_cities, LocationList.countries)
  locationSentences = []
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
    main_body = soup.findAll('p')
    for tag in main_body:
      main_string = main_string + tag.text.strip()
  
  report = generateReport(text)
  FinalDict = {"URL": article['URL'], "date_of_publication":article['DateTime'], "headline": article['TipText'],"main_text":main_string, "Description": text}
  with open("final.json", "a+") as f:
    json.dump(FinalDict,f, indent=2)
    f.write('\n')

