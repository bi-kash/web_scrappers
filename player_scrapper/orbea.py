from bs4 import BeautifulSoup
import requests
import pandas as pd
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

from pandas.api.types import CategoricalDtype
import numpy as np
import time

# from settings import export_path

dict_data = []


def scrap_list():
    rows = []
    url = "https://www.orbea.com/de-de/fahrrader/mountainbike/cat/"
    web_page = requests.get(url)

    soup = BeautifulSoup(web_page.content, features="lxml")

    bikes = soup.find_all("div", class_="grid__item")
    shop_name = "orbea"
    language = "de"
    for bike in bikes:
        prod_info = bike.find("div", class_="prod-info.bikes")
        base_url = "https://www.orbea.com"
        url_detail = base_url + bike.find("a")["href"]
        model = prod_info.find("h2").getText()
        price = prod_info.find("strong", class_="main-price").getText().split()[0]
        price = price.replace(",", "")
        rrp = prod_info.find("strong", class_="outlet-original-price")
        if rrp:
            rrp = rrp.getText().split()[0]
            rrp = rrp.replace(",", "")
        else:
            rrp = price

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
        print(rows)
    return rows


def scrap_each_page(rows):

    # for Testing only
    # rows = rows[:2]

    for row in rows:
        web_page = requests.get(row["url-detail"])
        soup = BeautifulSoup(web_page.content, features="lxml")
        model = deepcopy(row["modell"])
        colors = [color["title"] for color in soup.find_all("img", "tooltip-top")]
        variants = soup.find_all("div", class_="sizes")
        for variant, color in zip(variants, colors):
            stock_infos = variant.find_all("li")
            stock_sizes = []

            df = pd.DataFrame(columns=["stock_text", "stock_size"])

            for stock_info in stock_infos:
                if "not-available-orbea" in stock_info["class"]:
                    continue
                stock_info = BeautifulSoup(
                    str(stock_info).replace("<br/>", ", "), "html.parser"
                )
                stock_size = stock_info.find("span", class_="size-txt").getText()
                stock_text = stock_info.find("span", class_="delivery").getText()

                stock_sizes.append(stock_size)

                # stock_text = stock_text.replace(", "," - ")

                # df.loc[len(df.index)] = [stock_text,stock_size]

            stock_sizes = ", ".join(stock_sizes)
            print(row["url-detail"])
            print(stock_sizes)

            """
            #Ausgabe mit individuellen Lieferzeiten:

            df_new = df.groupby(by=["stock_text"])["stock_size"].agg(list)
            df_new = df
            stock_text_tmp=[]
 

            for index, row in df_new.iterrows():
                stock_text_tmp.append((row["stock_text"] + "<br>" + ", ".join(row["stock_size"]) ))


            stock_text = "<br>".join(stock_text_tmp)

            """

            stock_text = "lieferbar in:<br>" + stock_sizes

            stock_status = 1
            if len(stock_sizes) == 0:
                stock_status = 3
                stock_text = "individuell konfigurierbar"

            stock_sizes = "\n".join(stock_sizes)

            # individuell konfigurierbar

            row.update(
                {
                    "category_shop": category,
                    "brand": "Orbea",
                    "modell": "Orbea " + model + " | " + color,
                    "stock_status": stock_status,
                    "stock_sizes": stock_sizes,
                    "stock_text": stock_text,
                }
            )
            dict_data.append(deepcopy(row))
    print("Total handled: ", len(dict_data))


if __name__ == "__main__":
    rows = scrap_list()

    """

    max_workers = 16
    len_rows = len(rows)
    list_rows = []
    i = 0
    for i in range(int(len_rows / 16)):
        list_rows.append(rows[16 * i : 16 * (i + 1)])
    list_rows.append(rows[16 * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scrap_each_page, list_rows)
    """

    print("Total Bikes crawled: ", len(rows))

    # pd.DataFrame.from_records(rows).to_csv(export_path+"orbea.csv")

    pd.DataFrame.from_records(rows).to_excel("orbea.xlsx")
