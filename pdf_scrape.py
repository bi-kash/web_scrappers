from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import re
import os
import requests
import spacy
import pdfplumber
import zipfile
import pandas as pd
import traceback

# Load spaCy model
nlp = spacy.load("en_core_web_sm")


# Need these: shop_name,language,year,brand,modell,condition,category_shop,stock_status,stock_text,stock_sizes,url-detail,price,rrp
def get_driver():
    chromeOptions = webdriver.ChromeOptions()

    # Headless is faster. If headless is False then it opens a browser and you can see action of web driver. You can try making it False
    chromeOptions.headless = False
    chromeOptions.add_argument("--log-level=3")

    # installs chrome driver automatically if not present
    s = Service(ChromeDriverManager().install())
    # chromeOptions.add_argument("user-data-dir=/home/bikash/.config/google-chrome/Profile 1")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chromeOptions
    )
    return driver


files_already_downloaded = True
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("pdfs"):
    os.makedirs("pdfs")


def get_pdf(pdf, path):
    response = requests.get(pdf)
    # Save the PDF to a file
    with open(path, "wb") as file:
        file.write(response.content)


def download_files():

    base_url = "https://dl.ncsbe.gov/?prefix=data/SampleBallots/"
    driver = get_driver()

    driver.get(base_url)

    # wait for a tag to load
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "a")))

    date_links = {}
    # get all a tags
    for a_tag in driver.find_elements(By.TAG_NAME, "a")[1:-1]:
        href = a_tag.get_attribute("href")
        date = re.search(r"\d{4}-\d{2}-\d{2}", href).group()
        month = date.split("-")[1]
        if month == "11":
            # create dir if it doesnot exist within dir pdfs
            path = f"pdfs/{date}"
            if not os.path.exists(path) and not ".zip" in href:
                os.mkdir(path)

            date_links[path] = href

    file_urls = []
    for pdf_path, url in date_links.items():
        data = {}
        if ".zip" in url:
            zip_path = pdf_path + ".zip"
            data["file_name"] = zip_path.split("/")[-1]
            data["url"] = url

            file_urls.append(data)

            if os.path.exists(zip_path):
                continue
            response = requests.get(url)
            with open(zip_path, "wb") as file:
                file.write(response.content)

            continue

        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )

        pdfs = [
            element.get_attribute("href")
            for element in driver.find_element(By.TAG_NAME, "pre").find_elements(
                By.XPATH, "//a[contains(text(), '.pdf')]"
            )
        ]
        pdf_paths = []
        for pdf in pdfs:
            data = {}
            file_name = pdf.split("/")[-1]
            data["file_name"] = file_name
            data["url"] = pdf
            file_urls.append(data)
            path = pdf_path + "/" + file_name
            if os.path.exists(path):
                continue
            pdf_paths.append((pdf, path))

        with ThreadPoolExecutor() as executor:
            executor.map(lambda args: get_pdf(*args), pdf_paths)

    pd.DataFrame(file_urls).to_csv("pdfs/file_urls.csv", index=False)
    driver.quit()


def sort_columns(df):
    # Assuming df is your DataFrame
    columns = df.columns

    # Extract office and candidate columns
    office_columns = [col for col in columns if col.startswith("office")]
    candidate_columns = [col for col in columns if col.startswith("candidate")]

    # Sort office columns by the number
    office_columns_sorted = sorted(
        office_columns, key=lambda x: int(x.replace("office", ""))
    )
    candidate_columns_sorted = sorted(
        candidate_columns,
        key=lambda x: int(x.replace("candidate", "").replace(" ", "")),
    )

    # Create a new list for the sorted columns
    sorted_columns = []

    # keep other columns at the beginning
    sorted_columns.extend(
        [col for col in columns if col not in office_columns + candidate_columns]
    )

    # Reorder the columns to match the desired pattern
    for office in office_columns_sorted:
        office_number = office.replace("office", "")
        sorted_columns.append(office)
        sorted_columns.extend(
            [
                col
                for col in candidate_columns_sorted
                if col.startswith(f"candidate{office_number}_")
            ]
        )

    # Reorder the DataFrame columns
    df = df[sorted_columns]

    return df


def is_name(text):
    """
    Check if the given text is recognized as a name by spaCy.

    Args:
    text (str): The text to check.

    Returns:
    bool: True if the text is recognized as a name, False otherwise.
    """
    # Process the text with spaCy
    doc = nlp(text)

    # Check if any entity in the text is labeled as "PERSON"
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return True
    return False


def extract_starting_points(pdf):
    margin = 26
    starting_points = []
    search_results = []
    expressions = [
        r"\b(?:NC\s+)?Superior\s+Court\s+Judge\b",
        r"\b(?:NC\s+)?District\s+Court\s+Judge\b",
    ]
    for i, page in enumerate(pdf.pages):
        if i > 1:
            break

        for expression in expressions:
            pattern = re.compile(expression, re.IGNORECASE)
            search_results.extend(page.search(pattern=pattern))
        if search_results:
            for j in range(len(search_results)):
                result = search_results[j]
                k = 1
                while True:
                    if j + k < len(search_results):
                        next_search_result = search_results[j + k]
                        if abs(next_search_result["x0"] - result["x0"]) > margin:
                            k += 1
                            continue
                        else:
                            top = next_search_result["top"]
                            break

                    else:
                        top = page.height - 48
                        break

                starting_points.append(
                    {
                        "page": i,
                        "x0": result["x0"] - margin,
                        "y0": result["top"],
                        "x1": result["x1"] + margin,
                        "y1": top,
                    }
                )
    return starting_points


