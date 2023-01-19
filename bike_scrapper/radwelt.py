import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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

start_url = 'https://www.radwelt-shop.de/fahrraeder/mountainbikes/?p=1&o=1&n=100'

def check_overlay(driver):
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "usercentrics-root")))
    shadow_host = driver.find_element(By.ID, "usercentrics-root")
    script = "return arguments[0].shadowRoot"
    shadow_root = driver.execute_script(script, shadow_host)
    WebDriverWait(shadow_root, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "sc-eDvSVe.kaITzn")))
    shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.kaITzn").click()

def scrap_list():
    driver = get_driver()
    driver.get(start_url)
    check_overlay(driver)
    n_page = int(driver.find_element(By.CLASS_NAME, 'paging--display').find_element(By.TAG_NAME, 'strong').text)

    rows = []
    
    shop_name = 'radwelt-shop'
    language = 'de'
    category = 'Mountainbike'
    for page in range(1, n_page+1):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product--info')))
        bikes = driver.find_elements(By.CLASS_NAME, 'product--info')
        for bike in bikes:
            url_detail = bike.find_element(By.TAG_NAME, 'a')
            model = url_detail.get_attribute('title')
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
            url_detail = url_detail.get_attribute('href')
            split = url_detail.split('/')
            category = split[4]+"-"+split[5]
            brand = model.split()[0]
            price = bike.find_elements(By.CLASS_NAME, 'price--default')
            if price:
                try:
                    price = price[0].text.split()[0]
                except:
                    price = price[0].text.split('&nbsp;')[0]

            else:
                price = ''

            rrp = bike.find_elements(By.CLASS_NAME, 'price--discount')
            if rrp:
                try:
                    rrp = rrp[0].text.split()[0]
                except:
                    rrp = rrp[0].text.split('&nbsp;')[0]
            else:
                rrp = ''
            stock_status = 1

            stock_sizes = [item.get_attribute('innerText') for item in bike.find_element(By.CLASS_NAME, 'product-variants').find_elements(By.TAG_NAME, 'li')]
            if len(stock_sizes) == 0:
                stock_sizes = [item.get_attribute('innerText') for item in bike.find_element(By.CLASS_NAME, 'product-variants').find_elements(By.TAG_NAME, 'a')]
                if len(stock_sizes) == 0:
                    stock_status = 0
                    
            stock_sizes = "\n".join(stock_sizes)
            rows.append(
                {
                    "shop_name": shop_name,
                    "language": language,
                    "year": year,
                    "brand": brand,
                    "modell": model,
                    "condition": "new",
                    "category_shop": category,
                    "stock_status": stock_status,
                    "stock_text": "",
                    "stock_sizes": stock_sizes,
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )
        if page+1>n_page:
            return rows
            
        driver.get('https://www.radwelt-shop.de/fahrraeder/mountainbikes/?p={}&o=1&n=100'.format(page+1))
    return rows

if __name__ == "__main__":
    rows = scrap_list()
    pd.DataFrame.from_records(rows).to_csv('radwelt.csv')