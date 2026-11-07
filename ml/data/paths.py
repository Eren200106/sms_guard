"""Абсолютті жолдарға тәуелсіз болу үшін: барлық жол жоба түбірінен есептеледі."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
FIGURES = DOCS / "figures"
