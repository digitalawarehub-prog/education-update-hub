# ==========================================================
# Category Builder V4
# Part 1 : Imports + Configuration
# ==========================================================

import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("CategoryBuilderV4")

# ==========================================================
# Project Paths
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

TEMPLATE_FILE = (
    ROOT_DIR /
    "templates" /
    "category-template.html"
)

OUTPUT_DIR = ROOT_DIR

# ==========================================================
# Category Configuration
# ==========================================================

CATEGORIES = [

    {
        "file": "banking.html",
        "title": "Banking Jobs",
        "heading": "Latest Banking Jobs",
        "description": "Latest Banking Recruitment, IBPS, SBI, RBI, PNB and other bank job updates.",
        "keywords": "Bank Jobs, IBPS, SBI, RBI, PNB Recruitment",
        "category": "Banking Jobs"
    },

    {
        "file": "railway.html",
        "title": "Railway Jobs",
        "heading": "Latest Railway Jobs",
        "description": "Latest Railway Recruitment, RRB, RRC and Metro Rail Jobs.",
        "keywords": "Railway Jobs, RRB Recruitment, Railway Vacancy",
        "category": "Railway Jobs"
    },

    {
        "file": "upsc.html",
        "title": "UPSC Jobs",
        "heading": "Latest UPSC Recruitment",
        "description": "Latest UPSC Notifications, Civil Services, NDA, CDS and other UPSC Exams.",
        "keywords": "UPSC Recruitment, NDA, CDS, Civil Services",
        "category": "UPSC Jobs"
    },

    {
        "file": "ssc.html",
        "title": "SSC Jobs",
        "heading": "Latest SSC Recruitment",
        "description": "SSC CGL, CHSL, GD, MTS and other SSC Recruitment Updates.",
        "keywords": "SSC Jobs, SSC CGL, CHSL, GD",
        "category": "SSC Jobs"
    },

    {
        "file": "teacher-recruitment.html",
        "title": "Teacher Recruitment",
        "heading": "Latest Teacher Recruitment",
        "description": "Latest Teacher Vacancy, TGT, PGT, Lecturer and Education Department Jobs.",
        "keywords": "Teacher Recruitment, TGT, PGT, Lecturer",
        "category": "Teacher Recruitment"
    }

]

# ==========================================================
# Helper
# ==========================================================

def today():

    return datetime.today().strftime("%d-%m-%Y")

logger.info(
    "Category Builder V4 Part 1 Loaded Successfully"
)
# ==========================================================
# Category Builder V4
# Part 2 : Remaining Categories
# ==========================================================

CATEGORIES.extend([

    {
        "file": "ctet.html",
        "title": "CTET",
        "heading": "Latest CTET Updates",
        "description": "Latest CTET Notification, Admit Card, Answer Key and Result.",
        "keywords": "CTET, CTET Notification, CTET Result",
        "category": "CTET"
    },

    {
        "file": "utet.html",
        "title": "UTET",
        "heading": "Latest UTET Updates",
        "description": "Latest UTET Notification, Admit Card, Answer Key and Result.",
        "keywords": "UTET, UKTET, Uttarakhand TET",
        "category": "UTET"
    },

    {
        "file": "deled.html",
        "title": "D.El.Ed",
        "heading": "Latest D.El.Ed Updates",
        "description": "Latest D.El.Ed Admission, Counselling and Notification.",
        "keywords": "D.El.Ed, BTC, Diploma in Elementary Education",
        "category": "D.El.Ed"
    },

    {
        "file": "admit-card.html",
        "title": "Admit Card",
        "heading": "Latest Admit Cards",
        "description": "Download latest Government Exam Admit Cards.",
        "keywords": "Admit Card, Hall Ticket, Call Letter",
        "category": "Admit Card"
    },

    {
        "file": "result.html",
        "title": "Results",
        "heading": "Latest Results",
        "description": "Latest Government Exam Results and Merit Lists.",
        "keywords": "Result, Merit List, Score Card",
        "category": "Results"
    },

    {
        "file": "answer-key.html",
        "title": "Answer Key",
        "heading": "Latest Answer Keys",
        "description": "Latest Official Answer Keys for Government Exams.",
        "keywords": "Answer Key, Official Key",
        "category": "Answer Key"
    },

    {
        "file": "scholarship.html",
        "title": "Scholarship",
        "heading": "Latest Scholarship Updates",
        "description": "Government Scholarships, NSP and Financial Assistance Updates.",
        "keywords": "Scholarship, NSP, Financial Assistance",
        "category": "Scholarship"
    },

    {
        "file": "uttarakhand-jobs.html",
        "title": "Uttarakhand Jobs",
        "heading": "Latest Uttarakhand Government Jobs",
        "description": "Latest UKPSC, UKSSSC, UBSE and Uttarakhand Government Recruitment.",
        "keywords": "UKPSC, UKSSSC, Uttarakhand Jobs",
        "category": "Uttarakhand Jobs"
    },

    {
        "file": "central-government-jobs.html",
        "title": "Central Government Jobs",
        "heading": "Latest Central Government Jobs",
        "description": "Latest Central Government Recruitment and PSU Jobs.",
        "keywords": "Central Government Jobs, PSU Recruitment",
        "category": "Central Government Jobs"
    },

    {
        "file": "other-state-jobs.html",
        "title": "Other State Jobs",
        "heading": "Latest State Government Jobs",
        "description": "Latest Recruitment from various State Governments.",
        "keywords": "State Government Jobs, State Recruitment",
        "category": "Other State Jobs"
    }

])

