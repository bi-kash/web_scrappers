from bs4 import BeautifulSoup
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from copy import deepcopy


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


def get_categories(search_url):
    page = requests.get(search_url)
    soup = BeautifulSoup(page.content, features="lxml")
    categories = []
    for item in soup.find_all("div", class_="kmt-tree-item"):
        if item.find_all("div", class_="kmt-tree-item"):
            continue
        categories.append(item.getText().strip().split("\n")[0])
    return categories


def sel_scrap_dynamic(rows):

    driver = get_driver()
    driver.maximize_window()
    driver.get(rows[0]["url-detail"])
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.ID, "usercentrics-root"))
    shadow_host = driver.find_element(By.ID, "usercentrics-root")
    script = "return arguments[0].shadowRoot"

    shadow_root = driver.execute_script(script, shadow_host)
    wait.until(
        lambda driver: shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.eVGbhR")
    )
    for i in range(5):
        try:
            shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.eVGbhR").click()
            break
        except:
            time.sleep(2)
    for row in rows:
        driver.get(row["url-detail"])
        variants = driver.find_element(
            By.CLASS_NAME, "kmt-variantselection-list"
        ).find_elements(By.TAG_NAME, "span")
        for i in range(len(variants)):
            driver.find_element(
                By.CLASS_NAME, "kmt-variantselection-list"
            ).find_elements(By.TAG_NAME, "span")[i].click()
            stock_sizes = []

            for item in driver.find_element(By.CLASS_NAME, "kmt-select").find_elements(
                By.TAG_NAME, "option"
            )[1:]:
                stock_sizes.append(
                    item.get_attribute("innerText").strip().split("\n")[0]
                )
            status_dict = {}
            count_stock = 0
            no_status = []
            for stock_size in stock_sizes:

                try:
                    count_stock += 1
                    options = driver.find_element(
                        By.CLASS_NAME, "kmt-select"
                    ).find_elements(By.TAG_NAME, "option")
                    options[count_stock].click()

                    wait.until(
                        lambda driver: driver.find_element(
                            By.CLASS_NAME, "kmt-shippingselection-status"
                        )
                    )
                    time.sleep(2)
                    try:
                        status = driver.find_element(
                            By.CLASS_NAME, "kmt-shippingselection-status"
                        ).get_attribute("innerText")
                    except:
                        status = driver.find_element(
                            By.CLASS_NAME, "kmt-shippingselection-delivery"
                        ).get_attribute("innerText")

                    if status not in status_dict:
                        status_dict.update({status: [stock_size]})
                    else:
                        status_dict[status].append(stock_size)
                except:
                    no_status.append(stock_size)
                    print("No status for this stock size:", stock_size, " at ")

            stock_sizes = ""
            for status, values in status_dict.items():
                stock_sizes += status + ": " + ", ".join(values) + "\n"
            stock_status = 1
            if stock_sizes.strip() == "":
                stock_status = 0

            model = driver.find_element(
                By.CLASS_NAME, "kmt-productmain-title"
            ).text.strip()
            year = model.split("|")[0].strip()[-4:]
            color = (
                driver.find_element(By.CLASS_NAME, "kmt-productmain-variants")
                .find_element(By.TAG_NAME, "span")
                .text
            )
            if color not in model:
                model += " | " + color

            stock_text = (
                driver.find_element(By.CLASS_NAME, "kmt-iconlistitem")
                .find_element(By.TAG_NAME, "div")
                .get_attribute("innerText")
            )
            row.update(
                {
                    "year": year,
                    "stock_sizes": stock_sizes,
                    "stock_text": stock_text,
                    "modell": model,
                    "stock_status": stock_status,
                }
            )

            dict_data.append(deepcopy(row))

    print("Total handled bikes: ", len(dict_data))

    driver.quit()


