import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

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


def scrap(base_url):

    driver = get_driver()
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.ID, "usercentrics-root"))
    shadow_host = driver.find_element(By.ID, "usercentrics-root")
    script = "return arguments[0].shadowRoot"
    shadow_root = driver.execute_script(script, shadow_host)
    wait.until(
        lambda driver: shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.dGbgZi")
    )
    shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.dGbgZi").click()
    rows = []
    items = driver.find_elements(By.CLASS_NAME, "catalog-category-bikes__list-item")
    if items:
        links = [
            item.find_element(By.TAG_NAME, "a").get_attribute("href") for item in items
        ]

        for link in links[:1]:

            driver.get(link)
            if driver.find_elements(By.CLASS_NAME, "basic-tabs__link-title"):
                driver.find_elements(By.CLASS_NAME, "basic-tabs__link-title")[1].click()
            bikes = driver.find_elements(By.CLASS_NAME, "catalog-category-model__top")

            for bike in bikes:
                url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute("href")
                model = bike.find_element(
                    By.CLASS_NAME, "basic-headline__title"
                ).text.strip()
                if model == "":
                    continue
                Rrp = bike.find_element(By.CLASS_NAME, "product-tile-price__old-value")
                if Rrp:
                    Rrp = Rrp.text.split(" ")[0]
                price = bike.find_element(
                    By.CLASS_NAME, "product-tile-price__current-value"
                ).text
                shop_name = "rose-bikes"
                language = "de"

                rows.append(
                    {
                        "Shop_name": shop_name,
                        "Language": language,
                        "Model": model,
                        "Url-detail": url_detail,
                        "Price": price,
                        "Rrp": "",
                    }
                )
    else:
        current_scroll_position, new_height = 0, 1
        speed = 8
        while current_scroll_position <= new_height:
            current_scroll_position += speed
            driver.execute_script(
                "window.scrollTo(0, {});".format(current_scroll_position)
            )
            new_height = driver.execute_script("return document.body.scrollHeight")

        bikes = driver.find_elements(By.CLASS_NAME, "catalog-product-tile__link")
        for bike in bikes:

            url_detail = bike.get_attribute("href")
            model = bike.find_element(By.TAG_NAME, "img").get_attribute("alt")
            print(model)
            Rrp = bike.find_element(By.CLASS_NAME, "product-tile-price__old-value")
            if Rrp:
                Rrp = Rrp.text.split(" ")[0]
            price = bike.find_element(
                By.CLASS_NAME, "product-tile-price__current"
            ).text.split(" ")[0]
            # rent_price = bike.find_element(By.CLASS_NAME, 'product-tile-price__monthly-value').text.split(' ')[0]
            shop_name = "rose-bikes"
            language = "de"
            rows.append(
                {
                    "Shop_name": shop_name,
                    "Language": language,
                    "Model": model,
                    "Url-detail": url_detail,
                    "Price": price,
                    "Rrp": Rrp,
                }
            )

    for row in rows:
        driver.get(row["Url-detail"])
        category = [
            item.text
            for item in driver.find_elements(
                By.CLASS_NAME, "catalog-breadcrumb__list-item"
            )
        ]
        if "Sale" in category:
            category = category[3]
        else:
            category = category[2] + " " + category[3]
        links = [
            (ele.get_attribute("href"), ele.get_attribute("title"))
            for ele in driver.find_elements(
                By.CLASS_NAME, "bike-detail-color-picker__link"
            )
        ]

        for link, color in links:
            driver.get(link)
            driver.find_element(
                By.CLASS_NAME, "bike-detail-size-selector-trigger"
            ).click()
            stock_sizes = []
            wait.until(
                lambda driver: driver.find_element(By.CLASS_NAME, "basic-modal__list")
                .find_elements(By.CLASS_NAME, "select-size-link")[0]
                .find_element(By.CLASS_NAME, "select-size-link__key")
                .text
            )
            for item in driver.find_element(
                By.CLASS_NAME, "basic-modal__list"
            ).find_elements(By.CLASS_NAME, "select-size-link"):
                key = item.find_element(By.CLASS_NAME, "select-size-link__key").text
                try:
                    availability = item.find_element(
                        By.CLASS_NAME, "select-size-link__availability"
                    ).text
                except:
                    availability = item.find_element(
                        By.CLASS_NAME, "select-size-link__availability--link"
                    ).text
                print(key, availability)
                stock_sizes.append(key + ": " + availability)
            stock_sizes = "\n".join(stock_sizes)
            dict_data.append(
                {
                    "Shop_name": row["Shop_name"],
                    "Language": row["Language"],
                    "Model": row["Model"] + " " + color,
                    "Category": category,
                    "Url-detail": row["Url-detail"],
                    "Stock sizes": stock_sizes,
                    "Price": row["Price"],
                    "Rrp": row["Rrp"],
                }
            )


if __name__ == "__main__":
    scrap("https://www.rosebikes.de/sale?category%5B%5D=147#product_list")
    pd.DataFrame.from_records(dict_data).to_csv("rose-bikes.csv")
    # scrap()
