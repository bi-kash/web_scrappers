import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
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


dict_data = []


def sel_scrap_dynamic(page):
    base_url = "https://www.fitstore24.com/de/radsport/mountainbikes?page="
    driver = get_driver()
    base_url += str(page)
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.CLASS_NAME, "product-container"))
    bikes = driver.find_elements(By.CLASS_NAME, "product-container")

    rows = []
    for bike in bikes:

        model = bike.find_element(By.CLASS_NAME, "title").text.strip()
        year = model.split("|")[0].strip()[-4:]
        url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute("href")
        # category = url_detail.split('/')[4]
        # url_detail = url_brand['href']
        # brand = url_brand['title']

        try:
            year = int(year)
            if not (year > 1990 and year < 2050):
                year = ""

        except:
            year = ""

        price = bike.find_element(By.CLASS_NAME, "price-new").text.strip().split(" ")[0]
        rrp = bike.find_elements(By.CLASS_NAME, "price-old")
        if rrp:
            rrp = rrp[0].text.strip().split(" ")[0]
        else:
            rrp = ""
        ship_info = bike.find_element(By.CLASS_NAME, "product-shipping").text.strip()
        stock_text = bike.find_element(
            By.CLASS_NAME, "product-shipping-time"
        ).text.strip()
        stock_text += "\n" + ship_info
        # stock_text = ' '.join(re.findall(r'[0-9A-Za-z/: ]+', stock_text))
        language = "de"
        shop_name = "fit-store"
        rows.append(
            {
                "shop_name": shop_name,
                "language": language,
                "year": year,
                "brand": "",
                "modell": model,
                "condition": "new",
                "category_shop": "",
                "stock_status": 1,
                "stock_text": stock_text,
                "stock_sizes": "",
                "url-detail": url_detail,
                "price": price,
                "rrp": rrp,
            }
        )

    for row in rows:
        driver.get(row["url-detail"])
        stock_sizes = []
        category = (
            driver.find_element(By.CLASS_NAME, "breadcrumb.hidden-xs")
            .find_elements(By.TAG_NAME, "a")[3]
            .get_attribute("title")
        )

        brand = (
            driver.find_element(By.CLASS_NAME, "manufacturer-logo")
            .find_element(By.TAG_NAME, "img")
            .get_attribute("alt")
        )

        for item in driver.find_elements(By.TAG_NAME, "option"):
            stock_sizes.append(item.get_attribute("innerText").strip())

        stock_status = 1

        stock_sizes = "\n".join(stock_sizes[1:-2])
        if stock_sizes.strip() == "":
            stock_status = 0

        row.update(
            {
                "category_shop": category,
                "stock_sizes": stock_sizes,
                "stock_status": stock_status,
                "brand": brand,
            }
        )

        dict_data.append(row)

    print("Total handled bikes: ", len(dict_data))

    driver.quit()


if __name__ == "__main__":
    base_url = "https://www.fitstore24.com/de/radsport/mountainbikes"

    driver = get_driver()
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.TAG_NAME, "ff-template").text)

    n_items = int(
        re.findall(r"[0-9]+", driver.find_element(By.TAG_NAME, "ff-template").text)[0]
    )
    print(n_items)

    div = int(n_items / 30)
    if n_items != n_items / 30:
        div = div + 1
    pages = [i + 1 for i in range(div)]
    max_workers = div
    driver.quit()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(sel_scrap_dynamic, pages)

    pd.DataFrame.from_records(dict_data).to_csv("fit-store.csv")
