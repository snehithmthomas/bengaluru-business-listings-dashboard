"""Create a strict, complete-only seed dataset and its MySQL insert dump."""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_JSON = ROOT / "data" / "bengaluru_osm_shop_candidates.json"
SOURCE_CSV = ROOT / "data" / "bengaluru_listings.csv"
VERIFIED_CSV = ROOT / "data" / "bengaluru_complete.csv"
VERIFIED_JSON = ROOT / "data" / "bengaluru_complete.json"
SQL_DUMP = ROOT / "database" / "listings_dump.sql"
REQUIRED = ("business_name", "category", "city", "address", "source", "source_url")
CSV_FIELDS = ["business_name", "category", "city", "address", "phone", "source", "source_url", "source_id", "osm_id", "latitude", "longitude"]


def sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def main() -> None:
    if SOURCE_JSON.exists():
        source_rows = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    else:
        with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as stream:
            source_rows = list(csv.DictReader(stream))

    output: list[dict[str, str]] = []
    excluded = 0
    seen: set[tuple[str, str]] = set()
    for row in source_rows:
        if any(not (row.get(field) or "").strip() for field in REQUIRED):
            excluded += 1
            continue
        # A postcode alone is not a usable business address.
        if not re.search(r"[A-Za-z]", row["address"]):
            excluded += 1
            continue
        phone = (row.get("phone") or "").strip()
        if phone and not 8 <= len(re.sub(r"\D", "", phone)) <= 24:
            phone = ""

        city = row["city"].strip()
        if "bengaluru" in city.casefold() or "bangalore" in city.casefold():
            city = "Bengaluru"
        source_id = (row.get("source_id") or row["source_url"]).strip()
        dedupe_key = (row["source"].strip().casefold(), source_id)
        if dedupe_key in seen:
            excluded += 1
            continue
        seen.add(dedupe_key)
        output.append({
            "business_name": row["business_name"].strip(),
            "category": row["category"].strip(),
            "city": city,
            "address": row["address"].strip(),
            "phone": phone,
            "source": row["source"].strip(),
            "source_url": row["source_url"].strip(),
            "source_id": source_id,
            "osm_id": (row.get("osm_id") or source_id).strip(),
            "latitude": str(row["latitude"]) if row.get("latitude") is not None else "",
            "longitude": str(row["longitude"]) if row.get("longitude") is not None else "",
        })

    VERIFIED_CSV.parent.mkdir(parents=True, exist_ok=True)
    with VERIFIED_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(output)
    VERIFIED_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    insert_columns = ", ".join((
        "business_name", "category", "city", "address", "phone", "source", "source_url",
        "source_id", "latitude", "longitude",
    ))
    statements = [
        "-- Complete-only Bengaluru OSM seed records. See README.md for source and coverage notes.",
        "START TRANSACTION;",
    ]
    for row in output:
        values = [
            sql_string(row["business_name"]), sql_string(row["category"]), sql_string(row["city"]),
            sql_string(row["address"]), sql_string(row["phone"]) if row["phone"] else "NULL", sql_string(row["source"]),
            sql_string(row["source_url"]), sql_string(row["source_id"]),
            row["latitude"] if row["latitude"] else "NULL",
            row["longitude"] if row["longitude"] else "NULL",
        ]
        statements.append(
            f"INSERT INTO listing_master ({insert_columns}) VALUES ({', '.join(values)}) AS incoming "
            "ON DUPLICATE KEY UPDATE business_name=incoming.business_name, category=incoming.category, "
            "city=incoming.city, address=incoming.address, phone=incoming.phone, "
            "source_url=incoming.source_url, latitude=incoming.latitude, longitude=incoming.longitude;"
        )
    statements.append("COMMIT;")
    SQL_DUMP.write_text("\n".join(statements) + "\n", encoding="utf-8")
    print(f"source_rows={len(source_rows)} complete_rows={len(output)} excluded_rows={excluded}")


if __name__ == "__main__":
    main()
