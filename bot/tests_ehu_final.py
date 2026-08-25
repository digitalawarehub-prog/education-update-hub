import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    ROOT / "monitor.py", ROOT / "html_generator.py", ROOT / "homepage.py",
    ROOT / "category_generator.py", ROOT / "url_utils.py", ROOT / "optimizer.py",
    ROOT / "parser.py", ROOT / "filters.py", ROOT / "adapters" / "base.py",
]
for path in FILES:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

from url_utils import slugify, post_relative_url
job = {"job_id": "abc123456789", "title": "A Very Long Recruitment Notification 2026 for Assistant Professor"}
slug = slugify(job["title"], job)
assert slug.endswith("abc123456789"[-10:])
assert post_relative_url(job).endswith(slug + ".html")

from homepage import build_latest_post
html = build_latest_post(job)
assert "latest-title-item" in html
assert "<img" not in html
assert "Read More" not in html

from filters import allow_job
assert not allow_job("Click Here For Details", "https://example.gov.in/recruitment")
assert allow_job("Assistant Professor Recruitment 2026", "https://example.gov.in/recruitment/notice.pdf")
print("EHU FINAL TESTS: OK")
