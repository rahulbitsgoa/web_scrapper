import os
import re
import string
import time

import requests
from playwright.sync_api import sync_playwright, Error, Page
from bs4 import BeautifulSoup, Tag

def find_div_by_header_text(soup, header_text):
    for row in soup.find_all("div", class_="row bg-theme-blue"):
        nested = row.find("div", class_="col-md-12")
        if nested and header_text.lower() in nested.get_text(strip=True).lower():
            return row
    return None





def sanitize_filename(name, max_length=100):
    # Replace invalid Windows filename characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]



def download_as_pdf(pdf_url: str, download_dir: str):
    os.makedirs(sanitize_filename(download_dir), exist_ok=True)
    if not pdf_url.startswith('http'):
        pdf_url = 'https://eaindustry.nic.in/'+pdf_url
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, sanitize_filename(filename))
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def ea_scraper(selector: string):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://eaindustry.nic.in/')
        page.wait_for_load_state('domcontentloaded')

        if selector.lower()=='wpi':
            links = page.locator("ul.dropdown-menu[aria-labelledby='dropdown2-1'] a").all()
            page.eval_on_selector("ul.dropdown-menu[aria-labelledby='dropdown2-1'] a", "el => el.setAttribute('target', '_blank')")

            excel_links = []

            # Iterate over them and extract href and text
            for l in links:
                # page.click("#dropdown2")
                # page.click("#dropdown2-1")
                link = 'https://eaindustry.nic.in/'+l.get_attribute('href')
                if link.find('indx') != -1:
                    download_as_pdf(link, 'WPI_Data')
                    continue

                # Expect a new page to open
                new_page = browser.new_page()
                new_page.goto(link)
                new_page.wait_for_load_state('domcontentloaded')
                # page.click("a[href='"+link.get_attribute('href')+"']", force=True)
                html = new_page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Find the divs marking the start and end
                monthly_div = find_div_by_header_text(soup, "Monthly Index Files")
                yearly_div = find_div_by_header_text(soup, "Yearly Index Files")

                if not monthly_div:
                    print(" 'Monthly Index Files' section not found.")
                else:
                    excel_links = []
                    node = monthly_div.find_next_sibling()

                    while node and node != yearly_div:
                        if isinstance(node, Tag):
                            excel_links.extend(node.find_all("a"))
                        node = node.find_next_sibling()

                    if excel_links:
                        for a in excel_links:
                            href = 'https://eaindustry.nic.in/'+a.get("href")
                            text = a.get_text(strip=True)
                            print(f"{text}: {href}")
                            download_as_pdf(href, 'WPI_Data')
                    else:
                        print("⚠️ No <a> tags found between the two sections.")
                new_page.close()

        elif selector.lower()=='core':
            # add code to check for later years:
            page.locator('a#dropdown3').click()  # opens the dropdown
            download_link = page.locator("ul.dropdown-menu[aria-labelledby='dropdown3'] a", has_text='Download Data').first
            download_as_pdf('https://eaindustry.nic.in/'+download_link.get_attribute('href'), 'Core_Data')


# Core for 7, WPI for 6
ea_scraper('wpi')
