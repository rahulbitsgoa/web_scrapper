import os
import time
from playwright.sync_api import sync_playwright

def run():
    # Ensure downloads folder exists
    os.makedirs("downloads", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Step 1: Go to CPI homepage
        page.goto("https://cpi.mospi.gov.in")
        time.sleep(5)

        # Step 2: Hover over "All India Item Index"
        page.hover("text=All India Item Index")
        time.sleep(1)

        # Step 3: Click on "Base:2012"
        page.click("a[href*='AllIndia_Item_CombinedIndex_2012.aspx']")
        time.sleep(10)  # Let it fully load

        # Step 4: Click "Check All"
        page.click("#Content1_lbAll")
        time.sleep(1)

        # Step 5: Select latest year in "To" section
        year_select = page.locator("#Content1_DropDownList2")
        last_year = year_select.locator("option").last
        year_value = last_year.get_attribute("value")
        page.select_option("#Content1_DropDownList2", value=year_value)
        time.sleep(1)

        # Step 6: Select latest month in "To" section
        month_select = page.locator("#Content1_DropDownList4")
        last_month = month_select.locator("option").last
        month_value = last_month.get_attribute("value")
        page.select_option("#Content1_DropDownList4", value=month_value)
        time.sleep(1)

        # Step 7: Click "View Indices"
        page.click("#Content1_Button2")
        time.sleep(10)

        # Step 8: Select ".xls" format
        page.select_option("#Content1_DropDownList7", label="Excel 97-2003 Workbook(*.xls)")
        time.sleep(1)

        # Step 9: Click "Download"
        with page.expect_download() as download_info:
            page.click("#Content1_Button3")
        download = download_info.value

        # Save download to `downloads/`
        download_path = os.path.join("downloads", download.suggested_filename)
        download.save_as(download_path)

        print(f"✅ Downloaded: {download_path}")
        # input("Press Enter to close...")
        browser.close()

if __name__ == "__main__":
    run()
