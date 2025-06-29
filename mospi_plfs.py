import os
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

os.makedirs('mospi_downloads', exist_ok=True)

def scrape_mospi_table_pdfs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use headless=True for speed!
        page = browser.new_page()
        url = "https://www.mospi.gov.in/download-reports?main_cat=ODU5&cat=All&sub_category=All"
        page.goto(url, wait_until='networkidle', timeout=60000)
        print("Page loaded, finding table PDFs...")

        # Target only the main table
        table = page.locator("table.views-table.tableData").first
        if not table.is_visible():
            print("Table not found!")
            browser.close()
            return

        # Collect PDF links from table rows only
        pdf_links = []
        rows = table.locator("tbody tr").all()
        for i, row in enumerate(rows):
            try:
                pdf_link = row.locator("a[href*='.pdf']").first
                if pdf_link.is_visible():
                    href = pdf_link.get_attribute("href")
                    if href:
                        if not href.startswith("http"):
                            href = urljoin("https://www.mospi.gov.in", href)
                        pdf_links.append(href)
                        print(f"Row {i+1}: {href}")
            except Exception:
                continue

        print(f"\nFound {len(pdf_links)} PDF links in table")

        # Download each PDF, keeping original filename
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.mospi.gov.in/"}
        for url in pdf_links:
            try:
                filename = os.path.basename(url)
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    with open(f"mospi_downloads/{filename}", "wb") as f:
                        f.write(response.content)
                    print(f"✅ Saved: {filename}")
                else:
                    print(f"❌ Failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")

        browser.close()

if __name__ == "__main__":
    scrape_mospi_table_pdfs()
