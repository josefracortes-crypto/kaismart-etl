# Kaismart ETL — Evaluación de extracción, EDA y transformación (Medallion)

Proyecto en Python para Kaismart Solutions S.A.S.: extrae las dos fuentes de información de la compañía (sistema comercial en MySQL y sistema logístico en Excel), realiza una exploración inicial de calidad, y ejecuta un proceso de transformación e integración siguiendo la **metodología Medallion** (Bronze → Silver → Gold), con automatización mediante la librería `schedule`.

## Estructura del proyecto

```
kaismart-etl/
├── src/kaismart_etl/
│   ├── config.py              # Variables de entorno (.env)
│   ├── db.py                  # Conexión MySQL (SQLAlchemy + PyMySQL)
│   ├── extract.py              # Parte 1 y 2: extracción df_ventas / df_logistica
│   ├── quality.py              # Parte 3 y 4: comprensión y perfil de calidad
│   ├── stats.py                 # Parte 5: estadísticos descriptivos
│   ├── business_questions.py    # Parte 6: 10 preguntas de negocio
│   ├── catalogs.py              # Catálogos canónicos de categorías del negocio
│   ├── normalize.py             # Estandarización de texto/categorías
│   ├── transform/
│   │   ├── bronze.py            # Capa Bronze (datos crudos + trazabilidad)
│   │   ├── silver.py            # Capa Silver (limpieza documentada, Parte 7)
│   │   └── gold.py              # Capa Gold (integración por pedido_id + datamarts)
│   ├── pipeline.py               # Orquestador end-to-end del ETL
│   └── scheduler.py              # Parte 8: automatización con `schedule`
├── scripts/
│   ├── generate_mock_data.py     # Genera datos de prueba con problemas de calidad reales
│   ├── run_pipeline.py           # Corre el pipeline completo una vez
│   └── run_scheduler.py          # Inicia el orquestador periódico (Parte 8)
├── notebooks/
│   ├── 01_extraccion_y_eda.ipynb        # Partes 1 a 6
│   └── 02_transformacion_medallion.ipynb # Parte 7 (Bronze/Silver/Gold)
├── data/{raw,bronze,silver,gold}/
├── requirements.txt
└── .env.example
```

## Instalación

```powershell
cd kaismart-etl
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
Copy-Item .env.example .env   # y editar credenciales reales de MySQL
```

## Datos de prueba (opcional, si aún no tiene la BD/Excel reales)

El enunciado exige conectarse a una base de datos MySQL `clientes` (tabla `ventas`, 5.000 registros) y a un archivo `kaismart_eventos_logisticos.xlsx` (50.000 registros). Si aún no cuenta con esas fuentes, puede generar datos simulados con problemas de calidad inyectados a propósito (nulos, duplicados, categorías inconsistentes, tipos de dato incorrectos, outliers) para poder ejecutar y validar todo el proyecto:

```powershell
# Requiere un servidor MySQL accesible con las credenciales de .env
python scripts/generate_mock_data.py

# O bien, sin MySQL: solo genera el Excel + un respaldo CSV de ventas
python scripts/generate_mock_data.py --skip-mysql
```

## Uso

- **Notebooks** (recomendado para el ejercicio, Partes 1-7): abrir `notebooks/01_extraccion_y_eda.ipynb` y luego `notebooks/02_transformacion_medallion.ipynb` en VS Code / Jupyter.
- **Pipeline completo por línea de comandos**:
  ```powershell
  python scripts/run_pipeline.py
  ```
- **Automatización (Parte 8)**: ejecuta el pipeline de inmediato y luego cada `SCHEDULE_INTERVAL_MINUTES` (configurable en `.env`):
  ```powershell
  python scripts/run_scheduler.py
  ```

## Metodología Medallion

- **Bronze**: `df_ventas` y `df_logistica` se guardan tal cual llegan de las fuentes (`data/bronze/*.parquet`), solo con metadatos de trazabilidad.
- **Silver**: `silver.limpiar_ventas()` y `silver.limpiar_logistica()` producen `df_ventas_transformado` y `df_logistica_transformado`, aplicando de forma **documentada** (ver comentarios en `src/kaismart_etl/transform/silver.py`): eliminación de duplicados, estandarización de categorías, e imputación de nulos usando mediana/0/categoría "NO INFORMADO"/"SIN INCIDENCIA" o conservando el nulo, según el significado de negocio de cada variable.
- **Gold**: `gold.construir_gold_pedidos()` integra ambas fuentes por `pedido_id` y `gold.construir_marts()` genera datamarts agregados (ventas por ciudad/categoría, pedidos por estado logístico, KPIs por transportadora).

## Notas de diseño

- Cada decisión de imputación está comentada en el código explicando el motivo (mediana vs. media vs. moda vs. "NO INFORMADO" vs. conservar nulo), tal como lo exige la Parte 7 del ejercicio.
- Las funciones de `quality.py` (Parte 4) son de solo lectura: no eliminan ni imputan nada, solo diagnostican.
