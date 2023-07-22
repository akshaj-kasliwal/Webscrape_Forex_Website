import json
import time
from selenium import webdriver
import bs4
from bs4 import BeautifulSoup
from airtable import Airtable
from selenium.webdriver.chrome.options import Options
import requests
import re

k = 1

header = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) Chrome/109.0.0.0",
          'referer': 'https://www.earnforex.com'}
# Airtable configuration
AIRTABLE_PAT = "patW76CGPTxWdw78J.1777226e19418f26e75c4ee075ab891bdd451ffb453795a0a9034ec438c6f10d"
AIRTABLE_PAT_2 = "patcBa2Z4cyHGh2gv.89e85294028cbdf9fa3438c046d77f60d6d6e7e8aaed012ff3890afdd8902c57"

AIRTABLE_BASE_ID = "appTfzEkrciMKh5BI"
AIRTABLE_TABLE_NAME = "tbl2U68FveXNzp2ty"
PAYMENT_TABLE_NAME = "tblGZteFEx8Mpl01x"
LEVERAGE_TABLE_NAME = "tbl4kewFwyL9Rlycv"
OFFICE_TABLE_NAME = "tblDUt6UGHvLJPQzr"
PLATFORM_TABLE_NAME = "tblGWD3cAN9QoTZDz"
REGULATION_TABLE_NAME = "tbl8i1RFkqbwMcber"
CURRENCY_TABLE_NAME = "tblAVoQyz0VH79ukq"
TYPE_OF = 'mt4-forex-brokers'
earnfxurl = 'https://www.earnforex.com'

# Initialize Airtable
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, api_key=AIRTABLE_PAT)
global officeMap


# brokers_list =

# Scrape the desired data from the brokers list


def process_records(mapping, records):
    base_id = AIRTABLE_BASE_ID
    table_name = OFFICE_TABLE_NAME
    api_key = AIRTABLE_PAT
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    record_ids = []

    for record in records:
        name = record.get("Name")
        icon = record.get("Icon")
        if name in mapping:
            record_ids.append(mapping[name])
        else:
            converted_item = {
                "Name": name,
                "Icon": [
                    {
                        "url": icon
                    }
                ]
            }
            payload = {
                "records": [
                    {
                        "fields": converted_item
                    }
                ]
            }
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                added_record = response.json().get("records", [{}])[0]
                added_record_id = added_record.get("id")
                record_ids.append(added_record_id)
                mapping[name] = added_record_id
    return record_ids


