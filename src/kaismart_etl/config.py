
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Raiz del proyecto = dos niveles arriba de este archivo (src/kaismart_etl/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Carga el archivo .env si existe (no falla si no existe, para poder usar
# variables de entorno reales en un servidor de automatizacion)
load_dotenv(PROJECT_ROOT / ".env")


def _path(env_var: str, default: str) -> Path:
    value = os.getenv(env_var, default)
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


@dataclass(frozen=True)
class MySQLSettings:
    host: str = os.getenv("MYSQL_HOST", "localhost")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    user: str = os.getenv("MYSQL_USER", "root")
    password: str = os.getenv("MYSQL_PASSWORD", "")
    database: str = os.getenv("MYSQL_DATABASE", "clientes")
    tabla_ventas: str = os.getenv("MYSQL_TABLE_VENTAS", "ventas")

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class Settings:
    mysql: MySQLSettings = MySQLSettings()
    excel_logistica_path: Path = _path(
        "EXCEL_LOGISTICA_PATH", "data/raw/kaismart_eventos_logisticos.xlsx"
    )
    bronze_dir: Path = _path("BRONZE_DIR", "data/bronze")
    silver_dir: Path = _path("SILVER_DIR", "data/silver")
    gold_dir: Path = _path("GOLD_DIR", "data/gold")
    log_dir: Path = _path("LOG_DIR", "logs")
    schedule_interval_minutes: int = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "60"))

    def ensure_dirs(self) -> None:
        for d in (self.bronze_dir, self.silver_dir, self.gold_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
