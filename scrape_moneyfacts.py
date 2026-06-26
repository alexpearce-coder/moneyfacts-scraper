from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass
import html
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup


URL = "https://moneyfactscompare.co.uk/savings-accounts/easy-access-savings-accounts/?id=null&business-type=16&activity-type=null&investment-amount=25000&investment-type=1&account-types=2048&interest-paid-frequencies=null&terms=null&account-opening-methods=null&account-management-methods=null&notice-periods=null&include-notice-period=true&include-term=true&age=21&has-withdrawal-restrictions=2&existing-customers-only=2&is-shariaa=2&joint-account-only=2&flexible-isa-only=2&sort-filter=standard-order"


@dataclass(frozen=True)
class ProductRow:
    position: int
    provider: str
    product_name: str
    aer: str
    duplicate_key: str


def normalize(text: str) -> str:
    return " ".join(text.split()).strip()


def parse_aer(text: str) -> str | None:
    match = re.search(r"(\d+(?:\.\d+)?)%", text)
    if not match:
        return None
    return f"{Decimal(match.group(1)):.2f}"


def extract_rows(page_html: str) -> list[ProductRow]:
    soup = BeautifulSoup(page_html, "html.parser")
    model_script = soup.find("script", attrs={"data-id": "savings-finderV3"})
    if not model_script or not model_script.get("data-model"):
        return []

    raw_model = html.unescape(model_script["data-model"])
    data = json.loads(raw_model)
    results = data.get("Results", [])

    rows: list[ProductRow] = []
    seen: set[str] = set()
    position = 1

    for product in results:
        selected = product.get("PrimaryProduct") or {}
        provider = normalize(selected.get("ProviderName", ""))
        product_name = normalize(selected.get("ProductName", ""))
        aer_value = selected.get("AER")
        if not provider or not product_name or aer_value in (None, ""):
            continue

        aer = f"{Decimal(str(aer_value)):.2f}" if aer_value is not None else None
        if not provider or not product_name or not aer:
            continue

        duplicate_key = f"{provider}|{product_name}|{aer}"
        if duplicate_key in seen:
            continue
        seen.add(duplicate_key)
        rows.append(ProductRow(position=position, provider=provider, product_name=product_name, aer=aer, duplicate_key=duplicate_key))
        position += 1

    return rows


def rows_to_csv(rows: Iterable[dict[str, str]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["scrape_date", "rank", "provider", "product_name", "aer", "duplicate_key"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def read_existing_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sort_rows(rows: list[ProductRow]) -> list[ProductRow]:
    return sorted(rows, key=lambda row: (-Decimal(row.aer), row.provider, row.product_name))


def write_output(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)


def main() -> None:
    output_dir = os.getenv("OUTPUT_DIR", "data")
    history_path = Path(output_dir) / "moneyfacts-scraper-history.csv"

    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()

    parsed = extract_rows(response.text)
    today = date.today().isoformat()

    output_rows = []
    for rank, row in enumerate(sort_rows(parsed), start=1):
        output_rows.append(
            {
                "scrape_date": today,
                "rank": str(rank),
                "provider": row.provider,
                "product_name": row.product_name,
                "aer": row.aer,
                "duplicate_key": row.duplicate_key,
            }
        )

    history_rows = read_existing_rows(history_path)
    history_rows.extend(output_rows)
    history_csv = rows_to_csv(history_rows)
    latest_csv = rows_to_csv(output_rows)

    write_output(str(history_path), history_csv)
    write_output(os.path.join(output_dir, "latest.csv"), latest_csv)


if __name__ == "__main__":
    main()
