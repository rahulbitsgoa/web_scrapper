import os
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
import glob
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException

# ---------- CONFIG ----------
SITE_NAME = "commerce.gov.in"
BASE_URL = f"https://{SITE_NAME}"
TARGET_URL = f"{BASE_URL}/trade-statistics/latest-trade-figures/"
DOWNLOAD_DIR = SITE_NAME
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- SETUP VISIBLE CHROME ----------
chrome_options = Options()
# comment out headless to see what's happening
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)
driver.get(TARGET_URL)

# ---------- WAIT FOR FULL RENDER ----------
print("⏳ Waiting for page to load...")
time.sleep(10)  # wait longer for JS to inject PDFs

# ---------- GET AND SAVE PAGE SOURCE ----------
html = driver.page_source
with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ HTML written to debug_page.html")

# ---------- PARSE WITH BEAUTIFULSOUP ----------
soup = BeautifulSoup(html, "html.parser")

pdf_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if ".pdf" in href.lower():
        full_url = urllib.parse.urljoin(BASE_URL, href)
        pdf_links.append(full_url)

# ---------- DOWNLOAD FIRST 2 PDFs ----------
if not pdf_links:
    print("❌ No PDF links found. Check debug_page.html to verify content.")
else:
    print(f"✅ Found {len(pdf_links)} PDF(s). Downloading first 2...")
    for i, link in enumerate(pdf_links[:2]):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                filename = os.path.join(DOWNLOAD_DIR, f"document_{i+1}.pdf")
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ Saved: {filename}")
            else:
                print(f"❌ Failed to download {link} (status {response.status_code})")
        except Exception as e:
            print(f"❌ Error downloading {link}: {e}")

driver.quit()




# --- Get user input ---
month = input("Enter month (e.g., May): ")
year = input("Enter year (e.g., 2025): ")
folder_name = f"{month}_{year}"
os.makedirs(folder_name, exist_ok=True)

month_map = {
    "January": "1", "February": "2", "March": "3", "April": "4", "May": "5",
    "June": "6", "July": "7", "August": "8", "September": "9",
    "October": "10", "November": "11", "December": "12"
}
month_val = month_map[month]

# --- Absolute download folder ---
download_path = os.path.abspath(folder_name)

# --- Browser Setup ---
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
})
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

url = "https://tradestat.commerce.gov.in/meidb/principal_commodity_wise_all_HSCode_export"
driver.get(url)

# --- Set filters ---
wait.until(EC.presence_of_element_located((By.ID, "pddMonth")))
Select(driver.find_element(By.ID, "pddMonth"))\
.select_by_value(month_val)
Select(driver.find_element(By.ID, "pddYear")).select_by_visible_text(year)
Select(driver.find_element(By.ID, "pddReportVal")).select_by_value("1")
Select(driver.find_element(By.ID, "pddReportYear")).select_by_value("1")

# --- Get commodity list ---
commodity_select = Select(driver.find_element(By.ID, "pbrcitmdata"))
commodities = [(opt.get_attribute("value"), opt.text)
               for opt in commodity_select.options if opt.get_attribute("value") and opt.get_attribute("value") != "ZZ"]

def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)

for val, name in commodities:
    print(f"🔄 {name}")
    try:
        # Re-select all filters after reload
        Select(driver.find_element(By.ID, "pddMonth")).select_by_value(month_val)
        Select(driver.find_element(By.ID, "pddYear")).select_by_visible_text(year)
        Select(driver.find_element(By.ID, "pddReportVal")).select_by_value("1")
        Select(driver.find_element(By.ID, "pddReportYear")).select_by_value("1")
        Select(driver.find_element(By.ID, "pbrcitmdata")).select_by_value(val)

        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submit)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "buttons-pdf")))
        pdf_btn = driver.find_element(By.CLASS_NAME, "buttons-pdf")
        driver.execute_script("arguments[0].click();", pdf_btn)
        print(f"📥 Triggered PDF download for {name}. Waiting...")

        # Wait until the PDF finishes downloading
        downloaded = False
        timeout = 30  # seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            pdf_files = glob.glob(os.path.join(download_path, "*.pdf"))
            if pdf_files and not any(f.endswith(".crdownload") for f in pdf_files):
                downloaded = True
                break
            time.sleep(0.5)

        if downloaded:
            pdf_files = glob.glob(os.path.join(download_path, "*.pdf"))
            latest_file = max(pdf_files, key=os.path.getctime)
            new_filename = sanitize_filename(name.strip()) + ".pdf"
            new_path = os.path.join(download_path, new_filename)
            os.rename(latest_file, new_path)
            print(f"✅ Saved as {new_filename}")
        else:
            print(f"⚠️ Timed out waiting for download of {name}")

    except UnexpectedAlertPresentException:
        alert = driver.switch_to.alert
        print(f"❌ Failed: {name} — Alert Text: {alert.text}")
        alert.accept()
    except Exception as e:
        print(f"❌ Failed: {name} — {e}")

    driver.get(url)
    wait.until(EC.presence_of_element_located((By.ID, "pddMonth")))

print("✅ Download attempts complete.")
driver.quit()
