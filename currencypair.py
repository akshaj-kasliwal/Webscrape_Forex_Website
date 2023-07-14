import json
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from airtable import Airtable
from selenium.webdriver.chrome.options import Options
import requests
import re


# Airtable configuration
AIRTABLE_PAT = "patW76CGPTxWdw78J.1777226e19418f26e75c4ee075ab891bdd451ffb453795a0a9034ec438c6f10d"
AIRTABLE_BASE_ID = "appTfzEkrciMKh5BI"
AIRTABLE_TABLE_NAME = "tblAVoQyz0VH79ukq"
URL = "https://www.earnforex.com/mt4-forex-brokers/"
url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
URL = "https://www.earnforex.com/forex-brokers/CedarFX/"
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
driver = webdriver.Chrome(options=chrome_options)  # Replace with the appropriate WebDriver for your OS and browser
driver.get(URL)
time.sleep(10)  # Adjust the delay as needed
html = driver.page_source # Get the page source after the delay
driver.quit() # Close the browser
# Parse the HTML with Beautiful Soup
soup = BeautifulSoup(html, "html.parser")
# Find the element containing the brokers list

# Scrape the desired data from the brokers list
brokers_list = soup.find("div", class_="broker-card__content", style="max-height: 39px;")
data = []
all_data = []
currencies = brokers_list.find_all("div", class_="broker-card__col")

payload = []
maxleverage = {}
for currency in currencies:
    # Extract the maxLev from each broker card
    pair ={}
    pair['Name'] = currency.find("div", class_="broker-card__col-text --bold").get_text(strip=True)
    payload.append(pair)
# Remove dupes
res_list = [i for n, i in enumerate(payload)
            if i not in payload[n + 1:]]


url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

# Set up headers with the Personal Access Token
headers = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

# Update each record in the Airtable table
for record in res_list:
    payload = {
        "records": [
            {
                "fields": record
            }
        ]
    }
    json_payload = json.dumps(payload)
    response = requests.post(url, data=json_payload, headers=headers)
    # time.sleep(3)
    if response.status_code == 200:
        print(f"Record updated successfully: {record}")
    else:
        print(f"Error updating record: {response.text}")
