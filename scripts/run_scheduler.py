"""Parte 8: inicia el orquestador que automatiza el pipeline con la libreria
``schedule`` """
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


from kaismart_etl.scheduler import iniciar_scheduler  # noqa: E402

if __name__ == "__main__":
    iniciar_scheduler()
