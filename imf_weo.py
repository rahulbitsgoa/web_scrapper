import os
import re
import time

import requests
from playwright.sync_api import sync_playwright
import mimetypes
def sanitize_filename(name, max_length=100):
    # Replace invalid Windows filename characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]


def download_as_pdf(pdf_url: str, download_dir: str):
    os.makedirs(sanitize_filename(download_dir), exist_ok=True)
    filename = sanitize_filename(os.path.basename(pdf_url.split("?")[0]))
    save_path = os.path.join(download_dir, filename)
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def imf_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://www.imf.org/en/Publications/SPROLLs/world-economic-outlook-databases#sort=%40imfdate%20descending')
        page.wait_for_load_state('domcontentloaded')
        db_link = page.locator('a.CoveoResultLink').first.get_attribute('href') + "/download-entire-database"
        page.goto(db_link)
        page.wait_for_load_state('domcontentloaded')
        time.sleep(1)
        a_loc = page.locator("div.full-width.text-center.padded-vertical-40.bg-lightest-grey a")
        print(a_loc.count())
        os.makedirs('IMF WEO Database', exist_ok=True)
        for i in range(0, a_loc.count(), 3):
            # Base URL of the site
            base_url = "https://www.imf.org"

            # Relative path from the <a href> tag
            relative_url = a_loc.nth(i).get_attribute('href')

            # Combine to get the full URL
            full_url = base_url + relative_url
            print(full_url)

            # Optional: headers to simulate a browser (in case the server blocks bots)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }

            # Send request
            response = requests.get(full_url, headers=headers)

            # Save the file if the request succeeded
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "").lower()
                print(f"Content-Type: {content_type}")

                # Determine file extension based on MIME type
                extension = ""
                # Some fixes for missing MIME types
                if "spreadsheetml" in content_type:
                    extension = ".xlsx"
                elif "application/zip" in content_type or 'application/x-zip-compressed' in content_type:
                    extension = ".zip"
                else:
                    extension = mimetypes.guess_extension(content_type.split(";")[0]) or ".bin"
                fname = os.path.join("IMF WEO Database", f"DB {i}")
                # Save with detected extension
                filename = f"{fname}{extension}"
                with open(filename, "wb") as f:
                    f.write(response.content)

                print(f"Downloaded and saved as: {filename}")
            else:
                print(f"Failed to download. Status code: {response.status_code}")


imf_scraper()
