# Moneyfacts Daily Scraper

Daily scraper for the Moneyfacts easy-access savings ranking page.

## Output

- `gs://<bucket>/moneyfacts/YYYY-MM-DD.csv`
- `gs://<bucket>/moneyfacts/latest.csv`

## Environment

- `GCS_BUCKET`: target bucket name
- `GCP_SA_KEY_JSON`: GitHub secret containing a service account JSON key

## Run locally

```bash
python -m pip install -r requirements.txt
export GCS_BUCKET=your-bucket
python scrape_moneyfacts.py
```
