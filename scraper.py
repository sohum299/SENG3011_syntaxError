import requests
import bs5
URL = "https://www.cdc.gov/outbreaks/"
r = requests.get(URL)
print(r.content)