logger.info(
    "Category Builder V4 Part 2 Loaded Successfully"
)
# ==========================================================
# Category Builder V4
# Part 3 : Template Loader + Placeholder Engine
# ==========================================================

# ==========================================================
# Load Template
# ==========================================================

def load_template():

    if not TEMPLATE_FILE.exists():

        raise FileNotFoundError(

            f"Template not found : {TEMPLATE_FILE}"

        )

    with open(

        TEMPLATE_FILE,

        "r",

        encoding="utf-8"

    ) as file:

        return file.read()


# ==========================================================
# Replace Placeholders
# ==========================================================

def replace_placeholders(

    template,

    category

):

    html = template

    replacements = {

        "{{PAGE_TITLE}}":
            category["title"],

        "{{PAGE_HEADING}}":
            category["heading"],

        "{{PAGE_DESCRIPTION}}":
            category["description"],

        "{{META_DESCRIPTION}}":
            category["description"],

        "{{KEYWORDS}}":
            category["keywords"],

        "{{CATEGORY_NAME}}":
            category["category"],

        "{{PAGE_FILE}}":
            category["file"],

        "{{LAST_UPDATED}}":
            today()

    }

    for key, value in replacements.items():

        html = html.replace(

            key,

            str(value)

        )

    return html


# ==========================================================
# Build Category HTML
# ==========================================================

def build_category_html(category):

    template = load_template()

    html = replace_placeholders(

        template,

        category

    )

    return html


# ==========================================================
# Preview Builder
# ==========================================================

def preview_category(category):

    logger.info(

        "Generating : %s",

        category["file"]

    )

    html = build_category_html(

        category

    )

    logger.info(

        "HTML Size : %d bytes",

        len(html)

    )

    return html


logger.info(
    "Category Builder V4 Part 3 Loaded Successfully"
)
# ==========================================================
# Category Builder V4
# Part 4 : File Writer + Page Generator
# ==========================================================

# ==========================================================
# Write HTML File
# ==========================================================

def write_category_file(category, html):

    output_file = OUTPUT_DIR / category["file"]

    with open(

        output_file,

        "w",

        encoding="utf-8"

    ) as file:

        file.write(html)

    logger.info(

        "Generated : %s",

        output_file.name

    )

    return output_file


# ==========================================================
# Generate Single Category
# ==========================================================

def generate_category(category):

    logger.info(

        "Building Category : %s",

        category["category"]

    )

    html = build_category_html(category)

    output = write_category_file(

        category,

        html

    )

    return output


# ==========================================================
# Generate All Categories
# ==========================================================

def generate_all_categories():

    generated = []

    failed = []

    for category in CATEGORIES:

        try:

            file = generate_category(category)

            generated.append(file)

        except Exception as error:

            logger.exception(

                "Failed : %s",

                category["file"]

            )

            failed.append({

                "file": category["file"],

                "error": str(error)

            })

    logger.info("=" * 60)

    logger.info(

        "Generated : %d",

        len(generated)

    )

    logger.info(

        "Failed : %d",

        len(failed)

    )

    logger.info("=" * 60)

    return {

        "generated": generated,

        "failed": failed

    }


# ==========================================================
# Verify Output
# ==========================================================

def verify_generated_pages():

    missing = []

    for category in CATEGORIES:

        file = OUTPUT_DIR / category["file"]

        if not file.exists():

            missing.append(

                category["file"]

            )

    if missing:

        logger.warning(

            "Missing Pages : %s",

            ", ".join(missing)

        )

    else:

        logger.info(

            "All Category Pages Generated Successfully."

        )

    return missing


logger.info(
    "Category Builder V4 Part 4 Loaded Successfully"
)
# ==========================================================
# Category Builder V4
# Part 5 : Incremental Build + Backup + Statistics
# ==========================================================

import shutil

