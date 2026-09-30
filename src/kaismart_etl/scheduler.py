"""Parte 8: automatizacion del pipeline de extraccion con la libreria ``schedule``.

Actua como orquestador: ejecuta ``run_etl`` de forma inmediata al arrancar y
luego cada ``SCHEDULE_INTERVAL_MINUTES`` minutos, de forma indefinida, hasta
que el proceso se detenga (Ctrl+C).
"""
from __future__ import annotations

import time

import schedule

from .config import settings
from .logging_config import get_logger
from .pipeline import run_etl

logger = get_logger(__name__)


def job() -> None:
    try:
        run_etl()
    except Exception:
        # Un fallo en una ejecucion programada no debe tumbar el orquestador:
        # se registra el error y se espera a la siguiente ejecucion programada.
        logger.exception("Fallo la ejecucion programada del pipeline ETL.")


def iniciar_scheduler() -> None:
    intervalo = settings.schedule_interval_minutes
    logger.info("Orquestador iniciado. Intervalo de ejecucion: %s minutos.", intervalo)

    schedule.every(intervalo).minutes.do(job)

    logger.info("Ejecutando el pipeline una primera vez de inmediato...")
    job()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Orquestador detenido manualmente (Ctrl+C).")


if __name__ == "__main__":
    iniciar_scheduler()
