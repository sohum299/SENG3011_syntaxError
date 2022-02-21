import requests
from bs4 import BeautifulSoup
URL = "https://www.cdc.gov/outbreaks/"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')
print(soup.prettify())
