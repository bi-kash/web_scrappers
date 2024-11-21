from bs4 import BeautifulSoup
import requests
import pandas as pd
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import re

dict_data = []


def scrap_list():
    rows = []
    url = "https://www.orbea.com/de-de/fahrrader/mountainbike/cat/"
    web_page = requests.get(url)
    soup = BeautifulSoup(web_page.content, features="lxml")
    bikes = soup.find_all("div", class_="grid__item")
    base_url = "https://www.orbea.com"
    shop_name = "orbea"
    language = "de"
    for bike in bikes:
        url_detail = bike.find("a", class_="card__name")
        model = url_detail.text.strip()
        url_detail = base_url + url_detail["href"]

        rrp = bike.find("span", class_="cp__original")
        if rrp:
            rrp = rrp.getText().strip().split()[0]
        else:
            rrp = ""
        price = bike.find("span", class_="cp__current").getText().strip().split()[0]

        rows.append(
            {
                "shop_name": shop_name,
                "language": language,
                "year": "",
                "brand": "",
                "modell": model,
                "condition": "new",
                "category_shop": "",
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

    # for Testing only
    # rows = rows[:2]

    for row in rows:
        web_page = requests.get(row["url-detail"])
        soup = BeautifulSoup(web_page.content, features="lxml")
        model = deepcopy(row["modell"])
        colors = [
            color["data-tippy-content"]
            for color in soup.find("div", class_="radio-image block-menu").find_all(
                "div"
            )
        ]
        variants = soup.find_all("div", class_="radio-text size-selection block-menu")
        year = soup.find("div", class_="image left").find("img")["src"]
        years = re.findall("[0-9]+", year)
        for year_temp in years:
            try:
                year = int(year_temp)
                if not (year > 1990 and year < 2050):
                    year = ""
                else:
                    break

            except:
                year = ""
        for variant, color in zip(variants, colors):
            sizes = variant.find_all("span", class_="info-size")
            dates = variant.find_all("span", class_="dates")

            stock_sizes = [
                size.text.strip() + ": " + date.text.strip()
                for size, date in zip(sizes, dates)
            ]
            stock_sizes = "\n".join(stock_sizes)

            stock_status = 1
            if len(stock_sizes) == 0:
                stock_status = 0

            # individuell konfigurierbar
            row.update(
                {
                    "category_shop": "MountainBike",
                    "brand": "Orbea",
                    "modell": "Orbea " + model + " | " + color,
                    "stock_status": stock_status,
                    "stock_sizes": stock_sizes,
                    "stock_text": "",
                    "year": year,
                }
            )
            dict_data.append(deepcopy(row))
    print("Total handled: ", len(dict_data))


if __name__ == "__main__":
    rows = scrap_list()

    max_workers = 16
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / 16)):
        list_rows.append(rows[16 * i : 16 * (i + 1)])
    list_rows.append(rows[16 * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_each_page, list_rows)

    pd.DataFrame.from_records(dict_data).to_csv("orbea.csv")
