"""
This script scrapes the data from the website https://www.electionreturns.pa.gov/_ENR/General/OfficeResults?OfficeID=14&ElectionID=84&ElectionType=G&IsActive=0
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from copy import deepcopy
import re
import random
import os


def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = True
    chromeOptions.add_argument("--log-level=3")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chromeOptions
    )
    return driver


def random_sleep(min_sec=2, max_sec=3):
    # To make interaction human like
    time.sleep(random.randint(min_sec, max_sec))


def scrap_data(election_type, driver, data):
    offices = driver.find_elements(
        By.XPATH, "//div[@ng-repeat='levels in filterRecords(electionData)']"
    )
    office_name = offices[0].find_element(By.TAG_NAME, "span").text
    positions = (
        offices[0]
        .find_element(By.CLASS_NAME, "panel.panel-default")
        .find_elements(By.CLASS_NAME, "panel.panel-default")
    )
    for position in positions:
        data_dict = {}
        data_dict["url"] = driver.current_url
        data_dict["election"] = election_type
        data_dict["office"] = office_name
        position_name = position.find_element(By.TAG_NAME, "span").text
        data_dict["position"] = position_name

        candidates = position.find_elements(By.CLASS_NAME, "panel-body-party")
        for i in range(len(candidates)):
            infos = candidates[i].find_elements(By.TAG_NAME, "span")

            data_dict["candidate" + str(i + 1)] = infos[0].text
            data_dict["party" + str(i + 1)] = infos[1].text
            data_dict["votes" + str(i + 1)] = infos[3].text.split(" ")[-1].strip()
        data.append(data_dict)

    if len(offices) == 1:
        return data

    office_name = offices[1].find_element(By.TAG_NAME, "span").text
    positions = (
        offices[1]
        .find_element(By.CLASS_NAME, "panel.panel-default")
        .find_elements(By.CLASS_NAME, "panel.panel-default")
    )
    for position in positions:
        data_dict = {}
        data_dict["url"] = driver.current_url
        data_dict["election"] = election_type
        data_dict["office"] = office_name
        position_name = position.find_element(By.TAG_NAME, "span").text
        data_dict["position"] = position_name

        candidates = position.find_elements(By.CLASS_NAME, "panel-body-party")
        for i in range(len(candidates)):
            infos = candidates[i].find_elements(By.TAG_NAME, "span")
            data_dict["candidate" + str(i + 1)] = infos[0].text
            data_dict["votes_yes" + str(i + 1)] = infos[3].text.split(" ")[2].strip()
            data_dict["votes_no" + str(i + 1)] = infos[3].text.split(" ")[-1].strip()

        data.append(data_dict)
    return data


# code to check if number is in between or not
def drop_down_choices(periods, elections):
    drop_down_dict = {}
    for period in periods:
        splits = period.split(" - ")
        start = int(splits[0])
        end = int(splits[1])
        for election in deepcopy(elections):

            year = int(election.split(" ")[0])
            if year >= start and year <= end:
                drop_down_dict[election] = period
                elections.remove(election)

    return drop_down_dict


def main():
    directory = "data"
    # Check if the directory exists, otherwise create it
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory '{directory}' created.")

    base_url = "https://www.electionreturns.pa.gov/_ENR/General/OfficeResults?OfficeID=14&ElectionID=84&ElectionType=G&IsActive=0"
    driver = get_driver()
    driver.get(base_url)

    periods = [
        element.get_attribute("innerHTML")
        for element in driver.find_elements(By.XPATH, "//a[@alt = 'yearset.year']")
    ]
    elections = [
        element.get_attribute("innerHTML")
        for element in driver.find_elements(
            By.XPATH, "//a[contains(text(), 'Municipal Election')]"
        )
    ]

    type_period = drop_down_choices(periods, elections)
    office_names = [
        "Judge of the Court of Common Pleas",
        "Judge of the Court of Common Pleas - Philadelphia",
        "Judge of the Court of Common Pleas - Allegheny",
    ]

    for election_type, election_period in type_period.items():
        data = []
        file_name = "data/PA" + "_" + election_type + ".csv"
        if os.path.exists(file_name):
            continue

        driver.find_element(By.XPATH, f"//a[contains(text(), 'Elections')]").click()

        random_sleep()

        # Locate the element you want to move the mouse to
        element = driver.find_element(
            By.XPATH, f"//a[contains(text(), '{election_period}')]"
        )
        parent = element.find_element(By.XPATH, "..")

        # Create an instance of ActionChains
        actions = ActionChains(driver)

        # Move the mouse to the element
        actions.move_to_element(element).perform()

        random_sleep()
        element = parent.find_elements(
            By.XPATH, f"//a[@alt='electionTypes.type' and text() = 'Election']"
        )[periods.index(election_period)]
        actions.move_to_element(element).perform()

        element = parent.find_element(
            By.XPATH, f"//a[contains(text(), '{election_type}')]"
        ).click()
        random_sleep()

        for office_name in office_names:
            driver.find_element(By.XPATH, f"//a[contains(text(), 'Offices')]").click()
            random_sleep(max_sec=3)
            if not driver.find_elements(
                By.XPATH, f"//a[@class='ng-binding' and text() = '{office_name}']"
            ):
                continue
            else:
                driver.find_element(
                    By.XPATH, f"//a[@class='ng-binding' and text() = '{office_name}']"
                ).click()
                random_sleep()

                data = scrap_data(election_type, driver=driver, data=data)

        df = pd.DataFrame(data)
        df.to_csv(file_name, index=False)


if __name__ == "__main__":
    main()
