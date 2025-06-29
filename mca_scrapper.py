import base64
import json
import os
import re
import time

import requests


def sanitize_filename(name, max_length=100):
    # Replace invalid Windows filename characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]


def download_as_pdf(pdf_url: str, download_dir: str, name: str = ''):
    # Pass the PDF URL as pdf_url and the directory where you want to store file as download_dir
    os.makedirs(download_dir, exist_ok=True)
    filename = name.removesuffix('\n') if name else os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, sanitize_filename(filename))
    """
    Fill in your headers and cookies here in the same format

    
    Steps to fill in:
    1. Go to https://www.mca.gov.in/bin/ebook/dms/getdocument?doc=Nzc5Mg==&docCategory=Circulars&type=open or any pdf link of the website
    2. Go to Devtools (ctrl+shift+i) and then to Network
    3. Reload the page, keeping Devtools open
    4. Right click on first request starting with 'getDocument?' and copy as curl (choose any of the options depending on your command prompt)
    5. Paste the CURL in a text editor
    6. All the text preceded by -H should be in header, -b should be in cookies.
        eg.
        curl 'https://example.com/file.pdf' \
        -H 'accept: application/pdf' \
        -H 'user-agent: Mozilla/5.0' \
        -H 'referer: https://example.com/' \
        -b 'sessionid=abc123; csrftoken=xyz456'
        
        gets converted as:
        
        url = "https://example.com/file.pdf"

        headers = {
            "accept": "application/pdf",
            "user-agent": "Mozilla/5.0",
            "referer": "https://example.com/"
        }

        cookies = {
            "sessionid": "abc123",
            "csrftoken": "xyz456"
        }
 
    """
    headers = {
    }

    cookies = {
    }

    response = requests.get(pdf_url, headers=headers, cookies=cookies)
    if response and response.status_code != 200:
        print(f"Failed to load homepage: {response.status_code}")
        return
    if not save_path.lower().endswith('.pdf'):
        save_path += '.pdf'
    with open(save_path, "wb") as f:
        f.write(response.content)
        print(f"Downloaded to: {save_path}")
        f.close()
    if "application/pdf" not in response.headers.get("content-type", ""):
        print("Did not receive a PDF. Response content-type:", response.headers.get("content-type"))
        print("Response text:", response.text[:500])  # Print first 500 chars for debugging


def encode_link(link_value):
    # Ensure link_value is a string
    link_str = str(link_value)
    encoded = base64.b64encode(link_str.encode('utf-8')).decode('utf-8')
    return encoded

def build_download_url(link, docCategory="Circulars"):
    doc = encode_link(link)
    return f"https://www.mca.gov.in/bin/ebook/dms/getdocument?doc={doc}&docCategory={docCategory}&type=open"


def mca_scraper(year='-1'):
    d_dir = 'MCA_Circulars'
    # Load JSON into variable
    with open('urls.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        f.close()
    """
    # Code to make the json file more readable (not required for program): 
    # Get the JSON file manually from this link: https://www.mca.gov.in/bin/ebook/service/documentMetadata?docCategory=Circulars&flag=initial&status=Current
    pretty_json_string = json.dumps(data, indent=4, ensure_ascii=False)
    print(pretty_json_string)

    with open('pretty_file.json', 'w', encoding='utf-8') as f:
        f.write(pretty_json_string)
        f.close()
    """
    yrs = set(item['notificationdate'].strip()[-4:] for item in data['data'] if 'notificationdate' in item)
    for yr in yrs:
        os.makedirs(os.path.join(d_dir, sanitize_filename(yr)), exist_ok=True)
    links = [item['link'] for item in data['data'] if 'link' in item]
    names = [item['shortDescription'] for item in data['data'] if 'shortDescription' in item]
    years = [item['notificationdate'].strip()[-4:] for item in data['data'] if 'notificationdate' in item]
    print(links)
    for link, name, year in zip(links, names, years):
        url = build_download_url(link)
        print(d_dir)
        print(year)
        print(os.path.join(d_dir, sanitize_filename(year)))
        download_as_pdf(pdf_url=url, download_dir=os.path.join(d_dir, sanitize_filename(year)), name=name)
        time.sleep(3)



mca_scraper()
