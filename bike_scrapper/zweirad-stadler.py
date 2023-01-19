
from bs4 import BeautifulSoup
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import re

def scrap_list():
    base_url = "https://shop.zweirad-stadler.de/fahrrad-shop/mountainbikes/?_artperpage=96"
    web_page = requests.get(base_url)
    soup = BeautifulSoup(web_page.content, features="lxml")
    shop_name = "Zweirad-stadler"
    language = "de"
    category = "MountainBikes"

    rows = []
    bikes = soup.find_all("div", class_ = "productBox")
    for bike in bikes:
        url_detail = bike.find("a")['href']

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
        brand = bike.find("div", class_="productManufacturer").text
        model = bike.find("div", class_="productTitle").text.strip()
        prices = bike.find_all("span", class_="priceSpan")
        #stock_text = bike.find("div", class_="productbox-ribbon").text
        if len(prices) == 2:
            rrp = prices[0].text.replace(".", "").replace("-", "")
            price = prices[1].text.replace(".", "").replace("-", "")
        else:
            price = prices[0].text.replace(".", "").replace("-", "")

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
            }
        )
    return rows

def scrap_each_page(rows):
    for row in rows:
        web_page = requests.get(row["url-detail"])
        soup = BeautifulSoup(web_page.content, features="lxml")
        variants = soup.find_all("div", class_="varianttitle")
        stock_sizes = []
        dict_variant = {}
        for variant in variants:
            texts = variant.text.strip().split("\n")
            key = texts[-1].strip()
            if key not in dict_variant:
                dict_variant[key] = [texts[0]]
            else:
                dict_variant[key].append(texts[0])
            stock_sizes = []
            for key, value in dict_variant.items():
                stock_sizes.append(key + "\n" + ", ".join(value))    
            
        stock_sizes = "\n\n".join(stock_sizes)
        row.update({"stock_sizes":stock_sizes})
    return rows

if __name__ == "__main__":
    rows = scrap_list()

    # if you want only list view ignore code below this
    max_workers = 16
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / 16)):
        list_rows.append(rows[16 * i : 16 * (i + 1)])
    list_rows.append(rows[16 * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_each_page, list_rows)

    pd.DataFrame.from_records(rows).to_csv("zweirad.csv")




