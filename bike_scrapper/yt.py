
import time
import re
from bs4 import BeautifulSoup
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from copy import deepcopy

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

data_dict = []

def scrap_list():
    shop_name = "yt-industries"
    language = "de"
    category = "MountainBikes"

    page = 0
    rows = []
    while True:
        page+=1
        print(page)
        base_url = "https://www.yt-industries.com/de/produkte/bikes/?p={}".format(page)
        print(base_url)
        web_page = requests.get(base_url)
        soup = BeautifulSoup(web_page.content, features="lxml")

        
        bikes =  soup.find_all("div", class_="product--info")
        print(len(bikes))
        if len(bikes) == 0:
            break
        
        for bike in bikes:
            url_detail = bike.find("a")
            model = url_detail['title']
            url_detail = url_detail['href']
            price = bike.find("span", class_="price--default")
            try:
                rrp = bike.find("span", class_="price--discount")
            except:
                rrp = ""

            if rrp:
                rrp = rrp.text.split()[2].replace(".", "").replace(",", ".")

            price = price.text.split()[1].replace(".", "").replace(",", ".")

            rows.append(
                {
                    "shop_name": shop_name,
                    "language": language,
                    "year": "",
                    "brand": "",
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
    print("Total number of bikes: {}".format(len(rows)))
    return rows


def dict_update(row, driver):
    color_options = driver.find_elements(By.CLASS_NAME, "ytind-color-options")
    model_list = []
    for color_option in color_options:
        a = deepcopy(row)
        model = row['modell'] + " " + color_option.get_attribute('data-color')
        if model in model_list:
            continue
        model_list.append(model)
        print(model)
        size_frames = color_option.find_elements(By.CLASS_NAME, "ytind-frame-size-selection")
        sizes_dict = {}
        for size_frame in size_frames:
            value = size_frame.find_element(By.CLASS_NAME, "ytind-availability-table-size").text
            key = size_frame.find_element(By.CLASS_NAME, "ytind-availability-table-stock").text
            
            if key in sizes_dict:
                sizes_dict[key].append(value)
            else:
                sizes_dict[key] = [value]
        
        stock_sizes = []
        for key, value in sizes_dict.items():
            stock_sizes.append(key + "\n" + ", ".join(value))
        
        stock_sizes = "\n\n".join(stock_sizes) 
    

        
        a.update(
            {
                "modell": model,
                "stock_sizes": stock_sizes
            }
        )
        data_dict.append(a)

def scrap_pages(rows):
    driver = get_driver()
    for row in rows:
        driver = get_driver()
        base_url = row['url-detail']
        driver.get(base_url)
        driver.maximize_window()
        wheels = driver.find_elements(By.CLASS_NAME, "ytind-wheelsize-option")
        if len(wheels) <= 1:
            dict_update(row, driver)
        else:

            current_scroll_position, new_height = 0, 1
            speed = 100
            while current_scroll_position <= new_height:
                current_scroll_position += speed
                driver.execute_script(
                    "window.scrollTo(0, {});".format(current_scroll_position)
                )
                try:
                    driver.find_element(By.CLASS_NAME, "ytind-wheelsize-option").click()
                    break
                except:
                    new_height = driver.execute_script("return document.body.scrollHeight")
            
            wheels = driver.find_elements(By.CLASS_NAME, "ytind-wheelsize-option")
            model = row['modell']
            if wheels:
                wheels_ = []
                for wheel in wheels:
                
                    if wheel.text in row['modell'].split():
                        wheels_ = [wheel]
                        break
                    else:
                        wheels_.append(wheel)
                        
            for wheel in wheels_:

                
                wheel_size = wheel.text
                
                if wheel_size not in model.split(): 
                    row['modell'] = model + " " + wheel.text
        
                
                wheel.click()
                time.sleep(1)

                dict_update(row, driver)
    print("handled: ", len(data_dict))
    driver.quit()
 

if __name__ == "__main__":
    data_dict = []
    rows = scrap_list()
    max_workers = 6
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / max_workers)):
        list_rows.append(rows[max_workers * i : max_workers * (i + 1)])
    list_rows.append(rows[max_workers * (i + 1) :])
    print(len(list_rows))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_pages, list_rows)

    pd.DataFrame(data_dict).to_csv("yt-industries.csv")




