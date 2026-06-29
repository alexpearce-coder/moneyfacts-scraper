# Moneyfacts Daily Scraper

Daily scraper for the Moneyfacts easy-access savings ranking page.

## Output

- `data/moneyfacts_scraper_history.csv`
- `data/latest.csv`

## Environment

- none required for GitHub-only storage

## Run locally

```bash
python -m pip install -r requirements.txt
export OUTPUT_DIR=data
python scrape_moneyfacts.py
```
