# libraries imports
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import shutil
import re
import os
import time
import random
import traceback

download_path = '/Users/bikash/Downloads/'

# Define the directory where you want to save the files
directory = 'incident_files'

base_url = "https://www.gunviolencearchive.org/query"

def date_list(start_date, end_date, time_delta):
  date_list = []
  while start_date <= end_date:
    date_list.append((start_date, start_date + time_delta))
    start_date += time_delta +timedelta(days=1)
  return date_list


def random_sleep(min_sec=3, max_sec=8):
  # To make interaction human like
  time.sleep(random.randint(min_sec, max_sec))

# define start date and end date with certain time interval to produce date list. Each csv will consists incident of 7 days interval. From 8th day new csv is formed
date_list = date_list(datetime(year=2020, month=6, day=25), datetime(year=2020, month=12, day=24), timedelta(days=7))



# Check if the directory exists, otherwise create it
if not os.path.exists(directory):
    os.makedirs(directory)
    print(f"Directory '{directory}' created.")


def get_driver():
  options = webdriver.ChromeOptions()
  #options.add_argument('--headless')
  options.add_argument('--disable-gpu')
  options.add_argument('--window-size=1920,1080')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
  options.add_experimental_option('excludeSwitches', ['enable-automation'])
  options.add_experimental_option('useAutomationExtension', False)
  # installs chrome driver automatically if not present
  service = Service(ChromeDriverManager().install())
  driver = webdriver.Chrome(
        service=service, options=options
    )
  return driver


driver = get_driver()
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
wait = WebDriverWait(driver, 10) # option to wait 10 seconds atleast if some element takes time to load on page


file_dict = {}
for start_date, end_date in date_list:
  if os.path.exists(f"{directory}/gvs_{start_date.strftime('%m-%d-%Y')}_{end_date.strftime('%m-%d-%Y')}.csv"):
    continue

  try:
    driver.get(base_url)
    random_sleep()
    driver.find_element(By.CLASS_NAME, "filter-dropdown-trigger").click() # click on filter dropdown
    random_sleep()
    driver.find_element(By.XPATH, '//*[@data-value="IncidentDate"]').click() # select filter by date from dropdown
    random_sleep()
    date_inputs = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "date-picker-single"))) # get date inputs

    # start date calendar actions

    date_inputs[0].click()
    calendar = driver.find_elements(By.CLASS_NAME, "daterangepicker")[0].find_element(By.CLASS_NAME, "calendar")
    year_select = Select(calendar.find_element(By.CLASS_NAME, "yearselect"))
    year_select.select_by_value(str(start_date.year))
    random_sleep()
    month_select = Select(calendar.find_element(By.CLASS_NAME, "monthselect"))
    month_select.select_by_index(start_date.month - 1)
    random_sleep()

    for item in calendar.find_elements(By.XPATH, f'//td[contains(@class, "available") and not(contains(@class, "off")) and text()="{start_date.day}"]'):
        try:
            item.click()
            break
        except:
            pass
    random_sleep()

    # end date calendar actions
    date_inputs[1].click()
    random_sleep()
    calendar = driver.find_elements(By.CLASS_NAME, "daterangepicker")[1].find_element(By.CLASS_NAME, "calendar")
    year_select = Select(calendar.find_element(By.CLASS_NAME, "yearselect"))
    year_select.select_by_value(str(end_date.year))
    random_sleep()
    month_select = Select(calendar.find_element(By.CLASS_NAME, "monthselect"))
    month_select.select_by_index(end_date.month - 1)
    random_sleep()
    for item in calendar.find_elements(By.XPATH, f'//td[contains(@class, "available") and not(contains(@class, "off")) and text()="{end_date.day}"]'):
        try:
            item.click()
            break
        except:
            pass
    random_sleep()

    driver.find_element(By.XPATH, '//input[@value="Search"]').click()
    random_sleep()

    driver.find_element(By.XPATH, '//a[contains(text(), "Export as CSV")]').click()

    wait = WebDriverWait(driver, 10)
    download_link = wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "Download")]')))
    link = driver.current_url
    random_sleep()
    download_link.click() # download a csv


    pattern = r'filename=public%3A//([^&]+\.csv)'

    # Use re.search to find the pattern in the URL
    match = re.search(pattern, link)

    if match:
        filename = match.group(1)  # Extract the first group from the match
    else:
        print("Filename not found in the URL.")


    # rename downloaded csv and move it
    new_file_directory = directory + f"/gvs_{start_date.strftime('%m-%d-%Y')}_{end_date.strftime('%m-%d-%Y')}.csv"

    file_dict[download_path+filename] = new_file_directory

    # sometimes download may be delayed so instead of waiting for file to download, we move whatever file has already been downloaded into incident_files folder
    for key, value in file_dict.items():
      if os.path.exists(key):
        shutil.move(key, value)


  except Exception as e:
    print(traceback.format_exc())
    print("Error while scraping. Please checkout screenshot.png in root folder and checkout logs")
    driver.save_screenshot("screenshot.png")
    logs = driver.get_log('browser')  # Fetch browser logs
    for log in logs:
        print(log)
    print(driver.current_url)
    #move remaining files to incident files folder.
    for key, value in file_dict.items():
      if os.path.exists(key):
        shutil.move(key, value)

random_sleep(min_sec=16, max_sec=20)

#move remaining files to incident files folder.
for key, value in file_dict.items():
  if os.path.exists(key):
    shutil.move(key, value)