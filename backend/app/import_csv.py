"""Import a complete, source-attributed CSV into the local API."""

import argparse
import csv
import json
import urllib.error
import urllib.request
from pathlib import Path

REQUIRED = ("business_name", "category", "city", "address", "source", "source_url")


def read_listings(path: Path) -> list[dict[str, str]]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for line_number, row in enumerate(csv.DictReader(stream), start=2):
            missing = [key for key in REQUIRED if not (row.get(key) or "").strip()]
            if missing:
                raise ValueError(f"Row {line_number} is incomplete: {', '.join(missing)}")
            phone = (row.get("phone") or "").strip()
            phone_digits = "".join(ch for ch in phone if ch.isdigit())
            if phone and not 8 <= len(phone_digits) <= 24:
                raise ValueError(f"Row {line_number} has an implausible phone number")
            item = {key: row[key].strip() for key in REQUIRED}
            item["phone"] = phone or None
            item["source_id"] = (row.get("source_id") or row["osm_id"] or row["source_url"]).strip()
            for key in ("latitude", "longitude"):
                item[key] = float(row[key]) if row.get(key) else None
            rows.append(item)
    if not rows:
        raise ValueError("CSV contains no listing rows")
    return rows


def import_rows(rows: list[dict[str, str]], api_url: str) -> dict[str, object]:
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/listings/bulk",
        data=json.dumps({"listings": rows}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API rejected the import ({exc.code}): {detail}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    rows = read_listings(args.csv_file)
    print(json.dumps(import_rows(rows, args.api), indent=2))


if __name__ == "__main__":
    main()
