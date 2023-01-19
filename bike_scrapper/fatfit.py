import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import time
import re

# Need these: shop_name,language,year,brand,modell,condition,category_shop,stock_status,stock_text,stock_sizes,url-detail,price,rrp
def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = True
    chromeOptions.add_argument("--log-level=3")

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    # chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chromeOptions
    )
    return driver


start_url = 'https://www.fafit24.de/mountainbike'
dict_data = []


def check_overlay(driver):
    wait = WebDriverWait(driver, 5)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "js-offcanvas-cookie-accept-all" )))
        agree = driver.find_element(By.CLASS_NAME, "js-offcanvas-cookie-accept-all")
        agree.click()
    except:
        print("No agree button")


def scrap_list():
    rows = []
    driver = get_driver()
    driver.get(start_url)
    check_overlay(driver)
    shop_name = 'fatfit24'
    language = 'de'
    wait = WebDriverWait(driver, 5)
    while True:


        bikes = driver.find_elements(By.CLASS_NAME, 'card-body')

        for bike in bikes:
            url_detail = bike.find_element(By.TAG_NAME, 'a')
            model = url_detail.get_attribute('title')
            url_detail = url_detail.get_attribute('href')
            brand = bike.find_element(By.TAG_NAME, 'meta').get_attribute('content')
            year = ""
            years = re.findall('[0-9]+', model)
            for year_temp in years:
                try:
                    year = int(year_temp)
                    if not (year > 1990 and year < 2050):
                        year = ""
                    else:
                        break
                    
                except:
                    year = ""
            price = bike.find_element(By.CLASS_NAME, 'product-price').text.split()[0]
            rrp = ''

            rows.append(
                {
                    "shop_name": shop_name,
                    "language": language,
                    "year": year,
                    "brand": brand,
                    "modell": model,
                    "condition": "new",
                    "category_shop": "",
                    "stock_status": 1,
                    "stock_text": "",
                    "stock_sizes": "",
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )
        next = driver.find_element(By.CLASS_NAME, 'page-next')
        if 'disabled' in next.get_attribute('class'):
            break
        else:
            next.click()
            time.sleep(3)
        
    return rows


def scrap_pages(rows):
    driver = get_driver()
    driver.get(start_url)
    check_overlay(driver)

    wait = WebDriverWait(driver, 5)
    for row in rows:
        driver.get(row['url-detail'])
        category = driver.find_element(By.CLASS_NAME, 'nav-item.nav-link.navigation-flyout-link.is-level-2').get_attribute('title')
        labels = driver.find_elements(By.CLASS_NAME, 'product-detail-configurator-option-label.is-combinable.is-display-media')
        for i in range(len(labels)):
            label = driver.find_elements(By.CLASS_NAME, 'product-detail-configurator-option-label.is-combinable.is-display-media')[i]
            color = label.find_element(By.TAG_NAME, 'img').get_attribute('title')
            model = row['modell'] + " | " + color
            sizes = driver.find_elements(By.CLASS_NAME, 'product-detail-configurator-option-label.is-combinable.is-display-text')
            stock_sizes = []
            for i in range(len(sizes)):
                size = driver.find_elements(By.CLASS_NAME, 'product-detail-configurator-option-label.is-combinable.is-display-text')[i]
                stock_sizes.append(size.get_attribute('title')+ ": "+" ".join(driver.find_element(By.CLASS_NAME, 'delivery-available').text.split("\n")))

            stock_sizes = "\n".join(stock_sizes)
            stock_status = 1
            if not stock_sizes:
                stock_status= 0
            dict_data.append(
            {
                "shop_name": row["shop_name"],
                "language": row["language"],
                "year": row['year'],
                "brand": row['brand'],
                "modell": model,
                "condition": "new",
                "category_shop": category,
                "stock_status": stock_status,
                "stock_text": "",
                "stock_sizes": stock_sizes,
                "url-detail": row['url-detail'],
                "price": row['price'],
                "rrp": row['rrp'],
            }
        )
    print("Number of product handled is: ", len(dict_data))


rows = scrap_list()
print("Number of product to be scrapped: ", len(rows))
max_workers = 16
len_rows = len(rows)
list_rows = []
multiple = int(len_rows/(max_workers))
for i in range(max_workers-1):
    list_rows.append(rows[multiple * i : multiple * (i + 1)])
list_rows.append(rows[multiple * (i + 1) :])

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    executor.map(scrap_pages, list_rows)
pd.DataFrame.from_records(dict_data).to_csv("fatfit.csv")


