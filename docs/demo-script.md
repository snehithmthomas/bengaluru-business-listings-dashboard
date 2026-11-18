# Demo video script (about 4 minutes)

Keep the dashboard and terminal/API docs ready before recording. The script describes the current project accurately: 534 prepared listings, 39 phones, and 1,000 as an unmet stretch target.

## 0:00–0:35 — Introduction and data source

**Show:** Dashboard home and the Bengaluru label.

**Say:** “This is a business listings dashboard built with React, FastAPI, and MySQL. I collected source-linked shop records from OpenStreetMap using the Overpass API within Bengaluru. The prepared dataset has 534 listings, which meets the assignment’s 500-plus requirement. I keep each OSM source ID so branches with the same name are not merged. I did not invent missing contact details.”

## 0:35–1:30 — Dashboard overview

**Show:** Summary cards and category chart. Hover over a chart bar to show its count and percentage.

**Say:** “The summary shows the listing total, category count, phone coverage, and how many records have coordinates. The category chart ranks the top 10 categories and reports each category’s share of the full dataset. Clothes is the largest group, followed by supermarkets and bakeries.”

## 1:30–2:15 — Map and location analysis

**Show:** Map, zoom or pan, then select one point to show its business and source ID. Show the postcode chart.

**Say:** “The map plots records using latitude and longitude. Selecting a point shows the business details and source ID. The postcode chart counts six-digit postcodes parsed from addresses; it only covers addresses where a postcode was present. The dashboard also flags repeated names while preserving separate source IDs.”

## 2:15–3:15 — Phone coverage and data quality

**Show:** Phone coverage KPI/chart and data quality panel.

**Say:** “Only 39 of 534 records have a phone number, about 7.3 percent. Phone is optional in the source data, so unavailable numbers stay null in MySQL. I treat the phone-bearing sample as small and avoid generalizing from it. The quality panel also calls out eight `yes` category tags and addresses without a detected postcode.”

## 3:15–4:05 — API and database

**Show:** `http://localhost:8000/docs`, open the summary endpoint, execute it, then show a listing endpoint response. If time allows, show one matching MySQL row or the SQL seed file.

**Say:** “FastAPI exposes a summary endpoint, grouped counts for cities, categories, and sources, a listings endpoint, and a bulk import endpoint. The bulk endpoint validates required fields and upserts records using source plus source ID. MySQL stores the listings, and the SQL dump can seed the prepared dataset.”

## 4:05–4:20 — Close

**Show:** Return to dashboard.

**Say:** “The dashboard demonstrates the full data flow from a documented source to MySQL, through FastAPI, to React charts. The current 534-record dataset meets the stated minimum; collecting 1,000 authorized records remains a stretch goal.”
