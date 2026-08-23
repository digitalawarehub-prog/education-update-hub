Education Update Hub Auto Publisher - V5 Table Fix

This replacement fixes cross-post contamination in recruitment tables.

Main protections:
1. PDF/page source must match the post title before extracting vacancy,
   qualification, salary, age, fee, selection and dates.
2. Unrelated advertisement PDFs are rejected instead of being used as the
   notification for another post.
3. Fresh successful extraction is authoritative, so old contaminated values
   are cleared rather than preserved by the database merge.
4. Exam application-link posts no longer render a recruitment vacancy/salary
   table; they show exam/application details instead.
5. Existing known title-specific corrections remain intact.

Installation:
- Replace the existing GitHub bot/ folder with this bot/ folder.
- Run Auto Publisher once manually from GitHub Actions.
- Check a few affected posts after the run.
