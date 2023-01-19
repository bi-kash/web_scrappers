
from bs4 import BeautifulSoup
import requests
import pandas as pd
import math
import re

def scrap():

    base_url = "https://www.jonito.com/fahrraeder/mountainbikes/fullys/?availability=1&seite="
    web_page = requests.get(base_url)
    soup = BeautifulSoup(web_page.content, features="lxml")

    n_bikes = int(soup.find("span", class_="js-pager-max").text)
    n_bikes_per_page = int(soup.find("span", class_="js-pager-to").text)
    n_page = math.ceil(n_bikes/n_bikes_per_page)
    rows = []

    rows = []
    shop_name = "jonito"
    language = "de"
    category = "Mountainbikes"
    for i in range(n_page):
        base_url = base_url+str(i+1)
        web_page = requests.get(base_url)
        soup = BeautifulSoup(web_page.content, features="lxml")
        bikes = soup.find_all("div", class_ = "col product-wrapper productbox")
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
            brand = bike.find("div", class_="productlist-hersteller").text
            model = bike.find("div", class_="productbox-title").text.strip()
            price = bike.find("span", class_="range-price")
            stock_text = bike.find("div", class_="productbox-ribbon").text
            if price:
                price = price.text.split()[0].replace(".", "")
                price = price.split(',')[0]
            else:
                price = ""

            rrp = bike.find("span", class_="text-stroke")
            if rrp:
                rrp = rrp.text.split()[0].replace(".", "")
                rrp = rrp.split(',')[0]
                rrp = int(rrp)
            else:
                rrp = ""

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
                    "stock_text": stock_text,
                    "stock_sizes": "",
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )
    return rows

if __name__ == "__main__":
    rows = scrap()
    pd.DataFrame.from_records(rows).to_csv("jonito.csv")
