# Análisis de Combustible – Flota Exalmar

Panel en Streamlit para analizar el consumo de combustible de la flota,
con modelos de predicción por embarcación (`modelos_navales/modelos_flota.joblib`).

## Fuentes de datos
| Base | Servidor | Uso |
|------|----------|-----|
| Indicadores | SQL Server interno | Metas |
| BD_TEL_FLOTA_PRD | Azure SQL (QAS) | Telemetría |

## Ejecutar en local
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env     # completar credenciales
streamlit run app_final.py
```
Abrir http://localhost:8501

## Ramas
| Rama | Uso |
|------|-----|
| `main` | Producción (despliega automáticamente a Azure) |
| `test` | Validación antes de producción |
| `develop` | Integración del trabajo diario |
| `feature/*`, `fix/*`, `docs/*` | Cambios puntuales; nacen de `develop` |

Flujo: `feature/...` → `develop` → `test` → `main`

## Despliegue
GitHub Actions (`.github/workflows/deploy.yml`) construye la imagen Docker,
la publica en Azure Container Registry y actualiza Azure Container Instances.
Las credenciales están en **Settings → Secrets and variables → Actions**.