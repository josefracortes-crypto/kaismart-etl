"""Conexion con la base de datos MySQL (Fuente 1: sistema comercial)."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

from .config import MySQLSettings, settings
from .logging_config import get_logger

logger = get_logger(__name__)


def get_mysql_engine(mysql_settings: MySQLSettings | None = None) -> Engine:
    """Crea (pero no abre) el Engine de SQLAlchemy hacia la base de datos MySQL."""
    mysql_settings = mysql_settings or settings.mysql
    logger.info(
        "Creando engine MySQL -> host=%s db=%s tabla=%s",
        mysql_settings.host,
        mysql_settings.database,
        mysql_settings.tabla_ventas,
    )
    return create_engine(mysql_settings.sqlalchemy_url, pool_pre_ping=True)


def test_connection(engine: Engine) -> bool:
    """Verifica que la conexion a la base de datos pueda establecerse."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