def updateExistingRecord(existing_record_id, url, headers, Type_of):
    record_url = f"{url}/{existing_record_id}"
    response = requests.get(record_url, headers=headers)
    if response.status_code == 200:
        # Update the existing record
        existing_record = response.json()
        existing_type_of = existing_record["fields"].get("TYPE OF", "")
        if Type_of in existing_type_of:
            print("Record Already exists")
            return
        new_type_of = existing_type_of + ',' + Type_of
        payload = {
            "fields": {
                "TYPE OF": new_type_of
            }
        }
        response = requests.patch(record_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("Record updated successfully.")
        else:
            print("Failed to update record.")
    else:
        print("Failed to fetch existing record.")


def checkandUpdateIfexistsAndGoTonext(forxBrokerName, TypeOf):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    # Check if already exists :
    existing_record_id = check_duplicate(forxBrokerName)
    if existing_record_id:
        updateExistingRecord(existing_record_id, url, headers, TypeOf)
        return True
    return False


def get_and_push(URL, TYPEOF, mapping, sregMap, officemap):
    brokers_list = getMeBrokerList(URL)
    print("All cards from page: " + URL + " fetched")
    data = []

    broker_elements = brokers_list.find_all("div", class_="brokers-list__card")
    for broker in broker_elements:

        broker_data = {}
        name = broker.find("a", class_="brokers-list__broker-name").get_text(strip=True)
        broker_data['TYPE OF'] = TYPEOF
        broker_data['FOREX BROKER / SUBBROKER'] = name
        if checkandUpdateIfexistsAndGoTonext(name, TYPEOF):
            continue

        try:
            account_size = broker.find("div", class_="brokers-list__col").contents[-1].strip()
            broker_data['MIN. ACCOUNT SIZE'] = re.sub(r'\D', '', account_size)
        except:
            broker_data['MIN. ACCOUNT SIZE'] = ''
        try:
            rating = broker.find("div", class_="rating__nums").get_text(strip=True)
            broker_data['BROKER RATING'] = rating
        except:
            broker_data['BROKER RATING'] = ""
        # Three
        try:
            position_size = broker.find("div", class_="brokers-list__col", title="Min. Position Size").contents[
                -1].strip()
            broker_data['MIN. POSITION SIZE'] = position_size
        except:
            broker_data['MIN. POSITION SIZE'] = ""
        try:
            payment_elements = broker.find_all("span", class_="brokers-list__payment-name")
            broker_data['PAYMENT'] = []
            payments = []
            for payment_element in payment_elements:
                payment_type = payment_element.get_text(strip=True)
                payments.append(payment_type)
            broker_data['PAYMENT'] = payments
        except:
            broker_data['PAYMENT'] = []

        # Five
        try:
            broker_data['PAYMENT'] = list(map(lambda x: mapping[x], broker_data['PAYMENT']))
        except:

            print("Payment type error: " + broker_data['FOREX BROKER / SUBBROKER'])
            broker_data['PAYMENT'] = ""
            # Store the scraped data in Airtable

        # Six
        try:
            # broker_data['MAX. LEVERAGE'] = []
            div = broker.find("div", title="Max. Leverage")
            max_leverage = div.contents[-1].strip()
            broker_data['MAX. LEVERAGE'] = max_leverage
        except:

            # print("Payment type error: " + broker_data['MAX. LEVERAGE'])
            broker_data['MAX. LEVERAGE'] = ""

        # Seven
        try:
            div = broker.find("div", class_="brokers-list__plus")
            if div:
                sreg = '+'
            else:
                sreg = '-'
            broker_data['SERIOUS REGULATION'] = sregMap.get(sreg)
        except:

            print("Payment type error: " + broker_data['Name'])
            broker_data['SERIOUS REGULATION'] = ""

        # Eight
        rectangles = broker.find("div", title='Spread').find_all('rect')
        try:
            if rectangles[0]['fill'] == "#4FD1C5":
                broker_data['SPREAD'] = "Low"
            elif rectangles[1]['fill'] == "#4FD1C5":
                broker_data['SPREAD'] = "Medium"
            else:
                broker_data['SPREAD'] = "High"
        except:

            # Nine
            plusOrMinus = ''
        try:
            div = broker.find("div", title='US').find("div", class_="brokers-list__plus")
            if div:
                plusOrMinus = 'Yes'
            else:
                plusOrMinus = 'No'
            broker_data['US'] = plusOrMinus
        except:
            broker_data['US'] = ''

            # ten
        try:
            div = broker.find("div", title="Platforms").find_all('div')
            platform = ''
            platforms = ''
            for d in div:
                platform = d.get_text(strip=True)
                if not "Platform" in platform:
                    if platforms == '':
                        platforms = platform
                        continue
                    platforms = platforms + platform
            broker_data['PLATFORMS'] = platforms
        except:
            broker_data['PLATFORMS'] = ''
            # continue

        # eleven
        try:
            office_elements = broker.find("div", title="Offices in").find_all('div', class_="tooltip")
            broker_data['OFFICES IN'] = []
            offices = []
            for office_element in office_elements:
                office = office_element.find("div", class_="tooltip__modal").get_text(strip=True)
                offices.append(officemap.get(office))
            broker_data['OFFICES IN'] = offices
        except:
            broker_data['OFFICES IN'] = []
        # print("Payment type error: " + broker_data['MAX. LEVERAGE'])

        # twelve
        try:
            div = broker.find("div", title="Regulation").find_all('div')
            # regulations = []
            for d in div:
                regulation = d.get_text(strip=True)
                if not "Regulation" in regulation:
                    if regulations == '':
                        regulations = regulation
                        continue
                    regulations = regulation + ',' + regulations
            if len(regulations) > 0:
                broker_data['REGULATION'] = regulations
        except:
            broker_data['REGULATION'] = []
        # Store the scraped data in Airtable

        # Thirteen Currency pair And Currency
        try:
            childURL = broker.find("a", class_='brokers-list__broker-name').get('href')

            broker_data['CURRENCY PAIRS'], broker_data['ACCOUNT CURRENCIES'], descriptionString, broker_data[
                'COMPANY'], OfficesIn, Regulations, WebLanguage, platforms = getFromChild_(
                childURL)
            description_lines = descriptionString.strip().split('\n')
            formatted_description = '\n'.join([f'- {line.strip()}' for line in description_lines])
            if len(broker_data['OFFICES IN']) == 0:
                broker_data['OFFICES IN'] = process_records(officemap, OfficesIn)
            if len(broker_data['REGULATION']) == 0:
                broker_data['REGULATION'] = Regulations
            broker_data['WEBSITE LANGUAGES'] = WebLanguage
            if len(broker_data['PLATFORMS']) == 0:
                broker_data['PLATFORMS'] = platforms

            try:
                broker_data['FEATURES'] = formatted_description
            except:
                print("Error getting features for :" + broker_data['FOREX BROKER / SUBBROKER'])
                broker_data['CURRENCY PAIRS'] = ''
                broker_data['FEATURES'] = ''
        except:
            broker_data['CURRENCY PAIRS'] = ''
            broker_data['ACCOUNT CURRENCIES'] = ''

        # FINAL Save all
        data.append(broker_data)

    data = [i for n, i in enumerate(data)
            if i not in data[n + 1:]]

    for item in data:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT_2}",
            "Content-Type": "application/json"
        }
        # Check if already exists :
        existing_record_id = check_duplicate(item['FOREX BROKER / SUBBROKER'])
        if item['FOREX BROKER / SUBBROKER'].upper().__contains__("Trader's Way"):
            print("Check Trader's way")
        if existing_record_id:
            try:
                updateExistingRecord(existing_record_id, url, headers)
                continue
            except:
                continue

        # Go ahead normally
        payload = {
            "fields": item
        }
        try:
            if item['FOREX BROKER / SUBBROKER'] == 'Capital.com':
                print("Reached Capital.com")
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                print(f"Data stored successfully: {item}")
            else:
                print(f"Error storing data: {response.text}")
        except:
            print(f'Failed for: ' + item['FOREX BROKER / SUBBROKER'])

    print("Data stored in Airtable successfully.")


