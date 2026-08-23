# Education Update Hub – Deep Detail Extraction Engine

This replacement fixes the missing second/third navigation layer in recruitment extraction.

## Flow

1. Source/listing page is scanned for recruitment items.
2. The item's own detail/document page is opened.
3. The detail page is scanned for structured table/section data.
4. Notification links are resolved even when they do not end in `.pdf`.
5. Viewer wrappers are followed through `iframe`, `embed`, `object`, meta refresh and document links (maximum depth 2).
6. The resolved notification PDF is downloaded and parsed.
7. PDF identity is checked against the recruitment title before any fields are accepted.
8. Vacancy, qualification, salary, age, fee, selection process and dates are written only from the matching source.

## Important source-specific change

UKSSSC, PSC, IBPS, Railway, SSC and UPSC adapters now enrich their collected recruitment records before publishing. This prevents the monitor's small repair batch from being the only chance for a newly discovered post to receive its details.

SBI continues to use its card-level adapter because SBI puts the advertisement PDF and application link inside each opening card.

## Safety

- No unrestricted recursive crawl.
- No cross-post value copying.
- No recruitment table extraction for result/admit-card/answer-key/syllabus posts.
- Unrelated PDFs are rejected by title/PDF identity validation.
