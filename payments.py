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
AIRTABLE_PAT =  "patW76CGPTxWdw78J.1777226e19418f26e75c4ee075ab891bdd451ffb453795a0a9034ec438c6f10d"
AIRTABLE_BASE_ID = "appTfzEkrciMKh5BI"
AIRTABLE_TABLE_NAME = "tblGZteFEx8Mpl01x"
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
all_data=[]
broker_elements = brokers_list.find_all("div", class_="brokers-list__card")

paymentType = {}
payments_broker =[]
pay_allbrokers=[]
broker_elements = brokers_list.find_all("div", class_="brokers-list__card")
for broker in broker_elements:
    # Extract the payment types
    payment_listrows = broker.find_all("li", class_="brokers-list__payment-item")
    payments = []
    payments_broker=[]
    for row in payment_listrows:
        paymentType={}
        payment_type_name = row.find("span", class_="brokers-list__payment-name").get_text(strip=True)
        image = row.find('img')['src']
        paymentType['Name'] = payment_type_name
        paymentType['Image'] = "https://www.earnforex.com" + image
        payments_broker.append(paymentType)
    pay_allbrokers = pay_allbrokers + payments_broker


res_list = [i for n, i in enumerate(pay_allbrokers)
            if i not in pay_allbrokers[n + 1:]]
converted_data = []

for item in res_list:
    converted_item = {
        "Name": item["Name"],
        "Image": [
            {
                "url": item["Image"]
            }
        ]
    }
    converted_data.append(converted_item)
converted_data = [i for n, i in enumerate(converted_data)
                  if i not in converted_data[n + 1:]]

# Airtable configuration

# List of dictionaries with "Name" and "Image" keys


# Airtable API endpoint URL
url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

# Set up headers with the Personal Access Token
headers = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

# Update each record in the Airtable table
for record in converted_data:
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
