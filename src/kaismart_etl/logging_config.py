
from __future__ import annotations

import logging
from pathlib import Path

from .config import settings


def get_logger(name: str) -> logging.Logger:
    settings.ensure_dirs()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # evita duplicar handlers si ya fue configurado

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        Path(settings.log_dir) / "kaismart_etl.log", encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
