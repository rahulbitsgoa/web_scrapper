import os
import shutil
import time

from playwright.sync_api import sync_playwright
from datetime import date, timedelta


def on_popup(new_page):
    folder_name = f"DCA_Data"
    download_path = os.path.abspath(folder_name)
    os.makedirs(download_path, exist_ok=True)

    print("New tab detected:", new_page.url)
    new_page.wait_for_load_state('domcontentloaded')
    if 'The specified URL is inaccessible at this time. Please try after some time' in new_page.content():
        print('Inaccessible')
        return
    else:
        # Save the data
        with new_page.expect_download() as download_info:
            new_page.click('input#btnsave')
        download = download_info.value
        temp_file_path = download.path()
        new_filename = f"Report_"
        table = new_page.locator("table")  # or a more specific selector, e.g. table#myTable
        # Then find text inside that table:
        if table.locator(":text('Wholesale')").count() > 0:
            new_filename += "Wholesale"
        if table.locator(":text('Retail')").count() > 0:
            new_filename += "Retail"
        new_filename += ".xls"
        final_file_path = os.path.join(download_path, new_filename)
        shutil.move(temp_file_path, final_file_path)

        print(f"✅ File downloaded and saved as: {final_file_path}")

        time.sleep(2)
        new_page.close()
        return


def dca_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://fcainfoweb.nic.in/reports/Report_Menu_Web.aspx')
        page.wait_for_load_state('domcontentloaded')
        # Select dropdowns for retail reports
        retail_dropdown = page.locator("select#ctl00_MainContent_Ddl_Rpt_type").first
        retail_dropdown.click()
        retail_dropdown.wait_for(state="visible")
        # Select retail
        retail_dropdown.select_option("Retail")
        print('Successfully selected Retail')
        # Select Price report
        page.get_by_label("Price report").click()
        page.wait_for_load_state('domcontentloaded')
        time.sleep(2)
        # Select daily prices
        # Select dropdowns for retail reports
        price_dropdown = page.locator("select#ctl00_MainContent_Ddl_Rpt_Option0").first
        price_dropdown.click()
        price_dropdown.wait_for(state="visible")
        # Select retail
        options = price_dropdown.locator("option").all_inner_texts()
        page.evaluate("""
          ([selId, value]) => {
            const sel = document.getElementById(selId);
            if (!sel) throw new Error("Dropdown element not found: " + selId);
            sel.value = value;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
          }
        """, ["ctl00_MainContent_Ddl_Rpt_Option0", "Daily Prices"])

        print('Successfully selected Daily Prices')

        # Fill the date
        current_date = date.today() - timedelta(days=1)
        date_loc = page.locator('input#ctl00_MainContent_Txt_FrmDate')
        date_loc.click()  # to move focus to it
        # while True:
        if current_date.month in (10, 11, 12):
            page.keyboard.type(str(current_date.day) + '/' + str(current_date.month) + '/' + str(current_date.year),
                               delay=300)
        else:
            page.keyboard.type(str(current_date.day) + '/0' + str(current_date.month) + '/' + str(current_date.year),
                               delay=300)
        current_date -= timedelta(days=1)  # Go back one day each time
        input('Solve CAPTCHA...')
        print('Opening page...')
        context.on("page", on_popup)
        page.click("#ctl00_MainContent_btn_getdata1", modifiers=["Control"])
        page.wait_for_timeout(5000)  # adjust as needed

        # Select dropdowns for wholesale reports
        wholesale_dropdown = page.locator("select#ctl00_MainContent_Ddl_Rpt_type").first
        wholesale_dropdown.click()
        wholesale_dropdown.wait_for(state="visible")
        # Select retail
        wholesale_dropdown.select_option("Wholesale")
        print('Successfully selected Wholesale')

        # Fill the date
        page.click("#ctl00_MainContent_btn_getdata1", modifiers=["Control"])
        page.wait_for_timeout(5000)  # adjust as needed

        page.close()
        context.close()
        browser.close()


dca_scraper()





