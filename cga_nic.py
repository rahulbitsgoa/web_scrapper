import os
import pdfkit

folder_name = "cga_report"
os.makedirs(folder_name, exist_ok=True)

from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def pdf_converter(html , num):
    # --- Step 1: Final PDF file path ---
    pdf_filename = os.path.join(folder_name, f"report_{num}.pdf")

    # --- Step 2: wkhtmltopdf configuration (only needed on Windows) ---
    # Change the path below if it's installed elsewhere
    pdfkit_config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    # --- Step 3: Convert HTML string to PDF ---
    pdfkit.from_string(html, pdf_filename, configuration=pdfkit_config)

    print(f"✅ PDF saved at: {pdf_filename}")


def cga_scr():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://cga.nic.in/')
        page.click('input#ctl00_ContentPlaceHolder1_Mddle_btnSubmit')
        page.wait_for_load_state('domcontentloaded')
        iframe_loc = page.locator('iframe').first
        page_link = iframe_loc.get_attribute('src')
        if not page_link.startswith('http'):
            page_link = 'https://cga.nic.in' + page_link
        page.goto(page_link)
        page.wait_for_load_state('domcontentloaded')
        parsed = urlparse(page_link)

        # Split the path into parts
        path_parts = parsed.path.rstrip("/").split("/")

        # Remove the last segment (usually the file name)
        directory_path = "/".join(path_parts[:-1]) + "/"

        # Rebuild the URL without the file name or query
        month_prefix = urlunparse((
            parsed.scheme,
            parsed.netloc,
            directory_path,
            '', '', ''
        ))

        html_codes = []
        html = page.content()
        html_codes.append(html)
        soup = BeautifulSoup(html, "html.parser")
        # Create a set for unique links
        unique_links = set()

        # Extract href attributes from all <a> tags
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith('http'):
                href = month_prefix+href
            p_href = urlparse(href)

            # Rebuild the URL without query or fragment
            clean_url = urlunparse((
                p_href.scheme,
                p_href.netloc,
                p_href.path,
                '', '', ''
            ))
            unique_links.add(clean_url)
        print(unique_links)

        for link in unique_links:
            if not str(link).startswith('http'):
                link = month_prefix+link
            page.goto(str(link))
            page.wait_for_load_state('domcontentloaded')
            html_codes.append(page.content())

        # html_codes stores the codes of all the html pages
        count = 1
        for code in html_codes:
            pdf_converter(code, count)
            count+=1


cga_scr()

