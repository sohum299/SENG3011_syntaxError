from time import sleep
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
import re
import json
import validators 
import requests

#URL = "http://outbreaks.globalincidentmap.com/"  
#browser = webdriver.Chrome('C:\chromedriver\chromedriver.exe')
#browser.get(URL)
#keys = Select(browser.find_element_by_name("TimeScale"))
#keys.select_by_value("All")
#browser.find_element_by_name("Submit").click()
#with open('rawData.html', 'w', encoding="utf-8") as w:
  #w.write(browser.page_source)

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
  FinalDict = {"URL": article['URL'], "date_of_publication":article['DateTime'], "headline": article['TipText'],"main_text":main_string, "Description": text}
  with open("final.json", "a+") as f:
    json.dump(FinalDict,f, indent=2)
    f.write('\n')

    