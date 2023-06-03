import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import time
import re
from bs4 import BeautifulSoup
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
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
def scrap_list():
    shop_name = "fahrrad"
    language = "de"
    category = "MountainBikes"
    rows = []
    base_url = "https://www.fahrrad.de/fahrraeder/mountainbikes/?prefn1=f_2100&prefv1=kein%20E-Bike"
    web_page = requests.get(base_url)
    soup = BeautifulSoup(web_page.content, features="lxml")
    n_page = int(soup.find("a", class_="last pagination__listiteminner").text.strip())
    bikes = soup.find_all("div", class_="js-product-tile-lazyload")
    for i in range(n_page):
       
        web_page = requests.get(base_url+"&page="+str(i+1))
        soup = BeautifulSoup(web_page.content, features="lxml")
        bikes = soup.find_all("div", class_="js-product-tile-lazyload")
        for bike in bikes:
            url_detail = bike.find("a", class_="thumb-link")

            model = url_detail.text
            brand = url_detail["title"].split()[0]
            url_detail = url_detail['href']
            image = bike.find("div", class_="product-image").find("img")["src"]
            if "https" not in url_detail:
                url_detail = "https://www.fahrrad.de" + url_detail
            year = ""
            years = re.findall('[0-9]+', url_detail)
            for year_temp in years:
                try:
                    year = int(year_temp)
                    if not (year > 1990 and year < 2050):
                        year = ""
                    else:
                        break
                    
                except:
                    year = ""
            rrp = bike.find("span", "retail-price")
            if rrp:
                rrp = rrp.text.split()[1].replace(".", "").replace(",", ".")
            else:
                rrp = ""
            try:
                price = bike.find("span", class_="price-sales")
                if price:
                    price = price.text.split()[1].replace(".", "").replace(",", ".")
                else:
                    price = bike.find("span", class_="price-standard")
                    if price:
                        price = price.text.split()[1].replace(".", "").replace(",", ".")
                    else:
                        price = ""
            except:
                price = ""

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
                    "rrp": rrp,
                    "image": image
                }
            )
    return rows


def scrap_each_page(rows):
    sizes_ref = ["XXS", "XS", "S", "M", "ML", "L", "XL", "XXL"]
    driver = get_driver()
    driver.get(rows[0]["url-detail"])
    driver.maximize_window()
    driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
    for row in rows:
        try:
            driver.get(row['url-detail'])
        

                    
            variants = driver.find_elements(By.CLASS_NAME, "variation__option")
            dict_variant = {}
            sizes = []
            for variant in variants:
                value = variant.get_attribute("data-variationvalue").split("-")[0]
                key = variant.get_attribute("data-availability")
                sizes.append(value)
                if key not in dict_variant:
                    dict_variant[key] = [value]
                else:
                    dict_variant[key].append(value)

            stock_sizes = []
            for key, value in dict_variant.items():
                stock_sizes.append(key + "\n" + ", ".join(value))   
            stock_sizes = "\n\n".join(stock_sizes)
            row["stock_sizes"] = stock_sizes
            top_features = driver.find_element(By.CLASS_NAME, "topfeatures.contentwrapper.tns-wrapper")
            keys = [item.text for item in top_features.find_elements(By.CLASS_NAME, "cyc-color-text_secondary.is-center,cyc-typo_body")]
            values = [item.text for item in top_features.find_elements(By.CLASS_NAME, "pdp_featurelist_value.cyc-color-text.cyc-typo_headline-3.is-center.cyc-margin_top-1")]
            for key, value in zip(keys, values):
                row.update({key:value})

            driver.find_element(By.CLASS_NAME, "equipment-more.gtm-specificationsshowmore").click()
            features = driver.find_elements(By.CLASS_NAME, "pdp_featureitem")

            for feature in features:
                key = feature.find_element(By.CLASS_NAME, "pdp_featurelist_group").text
                list = feature.find_elements(By.CLASS_NAME, "pdp_featurelist_feature")
                if list:
                    vals = feature.find_elements(By.CLASS_NAME, "pdp_featurelist_value")
                    for item1, item2 in zip(list, vals):
                        row[key + " " + item1.text.replace(":", "")] = item2.text 

                else:
                    value = feature.find_element(By.CLASS_NAME, "pdp_featurelist_value").text
                    row[key] = value
                        

                
            row["image"] = driver.find_element(By.CLASS_NAME, "product-image.main-image.gtm-zoom").find_element(By.TAG_NAME, "img").get_attribute("src")
            try:
                driver.execute_script(
                    "window.scrollTo(0, {});".format(0)
                )
                driver.find_elements(By.CLASS_NAME, "label-inner")[-1].click()

                time.sleep(1)
                driver.switch_to.frame(driver.find_element(By.ID, "trigger-geometries-widget"))
                for tr in driver.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr"):
                    th = tr.find_element(By.TAG_NAME, "th").text
                    count = 0
                    for size, td in zip(sizes, tr.find_elements(By.TAG_NAME, "td")):
                        count += 1
                        letter_size = re.findall(r'[A-Z]+', size)
                        if letter_size:
                            letter_size = letter_size[0]
                        else:
                            letter_size = "A"
                        if letter_size in sizes_ref:
                            if (th + " " +  letter_size not in row): 
                                row[th + " " +  letter_size] = td.text
                            else:
                                row[th + " " +  letter_size] = row[th + " " +  letter_size] + ", " + td.text
                        else:
                            row[th + " " + sizes_ref[int(len(sizes_ref) - len(sizes))/2 + count ]] = td.text
                dict_data.append(row) 
                if len(dict_data) % 25 == 0:
                    print("Handled: ", len(dict_data))
                    df = pd.DataFrame.from_records(dict_data)
                    df["year"] = df["Modelljahr"]
                    df.to_csv("fahrrad.csv")
            except:
                pass
                

        except:
            driver.quit()
            driver = get_driver()
            driver.get(rows[0]["url-detail"])
            driver.maximize_window()
            driver.find_element(By.ID, "onetrust-accept-btn-handler").click()

   
    driver.quit()

if __name__ == "__main__":
    rows = scrap_list()
    print("To be handled: ", len(rows))
    # if you want only list view ignore code below this
    max_workers = 16
    len_per_dr = int(len(rows) / max_workers)
    list_rows = []
    i = 0
    for i in range(max_workers):
        list_rows.append(rows[len_per_dr * i : len_per_dr * (i + 1)])
    list_rows.append(rows[len_per_dr * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_each_page, list_rows)

    df = pd.DataFrame.from_records(dict_data)
    df["year"] = df["Modelljahr"]
    df.to_csv("fahrrad.csv")