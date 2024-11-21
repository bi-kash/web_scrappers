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


start_url = (
    "https://www.tradeinn.com/bikeinn/de/fahrrader-und-rahmen-mountainbikes/4020/s"
)
dict_data = []
error_data = []


def check_overlay(driver):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "cookie-permission--accept-button")
            )
        )
        agree = driver.find_element(By.CLASS_NAME, "cookie-permission--accept-button")
        agree.click()
    except:
        print("No agree button")


def scrap_list():
    rows = []
    driver = get_driver()
    driver.get(start_url)
    # check_overlay(driver)
    shop_name = "tradeinn"
    language = "de"
    wait = WebDriverWait(driver, 5)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "option"))
    )
    current_scroll_position, new_height = 0, 1
    speed = 1
    while current_scroll_position <= new_height:
        current_scroll_position += speed
        driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
        new_height = driver.execute_script("return document.body.scrollHeight")

    time.sleep(3)

    bikes = driver.find_elements(By.CLASS_NAME, "singleBoxMarcaCarrusel")

    for bike in bikes:
        url_detail = bike.find_element(By.TAG_NAME, "a")
        brand = url_detail.get_attribute("data-ta-product-brand")
        model = url_detail.find_element(By.TAG_NAME, "img").get_attribute("alt")
        category = url_detail.get_attribute("data-ta-product-category")
        url_detail = url_detail.get_attribute("href")

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

        price = bike.find_element(By.CLASS_NAME, "BoxPriceValor").text.split()[0]

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
                "stock_sizes": "",
                "url-detail": url_detail,
                "price": price,
                "rrp": "",
            }
        )

    return rows


error_data = []


def scrap_pages(rows):

    driver = get_driver()
    driver.get(rows[0]["url-detail"])
    for row in rows:
        try:
            driver.get(row["url-detail"])
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "option"))
            )
            options = driver.find_element(By.CLASS_NAME, "talla_select").find_elements(
                By.TAG_NAME, "option"
            )
            sizes = [item.text for item in options]

            stock_sizes = []
            not_available = False
            for i in range(len(options)):
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "option"))
                )
                option = driver.find_element(
                    By.CLASS_NAME, "talla_select"
                ).find_elements(By.TAG_NAME, "option")[i]
                if i != 0:
                    option.click()

                availability = driver.find_element(By.ID, "f_envio2").get_attribute(
                    "innerText"
                )
                stock_sizes.append(sizes[i] + ": " + availability)

                if availability.strip() == "":
                    not_available = True
                    break

            if not_available:
                error_data.append(row)
                continue

            stock_status = 1
            if not stock_sizes:
                stock_status = 0

            row.update(
                {"stock_sizes": "\n".join(stock_sizes), "stock_status": stock_status}
            )
            dict_data.append(row)
        except:
            error_data.append(row)
    print("total handled:", len(dict_data))

    driver.quit()


if __name__ == "__main__":
    rows = scrap_list()
    print("Number of product to be scrapped: ", len(rows))
    count = 0
    while True:
        count += 1
        print("Count:", count)
        error_data = []
        max_workers = 16
        len_rows = len(rows)
        if len_rows < 32:
            max_workers = 4
        if len_rows < 16:
            max_workers = 2
        list_rows = []
        multiple = int(len_rows / (max_workers))
        for i in range(max_workers - 1):
            list_rows.append(rows[multiple * i : multiple * (i + 1)])
        list_rows.append(rows[multiple * (i + 1) :])

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(scrap_pages, list_rows)
        print(len(error_data))
        if len(error_data) == 0:

            break
        else:
            rows = error_data

        pd.DataFrame.from_records(dict_data).to_csv("tradinn.csv")
