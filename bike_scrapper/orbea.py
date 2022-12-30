from bs4 import BeautifulSoup
import requests
import pandas as pd
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

dict_data = []


def scrap_list():
    rows = []
    url = "https://www.orbea.com/de-de/fahrrader/mountainbike/cat/"
    web_page = requests.get(url)
    soup = BeautifulSoup(web_page.content, features="lxml")
    bikes = soup.find_all("li", class_="prod-bikes")
    shop_name = "orbea"
    language = "de"
    for bike in bikes:
        prod_info = bike.find("div", class_="prod-info bikes")
        base_url = "https://www.orbea.com"
        url_detail = base_url + bike.find("a")["href"]
        model = prod_info.find("h2").getText()
        rrp = prod_info.find("strong", class_="outlet-original-price")
        if rrp:
            rrp = rrp.getText().split()[0]
        else:
            rrp = ""
        price = prod_info.find("strong", class_="main-price").getText().split()[0]

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
    for row in rows:
        web_page = requests.get(row["url-detail"])
        soup = BeautifulSoup(web_page.content, features="lxml")
        category_brand = soup.find("p", class_="breadcrumbs").find_all("a")
        category = category_brand[0].getText()
        brand = category_brand[1].getText()
        model = deepcopy(row["modell"])
        colors = [color["title"] for color in soup.find_all("img", "tooltip-top")]
        variants = soup.find_all("div", class_="sizes")
        for variant, color in zip(variants, colors):
            stock_infos = variant.find_all("li")
            stock_sizes = []
            for stock_info in stock_infos:
                if "not-available-orbea" in stock_info["class"]:
                    continue
                stock_info = BeautifulSoup(
                    str(stock_info).replace("<br/>", ", "), "html.parser"
                )
                stock_size = stock_info.find("span", class_="size-txt").getText()
                stock_text = stock_info.find("span", class_="delivery").getText()

                stock_sizes.append(stock_size + ": " + stock_text)
            stock_status = 1
            if len(stock_sizes) == 0:
                stock_status = 0
            stock_sizes = "\n".join(stock_sizes)
            row.update(
                {
                    "category_shop": category,
                    "brand": brand,
                    "modell": model + " | " + color,
                    "stock_status": stock_status,
                    "stock_sizes": stock_sizes,
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