def getCardElementfromname(soup_child, cardType):
    k = soup_child.find('div', class_='broker-card --full-height')
    next = k.nextSibling.next_siblings
    for p in next:
        if not isinstance(p, bs4.element.NavigableString):
            # print(type(p))
            if p.contents[0].get_text(strip=True) == cardType:
                return p
            else:
                continue
        else:
            continue
    print(f'Card Type {cardType} not found')
    return None


# ChildFun

def getFromChild_(childUrl):
    str_pair = ''
    str_curen2 = ''
    description = ''
    OfficesIn = []
    Regulations = ''
    WebLanguage = ''
    platforms = ''
    try:
        r = requests.get(earnfxurl + childUrl)
        soup_child = BeautifulSoup(r.content, "html.parser")
        curreencyelementset = soup_child.find_all('div', class_='broker-card --full-height --set-width')[1].find_all(
            'div', class_='broker-card__col-content')
        curreencyelementset_2 = soup_child.find_all('div', class_='broker-card --full-height --set-width')[0].find_all(
            'div', class_='broker-card__col-content')
        description_element = soup_child.find_all('li', class_='broker__feature')

        for element in curreencyelementset_2:
            currency = element.get_text(strip=True)[:3]
            if str_curen2 == '':
                str_curen2 = currency
                continue
            str_curen2 = str_curen2 + "," + currency

        for element in curreencyelementset:
            currency = element.get_text(strip=True)
            if str_pair == '':
                str_pair = currency
                continue
            str_pair = str_pair + "," + currency

        try:
            for element in description_element:
                feature = element.get_text(strip=True)
                if description == '':
                    description = feature
                    continue
                description = feature + "\n" + description
        except:
            print("Error fetching description from : " + childUrl)
            description = ''

        # OfficesIn
        try:
            OfficesIn_elements = getCardElementfromname(soup_child, "Offices in").find_all('div',
                                                                                           class_='broker-card__col')
            for element in OfficesIn_elements:
                office_dict = {}
                image = element.find('img')['src']
                office_dict['Name'] = element.get_text(strip=True)
                office_dict['Icon'] = "https://www.earnforex.com" + image
                OfficesIn.append(office_dict)
        except:
            print("Error fetching Offices from : " + childUrl)
            description = ''

        # Regulations
        try:
            Regulations_elements = getCardElementfromname(soup_child, "Regulated by").find_all('div',
                                                                                               class_='broker-card__col-text --bold')
            for element in Regulations_elements:
                regulation = element.get_text(strip=True)
                if Regulations == '':
                    Regulations = regulation
                    continue
                Regulations = Regulations + "," + regulation
        except:
            print("Error fetching Regulation from : " + childUrl)

        # WebLanguage
        try:
            WebLanguage_elements = getCardElementfromname(soup_child, "Website available in").find_all('div',
                                                                                                       class_='broker-card__col-text --bold')
            for element in WebLanguage_elements:
                language = element.get_text(strip=True)
                if WebLanguage == '':
                    WebLanguage = language
                    continue
                WebLanguage = WebLanguage + "," + language
        except:
            print("Error fetching description from : " + childUrl)
            WebLanguage = ''

        companyInfo = ''
        try:
            companyName = soup_child.find('div', class_='broker-card__col-text --bold').get_text(strip=True)
            companySince = soup_child.find_all('div', class_='broker-card__col-text')[1].contents[0].get_text(
                strip=True)
            companySince_2 = soup_child.find_all('div', class_='broker-card__col-text')[1].contents[2].get_text(
                strip=True)
            companyInfo = companyName + "\n" + companySince + "\n" + companySince_2

        except:
            print("Error getting company from: " + earnfxurl + childUrl)

        try:
            platform_ele = getCardElementfromname(soup_child, 'Demo platforms').find_all('div',
                                                                                         class_='broker-card__col-text --bold')
            for element in platform_ele:
                platform = element.get_text(strip=True)
                if platforms == '':
                    platforms = platform
                    continue
                platforms = platforms + "," + platform
        except:
            print("Didnt Find Platform for " + childUrl)

        return str_pair.replace(" ", ""), str_curen2.replace(" ",
                                                             ""), description, companyInfo, OfficesIn, Regulations, WebLanguage, platforms


    except:
        try:
            curreencyelementset = soup_child.find_all('div', class_='broker-card --set-width')[
                0].find_all('div', class_='broker-card__col-content')
            for element in curreencyelementset:
                currency = element.get_text(strip=True)
                if str_pair == '':
                    str_pair = currency
                    continue
                str_pair = str_pair + "," + currency
            return str_pair.replace(" ", ""), str_curen2.replace(" ",
                                                                 ""), description, companyInfo, OfficesIn, Regulations, WebLanguage, platforms
        except:
            return str_pair, str_curen2, description, companyInfo, OfficesIn, Regulations, WebLanguage, platforms