BACKUP_DIR = ROOT_DIR / "backup" / "categories"

BACKUP_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================================
# Backup Category Page
# ==========================================================

def backup_category(category):

    source = OUTPUT_DIR / category["file"]

    if not source.exists():
        return

    destination = BACKUP_DIR / category["file"]

    shutil.copy2(
        source,
        destination
    )

    logger.info(
        "Backup : %s",
        source.name
    )


# ==========================================================
# File Changed Check
# ==========================================================

def file_changed(output_file, html):

    if not output_file.exists():
        return True

    old = output_file.read_text(
        encoding="utf-8"
    )

    return old != html


# ==========================================================
# Generate Only Changed Pages
# ==========================================================

def generate_changed_pages():

    updated = 0

    skipped = 0

    for category in CATEGORIES:

        html = build_category_html(
            category
        )

        output = OUTPUT_DIR / category["file"]

        if file_changed(
            output,
            html
        ):

            backup_category(
                category
            )

            write_category_file(
                category,
                html
            )

            updated += 1

        else:

            skipped += 1

    logger.info(
        "Updated : %d",
        updated
    )

    logger.info(
        "Skipped : %d",
        skipped
    )

    return {

        "updated": updated,

        "skipped": skipped

    }


# ==========================================================
# Statistics
# ==========================================================

def builder_statistics():

    logger.info("=" * 60)

    logger.info(
        "Category Builder Statistics"
    )

    logger.info("=" * 60)

    logger.info(
        "Total Categories : %d",
        len(CATEGORIES)
    )

    logger.info(
        "Output Directory : %s",
        OUTPUT_DIR
    )

    logger.info(
        "Backup Directory : %s",
        BACKUP_DIR
    )

    logger.info("=" * 60)


logger.info(
    "Category Builder V4 Part 5 Loaded Successfully"
)
# ==========================================================
# Category Builder V4
# Part 6 : Final Build + Validation + Runner
# ==========================================================

# ==========================================================
# Validate Template
# ==========================================================

def validate_template():

    if not TEMPLATE_FILE.exists():

        logger.error(
            "Template File Not Found : %s",
            TEMPLATE_FILE
        )

        return False

    logger.info(
        "Template Verified : %s",
        TEMPLATE_FILE.name
    )

    return True


# ==========================================================
# Build Category Pages
# ==========================================================

def build():

    logger.info("=" * 60)

    logger.info(
        "Starting Category Builder V4"
    )

    logger.info("=" * 60)

    if not validate_template():

        return False

    builder_statistics()
    for category in CATEGORIES:

        migrate_category_page(
            OUTPUT_DIR / category["file"]
        )
    result = generate_changed_pages()

    missing = verify_generated_pages()

    logger.info("=" * 60)

    logger.info(
        "Updated Pages : %d",
        result["updated"]
    )

    logger.info(
        "Skipped Pages : %d",
        result["skipped"]
    )

    logger.info(
        "Missing Pages : %d",
        len(missing)
    )

    logger.info("=" * 60)

    logger.info(
        "Category Builder Completed Successfully."
    )

    return {

        "success": True,

        "updated": result["updated"],

        "skipped": result["skipped"],

        "missing": missing

    }


# ==========================================================
# Main Runner
# ==========================================================

def run():

    try:

        return build()

    except Exception as error:

        logger.exception(
            "Category Builder Error : %s",
            error
        )

        return {

            "success": False,

            "error": str(error)

        }


# ==========================================================
# Execute
# ==========================================================

if __name__ == "__main__":

    run()


logger.info("=" * 60)
logger.info("Category Builder V4 Loaded Successfully")
logger.info("=" * 60)
# ==========================================================
# Auto Migration (Manual → Automation)
# ==========================================================

AUTO_SECTION = """
<div class="post-list">

<!-- AUTO_CATEGORY_START -->

<!-- AUTO_CATEGORY_END -->

</div>
"""

def migrate_category_page(file_path):

    if not file_path.exists():
        return False

    html = file_path.read_text(
        encoding="utf-8"
    )

    # Already migrated
    if "<!-- AUTO_CATEGORY_START -->" in html:
        return False

    start = html.find('<div class="post-list">')

    if start == -1:
        logger.warning(
            "post-list not found : %s",
            file_path.name
        )
        return False

    end = html.find(
        '<div id="footer">',
        start
    )

    if end == -1:
        logger.warning(
            "footer not found : %s",
            file_path.name
        )
        return False

    html = (
        html[:start]
        + AUTO_SECTION
        + "\n\n"
        + html[end:]
    )

    file_path.write_text(
        html,
        encoding="utf-8"
    )

    logger.info(
        "Migrated : %s",
        file_path.name
    )

    return True
