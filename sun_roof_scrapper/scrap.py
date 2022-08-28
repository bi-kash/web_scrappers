from webbrowser import get
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import sys
import pandas as pd
import numpy as np
import re
from concurrent.futures import ThreadPoolExecutor
from time import sleep



def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = True

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    #chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)
    return driver


def extract_number_from_string(string):
    return ''.join(filter(lambda i: i.isdigit(), string))

def scrap(search_url, driver, wait):
    # Search for a web page
    driver.get(search_url)

    # maximize browser window
    
    try:
        wait.until(lambda driver: driver.find_element(By.TAG_NAME, "address-search").get_attribute("placeholder-text")!='')
        location = driver.find_element(By.TAG_NAME, "address-search").get_attribute("placeholder-text")
    except Exception as e:
        print("exception", e)
        try:
            sleep(2)
            location = driver.find_element(By.TAG_NAME, "address-search").get_attribute("placeholder-text")
        except:
            location = np.nan

 
    
    try:
        facts = driver.find_elements(By.CLASS_NAME, "panel-fact-text.md-body")
        sunlight_hours = extract_number_from_string(facts[0].text)
        sq_feet = extract_number_from_string(facts[1].text)
    except:
        sunlight_hours = np.nan
        sq_feet = np.nan
    
    return location, sunlight_hours, sq_feet
    
all_dfs = []
def crawl(dfs):
    driver = get_driver()
    wait = WebDriverWait(driver, 10)
   
    dfs["location"] = np.nan

    locations = []
    sunlight_hours = []
    area = []
    loc_x = dfs.x
    loc_y = dfs.y
    for index, roof_top in dfs.iterrows():
        try:
            y = str(roof_top['y'])
            x = str(roof_top['x'])
            search_url = f'https://sunroof.withgoogle.com/building/{y}/{x}/#?f=buy'

            loc, sun_hours, sq_feet = scrap(search_url, driver, wait)
            #loc = scrap(search_url, driver, wait)
            locations.append(loc)
            sunlight_hours.append(sun_hours)
            area.append(sq_feet)

        except Exception as e:
            pass
            
    
    dfs["location"] = locations
    dfs["sunlight hours"] = sunlight_hours
    dfs["sq feet"] = area
    all_dfs.to_csv('sun_roof_scrapper/scrapped.csv')
    driver.quit()
    


#roof_tops = pd.read_csv('CT_RoofTops08232022.csv')
roof_tops = pd.read_csv('sun_roof_scrapper/upload.csv')

max_workers=16
roof_tops = roof_tops[:]
list_df = np.array_split(roof_tops, max_workers)

del roof_tops

with ThreadPoolExecutor(max_workers = max_workers) as executor:
    executor.map(crawl, list_df)
