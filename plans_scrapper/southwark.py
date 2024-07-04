import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Need these: shop_name,language,year,brand,modell,condition,category_shop,stock_status,stock_text,stock_sizes,url-detail,price,rrp
def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = False
    chromeOptions.add_argument("--log-level=3")
    chromeOptions.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    # chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chromeOptions
    )

    return driver

def scrap():
    driver = get_driver()
    dict_list = []
    driver.get('https://planning.southwark.gov.uk/online-applications/search.do?action=weeklyList')
    driver.find_element(By.XPATH, "//input[@value='Search']").click()
    driver.find_element(By.XPATH, "//option[@value='100']").click()
    driver.find_element(By.XPATH, "//input[@value='Go']").click()
    plan_links = [element.get_attribute('href') for element in driver.find_elements(By.XPATH, "//li[@class='searchresult']/a")]
    count = 0
    for plan_link in plan_links:
        count+=1
        driver.get(plan_link)
        trs = driver.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        dict_data = {}
        dict_data['url'] = plan_link
        for tr in trs:
            key = tr.find_element(By.TAG_NAME, 'th').text.strip()
            value = tr.find_element(By.TAG_NAME, 'td').text.strip()
            dict_data[key] = value
        
        dict_list.append(dict_data)
        if count>3:
            break
    return dict_list

if __name__ == "__main__":
    filename = 'southwark_plan.csv'
    records = scrap()
    pd.DataFrame.from_records(records).to_csv(filename, index=False)



