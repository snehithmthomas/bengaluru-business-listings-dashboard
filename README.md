# Bengaluru Business Listings Dashboard

A full-stack business listings dashboard built with React, FastAPI, and MySQL. It uses source-linked OpenStreetMap data for Bengaluru and keeps source IDs so separate branches are not merged by name.

## Dataset

The prepared dataset and SQL seed contain **534 Bengaluru listings** with a business name, category, city, address, source link, source ID, and coordinates. In that seed, phone is optional in OpenStreetMap: 39 listings (7.3%) include one; the other 495 values remain SQL `NULL`. Of the seed addresses, 176 contain a six-digit postcode that the dashboard can extract. Eight records use the OSM category tag `yes`, which may indicate an unspecified category. Repeated business names are retained as separate records by source ID.

The dashboard reads the live MySQL database. A persistent local volume can include records from an earlier run in addition to the 534-row seed, because imports upsert by source ID and do not delete unrelated existing rows. Check `/api/dashboard/summary` for the live count; a fresh MySQL volume starts from the 534-row SQL seed.

The source is OpenStreetMap (OSM), collected through the Overpass API using a bounding box covering Bengaluru. `data/bengaluru_osm_shop_candidates.json` contains the larger candidate export; `data/bengaluru_complete.csv` and `.json` are the prepared records, and `database/listings_dump.sql` seeds those 534 rows. The preparation script excludes rows missing required listing details; it does not invent phone numbers or addresses.

OSM data is available under the Open Database License (ODbL). Listing links and IDs are kept in the data, and the dashboard displays attribution. Keep the attribution and review ODbL obligations before redistributing a modified database. This project does not bulk-scrape Google Maps, Opendi, or GullyDirectory. See the [OSM copyright and license page](https://www.openstreetmap.org/copyright), [Google Maps Platform policies](https://developers.google.com/maps/documentation/places/web-service/policies), [Opendi legal notice](https://www.opendi.com/en/contact.html), and [GullyDirectory terms](https://www.gullydirectory.com/terms).

The assignment asks for 500+ listings, which this prepared dataset meets. The earlier 1,000-record stretch target is not met; obtaining 1,000 complete records requires a source that permits collection and reuse.

## Features

- KPI summary for total listings, category count, phone coverage, and mapped coordinates.
- Category chart with counts and percentages for the top 10 categories.
- Interactive listing map with source-linked details.
- Phone coverage by category and postcode counts extracted from addresses.
- Data quality checks for repeated names, duplicate source IDs, `yes` categories, and addresses without a postcode.
- Listings table with business, category, address, available phone, source link, and source ID.
- FastAPI bulk import and grouped aggregate endpoints.

## Stack

- Frontend: React 18, Vite, Recharts, Leaflet, React Leaflet
- Backend: FastAPI, Pydantic, MySQL Connector/Python
- Database: MySQL 8.4
- Local orchestration: Docker Compose

## Run locally

1. Copy `.env.example` to `.env` and replace both example passwords with local values.
2. Start Docker Desktop or another Docker Engine with Compose.
3. From the project root, start all services:

   ```bash
   docker compose up --build -d
   ```

4. Wait until `docker compose ps` reports the database and backend as healthy.
5. Open the dashboard at <http://localhost:5173> and the API docs at <http://localhost:8000/docs>.

On first startup, MySQL runs `database/schema.sql` and `database/listings_dump.sql`. Existing named Docker volumes are not reseeded automatically. The backend startup migration makes the `phone` column nullable on older volumes. To import or refresh the prepared CSV after the API is healthy, run from the project root:

```bash
python3 backend/app/import_csv.py data/bengaluru_complete.csv --api http://localhost:8000
```

The importer reports `received: 534` when it reads this dataset. Check the current database count at <http://localhost:8000/api/dashboard/summary>. Do not use `docker compose down -v` unless you intend to delete the local database volume and all data stored in it.

## API

- `GET /api/health` - API and database readiness
- `GET /api/dashboard/summary` - totals, distinct categories and sources, and listings with phone/address
- `GET /api/dashboard/cities` - listing counts by city
- `GET /api/dashboard/categories` - listing counts by category
- `GET /api/dashboard/sources` - listing counts by source
- `GET /api/listings?limit=1000` - up to 1,000 source-linked listing records
- `POST /api/listings/bulk` - validate and idempotently insert/update a batch

The database uniqueness key is `(source, source_id)`, preserving distinct branches with repeated names. Required fields are validated; an absent phone is valid and stored as SQL `NULL`.

## Data preparation

`scripts/collect_osm_candidates.py` queries named OSM shop features inside the Bengaluru bounding box and writes candidate JSON and CSV exports. It preserves OSM feature URLs and IDs. `scripts/prepare_verified_data.py` reads the candidate JSON when present (otherwise the source CSV) and regenerates the complete CSV/JSON and SQL seed files:

```bash
python3 scripts/prepare_verified_data.py
```

Before using any alternative directory/API, confirm that its terms or license permit collection and reuse. Document the provider, collection date, license/permission, and remaining data coverage limits.

## Demo video checklist

Record a 3–5 minute walkthrough using [the timed demo script](docs/demo-script.md). Show the live dashboard, one API response in `/docs`, and a sample MySQL record with its source ID. Explain that phone coverage is sparse and be clear that the current dataset has 534 listings, not 1,000.

## Remaining limitations

- Phone coverage is 39/534 (7.3%); do not draw broad conclusions from the small phone-bearing sample.
- Every row is in Bengaluru and comes from OSM, so city/source comparisons have only one group.
- Postcodes are extracted only when present in the address; 358 addresses have no detected six-digit postcode.
- Eight `yes` categories may represent unclassified OSM tags. OSM provenance does not guarantee a phone number or address is current.
- The 1,000-record stretch target is not met.
