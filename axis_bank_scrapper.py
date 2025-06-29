from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import time
import pdfkit
import requests
from urllib.parse import urljoin
import re

# Update path as per your installation
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

def sanitize(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

def scrape_all_pages():
    """Your working pagination code - extracts all 9 pages"""
    os.makedirs("pages", exist_ok=True)
    base_url = "https://www.axismf.com/mutual-funds"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(base_url)

        while "captcha" in page.content().lower():
            input("Captcha detected. Please solve manually and press Enter...")

        # Extract total number of pages from pagination divs
        page.wait_for_selector("div[class^='pagination_']")
        pagination_divs = page.query_selector_all("div[class^='pagination_']")
        total_pages = len(pagination_divs)
        print(f"Total pages found: {total_pages}")

        for i in range(total_pages):
            # Re-select all pagination buttons after each reload
            pagination_divs = page.query_selector_all("div[class^='pagination_']")
            print(f"Clicking page {i+1}")
            pagination_divs[i].click()
            page.wait_for_timeout(2000)

            html = page.content()
            with open(f"pages/page_{i+1}.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved page {i+1} HTML")

        browser.close()

def extract_scheme_links():
    """Your working link extraction code - gets all 71 links"""
    scheme_links = []
    base_folder = "pages"
    
    for i in range(1, 10):  # Pages 1 to 9
        file_path = os.path.join(base_folder, f"page_{i}.html")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                
                # Find all <a> tags inside <td> with the unique class name pattern
                anchors = soup.select("td[class*='mutualFundsTable_hop-table-sort-input-row-value'] a")
                for a in anchors:
                    href = a.get("href")
                    if href and href.startswith("https://www.axismf.com"):
                        scheme_links.append(href)
        except FileNotFoundError:
            print(f"⚠️ Page {i} HTML file not found")
            continue

    # Remove duplicates and sort for consistent order
    scheme_links = sorted(list(set(scheme_links)))

    # Save to file
    with open("scheme_links.txt", "w") as f:
        for link in scheme_links:
            f.write(link + "\n")

    print(f"✅ Extracted {len(scheme_links)} unique scheme links.")
    return scheme_links

def extract_table_to_pdf(soup, table_selectors, filename, table_name):
    """Extract specific table and convert to PDF"""
    for selector in table_selectors:
        try:
            if selector.startswith("contains("):
                # Handle XPath-like contains selector
                text_to_find = selector.split("'")[1]
                tables = soup.find_all("table")
                for table in tables:
                    if text_to_find.lower() in table.get_text().lower():
                        found_table = table
                        break
                else:
                    continue
            else:
                found_table = soup.select_one(selector)
            
            if found_table:
                table_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h2 {{ color: #333; text-align: center; margin-bottom: 20px; }}
                        table {{ 
                            border-collapse: collapse; 
                            width: 100%; 
                            margin: 20px 0;
                        }}
                        th, td {{ 
                            border: 1px solid #ddd; 
                            padding: 12px; 
                            text-align: left; 
                        }}
                        th {{ 
                            background-color: #f2f2f2; 
                            font-weight: bold;
                        }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        .table-header {{ 
                            font-size: 16px; 
                            font-weight: bold; 
                            margin-bottom: 10px; 
                        }}
                    </style>
                </head>
                <body>
                    <h2>{table_name}</h2>
                    {str(found_table)}
                </body>
                </html>
                """
                
                pdfkit.from_string(table_html, filename, configuration=PDFKIT_CONFIG)
                print(f"📄 Saved {table_name}: {os.path.basename(filename)}")
                return True
        except Exception as e:
            print(f"⚠️ Error with selector '{selector}': {e}")
            continue
    
    print(f"⚠️ {table_name} table not found")
    return False

def process_scheme_pages(scheme_links):
    """Process each scheme page to extract portfolio, performance, and PDFs"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for faster processing
        page = browser.new_page()
        
        for i, url in enumerate(scheme_links, 1):
            print(f"\n🔍 Processing ({i}/{len(scheme_links)}): {url}")
            
            try:
                page.goto(url, timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                # Create folder for this scheme
                scheme_name = sanitize(url.split("/")[-3])  # Extract scheme name from URL
                os.makedirs(scheme_name, exist_ok=True)
                
                # Try clicking Portfolio tab first
                try:
                    portfolio_tab = page.query_selector("text=Portfolio")
                    if portfolio_tab:
                        portfolio_tab.click()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)
                        print("📊 Clicked Portfolio tab")
                except:
                    print("⚠️ No Portfolio tab found or unable to click")
                
                # Get page content
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                
                # Portfolio table selectors (based on your screenshot)
                portfolio_selectors = [
                    "contains('Issuers')",
                    "contains('Top 10 Issuers')",
                    "contains('% Of Net Assets')",
                    "table:contains('Holdings')",
                    ".portfolio-table",
                    "table[class*='portfolio']",
                    "div[id*='portfolio'] table",
                    "table:has(th:contains('Issuers'))",
                    "table:has(td:contains('%'))"
                ]
                
                # Extract Portfolio table
                portfolio_found = extract_table_to_pdf(
                    soup, 
                    portfolio_selectors, 
                    f"{scheme_name}/portfolio_table.pdf", 
                    "Portfolio Holdings"
                )
                
                # Try clicking Performance tab
                try:
                    performance_tab = page.query_selector("text=Performance")
                    if performance_tab:
                        performance_tab.click()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)
                        print("📈 Clicked Performance tab")
                        
                        # Get updated content after clicking Performance tab
                        html = page.content()
                        soup = BeautifulSoup(html, "html.parser")
                except:
                    print("⚠️ No Performance tab found or unable to click")
                
                # Performance table selectors
                performance_selectors = [
                    "contains('Performance')",
                    "contains('Returns')",
                    "contains('CAGR')",
                    ".performance-table",
                    "table[class*='performance']", 
                    "div[id*='performance'] table",
                    "table:has(th:contains('Returns'))",
                    "table:has(th:contains('Performance'))"
                ]
                
                # Extract Performance table
                performance_found = extract_table_to_pdf(
                    soup, 
                    performance_selectors, 
                    f"{scheme_name}/performance_table.pdf", 
                    "Performance Data"
                )
                
                # Download all PDF documents
                pdf_links = []
                for a in soup.find_all("a", href=True):
                    href = a['href']
                    if href.lower().endswith('.pdf'):
                        if href.startswith('http'):
                            pdf_links.append(href)
                        else:
                            pdf_links.append(urljoin(url, href))
                
                print(f"📋 Found {len(pdf_links)} PDF documents")
                
                for j, link in enumerate(pdf_links, start=1):
                    try:
                        response = requests.get(link, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        # Extract filename from URL
                        pdf_name = link.split('/')[-1]
                        if not pdf_name.endswith('.pdf'):
                            pdf_name = f"document_{j}.pdf"
                        
                        filename = f"{scheme_name}/{pdf_name}"
                        
                        with open(filename, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        print(f"✅ Downloaded: {pdf_name}")
                    except Exception as e:
                        print(f"❌ Failed to download PDF {j}: {e}")
                
                print(f"✅ Completed: {scheme_name}")
                
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                continue
        
        browser.close()

def main():
    print("🚀 Starting Axis Mutual Fund Complete Scraper...")
    
    # Step 1: Scrape all pages (if not already done)
    if not os.path.exists("pages"):
        print("📄 Scraping all pages...")
        scrape_all_pages()
    else:
        print("📄 Pages folder exists, skipping page scraping")
    
    # Step 2: Extract scheme links
    print("🔗 Extracting scheme links...")
    scheme_links = extract_scheme_links()
    
    if not scheme_links:
        print("❌ No scheme links found!")
        return
    
    # Step 3: Process each scheme
    print(f"🎯 Processing {len(scheme_links)} schemes...")
    process_scheme_pages(scheme_links)
    
    print("\n🎉 Scraping completed!")
    print(f"📊 Total schemes processed: {len(scheme_links)}")

if __name__ == "__main__":
    main()
