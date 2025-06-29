import os
import requests
from playwright.sync_api import sync_playwright, Error
import re
from urllib.parse import urlparse, urljoin

# Clean up filenames/folder names so Windows doesn't get mad
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip()

# Download a PDF file and save it safely in the right folder
def download_as_pdf(pdf_url: str, download_dir: str, file_name: str = None, dedupe_counter=0):
    os.makedirs(download_dir, exist_ok=True)

    if not file_name:
        file_name = os.path.basename(pdf_url.split("?")[0])

    file_name = sanitize_filename(file_name.strip())
    if not file_name:
        file_name = "document"

    if not file_name.lower().endswith(".pdf"):
        file_name += ".pdf"

    base_name, ext = os.path.splitext(file_name)
    final_name = f"{base_name}_{dedupe_counter}{ext}" if dedupe_counter > 0 else file_name
    save_path = os.path.join(download_dir, final_name)

    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {pdf_url}: {e}")
        return False

# Extract folder-friendly section name like "upi" or "nfs"
def extract_section_name(url):
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    return sanitize_filename(parts[-2] if len(parts) >= 2 else parts[-1])

# The main scraping function
def npci_scraper(user_agent='', year=''):
    npci_main_link = 'https://www.npci.org.in/'

    with sync_playwright() as p:
        print("🚀 Launching browser and opening NPCI...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            accept_downloads=True,
            user_agent=user_agent
        )
        page = context.new_page()

        # Step 1: Collect circular section links
        response = page.goto(npci_main_link, wait_until="domcontentloaded", timeout=90000)
        if response and response.status != 200:
            print(f"⚠️ Failed to load homepage: {response.status}")
            return

        l1 = page.query_selector_all("a[aria-label='Circulars']")
        circular_links = [l.get_attribute('href') for l in l1 if l.get_attribute('href')]
        browser.close()

        # Step 2: Visit each circular page and download PDFs
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()

        for link in circular_links:
            if not link.startswith("http"):
                link = urljoin(npci_main_link, link)
            section_name = extract_section_name(link)
            save_folder = os.path.join("circulars", section_name)

            print(f"\n📂 Visiting: {link}")
            print(f"📁 Will save PDFs to: {save_folder}")

            try:
                response = page.goto(link, wait_until="domcontentloaded", timeout=60000)
                if response and response.status != 200:
                    print(f"⚠️ Failed to load {link}: {response.status}")
                    continue

                pdf_items = []
                if year != '':
                    # Do for specific year
                    pdf_items = page.query_selector_all("div#year"+year+" .pdf-item")
                else:
                    # Do for all years
                    pdf_items = page.query_selector_all(".pdf-item")

                print(f"🔍 Found {len(pdf_items)} pdf-item blocks")

                seen_names = set()

                for item in pdf_items:
                    title_elem = item.query_selector("p")
                    link_elem = item.query_selector("a[href$='.pdf']")  # ✅ FIXED: picks any PDF link


                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.inner_text().strip()
                    raw_href = link_elem.get_attribute("href")

                    print(f"🔗 Found title: {title}\n   href: {raw_href}")

                    if not raw_href:
                        continue

                    pdf_url = urljoin(link, raw_href)

                    clean_name = sanitize_filename(title)
                    if not clean_name:
                        clean_name = "document"

                    original_name = clean_name
                    dedupe_count = 1
                    while clean_name in seen_names:
                        clean_name = f"{original_name}_{dedupe_count}"
                        dedupe_count += 1

                    seen_names.add(clean_name)
                    download_as_pdf(pdf_url, save_folder, clean_name)

            except Error as e:
                print(f"❌ Error visiting {link}: {e}")

        browser.close()

# 🎬 Run the scraper
npci_scraper(year='')
