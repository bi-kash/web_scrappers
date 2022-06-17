from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
from datetime import datetime
# import chromedriver_binary
PATH = "/usr/local/bin/chromedriver"


chrome_options = Options()
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-site-isolation-trials")
    #PROXY="54.39.102.233:3128"

    #chrome_options.add_argument('--proxy-server=%s' % PROXY)

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
chrome_options.headless = False

    # installs chrome driver automatically if not present
s = Service(ChromeDriverManager().install())
    #chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    #driver = Chrome(PATH)

    # account =  'https://www.tiktok.com/@thistrippyhippie' #'https://www.tiktok.com/@.nehabear'

last_date = datetime(2022, 5, 30)

def find_total(driver: Chrome, username: str) -> int:
    '''Find user video count'''

    username = username.strip("@")
    page = driver.find_element(By.CSS_SELECTOR,"#SIGI_STATE")
    metadata = json.loads(page.get_attribute("innerHTML"))
    return metadata ['UserModule']['stats'][username]['videoCount']

def collect_cards(driver: Chrome) -> list:
    '''Collect video posts'''
    #wait = WebDriverWait(driver, 20)
    #wait.until(lambda driver: driver.find_elements(By.CLASS_NAME, "tiktok-yvmafn-DivVideoFeedV2.e5w7ny40"))

    container = driver.find_element(By.CLASS_NAME,"tiktok-yvmafn-DivVideoFeedV2")
    cards = container.find_elements(By.CSS_SELECTOR,"div[data-e2e='user-post-item']")
    cards = [card.find_element(By.TAG_NAME,"a").get_attribute("href") for card in cards]
    print(cards)
    return cards

def find_entry(driver: Chrome, vid_url):
    '''Find post information'''
    
    # collect the data from html
    page = driver.find_element(By.CSS_SELECTOR,"#SIGI_STATE")
    content = json.loads(page.get_attribute("innerHTML"))
    metadata = content['ItemModule'] 

    # find post id
    vid_id = vid_url.split("/")[-1]

    # find post datetime
    item = metadata[vid_id]
    create_time = int(item['createTime'])
    post_date = datetime.fromtimestamp(create_time)

    # find sound name and link
    sound_name = item['music']['title'] + " by " + item['music']['authorName']
    sound_link = item['music']['playUrl']
    sound_tag = driver.find_element(By.CLASS_NAME,"tiktok-zo4ukd-H4Link")
    sound_url = sound_tag.find_element(By.TAG_NAME,"a").get_attribute("href")
    

    # find return post link
    direct_url = item['video']['playAddr']

    # assign collected data as an entry
    entry = dict(
        id_=vid_id,
        url=vid_url,
        direct_url=direct_url, # you can download the video directly from this link
        music=sound_name,
        music_direct_url=sound_link,
        music_url=sound_url,
        post_date=post_date
    )

    return entry

def waiting(t: int, units: str) -> int:
    if units == "seconds":
        return t
    elif units == "minutes":
        return t * 60
    elif units == "hour":
        return t * 3600


def scrape_videos(username):

    running = True
    scroll = False
    prev_len = 0
    all_cards = []
    video_limit = 10

    entries = []
    driver.get('https://www.tiktok.com/'+username)
    print(driver.title)

    st = time.time()
    mt = waiting(5,"minutes")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        all_cards.extend(collect_cards(driver))
        
        if len(all_cards)>video_limit:
            break
        wt = time.time() - st
        if wt > mt:
            running = False
            break
            
    cards = all_cards
    num_videos = find_total(driver,username)

    # filter cards based on entries
    collected = [a['url'] for a in entries]
    cards = [c for c in cards if c not in collected]
    print(cards)
    
    for vid_url in cards: #profile page

        # requests get to video url
        driver.get(vid_url)

        # get video information
        entry = find_entry(driver, vid_url)
        entries.append(entry)
        print(entry)

        if entry['post_date'] < last_date:
            running = False
            break
        


    # reformat the post date value
    for i in range(len(entries)):
        post_date = entries[i]['post_date']
        entries[i]['post_date'] = post_date.strftime("%H:%M:%S %d/%m/%Y")

    
    return entries
    
scrape_videos('@woahhhhfam')