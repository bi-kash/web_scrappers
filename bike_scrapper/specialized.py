import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time

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
    base_url = "https://www.specialized.com/de/de/shop/c/shop#/filter:group:Bikes/filter:group:Turbo$2520E-Bikes/filter:categoryproperty:Kids/filter:categoryproperty:MTB"
    driver = get_driver()
    driver.get(base_url)
    page = 1
    shop_name = "Specialized"
    language = "de"
    category = "MountainBikes"
    rows = []
    while True:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-list__item"))
            )
        except:
            break
        bikes = driver.find_elements(By.CLASS_NAME, "product-list__item")

        for bike in bikes:
            url_detail = bike.find_element(By.TAG_NAME, "a").get_attribute("href")
            model = bike.find_element(By.CLASS_NAME, "product-list__name").text
            condition = bike.find_element(By.CLASS_NAME, "product-badge").get_attribute("aria-label")
            brand = model.split()[0]
            prices = bike.find_element(By.CLASS_NAME, "product-list__item-price").find_elements(By.TAG_NAME, "div")
            price = prices[0].text.strip().split()[0].replace(".", "").replace(",", ".")
            rrp = ""
            if len(prices) > 1:
                rrp = prices[1].text.strip().split()[0].replace(".", "").replace(",", ".")

            rows.append(
                {
                    "shop_name": shop_name,
                    "language": language,
                    "year": "",
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
        page += 1
     
        page_n = str(page)
        base_url = f"https://www.specialized.com/de/de/shop/c/shop?page={page_n}#/filter:group:Bikes/filter:group:Turbo$2520E-Bikes/filter:categoryproperty:Kids/filter:categoryproperty:MTB"
        
        driver.get(base_url)
     
    driver.quit()
    return rows

def scrap_each_page(rows):
    driver = get_driver()

    for row in rows:
    
        driver.get(row['url-detail'])
        time.sleep(2)
        variant_buttons = driver.find_elements(By.CLASS_NAME, "colorSwatch__Container-RuNMR")
  
        for button in variant_buttons:
            button.click()
            row_copy = deepcopy(row)
            model = row['modell'] + " " + button.get_attribute("aria-label")
            size_buttons = driver.find_element(By.CLASS_NAME, "AttributeSelector__Attributes-hWZvGf").find_elements(By.CLASS_NAME, "Button__BaseButton-kNsioU")
            dict_size = {}
            for button_ in size_buttons:
                button_.click()
                try:
                    key = driver.find_element(By.CLASS_NAME, "Toast__Container-eqNNUH").find_element(By.CLASS_NAME, "TypographyTheme__StyledP-mQqiM").text

                except:
                    key = "Available"
                
               
                value = button_.text
                if key in dict_size:
                    dict_size[key].append(value)
                else:
                    dict_size[key] = [value] 
            stock_sizes = []
            for key, value in dict_size.items():
                stock_sizes.append(key + "\n" + ", ".join(value))  
        
            stock_sizes = "\n\n".join(stock_sizes) 
            row_copy.update({"modell": model, "stock_sizes": stock_sizes})
            dict_data.append(row_copy)

    print("Handled ", len(dict_data))
    driver.quit()

if __name__ == "__main__":
    rows = scrap_list()

    
    print("To be handled: ", len(rows))
   
    # if you want only list view ignore code below this
    max_workers = 6
    len_per_dr = int(len(rows) / max_workers)
    list_rows = []
    i = 0
    
    for i in range(max_workers):
        list_rows.append(rows[len_per_dr * i : len_per_dr * (i + 1)])
    list_rows.append(rows[len_per_dr * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_each_page, list_rows)

    pd.DataFrame(dict_data).to_csv("specialized.csv")
  