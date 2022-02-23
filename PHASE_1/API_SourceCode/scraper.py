from time import sleep
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select

def scrapeSite(key_terms, location):
  URL = "http://outbreaks.globalincidentmap.com/"  
  browser = webdriver.Chrome('./chromedriver.exe')
  browser.get(URL)
  keys = Select(browser.find_element_by_name("type"))
  keys.select_by_visible_text(key_terms)
  city = Select(browser.find_element_by_name("country"))
  city.select_by_visible_text(location)
  browser.find_element_by_name("clicktype").click()
  with open('rawData.html', 'w') as w:
    w.write(browser.page_source)

scrapeSite("Coronavirus", "AU")