def scrap_link(link=None, category=""):
    driver = get_driver()
    driver.get(link)
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.ID, "usercentrics-root"))
    shadow_host = driver.find_element(By.ID, "usercentrics-root")
    script = "return arguments[0].shadowRoot"
    import time

    shadow_root = driver.execute_script(script, shadow_host)
    wait.until(
        lambda driver: shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.eVGbhR")
    )
    for i in range(5):
        try:
            shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.eVGbhR").click()
            break
        except:
            time.sleep(2)

    rows = []
    for i in range(5):
        try:
            n_page = int(
                driver.find_element(By.CLASS_NAME, "kmt-paging-pagenr")
                .find_elements(By.TAG_NAME, "li")[-1]
                .text
            )
        except:
            time.sleep(1)
            continue
        break

    print("number of page:", n_page)
    category = "Mountainbike"

    for page in range(n_page):
        for item in driver.find_element(
            By.CLASS_NAME, "kmt-paging-pagenr"
        ).find_elements(By.TAG_NAME, "a"):
            if int(item.text) == page + 1:
                item.click()
                break

        bikes = driver.find_elements(By.CLASS_NAME, "kmt-productlist-item")
        for bike in bikes:
            model = ""

            url_brand = bike.find_element(
                By.CLASS_NAME, "kmt-productbox-manufacturer"
            ).find_element(By.TAG_NAME, "a")
            url_detail = url_brand.get_attribute("href")
            brand = url_brand.get_attribute("title")

            try:
                year = int(year)
                if not (year > 1990 and year < 2050):
                    year = ""

            except:
                year = ""

            price = bike.find_element(By.CLASS_NAME, "kmt-price-absolute").text.strip()
            rrp = ""
            if bike.find_elements(By.CLASS_NAME, "kmt-price--old"):
                rrp = (
                    bike.find_element(By.CLASS_NAME, "kmt-price--old")
                    .find_element(By.TAG_NAME, "del")
                    .text.split()[0]
                )
            language = "de"
            shop_name = "lucky-bike"
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

    return rows


def scrap(categories):

    base_url = "https://www.lucky-bike.de/index.php?stoken=16346BF&lang=0&cnid=2&actcontrol=alist&cl=alist&tpl=&oxloadid=&fnc=executefilter&fname=&attrfilter%5BKategorie%5D%5B%5D=ROOT%2FFahrr%C3%A4der%2F"

    rows = []
    # Get whatever information available from list page
    for category in categories:

        url = base_url + ("+").join(category.split(" "))
        rows.extend(scrap_link(url, category))
    # Go to individual pages for stock information
    return rows


if __name__ == "__main__":
    search_url = "https://www.lucky-bike.de/Fahrraeder/"
    """
    if you want all the categories to be scrapped

    categories = get_categories(search_url=search_url)
    print("For now only scrapped these categories: \n", categories[:5])
    rows = scrap(categories=categories)
    """

    """
    These are the categories

    ['BMX', 'Citybike', 'Crossbike', 'Dreiräder für Erwachsene', 'E-Citybike', 'E-Faltrad', 'E-Lastenrad', 'E-MTB Fully', 
    'E-MTB Hardtail', 'E-Trekkingbike', 'S-Pedelec', 'XXL-E-Bikes', 'Falt- & Klappräder', 'Hollandrad', 'Dreiräder', 
    'Jugendfahrrad ab 26 Zoll', 'Kinderfahrrad 12 Zoll bis 18 Zoll', 'Kinderfahrrad 20 Zoll', 'Kinderfahrrad 24 Zoll', 
    'Kinderroller & Scooter', 'Laufrad & Rutscher', 'Lastenrad', 'MTB-Fully', 'MTB-Hardtail', 'Cyclocross', 'Fitnessbike', 
    'Gravelbikes', 'Straßenrennrad', 'Trekkingrad', 'XXL Rad']
    """
    # we are only doing fot MTB bikes
    mtb_link = "https://www.lucky-bike.de/Fahrraeder/?pgNr=0&attrfilter[Kategorie][0]=ROOT%2FFahrr%C3%A4der%2FMountainbike&attrfilter[Kategorie][1]=ROOT%2FFahrr%C3%A4der%2FMountainbike%2FMTB-Fully&attrfilter[Kategorie][2]=ROOT%2FFahrr%C3%A4der%2FMountainbike%2FMTB-Hardtail"

    rows = scrap_link(mtb_link, "mountainbike")

    print("Dynamic pages to be handled: ", len(rows))
    max_workers = 16
    len_rows = len(rows)
    list_rows = []
    for i in range(int(len_rows / max_workers)):
        list_rows.append(rows[max_workers * i : max_workers * (i + 1)])
    list_rows.append(rows[max_workers * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(sel_scrap_dynamic, list_rows)
    # Scrap using selenium
    # rows = sel_scrap_dynamic(rows)

    # In case you require fast scraping, we can ignore shipment options and use
    # rows = scrap_each_page(rows)
    pd.DataFrame.from_records(dict_data).to_csv("lucky-bike.csv")
