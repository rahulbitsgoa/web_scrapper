# Economic Data Scrapers

This repository contains Python scripts for automated scraping and downloading of key economic datasets and reports from various official Indian government sources. Each script is dedicated to a specific dataset or publication, enabling efficient, up-to-date collection of economic indicators for analysis or research.

---

## 📁 Contents

### `GDP_scraper.py`
Scrapes and downloads GDP-related press releases and reports from the Ministry of Statistics and Programme Implementation (MOSPI) website, filtering for relevant keywords and date ranges.

### `IIP_data_scrapper.py`
Automates the extraction and downloading of all IIP (Index of Industrial Production) data files (Excel, image, etc.) from the MOSPI IIP Data section, ensuring only relevant files are collected.

### `IIP_press_release_scrapper.py`
Downloads all IIP press release PDFs from the MOSPI website, expanding all archive sections to ensure no files are missed.

### `PLFS_scrapper.py`
Scrapes Periodic Labour Force Survey (PLFS) reports and datasets from the MOSPI website, including all available PDF reports.

### `WPI_scraper.py`
Automates the download of Wholesale Price Index (WPI) datasets and reports from MOSPI or related government sources.It also automates downloading of latest Core Infrastructure data.

### `commerce_gov.py`
Scrapes trade and commerce data, such as export/import reports, from the official commerce ministry portal or related sources.

### `IMF_WEO_scraper.py`
Scrapes IMF's dataset from its website.


---

## ⚙️ Features

- **Automated Navigation**: Uses Playwright for robust browser automation, including handling dynamic content, popups, and menu navigation.
- **Targeted Downloading**: Each script is tailored to download only the relevant files (PDF, XLSX, JPG, etc.) from the correct section of the source site.
- **Duplicate Protection**: Scripts check for existing files and avoid redundant downloads.
- **Fast & Efficient**: Designed for speed using headless browsing and optimized selection logic.
- **Easy Customization**: Modular code structure for adapting to new data sources or changing website layouts.

---

## 📦 Requirements

- Python 3.8+
- `playwright`
- `beautifulsoup4`
- `requests`

### Install dependencies with:

```bash
pip install playwright beautifulsoup4 requests
playwright install
