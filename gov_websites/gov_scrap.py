# from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import pandas as pd
import traceback
import random
import openpyxl
import os


def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = False
    chromeOptions.add_argument("--log-level=3")

    # use rotating proxy. Configuration geo.iproyal allows for rotating proxy servers automatically. If you do not have proxy then increase sleep time in random_sleep function
    # proxy = "geo.iproyal.com:12321"
    # ChromeOptions.add_argument('--proxy-server={}'.format(proxy))

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    # chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chromeOptions
    )
    return driver


def remove_matching_dicts(list1, list2):
    # Extract Entity ID Numbers from list2
    entity_id_numbers = {d["Entity ID Number"] for d in list2}

    # Filter list1 to remove dictionaries with matching Entity ID Numbers
    filtered_list1 = [
        d for d in list1 if d["Entity ID Number"] not in entity_id_numbers
    ]

    return filtered_list1


def random_sleep(min_sec=4, max_sec=8):
    # avoiding ban
    time.sleep(random.randint(min_sec, max_sec))


data_dict_list = []
detailed_dict_list = []


def get_records(start_from=None):
    driver = get_driver()
    if start_from:
        driver.get(start_from)
    else:
        driver.get("https://arc-sos.state.al.us/CGI/CORPNAME.MBR/INPUT")
    # find element by tag input with value="search"
    driver.find_element(By.XPATH, '//*[@value="Search"]').click()
    entity_ids = []
    current_url = driver.current_url
    while True:
        try:
            current_url = driver.current_url
            rows = (
                driver.find_element(By.ID, "block-sos-content")
                .find_element(By.TAG_NAME, "tbody")
                .find_elements(By.TAG_NAME, "tr")
            )
            next_page = rows[-1].find_elements(By.TAG_NAME, "a")[-1]

            records = rows[:-1]
            for row in records:

                url = row.find_element(By.TAG_NAME, "a").get_attribute("href")
                tds = row.find_elements(By.TAG_NAME, "td")
                entity_id = tds[0].text
                if entity_id in entity_ids:
                    continue
                else:
                    entity_ids.append(entity_id)
                entity_name = tds[1].text
                city = tds[2].text
                type = tds[3].text
                status = tds[4].text
                data_dict_list.append(
                    {
                        "url": url,
                        "Entity ID Number": entity_id,
                        "Entity Name": entity_name,
                        "City": city,
                        "Entity type": type,
                        "Status": status,
                    }
                )
            if next_page.text != "Next >>":
                break
            else:
                next_page = next_page.get_attribute("href")

            driver.get(next_page)

        except:
            print(traceback.format_exc())
            print("current link:", current_url)
            print(
                "There is a error. But don't worry next time you run this script please pass the link to the function from where you want to start"
            )

            break

        # save dict_list to csv
        pd.DataFrame.from_records(data_dict_list).to_csv("alabama.csv", index=False)
        driver.quit()


def detailed_scrap(rows):
    # we have to visit each new link to scrap detaily so it takes time.
    driver = get_driver()
    try:
        for data_dict in rows:
            driver.get(data_dict["url"])
            infos = [
                info.find_elements(By.TAG_NAME, "td")
                for info in driver.find_element(By.TAG_NAME, "tbody").find_elements(
                    By.TAG_NAME, "tr"
                )
            ]

            info_dict = {}
            # info_dict["Entity Name"] = data_dict["Entity Name"]
            for info in infos:
                try:
                    key = info[0].text
                    value = info[1].text
                    info_dict[key] = value
                except IndexError:
                    pass

            detailed_dict_list.append(info_dict)
            if len(detailed_dict_list) % 10 == 0:
                print("Number of records scraped:", len(detailed_dict_list))
                pd.DataFrame.from_records(detailed_dict_list).to_csv(
                    "alabama_detailed.csv", index=False
                )
            random_sleep()
    except:
        print(driver.current_url)
        print(traceback.format_exc())
        print(
            "Do not worry. Make sure load_from_csv is set to True and detailed_csv_exists is set to True"
        )

    pd.DataFrame.from_records(detailed_dict_list).to_csv(
        "alabama_detailed.csv", index=False
    )
    driver.quit()


if __name__ == "__main__":

    # set this to true if you already have scraped records using get_records() function. There is no point repeating this step again except waste of time
    load_from_csv = False

    # we save scraped data regularly. If you want to start from where you left off then set this to True
    detailed_csv_exists = True

    if load_from_csv:
        if os.path.exists("alabama.csv"):
            data_dict_list = pd.read_csv("alabama.csv").to_dict(orient="records")
        else:
            get_records()
    else:
        get_records()

    if detailed_csv_exists:
        if os.path.exists("alabama_detailed.csv"):
            detailed_dict_list = pd.read_csv("alabama_detailed.csv").to_dict(
                orient="records"
            )
            data_dict_list = remove_matching_dicts(
                data_dict_list, detailed_dict_list
            )  # no need to scrape again if data already exists

    detailed_scrap(data_dict_list)
    """
    # if you want to use multithreading use this. But be careful. Simultanus website visit from same IP can lead to ban. So I have avoided it after trying
    max_workers = 6
    len_rows = len(data_dict_list)
    each_list_len = int(len_rows/max_workers)+1
    list_rows = []
    for i in range(max_workers-1):
        list_rows.append(data_dict_list[each_list_len * i : each_list_len* (i + 1)])
    list_rows.append(data_dict_list[each_list_len * (i + 1) :])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(detailed_scrap, list_rows)
    """

    df = pd.read_csv("alabama_detailed.csv")
    # Remove columns with "Unnamed" in their name
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # Reset index if needed
    df.reset_index(drop=True, inplace=True)

    # remove duplicates

    df.to_excel("result.xlsx")
