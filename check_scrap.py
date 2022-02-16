# Import necessary modules

from webbrowser import get
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import sys
import pandas as pd
import re

def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = False

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    #chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)
    return driver

driver = get_driver()

# Search for a web page
driver.get("https://destinationinsights.withgoogle.com/intl/en_ALL/")

# maximize browser window
driver.maximize_window()