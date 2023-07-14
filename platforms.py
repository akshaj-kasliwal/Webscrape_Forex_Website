import json
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from airtable import Airtable
from selenium.webdriver.chrome.options import Options
import requests
import re
import pandas

# Airtable configuration
AIRTABLE_PAT = "patW76CGPTxWdw78J.1777226e19418f26e75c4ee075ab891bdd451ffb453795a0a9034ec438c6f10d"
AIRTABLE_BASE_ID = "appTfzEkrciMKh5BI"
AIRTABLE_TABLE_NAME = "tblGWD3cAN9QoTZDz"
URL = "https://www.earnforex.com/mt4-forex-brokers/"
# Define the Airtable API endpoint URL
url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

URL = "https://www.earnforex.com/mt4-forex-brokers/"

# Initialize Airtable
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, api_key=AIRTABLE_PAT)

# Configure Chrome options for headless browsing
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode

# Set up Selenium WebDriver
driver = webdriver.Chrome(options=chrome_options)  # Replace with the appropriate WebDriver for your OS and browser
driver.get(URL)

time.sleep(15)  # Adjust the delay as needed

# Get the page source after the delay
html = driver.page_source

# Close the browser
driver.quit()

# Parse the HTML with Beautiful Soup
soup = BeautifulSoup(html, "html.parser")

# Find the element containing the brokers list
brokers_list = soup.find("div", id="brokers-list")

# Scrape the desired data from the brokers list
data = []
all_data = []
broker_elements = brokers_list.find_all("div", class_="brokers-list__card")
i=0
payload = []
platforms = []

maxleverage = {}
for broker in broker_elements:
    # Extract the maxLev from each broker card

    platform = {}
    try:
        div = broker.find("div", title="Platforms").find_all('div')
        for d in div:
            platform['Name'] = d.get_text(strip=True)
            if not "Platform" in platform:
                platforms.append(platform)
    except:
        i = i+1
        print(i)
        continue


# Remove dupes
res_list = [i for n, i in enumerate(platforms)
            if i not in platforms[n + 1:]]

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
