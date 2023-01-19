
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from copy import deepcopy
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

start_url = 'https://www.tretwerk.net/fahrraeder/mountainbikes/'
dict_data = []
error_data = []

def check_overlay(driver):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "js-cookie-accept-all-button" )))
        agree = driver.find_element(By.CLASS_NAME, "js-cookie-accept-all-button")
        agree.click()
    except:
        print("No agree button")


def scrap_list():
    rows = []
    driver = get_driver()
    driver.get(start_url)
    check_overlay(driver)
    shop_name = 'tretwerk'
    language = 'de'
    category = 'Mountainbike'
    wait = WebDriverWait(driver, 5)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-body" )))
    page = 1
    while True:
        bikes = driver.find_elements(By.CLASS_NAME, 'card-body')

        for bike in bikes:
            url_detail = bike.find_element(By.TAG_NAME, "a")
            brand = bike.find_element(By.TAG_NAME, "meta").get_attribute("content")
            model = url_detail.get_attribute('title')
        
            url_detail = url_detail.get_attribute('href')
            
            years = re.findall('[0-9]+', model)
            year = ""
        
            for num in years:
                try:
                    year = int(num)
                    if not (year > 1990 and year < 2050):
                        year = ""
                    else:
                        break
                except:
                    year = ""
        
            price = bike.find_element(By.CLASS_NAME, 'product-price').text.split()[0]
            rrp = bike.find_elements(By.CLASS_NAME, 'list-price-price')
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
                    "condition": 'new',
                    "category_shop": category,
                    "stock_status": 1,
                    "stock_text": "",
                    "stock_sizes": "",
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )
            
        page+=1
        driver.get('https://www.tretwerk.net/fahrraeder/mountainbikes/?order=topseller&p={}'.format(page))
        if driver.find_elements(By.CLASS_NAME, 'alert-content'):
            break
 
    return rows

def which_group(driver, search_for):
    groups = driver.find_elements(By.CLASS_NAME, 'product-detail-configurator-group')
    for group in groups:
        if group.find_element(By.CLASS_NAME, 'product-detail-configurator-group-title').get_attribute('innerText').strip().lower() == search_for.lower(): 
            variants = driver.find_elements(By.CLASS_NAME, 'product-detail-configurator-option')

            variants = [variant.find_element(By.TAG_NAME, 'label') for variant in variants]
            return variants
    return []

def find_sizes(driver, sizes):
    sizes = which_group(driver, 'Rahmengröße')
    stock_sizes = []
    sizes_temp = [size.get_attribute('title') for size in sizes]
    #print(sizes_temp)
    #rint("size of stock size:", len(sizes))
    for j in range(len(sizes)):
        if not any(char.isdigit() for char in sizes_temp[j]):
            continue
        sizes = which_group(driver, 'Rahmengröße')
        element = sizes[j]
        
        #print(element.get_attribute('title'))
        element.click()
        time.sleep(10)

        stock_text = driver.find_element(By.CLASS_NAME, 'delivery-information.delivery-available').get_attribute('innerText')
        stock_sizes.append(sizes_temp[j] + ": "+ stock_text)

    if stock_sizes:
        stock_sizes = "\n".join(stock_sizes)
    else:
        stock_sizes = ""
        stock_sizes = driver.find_element(By.CLASS_NAME, 'delivery-information.delivery-available').get_attribute('innerText')
    return stock_sizes
    
    

def scrap_pages(rows):
    driver = get_driver()
    driver.get(start_url)
    check_overlay(driver)
    for row in rows:
        driver.get(row['url-detail'])
        try:
            variants = which_group(driver, "farbe")
            if len(variants) >0:      
                for i in range(len(variants)):
                    #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-detail-configurator-option')))
                    
                    variants = which_group(driver, "farbe")
                    #WebDriverWait(variants[0], 10).until(EC.presence_of_element_located((By.TAG_NAME, 'label')))
                    stock_sizes = []
                    stock_text = ""
                    sizes = which_group(driver, 'Rahmengröße')
                    element = variants[i]
                    try:
                        element.click()
                        if len(sizes) == 0:
                            time.sleep(10)
                    except: pass


                    model = driver.find_element(By.CLASS_NAME, 'product-detail-name').get_attribute('innerText')
                    stock_sizes = find_sizes(driver, sizes)
                    row.update({"modell": model, "stock_sizes": stock_sizes})
                    dict_data.append(deepcopy(row))
                    
            else:
                stock_sizes = []
                stock_text = ""
                sizes = which_group(driver, 'Rahmengröße')
                

                model = driver.find_element(By.CLASS_NAME, 'product-detail-name').get_attribute('innerText')
                stock_sizes = find_sizes(driver, sizes)
                row.update({"modell": model, "stock_sizes": stock_sizes})
                dict_data.append(deepcopy(row))
        except:
            error_data.append(row)

rows = scrap_list()

print("Number of product to be scrapped: ", len(rows))
count = 0
for i in range(3):
    count += 1
    print("Count:", count)
    error_data = []
    max_workers = 16
    len_rows = len(rows)
    if len_rows <32:
        max_workers = 4
    if len_rows <16:
        max_workers = 2
    list_rows = []
    multiple = int(len_rows/(max_workers))
    for i in range(max_workers-1):
        list_rows.append(rows[multiple * i : multiple * (i + 1)])
    list_rows.append(rows[multiple * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_pages, list_rows)
    print(len(error_data))
    if len(error_data) == 0:

        break
    else:
        rows = error_data
    
    pd.DataFrame.from_records(dict_data).to_csv('tretwerk.csv')


