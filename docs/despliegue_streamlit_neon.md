# Despliegue Streamlit Cloud + Neon

## Flujo recomendado

1. Trabajar localmente con el Excel.
2. Cuando la base cambie, actualizar Neon:

```powershell
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\upload_to_neon.py
```

3. Subir a GitHub solo el codigo, nunca el Excel ni `.streamlit/secrets.toml`.
4. Configurar los secrets en Streamlit Cloud.

## Secrets para Streamlit Cloud

```toml
[app]
DATA_SOURCE = "neon"
DB_SCHEMA = "public"

[database]
url = "postgresql://USER:PASSWORD@HOST/neondb?sslmode=require"

[auth]
username = "evaluar"
password = "evaluar2026"
```

## Secrets locales

Para desarrollo local puedes usar:

```toml
[app]
DATA_SOURCE = "auto"
DB_SCHEMA = "public"

[database]
url = "postgresql://USER:PASSWORD@HOST/neondb?sslmode=require"

[auth]
username = "evaluar"
password = "evaluar2026"
```

Con `DATA_SOURCE = "auto"`, el dashboard usa el Excel local si existe. Si el Excel no existe, usa Neon.

## Seguridad

- `.streamlit/secrets.toml` esta ignorado por Git.
- Los archivos `.xlsx`, `.csv`, `.parquet`, `.db` y similares estan ignorados por Git.
- En Streamlit Cloud, la URL de Neon y la clave de acceso deben configurarse solo en la seccion Secrets.
- Si se comparte el repositorio, usar `.streamlit/secrets.example.toml` como plantilla sin credenciales reales.
