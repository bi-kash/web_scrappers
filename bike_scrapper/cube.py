from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import re


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


# Get lists of link
def get_bike_links(
    search_url="https://www.cube.eu/de-de/bikes/mountainbike/hardtail?p=1&properties=ad1cb35585ad922fdf2e4a81752bfe9d",
    driver=None,
):
    driver.get(search_url)
    bike_links = []
    for bike in driver.find_elements(By.CLASS_NAME, "card.product-box.box-standard"):
        bike_info = bike.find_element(By.TAG_NAME, "a")
        bike_links.append(bike_info.get_attribute("href"))
    return bike_links


def scrap_bike(bike_links, driver):
    list_of_rows = []
    wait = WebDriverWait(driver, 5)
    count = 0
    num_bike = 0
    for url in bike_links:

        row = {}
        driver.get(url)
        Img = (
            driver.find_element(By.CLASS_NAME, "cms-image-container.is-contain")
            .find_element(By.TAG_NAME, "img")
            .get_attribute("src")
        )
        Model = driver.find_element(By.CLASS_NAME, "product-detail-name")
        Model = Model.text.strip().splitlines()
        Model = [ele.strip() for ele in Model]
        Model = ";".join(Model)
        Rrp = (
            driver.find_element(By.CLASS_NAME, "product-detail-price-container")
            .find_element(By.TAG_NAME, "meta")
            .get_attribute("content")
        )

        try:
            Img2 = (
                driver.find_element(By.CLASS_NAME, "img-wrapper")
                .find_element(By.TAG_NAME, "a")
                .get_attribute("href")
            )

            Model2 = Model
            Rrp2 = Rrp

        except:
            # Sometime there are no second bicycle pictures
            Img2 = ""
            Model2 = ""
            Rrp2 = ""

        row.update(
            {
                "Source Url": url,
                "Img": Img,
                "Model": Model,
                "Rrp": Rrp,
                "Img2": Img2,
                "Model2": Model2,
                "Rrp2": Rrp2,
            }
        )
        wait.until(
            lambda driver: driver.find_element(
                By.CLASS_NAME, "product-detail-description-accordion"
            )
        )

        Highlights = driver.find_element(
            By.CLASS_NAME, "product-detail-description-accordion"
        ).find_elements(By.CLASS_NAME, "card-header")
        count = 0
        for Highlight in Highlights:
            count += 1
            col_name = "Highlight " + str(count)
            row.update({col_name: Highlight.get_attribute("innerText").strip()})

        properties = driver.find_element(
            By.CLASS_NAME, "product-property-tables"
        ).find_elements(By.CLASS_NAME, "table-row.row.no-gutters")
        for property in properties:
            title = (
                property.find_element(By.CLASS_NAME, "title")
                .get_attribute("innerText")
                .strip()
            )
            val = (
                property.find_element(By.CLASS_NAME, "mb-0")
                .get_attribute("innerText")
                .strip()
            )
            row.update({title: val})

        details = driver.find_element(By.CLASS_NAME, "product-detail-more-information")

        EINSATZKATEGORIE = (
            details.find_element(By.CLASS_NAME, "title")
            .get_attribute("innerText")
            .strip()
        )
        MAXIMALES = (
            details.find_element(By.CLASS_NAME, "weight-amount")
            .get_attribute("innerText")
            .strip()
        )
        MAXIMALES = re.findall(r"\b\d+\b", MAXIMALES)[0]
        EINSATZKATEGORIE = re.findall(r"\b\d+\b", EINSATZKATEGORIE)[0]
        row.update({"Bike Einsatzkategorie": EINSATZKATEGORIE})
        row.update({"Maximales Systemgewicht": MAXIMALES})

        geometries = driver.find_element(
            By.CLASS_NAME, "table.e-geometry-table"
        ).find_elements(By.TAG_NAME, "tr")
        size_keys = geometries[0].find_elements(By.CLASS_NAME, "geometry-table-field")
        count = 0
        for size_key in size_keys:
            col = "Sizekey " + str(count)
            if count == 0:
                col = "Sizekey"
            row.update({col: size_key.get_attribute("innerText").strip()})
            count += 1

        for geometry in geometries[1:]:
            col_name = geometry.find_element(By.TAG_NAME, "th").get_attribute(
                "innerText"
            )
            for info in geometry.find_elements(By.TAG_NAME, "td"):

                # key = col_name + " "+ re.sub(r'[0-9.]', '', info.get_attribute('data-sizekey'))
                key = col_name + " " + info.get_attribute("data-sizekey")
                value = info.get_attribute("innerText").strip()
                row.update({key: value})

                Marketing_text = driver.find_element(
                    By.CLASS_NAME, "wrapper-text"
                ).get_attribute("innerText")
                row.update({"Marketing Text": Marketing_text})
        num_bike += 1
        if num_bike % 5 == 0:
            print(num_bike, " bikes scraped")
        list_of_rows.append(row)
    return list_of_rows


if __name__ == "__main__":

    filename = "cube.xlsx"
    driver = get_driver()
    driver.maximize_window()
    bike_list_in = "https://www.cube.eu/de-de/bikes/mountainbike/hardtail?p=1&properties=ad1cb35585ad922fdf2e4a81752bfe9d"
    bike_links = get_bike_links(search_url=bike_list_in, driver=driver)
    rows = scrap_bike(bike_links=bike_links, driver=driver)
    driver.quit()
    df = pd.DataFrame.from_records(rows)
    df.to_excel(filename)
    print("file saved in ", filename)
