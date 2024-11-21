import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from copy import deepcopy
import re

from bs4 import BeautifulSoup
import requests


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


dict_data = []


def scrap_list():
    base_url = "https://www.alltricks.de/C-40425-fahrraeder/NW-7509-kategorien~full-suspension-mtb/NW-7509-kategorien~hardtail-mtb"
    driver = get_driver()
    driver.get(base_url)
    driver.maximize_window()
    try:
        driver.find_element(By.ID, "didomi-notice-agree-button").click()
    except:
        pass
    rows = []
    current_scroll_position, new_height = 0, 1
    speed = 5
    while current_scroll_position <= new_height:
        current_scroll_position += speed
        driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
        new_height = driver.execute_script("return document.body.scrollHeight")

    bikes = driver.find_elements(By.CLASS_NAME, "alltricks-Product-link-wrapper")
    shop_name = "Alltricks"
    language = "de"
    category = "MountainBikes"

    for bike in bikes:
        url_detail = bike.find_element(By.TAG_NAME, "a")
        model = url_detail.text.strip()
        condition = "new"
        if model.split()[0].lower() == "refurbished":
            condition = "used"
        url_detail = url_detail.get_attribute("href")
        year = ""
        years = re.findall("[0-9]+", url_detail)

        for year_temp in years:
            try:
                year = int(year_temp)
                if not (year > 1990 and year < 2050):
                    year = ""
                else:
                    break

            except:
                year = ""
        brand = bike.find_element(By.TAG_NAME, "strong").text
        price = (
            bike.find_element(By.CLASS_NAME, "alltricks-Product-actualPrice")
            .text.strip()
            .split()[0]
            .replace(".", "")
            .replace(",", ".")
        )
        try:
            rrp = (
                bike.find_element(By.CLASS_NAME, "alltricks-Product-newlinePrice")
                .text.strip()
                .split()[0]
                .replace(".", "")
                .replace(",", ".")
            )
        except:
            try:
                rrp = (
                    bike.find_element(
                        By.CLASS_NAME, "alltricks-Recommended-retail-price"
                    )
                    .find_element(By.TAG_NAME, "span")
                    .text.strip()
                    .split()[2]
                    .replace(".", "")
                    .replace(",", ".")
                )
            except:
                rrp = ""

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
                "stock_sizes": "",
                "url-detail": url_detail,
                "price": price,
                "rrp": rrp,
            }
        )
    driver.quit()
    return rows


def scrap_pages(rows):
    driver = get_driver()
    driver.get(rows[0]["url-detail"])
    try:
        driver.find_element(By.ID, "didomi-notice-agree-button").click()
    except:
        pass
    for row in rows:
        driver.get(row["url-detail"])
        options = driver.find_element(
            By.CLASS_NAME, "alltricks-ChildSelector--theBigOne"
        ).find_elements(By.TAG_NAME, "option")[1:]
        dict_size = {}
        for option in options:
            key = option.get_attribute("data-stock-label").strip()
            value = option.get_attribute("data-label").strip()
            if key in dict_size:
                dict_size[key].append(value)
            else:
                dict_size[key] = [value]
        stock_sizes = []
        for key, value in dict_size.items():
            stock_sizes.append(key + "\n" + ", ".join(value))

        stock_sizes = "\n\n".join(stock_sizes)
        try:
            stock_text = (
                driver.find_element(By.CLASS_NAME, "product-header-stock-delay")
                .find_element(By.TAG_NAME, "p")
                .get_attribute("innerText")
                .strip()
            )
        except:
            stock_text = ""
        row.update({"stock_sizes": stock_sizes, "stock_text": stock_text})
        dict_data.append(deepcopy(row))
    print("Handled: ", len(dict_data))
    driver.quit()


if __name__ == "__main__":
    rows = scrap_list()
    print("To be handled: ", len(rows))

    max_workers = 10
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / max_workers)):
        list_rows.append(rows[max_workers * i : max_workers * (i + 1)])
    list_rows.append(rows[max_workers * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_pages, list_rows)

    pd.DataFrame.from_records(dict_data).to_csv("alltricks.csv")
