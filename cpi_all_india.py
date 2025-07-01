import os
import shutil
import time
from playwright.sync_api import sync_playwright

# --- Step 1: Get User Input ---
month = input("Enter month (e.g., May): ")
year = input("Enter year (e.g., 2025): ")

# --- Step 2: Create Download Directory ---
folder_name = f"downloads_{year}_{month}"
download_path = os.path.abspath(folder_name)
os.makedirs(download_path, exist_ok=True)

# --- Step 3: Map Month Name to Numeric Value ---
month_map = {
    "January": "01", "February": "02", "March": "03", "April": "04", "May": "05",
    "June": "06", "July": "07", "August": "08", "September": "09",
    "October": "10", "November": "11", "December": "12"
}
month_val = month_map[month]

# --- Step 4: Automate with Playwright ---
with sync_playwright() as p:
    # Launch browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()

    # --- Step 5: Go to CPI MOSPI Website ---
    page.goto("https://cpi.mospi.gov.in", timeout=60000)
    page.wait_for_timeout(3000)

    # --- Step 6: Navigate Hover Menus ---
    page.hover("text=Time Series")
    page.wait_for_timeout(1000)
    page.hover("text=Base:2012")
    page.wait_for_timeout(1000)
    page.click("a[href*='TimeSeries_2012.aspx']")
    page.wait_for_timeout(5000)

    # --- Step 7: Select Checkboxes and Dropdowns ---
    page.click("#Content1_CheckBoxList1_0")  # Select CPI combined
    time.sleep(2)

    # Set Year and Month for From-Date
    page.select_option("#Content1_DropDownList1", label=year)
    page.wait_for_selector("#Content1_DropDownList3:enabled")
    page.select_option("#Content1_DropDownList3", value=month_val)

    # Set Year and Month for To-Date
    page.select_option("#Content1_DropDownList2", label=year)
    page.wait_for_selector("#Content1_DropDownList4:enabled")
    page.select_option("#Content1_DropDownList4", value=month_val)

    # Select State/District/Zone: "ALL India (27b)"
    page.select_option("#Content1_DropDownList5", value="27b")
    time.sleep(1)

    # --- Step 8: Click "View Indices" ---
    page.click("#Content1_Button2")
    time.sleep(2)

    # --- Step 9: Select Index (4 = All India General) ---
    page.select_option("#Content1_DropDownList7", value="4")
    time.sleep(1)

    # --- Step 10: Download the PDF ---
    with page.expect_download() as download_info:
        page.click("#Content1_Button3")
    download = download_info.value

    # --- Step 11: Move and Rename the Downloaded File ---
    temp_file_path = download.path()
    new_filename = f"ALL_India_CPI_{year}_{month}.pdf"
    final_file_path = os.path.join(download_path, new_filename)
    shutil.move(temp_file_path, final_file_path)

    print(f"✅ File downloaded and saved as: {final_file_path}")

    browser.close()

