import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
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



start_url = 'https://bikesale.de/mountainbikes-guenstig-kaufen'
dict_data = []


def check_overlay(driver):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "cookie-permission--accept-button" )))
        agree = driver.find_element(By.CLASS_NAME, "cookie-permission--accept-button")
        agree.click()
    except:
        print("No agree button")


def scrap_list():
    rows = []
    driver = get_driver()
    driver.get(start_url)
    check_overlay(driver)
    shop_name = 'bikesale'
    language = 'de'
    wait = WebDriverWait(driver, 5)

    current_scroll_position, new_height = 0, 1
    speed = 5
    while current_scroll_position <= new_height:
        current_scroll_position += speed
        driver.execute_script(
            "window.scrollTo(0, {});".format(current_scroll_position)
        )
        new_height = driver.execute_script("return document.body.scrollHeight")
  

    bikes = driver.find_elements(By.CLASS_NAME, 'product--info')

    for bike in bikes:
        url_detail = bike.find_elements(By.TAG_NAME, 'a')[1]
        model = url_detail.text
        brand = url_detail.find_element(By.CLASS_NAME, 'mm-product-title-supplier').text
        url_detail = url_detail.get_attribute('href')
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
        price = bike.find_element(By.CLASS_NAME, 'price--default').text.split(':')[1].split()[0]
        rrp = bike.find_elements(By.CLASS_NAME, 'price--discount')
        if rrp:
            rrp = rrp[0].text.split()[0]
        else:
            rrp = ''
        
        rows.append(
            {
                "shop_name": shop_name,
                "language": language,
                "year": year,
                "brand": brand,
                "modell": model,
                "condition": '',
                "category_shop": "",
                "stock_status": 1,
                "stock_text": "",
                "stock_sizes": "",
                "url-detail": url_detail,
                "price": price,
                "rrp": rrp,
            }
        )
 
    return rows


def scrap_pages(rows):
    driver = get_driver()
    driver.get(rows[0]['url-detail'])
    check_overlay(driver)
    for row in rows:
      
        wait = WebDriverWait(driver, 5)
        
        driver.get(row['url-detail'])
       
        labels = [item.get_attribute('innerText') for item in driver.find_element(By.CLASS_NAME, 'product--properties-col.col--1').find_elements(By.CLASS_NAME, 'product--properties-label')]
        values = [item.get_attribute('innerText') for item in driver.find_element(By.CLASS_NAME, 'product--properties-col.col--1').find_elements(By.CLASS_NAME, 'product--properties-value')]
        category = ''
        stock_size = ''
        condition = ''
        for label, value in zip(labels, values):
        
            if label == 'Kategorie:':
                category = value
            if label == 'Rahmengröße:':
                stock_size = value
            if label == 'Zustand:':
                condition = value
        
        stock_text = driver.find_element(By.CLASS_NAME, 'delivery--text-available').get_attribute('innerText')
        row.update({'category_shop': category, 'stock_sizes': stock_size, 'condition': condition, 'stock_text': stock_text})
        dict_data.append(row)
    print("total Handled: ", len(dict_data))
    driver.quit()


if __name__ == "__main__":
    rows = scrap_list()
    max_workers = 8
    len_rows = len(rows)
    list_rows = []
    multiple = int(len_rows/(max_workers))
    for i in range(max_workers):
        list_rows.append(rows[multiple * i : multiple * (i + 1)])
    list_rows.append(rows[multiple * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_pages, list_rows)
    pd.DataFrame.from_records(dict_data).to_csv("bikesale.csv")


