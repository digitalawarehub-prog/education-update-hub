# Education Update Hub – Full Detail Extraction Engine

This replacement uses a source-first extraction pipeline rather than copying values between posts.

## Detail priority
1. Official recruitment detail page structured tables (Label | Value).
2. Official detail-page sections.
3. The same post's official notification PDF, only after title/identity validation.
4. Conservative text fallback.

## Cross-post protection
Every recruitment record is cleared of old vacancy/qualification/salary/age/fee/selection/date/PDF fields before fresh enrichment. An unrelated PDF is rejected instead of supplying values.

## Important
This is an independent source-driven implementation. It is not a copy of any private Sarkari Result automation. Public portals can use different internal/manual workflows.
