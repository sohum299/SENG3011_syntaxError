from time import sleep
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
import re
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
print(dataStore[3]['Description'])
for article in dataStore:
  
