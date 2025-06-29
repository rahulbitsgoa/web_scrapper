# Run these commands in terminal:
# pip install playwright
# playwright install
# pip install beautifulsoup4
# pip install lxml

import json
import os
import random
import time
from multiprocessing import Pool

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Error, Page
import re


def process_fund_wrapper(args):
    return process_fund(*args)


def download_as_pdf(pdf_url: str, download_dir: str):
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, filename)
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def captcha_check(page: Page):
    while "captcha" in page.content().lower():
        print("Captcha detected. Please solve it in the browser window. Checking again in 60 seconds...")
        page.wait_for_timeout(60 * 1000)  # Wait 60 seconds (milliseconds)
    page.wait_for_timeout(3000)  # wait 3 seconds


def sanitize_filename(name):
    # Replace invalid Windows filename characters with underscore
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def process_fund(link, name, download_dir, user_agent):
    # Sanitise name
    safe_name = sanitize_filename(name)
    # make name directory
    os.makedirs(os.path.join(download_dir, safe_name), exist_ok=True)
    download_dir = os.path.join(download_dir, safe_name)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                accept_downloads=True,
                user_agent=user_agent
            )
            page = context.new_page()
            try:
                # prevent window from taking focus
                page.evaluate("window.blur();")
                response = page.goto(link, wait_until="domcontentloaded", timeout=90000)
                if response and response.status != 200:
                    print(f"Failed to load {link}: {response.status}")
                    return
            except Exception as e:
                print(f"Error visiting {link}: {e}")
                return

            page.wait_for_load_state('domcontentloaded', timeout=90000)
            # Captcha check
            captcha_check(page)
            docs_section_id = 'pd_documents'
            portfolio_section_id = 'pd_portfolio'
            performance_section_id = 'pd_performance'

            # Get the <head> HTML (with CSS/JS)
            head_html = page.evaluate("() => document.head.outerHTML")

            # Data extraction
            portfolio_section = page.locator(f'section#{portfolio_section_id}')
            performance_section = page.locator(f'section#{performance_section_id}')
            portfolio_stocks_html = ""
            performance_html = ""

            stocks_link = portfolio_section.locator("a#stk")
            if stocks_link.count() > 0 and stocks_link.is_visible():
                stocks_link.click()

            detail_link = portfolio_section.locator("a:has-text('Detail Holdings'):visible")
            if detail_link.count() > 0 and detail_link.is_visible():
                detail_link.click()

            if portfolio_section.count() != 0:
                portfolio_stocks_html = portfolio_section.evaluate("el => el.outerHTML")
            if performance_section.count() != 0:
                performance_html = performance_section.evaluate("el => el.outerHTML")

            final_html = f"""
            <html>
            {head_html}
            <body>
            <b>Portfolio</b>
            <br>
            {portfolio_stocks_html}
            <style>
            /* Disable scroll and JS effects for #pd_portfolio */
            #pd_portfolio, #pd_portfolio * {{
                max-height: none !important;
                overflow: visible !important;
                pointer-events: none;
            }}
            </style>            
            <br>
            <br>
            <b>Performance of stocks:</b>
            <br>
            {performance_html}
            </body>
            </html>
            """

            # Save HTML to file
            with open(os.path.join(download_dir, f"pdf_final_{name}.html"), 'w', encoding='utf-8') as f:
                f.write(final_html)

            # Save as PDF
            new_page = context.new_page()
            new_page.set_content(final_html)
            new_page.pdf(
                path=os.path.join(download_dir, safe_name + ".pdf"),
                format="A4",
                print_background=True
            )
            print('PDF saved at: ' + os.path.join(download_dir, safe_name + ".pdf"))
            new_page.close()

            # Download docs
            section = page.locator(f"section#{docs_section_id}")
            download_links = section.locator("a:has-text('Download'):visible")
            count = download_links.count()
            for i in range(count):
                d_link = download_links.nth(i)
                with context.expect_page() as new_page_info:
                    d_link.click(force=True)
                    time.sleep(0.2)
                new_tab = new_page_info.value
                new_tab.wait_for_load_state("domcontentloaded")
                pdf_url = new_tab.url
                print(f"PDF opened at URL: {pdf_url}")
                download_as_pdf(pdf_url, download_dir)
                new_tab.close()

            page.close()
            context.close()
            browser.close()
    except Exception as e:
        print(f"Exception in process_fund for {name}: {e}")


def kotak_scraper(reuse: bool):
    first_time = time.time()
    html_text = ""
    if not reuse:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://www.kotakmf.com/mutual-funds")
            captcha_check(page)
            while True:
                try:
                    load_more = page.locator('a.loadMoreTextSize.loadMoreTextMob')
                    if load_more.count() > 0 and load_more.is_visible():
                        print("Clicking Load More...")
                        load_more.click()
                        page.wait_for_timeout(1500)  # Wait for new items to load
                    else:
                        print("No more Load More button found.")
                        break
                except Exception as e:
                    print(f"Error clicking Load More: {e}")
                    break
            html_text = page.content()
            with open("kotak_source.html", 'w', encoding='utf-8') as f:
                f.write(html_text)
            page.close()
            context.close()
            browser.close()


    # Load cached HTML to avoid repeated captcha
    with open("kotak_source.html", 'r', encoding='utf-8') as f:
        html_text = f.read()

    soup = BeautifulSoup(html_text, 'lxml')

    jobs = soup.find_all('a', class_='fundName')
    links = []
    names = []
    for job in jobs:
        links.append(job.get('href'))
        names.append(job.get_text(strip=True))

    # Remove irrelevant links/names
    links = links[:len(links)//2]
    names = names[:len(names)//2]
    print(links)
    download_dir = "Downloads"
    os.makedirs(download_dir, exist_ok=True)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"

    # Use multiprocessing for parallelism
    max_workers = 3  # Adjust as needed
    args_list = [(link, name, download_dir, user_agent) for link, name in zip(links, names)]
    with Pool(processes=max_workers) as pool:
        pool.map(process_fund_wrapper, args_list)

    last_time = time.time()
    print('Successfully executed')
    print('Time taken: ' + str(last_time - first_time) + ' seconds')


if __name__ == '__main__':
    kotak_scraper(reuse=True)
