"""
=========================================================
Education Update Hub
Production Optimizer v4
=========================================================
"""

import hashlib
import logging
import re
from datetime import datetime

logger = logging.getLogger("Optimizer")

if not logger.handlers:
    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

# ==========================================================
# Category Mapping
# ==========================================================

CATEGORY_MAP = {
    "recruitment": "Recruitment",
    "vacancy": "Recruitment",
    "notification": "Recruitment",
    "admit": "Admit Card",
    "result": "Result",
    "answer key": "Answer Key",
    "syllabus": "Syllabus",
    "scholarship": "Scholarship",
}

# ==========================================================
# Department Rules
# ==========================================================

DEPARTMENT_RULES = {
    "Banking": [
        "bank",
        "ibps",
        "rbi",
        "nabard",
        "lic"
    ],

    "Railway": [
        "railway",
        "rrb",
        "rrc"
    ],

    "Defence": [
        "army",
        "navy",
        "air force",
        "drdo",
        "bsf",
        "crpf",
        "cisf",
        "itbp"
    ],

    "Teaching": [
        "teacher",
        "faculty",
        "lecturer",
        "professor",
        "principal"
    ],

    "Medical": [
        "medical",
        "doctor",
        "nurse",
        "pharmacist",
        "aiims"
    ]
}

logger.info("Optimizer Loaded Successfully")
