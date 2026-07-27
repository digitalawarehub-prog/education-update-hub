import requests


def check_source(source):

    try:

        r = requests.get(

            source["url"],

            timeout=10

        )

        return r.status_code == 200

    except Exception:

        return False
# ==========================================================
# Monitoring Configuration
# ==========================================================

from pathlib import Path
from datetime import datetime
import json
import platform
import time

BASE_DIR = Path(__file__).resolve().parent

REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

HEALTH_FILE = REPORT_DIR / "health_report.json"
ERROR_FILE = REPORT_DIR / "failed_sources.json"

START_TIME = time.time()
# ==========================================================
# Health Report
# ==========================================================

def generate_health_report(jobs):

    report = {

        "generated_at": datetime.utcnow().isoformat(),

        "total_jobs": len(jobs),

        "python_version": platform.python_version(),

        "platform": platform.system(),

        "runtime_seconds": round(

            time.time() - START_TIME,

            2

        )

    }

    with open(

        HEALTH_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            report,

            f,

            indent=4,

            ensure_ascii=False

        )

    logger.info(

        "Health Report Saved"

    )

    return report
    # ==========================================================
# Failed Sources
# ==========================================================

def save_failed_sources(failed_sources):

    with open(

        ERROR_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            failed_sources,

            f,

            indent=4,

            ensure_ascii=False

        )

    logger.info(

        "Failed Sources Saved"

    )
    # ==========================================================
# Runtime Summary
# ==========================================================

def runtime_summary(report):

    logger.info("=" * 60)

    logger.info("Execution Summary")

    logger.info("=" * 60)

    logger.info(

        "Jobs : %d",

        report["total_jobs"]

    )

    logger.info(

        "Runtime : %.2f sec",

        report["runtime_seconds"]

    )

    logger.info(

        "Platform : %s",

        report["platform"]

    )

    logger.info(

        "Python : %s",

        report["python_version"]

    )

    logger.info("=" * 60)
    # ==========================================================
# Public API
# ==========================================================

def monitor_execution(jobs, failed_sources=None):

    if failed_sources is None:

        failed_sources = []

    report = generate_health_report(jobs)

    save_failed_sources(failed_sources)

    runtime_summary(report)

    return report


logger.info(
    "Monitoring System Ready"
)
