"""Collect candidate Bengaluru shop listings from the OpenStreetMap Overpass API.

This creates candidates only. Use prepare_verified_data.py to create the
complete-only import file; missing business fields remain missing.
"""

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "bengaluru_osm_shop_candidates.json"
OUT_CSV = ROOT / "data" / "bengaluru_osm_shop_candidates.csv"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BBOX = "12.8334905,77.4598797,13.1426196,77.7840639"  # south,west,north,east


def address_from_tags(tags: dict[str, str]) -> str:
    parts = [
        tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:place"),
        tags.get("addr:suburb"), tags.get("addr:city_district"), tags.get("addr:postcode"),
    ]
    return ", ".join(part.strip() for part in parts if part and part.strip())


def main() -> None:
    query = f'''[out:json][timeout:60];
nwr["shop"]({BBOX});
out tags center;'''
    request = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "BengaluruBusinessDashboard/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))

    candidates = []
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        category = tags.get("shop")
        if not name or not category:
            continue
        point = element.get("center") or element
        object_type = element["type"]
        object_id = str(element["id"])
        candidates.append({
            "business_name": name,
            "category": category,
            "city": "Bengaluru",
            "address": address_from_tags(tags),
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "source": "OpenStreetMap",
            "source_url": f"https://www.openstreetmap.org/{object_type}/{object_id}",
            "source_id": f"{object_type}/{object_id}",
            "osm_id": object_id,
            "latitude": point.get("lat"),
            "longitude": point.get("lon"),
        })

    OUT_JSON.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["business_name", "category", "city", "address", "phone", "source", "source_url", "source_id", "osm_id", "latitude", "longitude"]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)
    print(f"Collected {len(candidates)} named shop candidates from OpenStreetMap.")
    print(f"Saved {OUT_JSON.relative_to(ROOT)} and {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
