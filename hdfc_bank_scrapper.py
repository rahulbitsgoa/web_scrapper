from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import time
import pdfkit
import requests
from urllib.parse import urljoin
import re

BASE_URL = "https://www.hdfcfund.com"
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

# Sanitize folder names
def sanitize(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

# Extract all scheme links by clicking "Load More" using Playwright
def get_scheme_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.hdfcfund.com/product-solutions")

        # Keep clicking "Load More" as long as it's available
        while True:
            try:
                load_more = page.query_selector("text=Load More")
                if load_more:
                    load_more.click()
                    time.sleep(2)
                else:
                    break
            except:
                break

        soup = BeautifulSoup(page.content(), "html.parser")
        browser.close()

        links = set()
        for a in soup.find_all("a", href=True):
            href = a['href']
            if "/product-solutions/overview/" in href and href.endswith("/direct"):
                links.add(urljoin(BASE_URL, href))
        return list(links)

# Process each scheme page
def process_scheme_pages(urls):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in urls:
            print(f"\n\U0001F50D Processing: {url}")
            page.goto(url)
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            html = page.content()

            soup = BeautifulSoup(html, "html.parser")

            # Folder name
            scheme_name = sanitize(url.split("/overview/")[1].split("/direct")[0])
            os.makedirs(scheme_name, exist_ok=True)

            # Extract portfolio table
            table = soup.select_one("table.Portfolio")
            if table:
                table_html = f"""
                <html><head><meta charset=\"utf-8\">
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    th {{ background-color: #f2f2f2; }}
                </style></head><body>{str(table)}</body></html>
                """
                pdfkit.from_string(table_html, f"{scheme_name}/portfolio_table.pdf", configuration=PDFKIT_CONFIG)
                print(f"\U0001F4C4 Saved portfolio_table.pdf under {scheme_name}/")
            else:
                print("\u26A0\uFE0F Portfolio table not found")

            # Download all PDF links
            pdf_links = [urljoin(url, a['href']) for a in soup.find_all("a", href=True) if a['href'].lower().endswith('.pdf')]
            for i, link in enumerate(pdf_links, start=1):
                try:
                    response = requests.get(link)
                    response.raise_for_status()
                    filename = f"{scheme_name}/scheme_document_{i}.pdf"
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"\u2705 Downloaded: {filename}")
                except Exception as e:
                    print(f"\u274C Failed to download {link}: {e}")
        
        browser.close()

if __name__ == "__main__":
    print("\U0001F504 Fetching fund scheme links...")
    schemes = get_scheme_links()
    print(f"\U0001F517 {len(schemes)} schemes found.")
    process_scheme_pages(schemes)
    # for scheme_url in schemes:
    #     process_scheme_page(scheme_url)
