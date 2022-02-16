# Import necessary modules

from webbrowser import get
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import sys
import pandas as pd
import re

def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = False

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    #chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)
    return driver


def check_overlay(driver: ChromeDriverManager):
    # Detects overlay and cancel it.
    action = webdriver.ActionChains(driver)
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(lambda driver: driver.find_elements(By.CLASS_NAME, "om-effect-overlay"))
        action.click()
        action.perform()
    except:
        pass


def scrapper(page_depth: int = 2, search_url: str = "https://www.oddsshopper.com/odds/shop/nfl", save_to: str = "player_props.csv"):
    driver = get_driver()

    # Search for a web page
    driver.get(search_url)

    # maximize browser window
    driver.maximize_window()

    # Usually used to wait for loading process. Scrap after page is fully loaded
    wait = WebDriverWait(driver, 20)
    '''
    scrapped = []
    check_overlay(driver)

    for i in range(page_depth):
        print("Scrapping page: ", i + 1)

        # wait for class to appear.
        wait.until(lambda driver: driver.find_elements(By.CLASS_NAME, "MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12"))

        # projection boxes containing individual informations
        individual_infos = driver.find_elements(By.CLASS_NAME, "MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12")
        for individual_info in individual_infos:
            # loop through projection boxes
            try:
                # Extract date time
                date_time = individual_info.find_element(By.CLASS_NAME, "MuiGrid-root.datetime.MuiGrid-item.MuiGrid-grid-xs-9").text
                # Extract League name
                league = individual_info.find_element(By.CLASS_NAME, "MuiChip-label.MuiChip-labelSmall").text
                # Extract player name
                name = individual_info.find_element(By.CLASS_NAME, "team1").text
                # Extract opponent
                opponent = individual_info.find_element(By.CLASS_NAME, "team2").text
                # Extract stat
                stat = individual_info.find_element(By.CLASS_NAME, "MuiTypography-root.name.MuiTypography-body1.MuiTypography-gutterBottom").text
                
                # Extract best bet informations
                best_bet_sport_books = individual_info.find_element(By.CLASS_NAME, "sportsbook").find_element(By.TAG_NAME, "h6").text
                best_bets = individual_info.find_element(By.CLASS_NAME, "bestodds")
                best_bet = best_bets.find_element(By.TAG_NAME, "p").text
                best_bet_odds = best_bets.find_element(By.TAG_NAME, "h6").text

                # Bottom row of projection boxes
                strengths = individual_info.find_elements(By.CLASS_NAME, "MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-3")
                projection = ""
                ROI = ""
                win = ""
                hold = ""
                for strength in strengths:
                    tags = strength.find_elements(By.TAG_NAME, "p")
                    
                    for i in range(len(tags)):

                        # Extract projection
                        if "Proj." in tags[i].text.split(" "):
                            projection = tags[i+1].text
                        
                        # Extract ROI
                        if tags[i].text == "xROI":
                            ROI = tags[i+1].text
                    
                        # Extract Wins
                        if tags[i].text == "xWIN":
                            win = tags[i+1].text
                    
                        # Extract holds
                        if tags[i].text == "HOLD":
                            hold = tags[i+1].text
 
                
                # make a list of dictionaries.
                scrapped.append({"Date": date_time.split("@")[0], "Time": date_time.split("@")[1],  "League": league, "Name": name, "Opponent": opponent, "Stat": stat, "Projection": projection, "Line": best_bet.split(" ")[1], "ROI": ROI, "Win": win, "Hold": hold, "Best Bet": best_bet, "Best Bet Sportsbook": best_bet_sport_books, "Best Bet Odds": best_bet_odds})
            
                
            except Exception as e:
                # Ignore if it does not have necessary information
                pass
        
        # Find next page button
        next_page = driver.find_element(By.CSS_SELECTOR, "[aria-label='Go to next page']")

        
        if next_page.get_attribute("disabled"):
            print("No further next page")
            # break from the loop if next page does not exist
            break

        # go to next page
        next_page.click()

        # wait for next page button to appear
        wait.until(lambda driver: driver.find_elements(By.CSS_SELECTOR, "[aria-label='Go to next page']"))

    df = pd.DataFrame.from_dict(scrapped)
    
    # drop in case duplicate is present or same information scrapped twice
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # save to particular csv file
    df.to_csv(save_to)
    return df

    '''

if __name__ == "__main__":
    page_depth = 30
    search_url = "www.facebook.com"
    save_to = "nba_player.csv"

    df = scrapper(page_depth = page_depth, search_url= search_url, save_to=save_to)
