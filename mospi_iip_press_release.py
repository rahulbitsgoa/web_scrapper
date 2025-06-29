import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def sanitize_filename(name, max_length=100):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]

def download_as_pdf(pdf_url: str, download_dir: str, filename: str, session: requests.Session):
    os.makedirs(download_dir, exist_ok=True)
    filename = sanitize_filename(filename)
    save_path = os.path.join(download_dir, filename)
    if not save_path.endswith('.pdf'):
        save_path += '.pdf'

    if os.path.exists(save_path):
        print(f"⏭️ Exists: {filename}")
        return True

    try:
        response = session.get(pdf_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://mospi.gov.in/"}, timeout=30)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} {filename}")
            return False
    except Exception as e:
        print(f"❌ Error: {filename} - {e}")
        return False

def iip_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        print("Navigating to IIP page...")
        page.goto('https://mospi.gov.in/iip', timeout=60000)
        page.click("button:has-text('Press Release')")
        page.wait_for_selector("ul#MainMenu_1", timeout=10000)

        print("Expanding all sections...")
        for _ in range(10):
            collapsed_count = page.locator("li.collapsed > span").count()
            if collapsed_count == 0:
                break
            # Try clicking all collapsed in one go (faster in some cases)
            for idx in range(collapsed_count):
                try:
                    page.locator("li.collapsed > span").nth(idx).click(timeout=1000)
                except Exception:
                    continue
            page.wait_for_timeout(100)

        print("Parsing page with BeautifulSoup...")
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        all_links = soup.find_all('a', href=True)
        pdf_links = []
        base_url = "https://mospi.gov.in"

        for link in all_links:
            href = link.get('href', '')
            if href.lower().endswith('.pdf'):
                filename = os.path.basename(href)
                if filename.lower().startswith('iip'):
                    pdf_links.append({
                        'url': urljoin(base_url, href),
                        'filename': filename
                    })

        print(f"\n>>> Total IIP PDFs found: {len(pdf_links)}")

        # Use ThreadPoolExecutor for parallel downloads
        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    executor.submit(download_as_pdf, pdf['url'], 'IIP_Press_Release', pdf['filename'], session)
                    for pdf in pdf_links
                ]
                for _ in as_completed(futures):
                    pass

        print('✅ IIP scraping finished successfully')
        browser.close()

if __name__ == "__main__":
    iip_scraper()
