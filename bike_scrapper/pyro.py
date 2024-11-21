import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from copy import deepcopy
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor


# Need these: shop_name,language,year,brand,modell,condition,category_shop,stock_status,stock_text,stock_sizes,url-detail,price,rrp
def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = False
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
    base_url = "https://pyrobikes.de/collections/fahrrader"
    driver = get_driver()
    driver.get(base_url)
    page = 1
    shop_name = "Pyrobikes"
    language = "de"
    category = "MountainBikes"
    rows = []

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "grid-product__content"))
        )
    except:
        pass
    bikes = driver.find_elements(By.CLASS_NAME, "grid-product__content")

    for bike in bikes:
        url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute("href")
        try:
            stock_status = bike.find_element(By.CLASS_NAME, "grid-product__tag").text
        except:
            stock_status = ""

        model = bike.find_element(By.CLASS_NAME, "grid-product__title").text
        price = (
            bike.find_element(By.CLASS_NAME, "grid-product__price")
            .text.strip()
            .split()[0]
            .replace(".", "")
            .replace(",", ".")
            .replace("€", "")
        )
        try:
            price = float(price)
        except:
            price = (
                bike.find_element(By.CLASS_NAME, "grid-product__price")
                .text.strip()
                .split()[1]
                .replace(".", "")
                .replace(",", ".")
                .replace("€", "")
            )

        rows.append(
            {
                "shop_name": shop_name,
                "language": language,
                "year": "",
                "brand": "",
                "modell": model,
                "condition": "",
                "category_shop": category,
                "stock_status": stock_status,
                "stock_text": "",
                "stock_sizes": "",
                "url-detail": url_detail,
                "price": price,
                "rrp": "",
            }
        )

    driver.quit()
    return rows


def scrap_each_page(rows):
    driver = get_driver()

    for row in rows:

        driver.get(row["url-detail"])
        fieldsets = driver.find_elements(By.TAG_NAME, "fieldset")

        variant_buttons = fieldsets[0].find_elements(By.CLASS_NAME, "variant-input")
        try:
            variant_sizes = fieldsets[1].find_elements(By.CLASS_NAME, "variant-input")
            sizes = [size.get_attribute("data-value") for size in variant_sizes]
        except:
            sizes = ["one-size"]

        size = ", ".join(sizes)
        # wait until all buttons are loaded

        for i in range(len(variant_buttons)):

            buttons = driver.find_element(
                By.XPATH, "//fieldset[@name='Farbe']"
            ).find_elements(By.CLASS_NAME, "variant-input")
            try:
                buttons[i].click()
            except:
                try:
                    time.sleep(3)
                    buttons[i].click()
                except:
                    pass

            row_copy = deepcopy(row)
            model = row_copy["modell"] + " " + buttons[i].get_attribute("data-value")

            try:
                stock_text = (
                    driver.find_elements(By.CLASS_NAME, "product-block--sales-point")[
                        -1
                    ]
                    .find_element(By.CLASS_NAME, "icon-and-text")
                    .find_elements(By.TAG_NAME, "span")[1]
                    .text
                )
            except:
                stock_text = ""

            row_copy.update(
                {"modell": model, "stock_sizes": size, "stock_text": stock_text}
            )
            dict_data.append(row_copy)
    print("Handled: ", len(dict_data))

    driver.quit()


if __name__ == "__main__":
    rows = scrap_list()
    print("To be handled: ", len(rows))
    max_workers = 3
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / max_workers)):
        list_rows.append(rows[max_workers * i : max_workers * (i + 1)])
    list_rows.append(rows[max_workers * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_each_page, list_rows)

    pd.DataFrame(dict_data).to_csv("pyro.csv")