###############MAPPING#################################################
def fetch_currency_record_ids():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{LEVERAGE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        records = data.get("records", [])
        lev_mapping = {}
        for record in records:
            payment_type = record.get("fields", {}).get("Name")
            record_id = record["id"]
            if payment_type:
                lev_mapping[payment_type] = record_id
        return lev_mapping
    else:
        # Add the entry here
        print("No need for now")
    return {}


def fetch_payment_record_ids():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{PAYMENT_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        records = data.get("records", [])
        payment_mapping = {}
        for record in records:
            payment_type = record.get("fields", {}).get("Name")
            record_id = record["id"]
            if payment_type:
                payment_mapping[payment_type] = record_id
        return payment_mapping
    return {}


def fetch_platform_record_ids():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{PLATFORM_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        records = data.get("records", [])
        payment_mapping = {}
        for record in records:
            payment_type = record.get("fields", {}).get("Name")
            record_id = record["id"]
            if payment_type:
                payment_mapping[payment_type] = record_id
        return payment_mapping
    return {}


def fetch_maxLev_record_ids():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{LEVERAGE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        records = data.get("records", [])
        lev_mapping = {}
        for record in records:
            payment_type = record.get("fields", {}).get("Name")
            record_id = record["id"]
            if payment_type:
                lev_mapping[payment_type] = record_id
        return lev_mapping
    return {}


def fetch_office_record_ids():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{OFFICE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        records = data.get("records", [])
        lev_mapping = {}
        for record in records:
            payment_type = record.get("fields", {}).get("Name")
            record_id = record["id"]
            if payment_type:
                lev_mapping[payment_type] = record_id
        return lev_mapping
    return {}


def fetch_regulation_record_ids():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{REGULATION_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        records = data.get("records", [])
        lev_mapping = {}
        for record in records:
            payment_type = record.get("fields", {}).get("Name")
            record_id = record["id"]
            if payment_type:
                lev_mapping[payment_type] = record_id
        return lev_mapping
    return {}


def fetch_sreg_record_ids():
    sregmap = {}
    sregmap['+'] = 'Yes'
    sregmap['-'] = 'No'
    return sregmap


def check_duplicate(broker_name):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT_2}",
        "Content-Type": "application/json"
    }
    params = {
        "filterByFormula": "AND({FOREX BROKER / SUBBROKER} =" + "'" + broker_name + "'" + ")"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        records = response.json().get('records')
        if records:
            return records[0]['id']  # Return the ID of the existing record
    return None


def getBrokerTypeMappingAndLinks():
    print("Getting all broker Type Of ...")
    response = requests.get(earnfxurl)
    main_soup = BeautifulSoup(response.content, "html.parser")
    links = main_soup.find_all("div", class_='menu__sub-menu-col')
    main_map = []
    for link in links:
        linkDict = {}
        linkDict['TypeOf'] = link.get_text(strip=True)
        linkDict['Link'] = earnfxurl + link.find('a').get('href')
        main_map.append(linkDict)
    return main_map


def getMeBrokerList(URL):
    # Configure Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    print("Getting Data")
    # Set up Selenium WebDriver
    driver = webdriver.Chrome(options=chrome_options)  # Replace with the appropriate WebDriver for your OS and browser
    driver.get(URL)
    time.sleep(15)  # Adjust the delay as needed
    # Get the page source after the delay
    html = driver.page_source
    # Close the browser
    driver.quit()
    print("Getting Data Completed ...")
    # Parse the HTML with Beautiful Soup
    soup = BeautifulSoup(html, "html.parser")

    # Find the element containing the brokers list
    brokers_list = soup.find("div", id="brokers-list")
    return brokers_list


if __name__ == '__main__':
    allLinks = []
    allLinks = getBrokerTypeMappingAndLinks()
    i = 0
    j = 31
    mapping = fetch_payment_record_ids()
    sregMap = fetch_sreg_record_ids()
    officemap = fetch_office_record_ids()
    allLinks = allLinks[i:j]
    i = 1
    for links in allLinks:
        print(
            f'******************************************Progress {i}/30   *******************************************')
        get_and_push(links['Link'], links['TypeOf'], mapping, sregMap, officemap)
        i = i + 1
