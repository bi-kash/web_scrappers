from bs4 import BeautifulSoup
import requests
import pandas as pd
import re


def scrap():
    base_url = "https://www.fahrrad-xxl.de/fahrraeder/mountainbikes/seite/"
    page = 0
    rows = []
    while True:
        page += 1
        web_page = requests.get(base_url + str(page))
        soup = BeautifulSoup(web_page.content, features="lxml")
        shop_name = "fahrrad-xxl"
        language = "de"
        category = "MountainBikes"

        bikes = soup.find_all(
            "div", class_="fxxl-element-artikel fxxl-element-artikel--slider"
        )
        if len(bikes) < 10:
            break

        for bike in bikes:
            url_detail = bike.find("a")["href"]

            year = ""

            brand = bike.find("div", class_="fxxl-element-artikel__brand").text
            model = bike.find("div", class_="fxxl-element-artikel__title").text.strip()
            years = re.findall("[0-9]+", model)
            for year_temp in years:
                try:
                    year = int(year_temp)
                    if not (year > 1990 and year < 2050):
                        year = ""
                    else:
                        break

                except:
                    year = ""
            # stock_text = bike.find("div", class_="productbox-ribbon").text
            price = bike.find("div", class_="fxxl-element-artikel__price--new")
            if not price:
                price = bike.find("div", class_="fxxl-price")
                price = (
                    price.text.strip()
                    .split()[0]
                    .replace(".", "")
                    .replace(",", ".")
                    .replace("-", "")
                )

            else:
                price = price.text.strip().split()
                if price[0] == "ab":
                    price = price[1].replace(".", "").replace(",", ".").replace("-", "")
                else:
                    price = price[0].replace(".", "").replace(",", ".").replace("-", "")
            rrp = bike.find("span", class_="fxxl-strike-price")
            if rrp:
                rrp = (
                    rrp.text.strip()
                    .split()[0]
                    .replace(".", "")
                    .replace(",", ".")
                    .replace("-", "")
                )
            else:
                rrp = ""

            stock_sizes = bike.find_all(
                "div", class_="fxxl-element-artikel__variant-slider-size-item"
            )
            if stock_sizes:
                stock_sizes = [item.text for item in stock_sizes]

            stock_sizes = ", ".join(stock_sizes)
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
                    "stock_sizes": stock_sizes,
                    "url-detail": url_detail,
                    "price": price,
                    "rrp": rrp,
                }
            )
    return rows


if __name__ == "__main__":
    rows = scrap()
    pd.DataFrame.from_records(rows).to_csv("fahrrad-xxl.csv")
