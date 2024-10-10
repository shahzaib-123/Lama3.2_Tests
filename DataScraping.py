import sys
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append('/usr/lib/chromium-browser/chromedriver')

# Function to sanitize file names (removing invalid characters)
def sanitize_filename(filename):
    # Replace invalid characters like slashes, backslashes, or colons with underscores or another safe character
    return filename.replace("/", "_").replace("\\", "_").replace(":", "_").strip()

# Function to fetch document links
def fetch_documents(driver):
    time.sleep(7)  # Wait for the page to load
    documents = []

    # Locate document links
    document_elements = driver.find_elements(By.XPATH, "//a[@ng-href]")

    for element in document_elements:
        document_name = element.get_attribute("ng-href").split("/")[-1]  # Extract the document name
        document_path = element.get_attribute("ng-href")  # Full path
        
        # Skip non-English documents
        if any(subj in document_name.lower() for subj in ['urdu', "islamiyat",'islamic','islam','arab','french','spanish','sindh','sindhi','jpg','jpeg','png']):
            print(f"**Skipping non-English document: {document_name}**")
            continue

        documents.append((document_name, document_path))
    return documents

# Function to click next page
def click_next_page(driver):
    try:
        # Find the next page button
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@ng-class='DisableNextPage()']//a[@ng-click='nextPage()']"))
        )

        # Scroll the element into view to avoid obstruction issues
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)

        # Use JavaScript click to ensure it bypasses any visual obstructions
        driver.execute_script("arguments[0].click();", next_button)

        time.sleep(3)  # Wait for the next page to load
        return True
    except (NoSuchElementException, ElementClickInterceptedException, Exception) as e:
        print(f"Error navigating to the next page: {e}")
        return False

# Function to download documents
def download_documents(documents, download_dir):
    os.makedirs(download_dir, exist_ok=True)

    for document_name, url in documents:
        # Sanitize the document name
        document_name = sanitize_filename(document_name)
        
        # Ensure the document name is not empty
        if not document_name:
            print("Skipping invalid document with empty name.")
            continue

        file_path = os.path.join(download_dir, document_name)

        try:
            full_url = "https://examinationboard.aku.edu/" + url
            response = requests.get(full_url, stream=True)
            response.raise_for_status()

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Downloaded: {document_name}")
        except Exception as e:
            print(f"Failed to download {document_name}. Reason: {e}")

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    url = "https://examinationboard.aku.edu/learning-materials/Pages/learning-resources-for-SSC-and-HSSC.aspx"
    driver.get(url)

    download_directory = "/workspaces/Lama3.2_Tests/Documents"
    docs = []
    page_num = 1

    while True:
        print(f"Scraping page {page_num}...")
        documents = fetch_documents(driver)
        docs.extend(documents)
        download_documents(documents, download_directory)
        print(f"Page {page_num} Scraped | Total Docs: {len(docs)}")
        
        # Try to navigate to the next page, stop if there are no more pages
        if not click_next_page(driver):
            print("No more pages to scrape.")
            break

        page_num += 1

    driver.quit()

    # Save the results to a CSV
    df = pd.DataFrame(docs, columns=['Document Name', 'URL'])
    df.to_csv('scraped_documents.csv', index=False, encoding='utf-8')
    print(f"Scraped {len(docs)} documents. Details saved to scraped_documents.csv.")
