
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import time

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

def scrap_list():
    shop_name = "buycycle"
    language = "de"
    rows = []
    base_url = "https://buycycle.com/de/shop/bike-types/mountainbike"
    driver = get_driver()
    driver.get(base_url)

    while True:
        time.sleep(4)
        bikes = driver.find_elements(By.CLASS_NAME, "shop-product-item")
        for bike in bikes:
            url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute('href')
            try:
                condition = bike.find_element(By.CLASS_NAME, "bike-item-tag").get_attribute("innerText")
            except:
                condition = "new"

            infos = bike.find_elements(By.CLASS_NAME, "border-bottom")
            try:
                year = infos[0].text
            except:
                continue
            stock_sizes = infos[1].text
            model = infos[2].text

            
            brand_cat = bike.find_element(By.CLASS_NAME, "pr-3").find_elements(By.TAG_NAME, "p")
            brand = brand_cat[0].text
            model = brand_cat[1].text + " | " + model
            category = brand_cat[-1].text
            
            rrp = bike.find_element(By.TAG_NAME, "del").text[:-1]
            price = bike.find_element(By.CLASS_NAME, "font-700").text[:-1]
            
            rows.append(
                {
                    "shop_name": shop_name,
                    "language": language,
                    "year": year,
                    "brand": brand,
                    "modell": model,
                    "condition": condition,
                    "category_shop": category,
                    "stock_status": 1,
                    "stock_text": "",
                    "stock_sizes": stock_sizes,
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )
        if len(rows) % 20 == 0:
            pd.DataFrame.from_records(rows).to_csv("buycycle.csv")
        next = driver.find_element(By.CLASS_NAME, "btn-next")
        if next.get_attribute("aria-disabled") == "true":
            break
        else:
            
            next.click()
    return rows

if __name__ == "__main__":
    scrap_list()





