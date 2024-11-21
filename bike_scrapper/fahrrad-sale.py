from bs4 import BeautifulSoup
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
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


def sel_scrap_dynamic(rows):

    driver = get_driver()
    driver.maximize_window()
    # wait = WebDriverWait(driver, 10)
    for row in rows:
        driver.get(row["url-detail"])
        stock_sizes = []
        brand = (
            driver.find_element(By.CLASS_NAME, "manufacturer-logo")
            .find_element(By.TAG_NAME, "img")
            .get_attribute("alt")
        )

        for item in driver.find_elements(By.TAG_NAME, "option")[1:]:
            stock_sizes.append(item.get_attribute("innerText").strip())

        stock_sizes = "\n".join(stock_sizes)

        row.update({"brand": brand, "stock_sizes": stock_sizes})
        dict_data.append(row)

    print("Total handled bikes: ", len(dict_data))

    driver.quit()


def scrap():
    base_url = "https://www.fahrrad-sale.de/Fahrrad/?view_mode=tiled&listing_sort=&listing_count=180&page="
    rows = []
    page_no = 1

    while True:
        url = base_url + str(page_no)
        web_page = requests.get(url)
        soup = BeautifulSoup(web_page.content, features="lxml")
        bikes = soup.find_all("div", class_="content-container-inner")

        for bike in bikes:

            model = bike.find("span")["title"]
            year = model.split("|")[0].strip()[-4:]
            url_detail = bike.find("a")["href"]
            category = url_detail.split("/")[4]
            # url_detail = url_brand['href']
            # brand = url_brand['title']

            try:
                year = int(year)
                if not (year > 1990 and year < 2050):
                    year = ""

            except:
                year = ""

            prices = (
                bike.find("span", class_="current-price-container").getText().strip()
            )
            prices = [pr.strip() for pr in prices.split("EUR")]
            stock_text = (
                bike.find("div", class_="shipping-info-short").getText().strip()
            )
            stock_text = " ".join(re.findall(r"[0-9A-Za-z/: ]+", stock_text))
            if prices[1] == "":
                price = prices[0]
                rrp = ""
            else:
                rrp = prices[0].split(" ")[1]
                price = prices[1]
            language = "de"
            shop_name = "fahrrad-sale"
            rows.append(
                {
                    "shop_name": shop_name,
                    "language": language,
                    "year": year,
                    "brand": "",
                    "modell": model,
                    "condition": "new",
                    "category_shop": category,
                    "stock_status": 1,
                    "stock_text": stock_text,
                    "stock_sizes": "",
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )

        page_limit = int(
            soup.find("ul", class_="pagination").find_all("li")[-2].getText().strip()
        )
        if page_limit <= page_no:
            break
        page_no += 1
    return rows


if __name__ == "__main__":
    rows = scrap()
    print("Dynamic pages to be handled: ", len(rows))

    max_workers = 16
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / 16)):
        list_rows.append(rows[16 * i : 16 * (i + 1)])
    list_rows.append(rows[16 * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(sel_scrap_dynamic, list_rows)
    # Scrap using selenium
    # rows = sel_scrap_dynamic(rows)

    # In case you require fast scraping, we can ignore shipment options and use
    # rows = scrap_each_page(rows)
    pd.DataFrame.from_records(dict_data).to_csv("fahrrad-sale.csv")
