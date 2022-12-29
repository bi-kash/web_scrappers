import pandas as pd
from concurrent.futures import ThreadPoolExecutor
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


def sel_scrap_dynamic(page_no):
    base_url = "https://boc24.de/collections/mountainbikes?page="

    driver = get_driver()
    driver.get(base_url + str(page_no))
    shadow_host = driver.find_element(By.ID, "usercentrics-root")
    script = "return arguments[0].shadowRoot"
    shadow_root = driver.execute_script(script, shadow_host)
    shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.kXwvj").click()
    wait = WebDriverWait(driver, 10)
    wait.until(
        lambda driver: driver.find_element(
            By.ID, "main-collection-product-grid"
        ).find_element(By.CLASS_NAME, "card-wrapper")
    )
    bikes = driver.find_element(By.ID, "main-collection-product-grid").find_elements(
        By.CLASS_NAME, "card-wrapper"
    )

    rows = []
    for bike in bikes:

        url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute("href")
        category = "mountainbikes"
        # url_detail = url_brand['href']
        # brand = url_brand['title']

        price = bike.find_element(By.CLASS_NAME, "price-item.price-item--sale").text[1:]

        rrp = (
            bike.find_element(By.CLASS_NAME, "price__sale")
            .find_element(By.CLASS_NAME, "price-item.price-item--regular")
            .text[1:]
        )
        if rrp == "0":
            rrp = ""

        if not price:
            price = bike.find_element(
                By.CLASS_NAME, "price-item.price-item--regular"
            ).text[1:]

        # ship_info = bike.find_element(By.CLASS_NAME, 'product-shipping').text.strip()
        # stock_text = bike.find_element(By.CLASS_NAME, 'product-shipping-time').text.strip()
        # stock_text = ' '.join(re.findall(r'[0-9A-Za-z/: ]+', stock_text))
        language = "de"
        shop_name = "boc-store"
        rows.append(
            {
                "shop_name": shop_name,
                "language": language,
                "year": "",
                "brand": "",
                "modell": "",
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

    for row in rows:
        driver.get(row["url-detail"])
        stock_sizes = []
        model = (
            driver.find_element(By.CLASS_NAME, "product__title")
            .get_attribute("innerText")
            .split("\n")[0]
        )
        brand = driver.find_element(
            By.CLASS_NAME, "product__text.caption-with-letter-spacing"
        ).text

        for item in driver.find_element(
            By.CLASS_NAME, "product-form__input"
        ).find_elements(By.TAG_NAME, "option"):
            if item.get_attribute("data-available") == "true":
                stock_sizes.append(item.get_attribute("innerText").strip())

        stock_status = 0
        if len(stock_sizes):
            stock_status = 1
        stock_sizes = "\n".join(stock_sizes)
        stock_text = (
            driver.find_element(By.ID, "shopify-section-delivery")
            .get_attribute("innerText")
            .strip()
        )
        colors = [
            ele.get_attribute("value")
            for ele in driver.find_elements(By.CLASS_NAME, "swiper-slide-helper-class")
        ]
        for color in colors:
            row.update(
                {
                    "modell": model + " " + color,
                    "brand": brand,
                    "stock_sizes": stock_sizes,
                    "stock_text": stock_text,
                    "stock_status": stock_status,
                }
            )
            dict_data.append(deepcopy(row))

    print("Total handled bikes: ", len(dict_data))

    driver.quit()


if __name__ == "__main__":
    base_url = "https://boc24.de/collections/mountainbikes?page=1"
    page = 1
    base_url += str(page)
    driver = get_driver()
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(lambda driver: driver.find_element(By.ID, "usercentrics-root"))
        shadow_host = driver.find_element(By.ID, "usercentrics-root")
        script = "return arguments[0].shadowRoot"
        shadow_root = driver.execute_script(script, shadow_host)
        shadow_root.find_element(By.CLASS_NAME, "sc-eDvSVe.kXwvj").click()
    except:
        pass
    wait.until(
        lambda driver: driver.find_elements(By.CLASS_NAME, "pagination__item")[-2].text
    )

    n_pages = int(driver.find_elements(By.CLASS_NAME, "pagination__item")[-2].text)
    print("Total pages: ", n_pages)
    driver.quit()

    pages_list = [i + 1 for i in range(n_pages)]
    max_workers = n_pages

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(sel_scrap_dynamic, pages_list)
    pd.DataFrame.from_records(dict_data).to_csv("boc.csv")
