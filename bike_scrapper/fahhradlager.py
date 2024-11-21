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


rows = []


def scrap(url):
    driver = get_driver()
    driver.get(url + "&count=500")
    time.sleep(5)
    shop_name = "fahrradlagerverkauf"
    language = "de"
    bikes = driver.find_elements(By.CLASS_NAME, "product-item-info")
    print("Number of bikes:", len(bikes))
    for bike in bikes:
        url_detail = bike.find_element(By.TAG_NAME, "a")
        model = url_detail.get_attribute("data-fl-item-name")
        category = url_detail.get_attribute("data-fl-product-placement")
        if not category:
            category = "MountainBike"
        brand = model.split()[0]
        if len(brand) < 2:
            brand = model.split()[1]
        price = (
            bike.find_element(By.CLASS_NAME, "price-final_price")
            .get_attribute("innerText")
            .split()[0]
        )
        url_detail = url_detail.get_attribute("href")
        rrp = bike.find_elements(By.CLASS_NAME, "old-price")
        if rrp:
            rrp = rrp[0].get_attribute("innerText").split()[0]
        else:
            rrp = ""

        years = re.findall("[0-9]+", model)
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
        stock_sizes = []
        swatch_options = bike.find_elements(By.CLASS_NAME, "swatch-option")
        for option in swatch_options:
            size = option.get_attribute("aria-label")
            if "green" in option.get_attribute("class"):
                availability = "Lieferzeit: 2-6 Tage"
            else:
                availability = "Lieferfrist: aktuell nicht auf Lager"

            stock_sizes.append(size + ": " + availability)

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
                "stock_status": 1,
                "stock_text": "",
                "stock_sizes": stock_sizes,
                "url-detail": url_detail,
                "price": price,
                "rrp": rrp,
            }
        )


start_url_1 = "https://www.fahrradlagerverkauf.com/fahrraeder/sport/mountainbike-hardtail#navigation:attrib%5Bcat_url%5D%5B0%5D=%2Ffahrraeder%2Fsport%2Fmountainbike-hardtail&attrib%5Bproduct_delivery_label%5D%5B0%5D=2-6+Tage&first=0"
start_url_2 = "https://www.fahrradlagerverkauf.com/e-bikes/e-sport/e-mountainbike-fully#navigation:attrib%5Bcat_url%5D%5B0%5D=%2Fe-bikes%2Fe-sport%2Fe-mountainbike-fully&attrib%5Bproduct_delivery_label%5D%5B0%5D=2-6+Tage&first=0"
scrap(start_url_1)
scrap(start_url_2)

pd.DataFrame.from_records(rows).to_csv("fahrradlagerverkauf.csv")
