# Education Update Hub – Detail Crawler Fix

This package fixes the specific failure where the automation reads a recruitment listing/homepage but does not enter the job's detail/document page to locate the notification PDF.

## New flow

`source homepage/listing -> recruitment link -> detail/document page -> viewer/iframe/embed/CDN -> official PDF -> identity check -> field extraction -> post table`

The crawler is title-aware and validates the PDF against the exact recruitment title before copying any vacancy/qualification/salary/selection/date data. This is designed to prevent the cross-post contamination visible in older tables.

## Important files

- `bot/detail_crawler.py` – new multi-level crawler
- `bot/adapters/base.py` – uses the crawler for recruitment enrichment and resolves embedded/document PDFs
- `bot/adapters/sbi.py` – keeps SBI card-to-PDF association
- `bot/adapters/ibps.py` – keeps IBPS recruitment source handling
- `bot/adapters/uk.py` – handles UKPSC/UKSSSC document links
- `bot/sources.json` – canonical source library
- `sources.json` – synchronized copy for deployment clarity

## Install

Replace the existing `bot/` folder with this package's `bot/` folder. Keep your existing `bot/database/jobs.json` if you already have production data.

Run the GitHub Action manually once. Do not judge the result from the first 1–2 minutes; detail crawling and PDF extraction are intentionally slower than homepage-only scraping.

## What the system will NOT do

It will not invent missing values. If the exact recruitment notification cannot be verified, the table keeps the field as unavailable rather than copying a number or selection process from another post.