def get_boxes(pdf, starting_point):
    page = pdf.pages[starting_point["page"]]
    x0 = starting_point["x0"]
    y0 = starting_point["y0"]
    x1 = starting_point["x1"]
    y1 = starting_point["y1"]
    box = (x0, y0, x1, y1)
    boxes = page.within_bbox(box)
    boxes = boxes.extract_text_lines()
    return boxes


def get_office_name(boxes):
    office = ""
    a = 0
    for i in range(len(boxes)):
        box = boxes[i]
        a = i
        if "continue" in box["text"].lower() or "next" in box["text"].lower():
            break
        if "vote" not in box["text"].lower():
            office = office + " " + box["text"]
        else:
            break

    return office.strip(), a


def get_candidates(boxes, is_last_element):
    candidates = []
    vote_found = False
    skip = False
    for i in range(len(boxes)):
        if skip:
            skip = False
            continue
        box = boxes[i]
        if any(keyword in box["text"].lower() for keyword in ("continue", "next")):
            break
        next_box = boxes[i + 1] if i + 1 < len(boxes) else None

        if next_box:
            if "vote" in next_box["text"].lower() or "vote" in box["text"].lower():
                vote_found = True
                break

            elif abs(next_box["top"] - box["bottom"]) < 2.5:
                skip = True
                if next_box["chars"][0]["height"] < box["chars"][0]["height"]:
                    candidate_name = box["text"]
                    candidates.append(candidate_name)
                    continue

                candidate_name = box["text"] + " " + next_box["text"]
                candidates.append(candidate_name)

            else:
                candidate_name = box["text"]
                candidates.append(candidate_name)
        else:
            candidate_name = box["text"]
            candidates.append(candidate_name)

    if is_last_element or vote_found:
        for candidate in candidates[1:]:
            if not is_name(candidate):
                index = candidates.index(candidate)
                return candidates[:index]

    for candidate in candidates:
        if len(candidate.split(" ")) == 1:
            candidates.remove(candidate)

    return candidates


def process_pdf(pdf_path, pdf_file=None, pdf_url=None):
    try:
        pdf = pdfplumber.open(pdf_path)
        starting_points = extract_starting_points(pdf)
        data = {"pdf_file": pdf_file, "pdf_url": pdf_url}
        count = 0

        for starting_point in starting_points:

            boxes = get_boxes(pdf, starting_point)

            office, i = get_office_name(boxes)

            if "court" not in office.lower():
                continue

            count += 1

            data[f"office{count}"] = office
            boxes = boxes[i + 1 :]
            if count == len(starting_points):
                candidates = get_candidates(boxes, True)
            else:
                candidates = get_candidates(boxes, False)

            for i in range(len(candidates)):
                data[f"candidate{count}_{i+1}"] = candidates[i]

        return data
    except Exception:
        print(pdf_file, pdf_url)
        print(traceback.format_exc())


def check_if_csv_already_exists_for_date(date):
    # find all csvs inside data data directory
    csvs = [f for f in os.listdir("data") if f.endswith(".csv")]

    for csv in csvs:
        if date in csv:
            return True

    return False


if __name__ == "__main__":
    files_already_downloaded = True
    if not files_already_downloaded:
        download_files()
    file_to_process = {}
    df = pd.read_csv("pdfs/file_urls.csv")
    # Traverse the directory tree
    dates = []
    count = 0

    for root, dirs, files in os.walk("pdfs"):
        if not root == "pdfs":
            date = root.split("/")[-1]
            if date in dates:
                continue

            dates.append(date)
            if check_if_csv_already_exists_for_date(date):
                continue
            file_to_process[date] = []
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.endswith(".pdf"):

                url = df[df["file_name"] == file_name]["url"].values[0]
                file_to_process[date].append((file_path, file_name, url))
                """
                if len(file_to_process[date]) == 10:
                    break
                """
            elif file_name.endswith(".zip"):
                date = file_name.replace(".zip", "")
                if date in dates:
                    continue
                dates.append(date)

                if check_if_csv_already_exists_for_date(date):
                    continue

                file_to_process[date] = []
                print(f"Processing ZIP file: {file_path}")
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    for zip_file_name in zip_ref.namelist():
                        if zip_file_name.endswith(".pdf"):
                            pdf_file = zip_ref.open(zip_file_name)
                            url = df[df["file_name"] == file_name]["url"].values[0]
                            file_to_process[date].append(
                                (pdf_file, zip_file_name.split("/")[-1], url)
                            )
                            """
                            if len(file_to_process[date]) == 10:
                                break
                            """

    for date, files in file_to_process.items():
        csv_file_name = "data/" + date + "_sample_ballots.csv"
        if os.path.exists(csv_file_name):
            continue
        print("Extracting for: ", csv_file_name)
        with ThreadPoolExecutor() as executor:
            all_data = list(executor.map(lambda args: process_pdf(*args), files))
            df = pd.DataFrame(all_data)
            df = sort_columns(df)
            df.to_csv(csv_file_name, index=False)
            all_data = []
