import os
import re
import string
import time

import requests
from playwright.sync_api import sync_playwright, Error, Page
from bs4 import BeautifulSoup, Tag
from datetime import date


def sanitize_filename(name, max_length=100):
    # Replace invalid Windows filename characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]


def download_as_pdf(pdf_url: str, download_dir: str, filename: str):
    os.makedirs(sanitize_filename(download_dir), exist_ok=True)
    filename = sanitize_filename(filename)
    save_path = os.path.join(download_dir, filename)
    if not save_path.endswith('.pdf'):
        save_path += '.pdf'
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def gdp_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://www.mospi.gov.in/press-release')
        page.wait_for_load_state('domcontentloaded')
        ministry_dropdown = page.locator("select#edit-field-press-release-category-tid").first
        ministry_dropdown.click()
        ministry_dropdown.wait_for(state="visible")
        # Select NAD
        ministry_dropdown.select_option("825")
        print('Successfully selected NAD')
        current_date = date.today()
        start_date = ''
        end_date = ''
        if current_date.month >= 4:
            # New financial year
            start_date = '01-04-'+str(current_date.year)
            end_date = '31-03-'+str(current_date.year+1)
        else:
            # Old financial year
            start_date = '01-04-'+str(current_date.year-1)
            end_date = '31-03-'+str(current_date.year)
        page.fill('input#edit-date-filter-min-datepicker-popup-0', start_date)
        page.fill('input#edit-date-filter-max-datepicker-popup-0', end_date)
        print('Succesfully filled date ')
        # Click 'apply'
        page.click('input#edit-submit-press-release-view')
        print('Applied filters')
        page.wait_for_load_state('domcontentloaded')

        while True:
            # Parse the HTML
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Find all <td> with class 'pressReleaseTitle'
            tds = soup.find_all('td', class_='pressReleaseTitle')
            print('Found all <td>')

            # Extract all <a> tags from those <td>s
            for td in tds:
                a_tags = td.find_all('a')
                for a in a_tags:
                    link_txt = a.get_text(strip=True).lower()
                    if link_txt.find('gdp') != -1 or link_txt.find('gross domestic product') != -1:
                        download_as_pdf(a['href'], 'GDP_Data', link_txt)

            # Check for next pages. If present, click
            if soup.find('li', class_='pager-next'):
                print('Moving to next page...')
                next_btn = page.locator('li.pager-next a')
                next_href = next_btn.get_attribute("href")
                next_url = "https://www.mospi.gov.in" + next_href
                print(f"Navigating to next page: {next_url}")
                page.goto(next_url)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(1) # to not overload server

            else:
                break

        print('Finished successfully')
        page.close()


gdp_scraper()
