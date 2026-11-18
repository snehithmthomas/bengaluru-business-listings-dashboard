import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mysql.connector import Error as MySQLError

from .config import get_cors_origins
from .database import connection
from .schemas import BulkListingsInput, CountRow, DashboardSummary


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Existing MySQL volumes do not rerun schema.sql. Keep the live table
    # compatible with the API's optional phone field before serving requests.
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE listing_master MODIFY COLUMN phone VARCHAR(64) NULL")
        cursor.close()
    yield


app = FastAPI(
    title="Bengaluru Business Listings API",
    description="Complete, source-linked business listings and dashboard aggregates.",
    version="1.0.0",
    lifespan=lifespan,
)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

LISTING_COLUMNS = (
    "business_name, category, city, address, phone, source, source_url, "
    "source_id, latitude, longitude, created_at"
)


def _database_error() -> HTTPException:
    return HTTPException(status_code=503, detail="Database is unavailable")


@app.get("/api/health")
def health() -> dict[str, str]:
    try:
        with connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return {"status": "ok", "database": "connected"}
    except MySQLError as exc:
        raise _database_error() from exc


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary() -> DashboardSummary:
    sql = """
        SELECT COUNT(*) AS total_listings,
               COUNT(DISTINCT category) AS categories,
               COUNT(DISTINCT source) AS sources,
               COUNT(CASE WHEN address <> '' AND phone <> '' THEN 1 END) AS addresses_with_phone
        FROM listing_master
    """
    try:
        with connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            row = cursor.fetchone() or {}
            cursor.close()
        return DashboardSummary(**{key: int(value or 0) for key, value in row.items()})
    except MySQLError as exc:
        raise _database_error() from exc


def _count_query(column: str) -> list[dict[str, object]]:
    # Column names are selected only from the fixed routes below.
    sql = f"SELECT {column} AS label, COUNT(*) AS count FROM listing_master GROUP BY {column} ORDER BY count DESC, label ASC"
    try:
        with connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
        return [{"label": str(row["label"]), "count": int(row["count"])} for row in rows]
    except MySQLError as exc:
        raise _database_error() from exc


@app.get("/api/dashboard/cities", response_model=list[CountRow])
def city_counts() -> list[dict[str, object]]:
    return _count_query("city")


@app.get("/api/dashboard/categories", response_model=list[CountRow])
def category_counts() -> list[dict[str, object]]:
    return _count_query("category")


@app.get("/api/dashboard/sources", response_model=list[CountRow])
def source_counts() -> list[dict[str, object]]:
    return _count_query("source")


@app.get("/api/listings")
def listings(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, object]]:
    try:
        with connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT {LISTING_COLUMNS} FROM listing_master ORDER BY business_name ASC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall()
            cursor.close()
        for row in rows:
            if row.get("created_at") is not None:
                row["created_at"] = row["created_at"].isoformat()
        return rows
    except MySQLError as exc:
        raise _database_error() from exc


@app.post("/api/listings/bulk")
def bulk_insert(payload: BulkListingsInput) -> dict[str, int]:
    sql = """
        INSERT INTO listing_master
          (business_name, category, city, address, phone, source, source_url,
           source_id, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS incoming
        ON DUPLICATE KEY UPDATE
          business_name = incoming.business_name,
          category = incoming.category,
          city = incoming.city,
          address = incoming.address,
          phone = incoming.phone,
          source_url = incoming.source_url,
          latitude = incoming.latitude,
          longitude = incoming.longitude
    """
    values = []
    for listing in payload.listings:
        item = listing.model_dump()
        source_url = str(item["source_url"])
        values.append(
            (
                item["business_name"], item["category"], item["city"], item["address"],
                item["phone"], item["source"], source_url,
                item["source_id"] or source_url,
                item["latitude"], item["longitude"],
            )
        )
    try:
        with connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, values)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
        return {"received": len(values), "database_rows_affected": affected}
    except MySQLError as exc:
        logger.exception("Bulk listing import failed in MySQL")
        raise _database_error() from exc
