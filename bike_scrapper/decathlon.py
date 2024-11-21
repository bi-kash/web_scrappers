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


start_url = "https://www.decathlon.de/browse/c0-alle-sportarten-a-z/c1-fahrrad-welt/c3-mountainbike/_/N-obq78x"
url = "https://www.decathlon.de"
dict_data = []


def check_overlay(driver):
    wait = WebDriverWait(driver, 5)
    try:
        wait.until(
            EC.presence_of_all_elements_located((By.ID, "didomi-notice-agree-button"))
        )
        agree = driver.find_element(By.ID, "didomi-notice-agree-button")
        agree.click()
    except:
        print("No agree button")


def scrap_list():
    driver = get_driver()
    driver.get(url)
    check_overlay(driver)

    rows = []
    driver.get(start_url)
    shop_name = "decathlon"
    language = "de"
    category = "Mountainbike"
    while True:

        time.sleep(3)
        bikes = driver.find_elements(By.CLASS_NAME, "vtmn-z-0.dpb-holder")
        for bike in bikes:
            try:
                url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute("href")
                brand_model = bike.find_element(
                    By.CLASS_NAME, "dpb-product-link"
                ).text.split("\n")
                brand = brand_model[0]
                model = brand_model[1]
                year = ""
                years = re.findall("[0-9]+", model)
                for year_temp in years:
                    try:
                        year = int(year_temp)
                        if not (year > 1990 and year < 2050):
                            year = ""
                        else:
                            break

                    except:
                        year = ""
                rrp = bike.find_elements(By.CLASS_NAME, "vtmn-price_size--small")
                if rrp:
                    rrp = rrp[0].text.split()[0]
                else:
                    rrp = ""
                price = bike.find_element(
                    By.CLASS_NAME, "vtmn-price_size--medium"
                ).text.split()[0]

                rows.append(
                    {
                        "shop_name": shop_name,
                        "language": language,
                        "year": "",
                        "brand": brand,
                        "modell": model,
                        "condition": "new",
                        "category_shop": category,
                        "stock_status": 1,
                        "stock_text": "",
                        "stock_sizes": "",
                        "url-detail": url_detail,
                        "price": price,
                        "rrp": rrp,
                    }
                )
            except:
                pass
        next = driver.find_element(By.CLASS_NAME, "pagination").find_elements(
            By.TAG_NAME, "a"
        )[-1]
        if "disabled" in next.get_attribute("class"):
            break
        else:
            next.click()
    return rows


def scrape_pages(rows):
    driver = get_driver()
    driver.get(url)
    check_overlay(driver)

    wait = WebDriverWait(driver, 10)
    for row in rows:
        driver.get(row["url-detail"])
        stock_status = 1
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "select.svelte-1q3l5n3"))
            )
            driver.find_element(By.CLASS_NAME, "select.svelte-1q3l5n3").find_element(
                By.TAG_NAME, "button"
            ).click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "size-option"))
            )
            stock_sizes = [
                ": ".join(item.text.split("\n"))
                for item in driver.find_elements(By.CLASS_NAME, "size-option")
            ]
            if ": " not in stock_sizes[0]:
                time.sleep(4)
                stock_sizes = [
                    ": ".join(item.text.split("\n"))
                    for item in driver.find_elements(By.CLASS_NAME, "size-option")
                ]

        except:
            stock_sizes = [
                ": ".join(
                    driver.find_element(By.CLASS_NAME, "size-option").text.split("\n")
                )
            ]
            if ": " not in stock_sizes[0]:
                time.sleep(4)
                stock_sizes = [
                    ": ".join(item.text.split("\n"))
                    for item in driver.find_elements(By.CLASS_NAME, "size-option")
                ]

        stock_status = 0
        for stock_status_text in stock_sizes:
            if ("auf lager" in stock_status_text.lower()) or (
                "verfügbar" in stock_status_text.lower()
            ):
                stock_status = 1
                break

        stock_sizes = "\n".join(stock_sizes)
        row.update({"stock_sizes": stock_sizes, "stock_status": stock_status})
        dict_data.append(deepcopy(row))
    print(len(dict_data), ": Handled")


if __name__ == "__main__":
    rows = scrap_list()
    print("Dynamic pages to be handled: ", len(rows))
    max_workers = 4
    len_rows = len(rows)
    list_rows = []

    multiple = int(len_rows / (max_workers))
    for i in range(max_workers - 1):
        list_rows.append(rows[multiple * i : multiple * (i + 1)])
    list_rows.append(rows[multiple * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrape_pages, list_rows)
    pd.DataFrame.from_records(dict_data).to_csv("decathlon.csv")
