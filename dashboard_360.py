"""
Dashboard de EvaluaciÃ³n 360Â° â€” Evaluar.com
==========================================
EjecuciÃ³n:
    pip install streamlit pandas openpyxl plotly
    streamlit run dashboard_360.py

â•â• CONFIGURACIÃ“N DEL PROYECTO â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  Las dos constantes de abajo son los Ãºnicos valores que
  se deben editar al adaptar el dashboard a un nuevo proyecto.
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

import base64
import html as html_lib
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from reporte import calculos as motor_360
from reporte import potencial as motor_potencial
from reporte import objetivos as motor_objetivos
from reporte import db as data_db


ARCHIVO_BASE = next(
    Path(__file__).parent.glob("Fase_I_Evaluaci*n_360__180__90__copia_.xlsx"),
    Path(__file__).with_name("Fase_I_Evaluación_360__180__90__copia_.xlsx"),
)
VERSION_CARGA_BASE = 3
VERSION_CARGA_DB = 2

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CONFIGURACIÃ“N DEL PROYECTO â€” editar aquÃ­ si cambia el proyecto
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# TransformaciÃ³n de respuesta (escala 1-5) a puntaje interno
MAPA_PUNTAJE = motor_360.ESCALA_TRANSFORM

# Pesos de ponderaciÃ³n por tipo de relaciÃ³n (deben sumar 1.0)
PESOS_PONDERACION = motor_360.PESOS_BASE.copy()
assert abs(sum(PESOS_PONDERACION.values()) - 1.0) < 1e-9, "Los pesos deben sumar 100%"

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIGURACIÃ“N DE PÃGINA
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.set_page_config(
    page_title="Evaluaci\u00f3n 360 | Evaluar",
    page_icon="ðŸ“Š",
    layout="wide",
    initial_sidebar_state="expanded",
)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ESTILOS EVALUAR
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
EVALUAR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Topbar */
.ev-topbar {
    background: #1a1a3e;
    padding: 14px 24px;
    border-radius: 10px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ev-logo {
    font-size: 24px;
    font-weight: 700;
    color: white;
    letter-spacing: -0.5px;
}
.ev-logo-v {
    background: linear-gradient(90deg, #c13bc4, #f47c3c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.ev-cycle {
    background: rgba(255,255,255,0.15);
    color: white;
    font-size: 12px;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 500;
}

/* KPI cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}
.kpi-card {
    background: white;
    border: 0.5px solid #e8e4f4;
    border-radius: 10px;
    padding: 16px;
}
.kpi-label {
    font-size: 11px;
    color: #6b6b8a;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 600;
    color: #1a1a3e;
}
.kpi-value.gradient {
    background: linear-gradient(135deg, #6c3fc5, #e8357a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.kpi-value.green  { color: #185fa5; }  /* Alto desempeÃ±o = azul */
.kpi-sub { font-size: 11px; color: #6b6b8a; margin-top: 2px; }

/* Score chips â€” colores por escala de desempeÃ±o */
.chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
}
/* Alto desempeÃ±o  â‰¥ 90 â†’ azul */
.chip-alto  { background: #ddeeff; color: #0c447c; }
/* Satisfactorio  80â€“90 â†’ verde */
.chip-sat   { background: #e1f5ee; color: #085041; }
/* Bajo           70â€“80 â†’ Ã¡mbar */
.chip-bajo  { background: #faeeda; color: #633806; }
/* Insatisfactorio < 70 â†’ rojo */
.chip-insat { background: #fcebeb; color: #791f1f; }

/* SecciÃ³n */
.section-header {
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1.5px solid #e8e4f4;
}
.section-title {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a3e;
}
.section-sub {
    font-size: 13px;
    color: #6b6b8a;
    margin-top: 2px;
}

/* Tablas */
.ev-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.ev-table th {
    font-weight: 600;
    color: #6b6b8a;
    padding: 6px 10px;
    text-align: left;
    border-bottom: 0.5px solid #e8e4f4;
    background: #f8f7fc;
}
.ev-table td {
    padding: 7px 10px;
    border-bottom: 0.5px solid #e8e4f4;
    color: #1a1a3e;
}
.ev-table tr:last-child td { border-bottom: none; }
.ev-table tr:hover td { background: #f5f0ff; }
.ev-items-group td {
    padding: 10px;
    background: #f0ebff;
    border-top: 1px solid #d9cff2;
    border-bottom: 1px solid #d9cff2;
}
.ev-items-group:first-child td { border-top: none; }
.ev-items-group:hover td { background: #f0ebff !important; }
.ev-items-group-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}
.ev-items-group-name {
    color: #4f2c99;
    font-size: 13px;
    font-weight: 700;
}
.ev-items-group-meta {
    color: #6b6b8a;
    font-size: 11px;
    white-space: nowrap;
}
.ev-items-table th:last-child,
.ev-items-table td:last-child {
    width: 92px;
    text-align: right;
}

/* Sidebar */
.ev-sidebar-title {
    font-size: 13px;
    font-weight: 600;
    color: #1a1a3e;
    margin-bottom: 4px;
}

/* Ocultar elementos de Streamlit */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

/* Contenedor de filtros globales */
.ev-filter-container {
    background: white;
    border: 0.5px solid #e8e4f4;
    border-left: 3px solid #6c3fc5;
    border-radius: 10px;
    padding: 10px 16px 6px;
    margin-bottom: 8px;
}
.ev-filter-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 2px;
}
.ev-filter-icon {
    font-size: 13px;
    color: #6c3fc5;
}
.ev-filter-title {
    font-size: 12px;
    font-weight: 600;
    color: #1a1a3e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.ev-filter-hint {
    font-size: 11px;
    color: #9b9bb5;
    margin-left: 4px;
}
.ev-filter-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #f0ebff;
    color: #6c3fc5;
    font-size: 12px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 2px;
}

/* Filtros y pestaÃ±as se fijan solo despuÃ©s de alcanzar el borde superior */
.st-key-sticky_filtros_desempeno,
.st-key-sticky_filtros_potencial {
    background: white;
    padding-top: 4px;
    padding-bottom: 6px;
}
body.phase-controls-pinned .st-key-sticky_filtros_desempeno,
body.phase-controls-pinned .st-key-sticky_filtros_potencial {
    position: fixed;
    top: 0;
    left: 21.5rem;
    right: 4.5rem;
    z-index: 1000;
    background: white;
    box-shadow: 0 8px 12px -12px rgba(26, 26, 62, 0.35);
}
body.phase-controls-pinned [data-testid="stTabs"] [data-baseweb="tab-list"] {
    position: fixed;
    top: var(--phase-filter-height, 7.35rem);
    left: 21.5rem;
    right: 4.5rem;
    z-index: 999;
    background: white;
    padding-top: 4px;
    box-shadow: 0 8px 12px -12px rgba(26, 26, 62, 0.28);
}
.sticky-controls-spacer {
    height: 0;
}
body.phase-controls-pinned .sticky-controls-spacer {
    height: calc(var(--phase-filter-height, 7.35rem) + 3rem);
}
@media (max-width: 768px) {
    body.phase-controls-pinned .st-key-sticky_filtros_desempeno,
    body.phase-controls-pinned .st-key-sticky_filtros_potencial,
    body.phase-controls-pinned [data-testid="stTabs"] [data-baseweb="tab-list"] {
        left: 1rem;
        right: 1rem;
    }
    body.phase-controls-pinned [data-testid="stTabs"] [data-baseweb="tab-list"] {
        overflow-x: auto;
    }
}

/* Sidebar oscuro estilo Evaluar */
[data-testid="stSidebar"] {
    background: #1a1a3e !important;
}
/* Textos generales del sidebar en blanco */
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown strong,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown div {
    color: rgba(255,255,255,0.85) !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.12) !important;
}
/* File uploader: fondo blanco y textos oscuros */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: white;
    border-radius: 8px;
    padding: 6px;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] * {
    color: #1a1a3e !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
[data-testid="stSidebar"] [data-testid="stFileUploader"] p {
    color: #4a4a6a !important;
}
/* BotÃ³n calcular con degradado Evaluar */
[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(135deg, #c13bc4, #f47c3c) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
    opacity: 0.9;
}
/* LÃ­nea decorativa degradada bajo el logo */
.ev-sidebar-accent {
    height: 2px;
    background: linear-gradient(90deg, #c13bc4, #f47c3c);
    border-radius: 2px;
    margin: 12px 0 16px;
}

/* Navegador de fases â€” estilo custom */
.ev-nav {
    display: flex;
    gap: 6px;
    background: #1a1a3e;
    border-radius: 12px;
    padding: 8px;
    margin-bottom: 20px;
}
.ev-nav-btn {
    flex: 1;
    padding: 10px 12px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: rgba(255,255,255,0.55);
    background: transparent;
    transition: all 0.15s;
    text-align: center;
    white-space: nowrap;
}
.ev-nav-btn:hover {
    color: rgba(255,255,255,0.85);
    background: rgba(255,255,255,0.08);
}
.ev-nav-btn.active {
    background: white;
    color: #1a1a3e;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Bloques compactos para vistas con muchos colaboradores */
.ev-scroll-table {
    max-height: 360px;
    overflow-y: auto;
    border: 0.5px solid #e8e4f4;
    border-radius: 8px;
}
.ev-scroll-table table {
    margin: 0;
}
.ev-scroll-table thead th {
    position: sticky;
    top: 0;
    z-index: 1;
}
.ev-mini-note {
    color: #6b6b8a;
    font-size: 12px;
    margin: -4px 0 10px;
}
</style>
"""

st.markdown(EVALUAR_CSS, unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONSTANTES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
TIPO_LABEL = {
    "autoEvaluation":    "Autoevaluaci\u00f3n",
    "bossToSubordinate": "Jefe",
    "subordinateToBoss": "Subordinado",
    "peerToPeer":        "Pares",
    "insideClients":     "Cliente interno",
}

ESCALA_LABELS  = ["Alto desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"]
# Azul=alto >=90 | Verde=satisfactorio 80-90 | Ambar=bajo 70-80 | Rojo=insatisfactorio <70
ESCALA_COLORES = ["#185fa5", "#1d9e75", "#ba7517", "#a32d2d"]
ESCALA_FONDO   = ["#ddeeff",  "#e1f5ee", "#faeeda", "#fcebeb"]   # fondos para chips/bandas
ESCALA_TEXTO   = ["#0c447c",  "#085041", "#633806", "#791f1f"]   # textos sobre fondo claro
ESCALA_MIN     = [90, 80, 70, 0]

COLORES_TIPO = {
    "autoEvaluation":    "#6c3fc5",
    "bossToSubordinate": "#e8357a",
    "subordinateToBoss": "#f47c3c",
    "peerToPeer":        "#185fa5",
    "insideClients":     "#1d9e75",
}

PLOTLY_LAYOUT = dict(
    font_family="DM Sans",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=30, b=10),
)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def clean_comp_name(s: str) -> str:
    """Elimina el prefijo numÃ©rico del nombre de secciÃ³n (ej: '2.1 ')."""
    import re
    return re.sub(r"^\d+\.\d+\s*", "", str(s)).strip()


def get_escala(v: float) -> int:
    if v >= 90: return 0
    if v >= 80: return 1
    if v >= 70: return 2
    return 3


def score_color(v: float) -> str:
    return ESCALA_COLORES[get_escala(v)]


def chip_html(v: float) -> str:
    i = get_escala(v)
    bg, fg = ESCALA_FONDO[i], ESCALA_TEXTO[i]
    return f'<span class="chip" style="background:{bg};color:{fg}">{v:.2f}</span>'


def formato_peso(peso: float) -> str:
    return f"{peso * 100:.0f}%" if abs(peso * 100 - round(peso * 100)) < 0.01 else f"{peso * 100:.1f}%"


def etiquetas_tipo_con_pesos(df_comp: pd.DataFrame, tipos: list[str]) -> dict:
    pesos_por_tipo = {tipo: [] for tipo in tipos}
    for _, fila in df_comp.iterrows():
        presentes = [tipo for tipo in tipos if pd.notna(fila.get(f"tipo_{tipo}"))]
        if not presentes:
            continue
        pesos = motor_360.calcular_pesos_redistribuidos(presentes, PESOS_PONDERACION)
        for tipo, peso in pesos.items():
            pesos_por_tipo.setdefault(tipo, []).append(float(peso))

    etiquetas = {}
    for tipo in tipos:
        valores = pesos_por_tipo.get(tipo, [])
        if not valores:
            etiquetas[tipo] = TIPO_LABEL.get(tipo, tipo)
            continue
        minimo, maximo = min(valores), max(valores)
        if abs(minimo - maximo) < 0.0001:
            peso_txt = formato_peso(minimo)
        else:
            peso_txt = f"{formato_peso(minimo)}-{formato_peso(maximo)}"
        etiquetas[tipo] = f"{TIPO_LABEL.get(tipo, tipo)} ({peso_txt})"
    return etiquetas


def escala_label(v: float) -> str:
    return ESCALA_LABELS[get_escala(v)]


def escala_objetivos_label(v: float) -> str:
    if v >= 90:
        return "Alto Desempeño"
    if v >= 80:
        return "Desempeño satisfactorio"
    if v >= 70:
        return "Bajo desempeño"
    return "Desempeño insatisfactorio"


POTENCIAL_ESCALAS = ["Ajustado al perfil", "Cercano al perfil", "Alejado al perfil"]
POTENCIAL_COLORES = {
    "Ajustado al perfil": "#36a65c",
    "Cercano al perfil": "#f0c419",
    "Alejado al perfil": "#d94a45",
}
DISC_PALETA = [
    "#185fa5", "#1d9e75", "#e6a700", "#d95f59", "#7c5cc4",
    "#285b78", "#f47c3c", "#6c3fc5", "#2f9f8f", "#b64e82",
]
IQ_PALETA = ["#285b78", "#3f7ee8", "#1d9e75", "#e6a700", "#f47c3c", "#d95f59", "#7c5cc4"]
CURVA_DESARROLLO_DESCRIPCIONES = {
    10: "Extremadamente desarrollada",
    9: "Muy desarrollada",
    8: "Desarrollada",
    7: "Sobre la media",
    6: "Medio-Superior",
    5: "Medio",
    4: "Medio Inferior",
    3: "Poco desarrollada",
    2: "Muy poco desarrollada",
    1: "Casi Inexistente",
    0: "Inexistente",
}
def reparar_texto(texto: object) -> str:
    if texto is None or pd.isna(texto):
        return ""
    valor = str(texto)
    if any(marca in valor for marca in ("Ã", "Â", "â")):
        try:
            valor = valor.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return valor


def clave_texto(texto: object) -> str:
    valor = reparar_texto(texto)
    valor = unicodedata.normalize("NFKD", valor)
    valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
    valor = re.sub(r"[^a-zA-Z0-9]+", " ", valor).strip().casefold()
    return re.sub(r"\s+", " ", valor)


ORDEN_VALORES_POTENCIAL = [
    "Cultura Digital (Habilidad Digital)",
    "Alta Energía y dinamismo",
    "Ética profesional",
    "Proactividad",
    "Escucha activa",
    "Administración del tiempo",
    "Orden y la calidad (QA)",
    "Trabajo sin supervisión",
    "Responsabilidad",
    "Flexibilidad y Adaptabilidad",
    "Agresividad comercial (tipo cazador)",
    "Relaciones públicas",
    "Empatía",
    "Gestión de conflictos",
    "Orientación y adaptabilidad a las ventas",
    "Colaboración",
    "Inteligencia Emocional",
    "Gestión del riesgo/seguridad",
    "Trabajo en equipo",
    "Integridad",
    "Cumplimiento de Normas (Compliance)",
    "Construcción del conocimiento en equipo",
    "Orientación al Cliente",
    "Comunicación efectiva",
    "Habilidades de contacto",
    "Orientación / Asesoramiento",
    "Calidad del trabajo",
    "Negociación efectiva",
    "Discernimiento y criterio",
    "Escrupulosidad/Minuciosidad",
    "Administración de procesos",
    "Credibilidad técnica",
    "Productividad",
    "Búsqueda de datos e información",
    "Desarrollo de relaciones",
    "Resolución de problemas",
    "Gestión operativa",
    "Capacidad de planificación",
    "Trabajo bajo presión",
    "Impacto e influencia",
    "Iniciativa",
    "Pensamiento Analítico",
    "Capacidad de Gestión",
    "Orientación al Logro",
    "Asertividad",
    "Mejora continua",
    "Potencial de liderazgo",
    "Visión del Negocio",
    "Liderazgo ORIENTATIVO",
    "Didáctica",
    "Creatividad",
    "Innovación",
    "Pensamiento estratégico",
    "Desarrollo de equipo",
    "Autocontrol",
    "Liderazgo FACILITADOR",
    "Desarrollo de personas",
    "Gestión del riesgo",
    "Creación de equipos de alto rendimiento",
    "Toma de riesgos y decisiones",
    "Gestión estratégica del talento humano",
]


def color_valor_potencial(valor: float, limites: tuple[float, float]) -> tuple[str, str]:
    if pd.isna(valor):
        return "#f3f4f6", "#6b7280"
    if valor < limites[0]:
        return "#fcebeb", "#791f1f"
    if valor < limites[1]:
        return "#fff3cd", "#633806"
    return "#e1f5ee", "#085041"


def fig_valores_potencial(df: pd.DataFrame, limites: tuple[float, float]) -> go.Figure:
    datos = df[df["puntaje"].notna()].copy()
    datos["competencia"] = datos["competencia"].map(reparar_texto)
    altura = max(520, len(df) * 24)
    datos["color_barra"] = datos["puntaje"].apply(
        lambda valor: "#d94a45" if valor < limites[0] else "#f0c419" if valor < limites[1] else "#36a65c"
    )
    fig = go.Figure(go.Bar(
        x=datos["puntaje"],
        y=datos["competencia"],
        orientation="h",
        marker=dict(
            color=datos["color_barra"],
            line=dict(color="rgba(26,26,62,0.18)", width=0.6),
        ),
        text=datos["puntaje"].map(lambda valor: f"{valor:.2f}%"),
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>%{x:.2f}%<extra></extra>",
    ))
    fig.add_vrect(x0=0, x1=limites[0], fillcolor="#d94a45", opacity=0.20, line_width=0, layer="below")
    fig.add_vrect(x0=limites[0], x1=limites[1], fillcolor="#f0c419", opacity=0.25, line_width=0, layer="below")
    fig.add_vrect(x0=limites[1], x1=100, fillcolor="#36a65c", opacity=0.22, line_width=0, layer="below")
    layout_valores = {**PLOTLY_LAYOUT, "margin": dict(l=240, r=55, t=20, b=40)}
    fig.update_layout(
        **layout_valores,
        height=altura,
        showlegend=False,
        xaxis=dict(title="Promedio", range=[0, 103], ticksuffix="%", dtick=10, gridcolor="white"),
        yaxis=dict(
            title="",
            autorange="reversed",
            categoryorder="array",
            categoryarray=[reparar_texto(valor) for valor in ORDEN_VALORES_POTENCIAL],
            tickfont_size=10,
        ),
    )
    return fig


def fig_medidor_potencial(valor: float, limites: tuple[float, float]) -> go.Figure:
    """Medidor del promedio filtrado con bandas de la escala indicada."""
    limite_bajo, limite_alto = limites
    valor_grafico = float(valor) if pd.notna(valor) else 0.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor_grafico,
        number={"valueformat": ".2f", "font": {"size": 22, "color": "#1a1a3e"}},
        gauge={
            "axis": {"range": [0, 100], "visible": False},
            "bar": {"color": "rgba(0,0,0,0)"},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, limite_bajo], "color": "#d94a45"},
                {"range": [limite_bajo, limite_alto], "color": "#f0c419"},
                {"range": [limite_alto, 100], "color": "#36a65c"},
            ],
            "threshold": {
                "line": {"color": "#1a1a3e", "width": 4},
                "thickness": 0.8,
                "value": valor_grafico,
            },
        },
        domain={"x": [0.06, 0.94], "y": [0.05, 1]},
    ))
    fig.update_layout(
        height=210,
        margin=dict(l=12, r=12, t=8, b=8),
        paper_bgcolor="white",
        font_family="DM Sans",
    )
    return fig


def fig_escala_potencial(df: pd.DataFrame, columna: str) -> go.Figure:
    mapa_escala = {etiqueta.casefold(): etiqueta for etiqueta in POTENCIAL_ESCALAS}
    valores = (
        df[columna]
        .dropna()
        .astype(str)
        .str.strip()
        .str.casefold()
        .map(mapa_escala)
    )
    conteos = valores.value_counts().reindex(POTENCIAL_ESCALAS, fill_value=0)
    fig = go.Figure(go.Bar(
        x=POTENCIAL_ESCALAS,
        y=conteos.values,
        marker_color=[POTENCIAL_COLORES[escala] for escala in POTENCIAL_ESCALAS],
        text=conteos.values,
        textposition="outside",
        hovertemplate="%{x}<br>%{y} colaboradores<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=280,
        showlegend=False,
        xaxis=dict(tickfont_size=11),
        yaxis=dict(title="Colaboradores", gridcolor="#f0eef8", rangemode="tozero"),
    )
    return fig


def fig_distribucion_potencial(df: pd.DataFrame, dimension: str) -> go.Figure:
    conteos = (
        df[dimension]
        .fillna("Sin dato")
        .replace("", "Sin dato")
        .value_counts()
    )
    etiquetas_cortas = {
        "Macrotech Farmaceutica": "Macrotech",
        "RepÃºblica Dominicana": "R. Dominicana",
    }
    etiquetas = [etiquetas_cortas.get(str(valor), str(valor)) for valor in conteos.index]
    paleta = ["#3f7ee8", "#1d9e75", "#e6a700", "#d95f59", "#7c5cc4"]
    fig = go.Figure(go.Pie(
        labels=etiquetas,
        values=conteos.values,
        hole=0.52,
        sort=False,
        direction="clockwise",
        domain=dict(x=[0.08, 0.92], y=[0.08, 0.92]),
        marker=dict(colors=paleta[:len(conteos)], line=dict(color="white", width=2)),
        textposition="outside",
        texttemplate="%{label}<br>%{value} Â· %{percent}",
        textfont=dict(size=9),
        automargin=True,
        customdata=conteos.index,
        hovertemplate="%{customdata}<br>%{value} colaboradores<br>%{percent}<extra></extra>",
    ))
    layout_dona = {**PLOTLY_LAYOUT, "margin": dict(l=42, r=42, t=34, b=34)}
    fig.update_layout(
        **layout_dona,
        height=330,
        showlegend=False,
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    return fig


def fig_comparativo_potencial(df: pd.DataFrame) -> go.Figure:
    valores = [df["potencial_2025"].mean(), df["evaluacion_potencial"].mean()]
    coberturas = [df["potencial_2025"].notna().sum(), df["evaluacion_potencial"].notna().sum()]
    textos = [f"{valor:.2f}" if pd.notna(valor) else "Sin dato" for valor in valores]
    valores_validos = [valor for valor in valores if pd.notna(valor)]
    if valores_validos:
        eje_min = max(0, np.floor(min(valores_validos) * 2) / 2 - 1.5)
        eje_max = min(100, np.ceil(max(valores_validos) * 2) / 2 + 0.5)
        if eje_max - eje_min < 2:
            eje_min = max(0, eje_max - 2)
    else:
        eje_min, eje_max = 0, 100
    fig = go.Figure(go.Bar(
        x=["2025", "2026"],
        y=valores,
        marker_color=["#78a6f5", "#185fa5"],
        text=textos,
        textposition="outside",
        customdata=coberturas,
        hovertemplate="%{x}<br>Promedio %{y:.2f}<br>%{customdata} colaboradores<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=330,
        showlegend=False,
        yaxis=dict(
            title="Puntaje promedio",
            range=[eje_min, eje_max],
            dtick=0.5,
            tickformat=".1f",
            gridcolor="#e8e4f4",
        ),
        xaxis=dict(
            title="",
            type="category",
            tickmode="array",
            tickvals=["2025", "2026"],
            ticktext=["2025", "2026"],
            categoryorder="array",
            categoryarray=["2025", "2026"],
        ),
    )
    return fig


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MOTOR DE CÃLCULO
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def contar_arquetipos_disc(df: pd.DataFrame) -> pd.DataFrame:
    if "disc" not in df.columns:
        return pd.DataFrame(columns=["arquetipo", "colaboradores", "participacion"])
    conteos = (
        df["disc"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", np.nan)
        .dropna()
        .value_counts()
    )
    total = int(conteos.sum())
    if total == 0:
        return pd.DataFrame(columns=["arquetipo", "colaboradores", "participacion"])
    salida = conteos.rename_axis("arquetipo").reset_index(name="colaboradores")
    salida["participacion"] = salida["colaboradores"] / total
    return salida


def fig_disc_arquetipos(df_disc: pd.DataFrame) -> go.Figure:
    if df_disc.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT, height=420)
        return fig

    datos = df_disc.copy()
    maximo = int(datos["colaboradores"].max())
    rango_max = max(10, int(np.ceil(maximo / 10) * 10 + 10))
    colores = [DISC_PALETA[i % len(DISC_PALETA)] for i in range(len(datos))]
    theta = datos["arquetipo"].tolist() + [datos["arquetipo"].iloc[0]]
    valores = datos["colaboradores"].tolist() + [datos["colaboradores"].iloc[0]]

    fig = go.Figure(go.Scatterpolar(
        r=valores,
        theta=theta,
        mode="lines+markers+text",
        line=dict(color="#1a1a3e", width=2),
        fill="toself",
        fillcolor="rgba(24, 95, 165, 0.08)",
        marker=dict(
            size=9,
            color=colores + [colores[0]],
            line=dict(color="white", width=1.5),
        ),
        text=[f"{v}" for v in valores],
        textposition="top center",
        textfont=dict(size=10, color="#4a4a6a"),
        hovertemplate="%{theta}<br>%{r} colaboradores<extra></extra>",
        showlegend=False,
    ))
    layout = {**PLOTLY_LAYOUT, "margin": dict(l=55, r=55, t=34, b=34)}
    fig.update_layout(
        **layout,
        height=430,
        polar=dict(
            bgcolor="white",
            radialaxis=dict(
                range=[0, rango_max],
                gridcolor="#e8e4f4",
                tickfont_size=9,
                showline=False,
            ),
            angularaxis=dict(
                gridcolor="#f0eef8",
                tickfont_size=10,
                rotation=90,
                direction="clockwise",
            ),
        ),
    )
    return fig


def fig_disc_top_barras(df_disc: pd.DataFrame, top_n: int = 8) -> go.Figure:
    datos = df_disc.head(top_n).sort_values("colaboradores")
    colores = [DISC_PALETA[i % len(DISC_PALETA)] for i in range(len(datos))]
    fig = go.Figure(go.Bar(
        y=datos["arquetipo"],
        x=datos["colaboradores"],
        orientation="h",
        marker=dict(color=colores, line=dict(color="white", width=1)),
        text=datos["colaboradores"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>%{x} colaboradores<extra></extra>",
    ))
    layout = {**PLOTLY_LAYOUT, "margin": dict(l=145, r=45, t=12, b=28)}
    fig.update_layout(
        **layout,
        height=300,
        showlegend=False,
        xaxis=dict(title="Colaboradores", gridcolor="#f0eef8", rangemode="tozero"),
        yaxis=dict(title="", tickfont_size=10),
    )
    return fig


def _extraer_puntaje_iq(etiqueta: object) -> float:
    import re
    match = re.search(r"\d+(?:[.,]\d+)?", str(etiqueta))
    if not match:
        return np.nan
    return float(match.group(0).replace(",", "."))


def contar_iq(df: pd.DataFrame) -> pd.DataFrame:
    if "iq" not in df.columns:
        return pd.DataFrame(columns=["iq", "puntaje", "colaboradores", "participacion"])
    valores = (
        df["iq"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", np.nan)
        .dropna()
    )
    conteos = valores.value_counts()
    total = int(conteos.sum())
    if total == 0:
        return pd.DataFrame(columns=["iq", "puntaje", "colaboradores", "participacion"])
    salida = conteos.rename_axis("iq").reset_index(name="colaboradores")
    salida["puntaje"] = salida["iq"].apply(_extraer_puntaje_iq)
    salida["participacion"] = salida["colaboradores"] / total
    return salida.sort_values(["puntaje", "iq"], ascending=[True, True]).reset_index(drop=True)


def fig_iq_distribucion(df_iq: pd.DataFrame) -> go.Figure:
    datos = df_iq.copy()
    colores = [IQ_PALETA[i % len(IQ_PALETA)] for i in range(len(datos))]
    fig = go.Figure(go.Bar(
        y=datos["iq"],
        x=datos["colaboradores"],
        orientation="h",
        marker=dict(color=colores, line=dict(color="white", width=1)),
        text=datos["colaboradores"].astype(str) + " Â· " + datos["participacion"].map(lambda v: f"{v:.1%}"),
        textposition="outside",
        cliponaxis=False,
        customdata=np.stack([datos["puntaje"], datos["participacion"]], axis=-1),
        hovertemplate="%{y}<br>%{x} colaboradores<br>Puntaje %{customdata[0]:.0f}<br>%{customdata[1]:.1%}<extra></extra>",
    ))
    layout = {**PLOTLY_LAYOUT, "margin": dict(l=210, r=70, t=12, b=35)}
    fig.update_layout(
        **layout,
        height=max(300, len(datos) * 42 + 80),
        showlegend=False,
        xaxis=dict(title="Colaboradores", gridcolor="#f0eef8", rangemode="tozero", dtick=1),
        yaxis=dict(title="", tickfont_size=11),
    )
    return fig


def preparar_curva_desarrollo(df_competencias: pd.DataFrame, competencia: str) -> pd.DataFrame:
    if df_competencias.empty or "valor" not in df_competencias.columns:
        return pd.DataFrame(columns=["puntaje", "descripcion", "colaboradores", "participacion"])
    datos = df_competencias[df_competencias["competencia"] == competencia].copy()
    valores = pd.to_numeric(datos["valor"], errors="coerce").dropna()
    if valores.empty:
        return pd.DataFrame(columns=["puntaje", "descripcion", "colaboradores", "participacion"])
    puntajes = np.floor(valores).astype(int).clip(0, 10)
    conteos = puntajes.value_counts().reindex(range(0, 11), fill_value=0).sort_index()
    total = int(conteos.sum())
    tabla = pd.DataFrame({
        "puntaje": conteos.index.astype(int),
        "descripcion": [CURVA_DESARROLLO_DESCRIPCIONES[int(p)] for p in conteos.index],
        "colaboradores": conteos.values.astype(int),
    })
    tabla["participacion"] = tabla["colaboradores"] / total if total else 0
    return tabla


def fig_curva_desarrollo(tabla: pd.DataFrame, competencia: str) -> go.Figure:
    datos = tabla.copy()
    max_y = max(1, int(datos["colaboradores"].max()))
    x_curva = np.linspace(0, 10, 240)
    y_curva = np.exp(-0.5 * ((x_curva - 5) / 1.75) ** 2)
    y_curva = y_curva / y_curva.max() * max_y * 1.12

    fig = go.Figure()
    bandas = [
        (0, 1, "rgba(239, 83, 80, 0.30)"),
        (1, 2, "rgba(244, 115, 115, 0.30)"),
        (2, 3, "rgba(248, 173, 97, 0.34)"),
        (3, 4, "rgba(250, 202, 120, 0.38)"),
        (4, 5, "rgba(255, 237, 117, 0.45)"),
        (5, 6, "rgba(223, 237, 143, 0.42)"),
        (6, 7, "rgba(190, 226, 132, 0.40)"),
        (7, 8, "rgba(148, 218, 136, 0.38)"),
        (8, 9, "rgba(104, 203, 126, 0.36)"),
        (9, 10, "rgba(67, 181, 109, 0.34)"),
    ]
    for x0, x1, color in bandas:
        mascara = (x_curva >= x0) & (x_curva <= x1)
        x_segmento = x_curva[mascara]
        y_segmento = y_curva[mascara]
        if len(x_segmento):
            fig.add_trace(go.Scatter(
                x=x_segmento,
                y=y_segmento,
                mode="lines",
                line=dict(color="rgba(0,0,0,0)", width=0),
                fill="tozeroy",
                fillcolor=color,
                hoverinfo="skip",
                showlegend=False,
            ))

    fig.add_trace(go.Scatter(
        x=x_curva,
        y=y_curva,
        mode="lines",
        line=dict(color="#1a1a3e", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,0,0,0)",
        hoverinfo="skip",
        name="Curva de referencia",
    ))
    fig.add_trace(go.Scatter(
        x=datos["puntaje"],
        y=datos["colaboradores"],
        mode="lines+markers",
        line=dict(color="#1a1a3e", width=2),
        marker=dict(color="white", size=7, line=dict(color="#1a1a3e", width=1.5)),
        customdata=np.stack([datos["descripcion"], datos["participacion"]], axis=-1),
        hovertemplate="Puntaje %{x}<br>%{customdata[0]}<br>%{y} colaboradores<br>%{customdata[1]:.1%}<extra></extra>",
        showlegend=False,
    ))
    for _, fila in datos.iterrows():
        fig.add_annotation(
            x=int(fila["puntaje"]),
            y=int(fila["colaboradores"]),
            text=str(int(fila["colaboradores"])),
            showarrow=False,
            yshift=10,
            font=dict(size=11, color="#111827"),
            bgcolor="white",
            bordercolor="#1a1a3e",
            borderwidth=1,
            borderpad=2,
        )
    layout = {**PLOTLY_LAYOUT, "margin": dict(l=40, r=30, t=45, b=75)}
    fig.update_layout(
        **layout,
        height=460,
        title=dict(text=competencia, x=0.5, xanchor="center", font=dict(size=18)),
        showlegend=False,
        xaxis=dict(
            title="Escala de desarrollo",
            range=[-0.5, 10.5],
            tickmode="array",
            tickvals=list(range(0, 11)),
            gridcolor="rgba(255,255,255,0.60)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Colaboradores",
            rangemode="tozero",
            gridcolor="rgba(232,228,244,0.65)",
            side="right",
        ),
    )
    return fig


NINEBOX_COLORES = {
    1: "#00b050", 2: "#c6e0b4", 3: "#f2f2f2",
    4: "#5b9bd5", 5: "#ffc000", 6: "#f4b6e8",
    7: "#1f66d1", 8: "#c00000", 9: "#ff0000",
}
NINEBOX_LABELS = {
    1: "Super Estrella",
    2: "Alto potencial",
    3: "Potencial por activar",
    4: "Alto desempeño",
    5: "Talento clave",
    6: "Desarrollo dirigido",
    7: "Especialista",
    8: "Riesgo de desempeño",
    9: "Bajo ajuste",
}


def normalizar_nombre_match(nombre: object) -> str:
    texto = "" if nombre is None else str(nombre)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto).strip().casefold()
    return re.sub(r"\s+", " ", texto)


def preparar_ninebox(df_360_global: pd.DataFrame, df_potencial: pd.DataFrame) -> pd.DataFrame:
    desempeno = df_360_global[["colaborador", "global"]].copy()
    potencial = df_potencial[["colaborador", "evaluacion_potencial"]].copy()
    desempeno["match_nombre"] = desempeno["colaborador"].map(normalizar_nombre_match)
    potencial["match_nombre"] = potencial["colaborador"].map(normalizar_nombre_match)
    desempeno = desempeno.drop_duplicates("match_nombre")
    potencial = potencial.drop_duplicates("match_nombre")
    merged = desempeno.merge(
        potencial,
        on="match_nombre",
        how="inner",
        suffixes=("_360", "_potencial"),
    )
    merged = merged.dropna(subset=["global", "evaluacion_potencial"]).copy()
    merged = merged.rename(columns={
        "colaborador_360": "colaborador",
        "global": "desempeno_360",
        "evaluacion_potencial": "potencial",
    })
    return merged[["colaborador", "match_nombre", "potencial", "desempeno_360"]].sort_values("colaborador")


def cortes_ninebox(df_ninebox: pd.DataFrame) -> dict:
    potencial_prom = df_ninebox["potencial"].mean()
    potencial_std = df_ninebox["potencial"].std(ddof=1)
    desempeno_prom = df_ninebox["desempeno_360"].mean()
    desempeno_std = df_ninebox["desempeno_360"].std(ddof=1)
    return {
        "potencial_prom": potencial_prom,
        "potencial_std": potencial_std,
        "potencial_sup": potencial_prom + potencial_std,
        "potencial_inf": potencial_prom - potencial_std,
        "desempeno_prom": desempeno_prom,
        "desempeno_std": desempeno_std,
        "desempeno_sup": desempeno_prom + desempeno_std,
        "desempeno_inf": desempeno_prom - desempeno_std,
    }


def clasificar_ninebox(df_ninebox: pd.DataFrame, cortes: dict) -> pd.DataFrame:
    df = df_ninebox.copy()

    def nivel(valor: float, inferior: float, superior: float) -> str:
        if valor >= superior:
            return "alto"
        if valor < inferior:
            return "bajo"
        return "medio"

    def cuadrante(potencial: str, desempeno: str) -> int:
        mapa = {
            ("alto", "alto"): 1, ("alto", "medio"): 2, ("alto", "bajo"): 3,
            ("medio", "alto"): 4, ("medio", "medio"): 5, ("medio", "bajo"): 6,
            ("bajo", "alto"): 7, ("bajo", "medio"): 8, ("bajo", "bajo"): 9,
        }
        return mapa[(potencial, desempeno)]

    df["nivel_potencial"] = df["potencial"].apply(
        lambda v: nivel(v, cortes["potencial_inf"], cortes["potencial_sup"])
    )
    df["nivel_desempeno"] = df["desempeno_360"].apply(
        lambda v: nivel(v, cortes["desempeno_inf"], cortes["desempeno_sup"])
    )
    df["cuadrante"] = [
        cuadrante(pot, desp) for pot, desp in zip(df["nivel_potencial"], df["nivel_desempeno"])
    ]
    df["cuadrante_nombre"] = df["cuadrante"].map(NINEBOX_LABELS)
    return df


def matriz_ninebox(df_clasificado: pd.DataFrame) -> pd.DataFrame:
    filas = ["alto", "medio", "bajo"]
    columnas = ["bajo", "medio", "alto"]
    matriz = pd.crosstab(
        df_clasificado["nivel_potencial"],
        df_clasificado["nivel_desempeno"],
    ).reindex(index=filas, columns=columnas, fill_value=0)
    return matriz


def fig_ninebox(df_clasificado: pd.DataFrame) -> go.Figure:
    filas = ["alto", "medio", "bajo"]
    columnas = ["bajo", "medio", "alto"]
    z_cuadrantes = [[3, 2, 1], [6, 5, 4], [9, 8, 7]]
    conteos = matriz_ninebox(df_clasificado)
    z = [[z_cuadrantes[i][j] for j in range(3)] for i in range(3)]
    colorscale = []
    for idx, q in enumerate(range(1, 10)):
        pos = idx / 8
        colorscale.append([pos, NINEBOX_COLORES[q]])
        colorscale.append([pos, NINEBOX_COLORES[q]])

    total = max(len(df_clasificado), 1)
    fig = go.Figure(go.Heatmap(
        z=z,
        x=["Bajo desempeño", "Desempeño medio", "Alto desempeño"],
        y=["Alto potencial", "Potencial medio", "Bajo potencial"],
        colorscale=colorscale,
        showscale=False,
        hoverinfo="skip",
        xgap=4,
        ygap=4,
    ))
    for i, fila in enumerate(filas):
        for j, columna in enumerate(columnas):
            cuadrante = z_cuadrantes[i][j]
            conteo = int(conteos.loc[fila, columna])
            pct = conteo / total
            label = NINEBOX_LABELS[cuadrante]
            color_texto = "#ffffff" if cuadrante in {1, 4, 7, 8, 9} else "#07133a"
            fig.add_annotation(
                x=j,
                y=i,
                text=(
                    f"<b style='font-size:24px'>{conteo}</b><br>"
                    f"<span style='font-size:11px'>{label}</span><br>"
                    f"<span style='font-size:10px'>{pct:.1%}</span>"
                ),
                showarrow=False,
                font=dict(color=color_texto, size=13),
                align="center",
            )

    fig.update_layout(
        **{
            **PLOTLY_LAYOUT,
            "margin": dict(l=120, r=28, t=28, b=92),
            "height": 460,
            "paper_bgcolor": "#ffffff",
            "plot_bgcolor": "#ffffff",
        },
        xaxis=dict(
            title=dict(text="Desempeño 360", font=dict(size=13)),
            side="bottom",
            tickfont=dict(size=11),
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(text="Potencial", font=dict(size=13)),
            tickfont=dict(size=11),
            autorange="reversed",
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
    )
    return fig


def calcular(df: pd.DataFrame, weights: dict) -> dict:
    """Calcula el dashboard usando el motor compartido del proyecto."""
    res = motor_360.calcular_dashboard(df, weights)
    res["df_global"]["escala"] = res["df_global"]["escala_idx"].apply(lambda i: ESCALA_LABELS[i])
    return res


def leer_config_app(clave: str, default=None):
    app_config = st.secrets.get("app", {})
    if isinstance(app_config, Mapping) and clave in app_config:
        return app_config.get(clave, default)
    return st.secrets.get(clave, default)


def resolver_fuente_datos() -> str:
    fuente = str(leer_config_app("DATA_SOURCE", "auto")).strip().lower()
    if fuente not in {"auto", "excel", "neon"}:
        fuente = "auto"
    if fuente == "auto":
        return "excel" if ARCHIVO_BASE.exists() else "neon"
    return fuente


def obtener_credenciales_auth() -> tuple[str, str]:
    auth = st.secrets.get("auth", {})
    if not isinstance(auth, Mapping):
        auth = {}
    usuario = str(auth.get("username", "evaluar"))
    clave = str(auth.get("password", "evaluar2026"))
    return usuario, clave


def requerir_login() -> None:
    if st.session_state.get("autenticado"):
        return

    usuario_ok, clave_ok = obtener_credenciales_auth()

    try:
        svg_bytes = Path("brand_evaluar_on_dark.svg").read_bytes()
        svg_b64 = base64.b64encode(svg_bytes).decode("ascii")
        logo_login_html = (
            f'<img class="login-logo" src="data:image/svg+xml;base64,{svg_b64}" alt="Evaluar">'
        )
    except FileNotFoundError:
        logo_login_html = (
            '<span class="login-logo-fallback">'
            'e<span style="background:linear-gradient(90deg,#c13bc4,#f47c3c);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            'background-clip:text">v</span>aluar</span>'
        )

    st.markdown(
        f"""
        <style>
        div[data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at 50% 18%, rgba(232, 53, 122, 0.08), transparent 26%),
                linear-gradient(180deg, #ffffff 0%, #fbfbfe 100%);
        }}
        .login-shell {{
            display: block;
            padding: 9vh 12px 0;
        }}
        .login-card {{
            width: min(100%, 360px);
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #ebe7f6;
            border-radius: 18px 18px 0 0;
            box-shadow: 0 22px 64px rgba(26, 26, 62, 0.10);
            overflow: hidden;
        }}
        .login-brand {{
            background: #1a1a3e;
            padding: 30px 28px 26px;
            border-bottom: 3px solid transparent;
            border-image: linear-gradient(90deg, #c13bc4, #ff4b4b, #f47c3c) 1;
        }}
        .login-logo {{
            height: 42px;
            width: auto;
            display: block;
            margin: 0 auto;
        }}
        .login-logo-fallback {{
            display: block;
            text-align: center;
            font-size: 36px;
            font-weight: 700;
            color: white;
            letter-spacing: -0.5px;
        }}
        .login-body {{
            padding: 24px 28px 12px;
            text-align: center;
        }}
        .login-title {{
            color: #1a1a3e;
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .login-subtitle {{
            color: #6b6b8a;
            font-size: 13px;
            line-height: 1.45;
            margin-bottom: 6px;
        }}
        div[data-testid="stForm"] {{
            max-width: 360px;
            margin: -1px auto 0;
            padding: 4px 28px 28px;
            border: 1px solid #ebe7f6;
            border-top: 0;
            border-radius: 0 0 18px 18px;
            box-shadow: 0 22px 64px rgba(26, 26, 62, 0.10);
            background: #ffffff;
        }}
        div[data-testid="stForm"] label {{
            color: #1a1a3e;
            font-size: 12px;
            font-weight: 600;
        }}
        div[data-testid="stForm"] input {{
            border-radius: 10px;
            min-height: 42px;
        }}
        div[data-testid="stForm"] button {{
            border-radius: 10px;
            font-weight: 700;
            min-height: 42px;
            background: #ff4b4b;
            color: white;
            border: 0;
        }}
        div[data-testid="stForm"] button:hover {{
            background: #e8357a;
            color: white;
            border: 0;
        }}
        </style>
        <div class="login-shell">
            <div class="login-card">
                <div class="login-brand">{logo_login_html}</div>
                <div class="login-body">
                    <div class="login-title">Dashboard confidencial</div>
                    <div class="login-subtitle">
                        Accede con las credenciales autorizadas para consultar los resultados.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, centro, _ = st.columns([1, 1.05, 1])
    with centro:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Clave", type="password")
            enviar = st.form_submit_button("Ingresar", use_container_width=True)

    if enviar:
        if usuario == usuario_ok and clave == clave_ok:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos.")

    st.stop()


@st.cache_data(show_spinner="Cargando base local de talento...")
def cargar_base_excel(
    ruta: str, ultima_modificacion: int, version_carga: int
) -> tuple[dict, dict, dict]:
    """Carga ambas fases desde el Excel local."""
    del ultima_modificacion, version_carga
    df_desempeno = motor_360.leer_exportacion_dashboard(ruta)
    return (
        calcular(df_desempeno, PESOS_PONDERACION),
        motor_potencial.leer_potencial(ruta),
        motor_objetivos.leer_objetivos(ruta),
    )


@st.cache_data(show_spinner="Cargando base de talento desde Neon...")
def cargar_base_neon(database_url: str, schema: str, version_carga: int) -> tuple[dict, dict, dict]:
    """Carga ambas fases desde PostgreSQL y recalcula las metricas del dashboard."""
    del version_carga
    df_desempeno, res_potencial, res_objetivos = data_db.leer_base_dashboard(database_url, schema)
    return calcular(df_desempeno, PESOS_PONDERACION), res_potencial, res_objetivos


def cargar_datos_dashboard() -> tuple[dict, dict, dict, dict]:
    fuente = resolver_fuente_datos()
    if fuente == "excel":
        if not ARCHIVO_BASE.exists():
            raise FileNotFoundError(f"No se encontro el archivo base: {ARCHIVO_BASE.name}")
        res_local, potencial_local, objetivos_local = cargar_base_excel(
            str(ARCHIVO_BASE), ARCHIVO_BASE.stat().st_mtime_ns, VERSION_CARGA_BASE
        )
        return res_local, potencial_local, objetivos_local, {
            "tipo": "excel",
            "nombre": ARCHIVO_BASE.name,
            "detalle": "Desempeño - Potencial",
        }

    database_url = data_db.resolver_database_url(st.secrets)
    schema = str(leer_config_app("DB_SCHEMA", "public"))
    res_db, potencial_db, objetivos_db = cargar_base_neon(database_url, schema, VERSION_CARGA_DB)
    return res_db, potencial_db, objetivos_db, {
        "tipo": "neon",
        "nombre": "Neon PostgreSQL",
        "detalle": f"schema: {schema}",
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# GRÃFICOS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def fig_escala(df_global: pd.DataFrame) -> go.Figure:
    counts = [len(df_global[df_global["escala_idx"] == i]) for i in range(4)]
    fig = go.Figure(go.Bar(
        x=ESCALA_LABELS, y=counts,
        marker_color=ESCALA_COLORES,
        text=counts, textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=260,
                      xaxis=dict(tickfont_size=11),
                      yaxis=dict(title="Colaboradores", gridcolor="#f0eef8"))
    return fig


def fig_relaciones(rel_prom: dict) -> go.Figure:
    tipos  = [t for t in TIPO_LABEL if t in rel_prom]
    labels = [TIPO_LABEL[t] for t in tipos]
    vals   = [rel_prom[t] for t in tipos]

    # Bandas de fondo por escala â€” misma paleta que chips y barras
    BANDA_ALTO  = "rgba(24,  95, 165, 0.12)"   # azul  â€” â‰¥ 90
    BANDA_SAT   = "rgba(29, 158, 117, 0.12)"   # verde â€” 80â€“90
    BANDA_BAJO  = "rgba(186,117,  23, 0.12)"   # Ã¡mbar â€” 70â€“80
    BANDA_INSAT = "rgba(163, 45,  45, 0.12)"   # rojo  â€” < 70

    Y_MIN, Y_MAX = 60, 102

    fig = go.Figure()

    # â”€â”€ Bandas de fondo por escala â”€â”€
    bandas = [
        (90, Y_MAX, BANDA_ALTO,  "Alto desempeño"),
        (80, 90,    BANDA_SAT,   "Desempeño satisfactorio"),
        (70, 80,    BANDA_BAJO,  "Bajo desempeño"),
        (Y_MIN, 70, "rgba(163, 45, 45, 0.12)", "Desempeño insatisfactorio"),
    ]
    for y0, y1, color, nombre in bandas:
        fig.add_hrect(
            y0=y0, y1=y1,
            fillcolor=color,
            line_width=0,
            annotation_text=nombre,
            annotation_position="right",
            annotation=dict(font_size=9, font_color="#999", xanchor="left"),
        )

    # â”€â”€ LÃ­neas de corte sutiles â”€â”€
    for corte in [70, 80, 90]:
        fig.add_hline(
            y=corte,
            line_dash="dot",
            line_color="rgba(0,0,0,0.15)",
            line_width=1,
        )

    # â”€â”€ LÃ­nea de valores con marcadores â”€â”€
    fig.add_trace(go.Scatter(
        x=labels, y=vals,
        mode="lines+markers+text",
        line=dict(color="#1a1a3e", width=2.5),
        marker=dict(
            color=[score_color(v) for v in vals],
            size=10,
            line=dict(color="white", width=2),
        ),
        text=[f"{v:.2f}" for v in vals],
        textposition="top center",
        textfont=dict(size=12, color="#1a1a3e", family="DM Sans"),
        showlegend=False,
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        yaxis=dict(range=[Y_MIN, Y_MAX], gridcolor="rgba(0,0,0,0)", tickfont_size=11),
        xaxis=dict(tickfont_size=12, tickfont_color="#1a1a3e"),
    )
    return fig


def fig_comp_barras(df_comp_prom: pd.DataFrame) -> go.Figure:
    df = df_comp_prom.sort_values("prom_comp")
    fig = go.Figure(go.Bar(
        y=df["competencia"], x=df["prom_comp"],
        orientation="h",
        marker_color=[score_color(v) for v in df["prom_comp"]],
        text=[f"{v:.2f}" for v in df["prom_comp"]],
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
                      height=max(260, len(df) * 34 + 60),
                      xaxis=dict(range=[60, 105], gridcolor="#f0eef8"),
                      yaxis=dict(tickfont_size=11))
    return fig


def fig_radar(df_comp_prom: pd.DataFrame) -> go.Figure:
    cats  = df_comp_prom["competencia"].tolist()
    vals  = df_comp_prom["prom_comp"].tolist()
    cats  += [cats[0]]
    vals  += [vals[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats,
        fill="toself",
        line_color="#6c3fc5",
        fillcolor="rgba(108,63,197,0.12)",
        marker=dict(color="#6c3fc5", size=5),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=340,
        polar=dict(
            radialaxis=dict(range=[60, 100], tickfont_size=9, gridcolor="#e8e4f4"),
            angularaxis=dict(tickfont_size=10),
        ),
    )
    return fig


def fig_rel_comp(comp_rel: dict, competencias: list, tipo_labels: dict | None = None) -> go.Figure:
    tipos = [t for t in TIPO_LABEL if t in comp_rel]
    tipo_labels = tipo_labels or TIPO_LABEL
    fig = go.Figure()
    for tipo in tipos:
        vals = [comp_rel[tipo].get(c, None) for c in competencias]
        fig.add_trace(go.Bar(
            name=tipo_labels.get(tipo, TIPO_LABEL[tipo]), x=competencias, y=vals,
            marker_color=COLORES_TIPO.get(tipo, "#888"),
        ))
    layout = PLOTLY_LAYOUT.copy()
    layout["margin"] = dict(l=12, r=12, t=56, b=92)
    fig.update_layout(
        **layout,
        height=330,
        barmode="group",
        legend=dict(
            orientation="h",
            x=0,
            xanchor="left",
            y=1.18,
            yanchor="bottom",
            font_size=11,
        ),
        yaxis=dict(range=[60, 105], gridcolor="#f0eef8"),
        xaxis=dict(tickfont_size=10, tickangle=-35),
    )
    return fig


def fig_colab_ranking(
    df_global: pd.DataFrame,
    height: int | None = None,
    colaborador_sel: str | None = None,
) -> go.Figure:
    df = df_global.sort_values("global")
    line_colors = [
        "#1a1a3e" if colaborador_sel and colab == colaborador_sel else "rgba(0,0,0,0)"
        for colab in df["colaborador"]
    ]
    line_widths = [
        2 if colaborador_sel and colab == colaborador_sel else 0
        for colab in df["colaborador"]
    ]
    fig = go.Figure(go.Bar(
        y=df["colaborador"], x=df["global"],
        orientation="h",
        marker_color=[score_color(v) for v in df["global"]],
        marker_line_color=line_colors,
        marker_line_width=line_widths,
        text=[f"{v:.2f}" for v in df["global"]],
        textposition="outside",
    ))
    layout = PLOTLY_LAYOUT.copy()
    layout["margin"] = dict(l=12, r=48, t=24, b=24)
    fig.update_layout(
        **layout,
        height=height or max(220, min(520, len(df) * 28 + 80)),
        xaxis=dict(range=[60, 105], gridcolor="#f0eef8"),
        yaxis=dict(tickfont_size=10),
    )
    return fig


def fig_colab_radar(df_comp: pd.DataFrame, colaborador: str) -> go.Figure:
    df = df_comp[df_comp["colaborador"] == colaborador]
    cats = df["competencia"].tolist() + [df["competencia"].iloc[0]]
    vals = df["puntaje"].tolist()    + [df["puntaje"].iloc[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats,
        fill="toself",
        line_color="#e8357a",
        fillcolor="rgba(232,53,122,0.10)",
        marker=dict(color="#e8357a", size=5),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        polar=dict(
            radialaxis=dict(range=[60, 100], tickfont_size=9, gridcolor="#e8e4f4"),
            angularaxis=dict(tickfont_size=10),
        ),
    )
    return fig


def fig_objetivos_distribucion(df_colab: pd.DataFrame) -> go.Figure:
    bins = pd.cut(
        df_colab["puntaje"],
        bins=[-0.01, 69.99, 79.99, 89.99, 100.0],
        labels=["Desempeño insatisfactorio", "Bajo desempeño", "Desempeño satisfactorio", "Alto Desempeño"],
    )
    orden = ["Alto Desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"]
    colores = ["#1f66d1", "#00b050", "#ffc000", "#ff0000"]
    conteos = bins.value_counts().reindex(orden, fill_value=0)
    fig = go.Figure(go.Bar(
        x=orden,
        y=conteos.values,
        marker_color=colores,
        text=conteos.values,
        textposition="outside",
        hovertemplate="%{x}<br>%{y} colaboradores<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=280,
        showlegend=False,
        xaxis=dict(tickfont_size=11),
        yaxis=dict(title="Colaboradores", gridcolor="#f0eef8", rangemode="tozero"),
    )
    return fig


def fig_objetivos_bullet(promedio: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="number+gauge",
        value=float(promedio),
        number={"valueformat": ".0f", "font": {"size": 18, "color": "#1a1a3e"}},
        gauge={
            "shape": "bullet",
            "axis": {"range": [50, 100], "tickmode": "array", "tickvals": [50, 60, 70, 80, 90, 100]},
            "bar": {"color": "#1f3f77", "thickness": 0.42},
            "steps": [
                {"range": [50, 70], "color": "#ff7276"},
                {"range": [70, 80], "color": "#ffe180"},
                {"range": [80, 90], "color": "#7fd3a1"},
                {"range": [90, 100], "color": "#82a9e6"},
            ],
        },
        domain={"x": [0.05, 0.95], "y": [0.2, 0.85]},
        title={"text": "Evaluación Objetivos", "font": {"size": 16}},
    ))
    fig.update_layout(
        height=190,
        margin=dict(l=18, r=18, t=30, b=12),
        paper_bgcolor="white",
        font_family="DM Sans",
    )
    return fig


def fig_objetivos_dimension(df_dim: pd.DataFrame, dimension: str) -> go.Figure:
    datos = df_dim.sort_values("puntaje", ascending=True)
    fig = go.Figure(go.Bar(
        y=datos[dimension],
        x=datos["puntaje"],
        orientation="h",
        marker_color="#1f3f77",
        text=[f"{v:.0f}" for v in datos["puntaje"]],
        textposition="outside",
        customdata=datos[["colaboradores", "participacion"]],
        hovertemplate="%{y}<br>Promedio %{x:.2f}<br>%{customdata[0]} colaboradores<br>%{customdata[1]:.1%}<extra></extra>",
    ))
    fig.add_vrect(x0=50, x1=70, fillcolor="#ff7276", opacity=0.75, line_width=0, layer="below")
    fig.add_vrect(x0=70, x1=80, fillcolor="#ffe180", opacity=0.85, line_width=0, layer="below")
    fig.add_vrect(x0=80, x1=90, fillcolor="#7fd3a1", opacity=0.78, line_width=0, layer="below")
    fig.add_vrect(x0=90, x1=100, fillcolor="#82a9e6", opacity=0.85, line_width=0, layer="below")
    layout = PLOTLY_LAYOUT.copy()
    layout["margin"] = dict(l=20, r=42, t=34, b=32)
    fig.update_layout(
        **layout,
        height=max(260, len(datos) * 38 + 90),
        xaxis=dict(range=[50, 100], tickmode="array", tickvals=[50, 60, 70, 80, 90, 100], side="top"),
        yaxis=dict(title="", tickfont_size=11),
        showlegend=False,
    )
    return fig


def fig_objetivos_cargos(df_cargos: pd.DataFrame, top_n: int = 15) -> go.Figure:
    datos = df_cargos.sort_values("puntaje", ascending=True).tail(top_n)
    fig = go.Figure(go.Bar(
        y=datos["cargo_objetivo"],
        x=datos["puntaje"],
        orientation="h",
        marker_color=[score_color(v) for v in datos["puntaje"]],
        text=[f"{v:.2f}" for v in datos["puntaje"]],
        textposition="outside",
        customdata=datos[["colaboradores", "objetivos"]],
        hovertemplate="%{y}<br>Puntaje %{x:.2f}<br>%{customdata[0]} colaboradores<br>%{customdata[1]} objetivos<extra></extra>",
    ))
    layout = PLOTLY_LAYOUT.copy()
    layout["margin"] = dict(l=12, r=52, t=18, b=36)
    fig.update_layout(
        **layout,
        height=max(320, len(datos) * 30 + 80),
        xaxis=dict(title="Puntaje", range=[0, 105], gridcolor="#f0eef8"),
        yaxis=dict(tickfont_size=10),
        showlegend=False,
    )
    return fig


def fig_objetivos_colaboradores(df_colab: pd.DataFrame, top_n: int = 20) -> go.Figure:
    datos = df_colab.sort_values("puntaje", ascending=True).tail(top_n)
    fig = go.Figure(go.Bar(
        y=datos["colaborador"],
        x=datos["puntaje"],
        orientation="h",
        marker_color=[score_color(v) for v in datos["puntaje"]],
        text=[f"{v:.2f}" for v in datos["puntaje"]],
        textposition="outside",
        customdata=datos[["cargo_objetivo", "jefe", "objetivos"]],
        hovertemplate="%{y}<br>Puntaje %{x:.2f}<br>%{customdata[0]}<br>Jefe: %{customdata[1]}<br>%{customdata[2]} objetivos<extra></extra>",
    ))
    layout = PLOTLY_LAYOUT.copy()
    layout["margin"] = dict(l=12, r=52, t=18, b=36)
    fig.update_layout(
        **layout,
        height=max(360, len(datos) * 28 + 80),
        xaxis=dict(title="Puntaje", range=[0, 105], gridcolor="#f0eef8"),
        yaxis=dict(tickfont_size=10),
        showlegend=False,
    )
    return fig


def enriquecer_objetivos(
    df_colab: pd.DataFrame,
    df_fuente: pd.DataFrame,
    df_potencial_personas: pd.DataFrame,
) -> pd.DataFrame:
    df = df_colab.copy()
    potencial_cols = ["colaborador", "empresa", "pais", "grupo"]
    potencial = df_potencial_personas[
        [col for col in potencial_cols if col in df_potencial_personas.columns]
    ].copy()
    if not potencial.empty:
        potencial["match_nombre"] = potencial["colaborador"].map(normalizar_nombre_match)
        potencial = potencial.drop_duplicates("match_nombre")
        df["match_nombre"] = df["colaborador"].map(normalizar_nombre_match)
        df = df.merge(
            potencial.drop(columns=["colaborador"], errors="ignore"),
            on="match_nombre",
            how="left",
        )
    evaluadores = set(df_fuente["nombre_evaluador"].dropna().map(normalizar_nombre_match))
    df["gente_a_cargo"] = df["colaborador"].map(
        lambda nombre: "SI" if normalizar_nombre_match(nombre) in evaluadores else "NO"
    )
    for col in ["grupo", "empresa", "pais"]:
        if col not in df.columns:
            df[col] = "Sin dato"
        df[col] = df[col].fillna("Sin dato").replace("", "Sin dato")
    df["grupo"] = df["grupo"].astype(str).str.title()
    df["grupo"] = df["grupo"].replace({
        "Tácticos": "Tácticos",
        "No Aplica": "No aplica",
    })
    return df


def resumen_dimension_objetivos(df_colab: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if df_colab.empty:
        return pd.DataFrame(columns=[dimension, "puntaje", "colaboradores", "participacion"])
    total = max(1, df_colab["colaborador"].nunique())
    resumen = (
        df_colab.groupby(dimension, dropna=False)
        .agg(
            puntaje=("puntaje", "mean"),
            colaboradores=("colaborador", "nunique"),
        )
        .reset_index()
    )
    resumen["participacion"] = resumen["colaboradores"] / total
    return resumen.sort_values(["puntaje", "colaboradores"], ascending=[False, False])


def render_tabla_dimension_objetivos(
    titulo: str,
    df_resumen: pd.DataFrame,
    dimension: str,
    total_colab: int,
    promedio: float,
) -> None:
    st.markdown(f"**{titulo}**")
    html = '<div style="overflow-x:auto"><table class="ev-table">'
    html += (
        f"<thead><tr><th>{titulo}</th><th style='text-align:right'>Promedio de Objetivos</th>"
        "<th style='text-align:right'>Colaboradores</th><th style='text-align:right'>Participación</th></tr></thead><tbody>"
    )
    for _, fila in df_resumen.iterrows():
        etiqueta = html_lib.escape(str(fila[dimension]))
        html += (
            "<tr>"
            f"<td style='font-weight:600'>{etiqueta}</td>"
            f"<td style='text-align:right;color:#185fa5;font-weight:700'>{fila['puntaje']:.0f}</td>"
            f"<td style='text-align:right'>{int(fila['colaboradores'])}</td>"
            f"<td style='text-align:right'>{fila['participacion']:.0%}</td>"
            "</tr>"
        )
    html += (
        "<tr style='font-weight:700;background:#f8f7fc'>"
        "<td>Total general</td>"
        f"<td style='text-align:right;color:#185fa5'>{promedio:.0f}</td>"
        f"<td style='text-align:right'>{total_colab}</td>"
        "<td style='text-align:right'>100%</td>"
        "</tr></tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_tabla_escala_objetivos(df_colab: pd.DataFrame) -> None:
    st.markdown("**Escala de objetivos**")
    escala = pd.Series(index=[
        "Alto Desempeño",
        "Desempeño satisfactorio",
        "Bajo desempeño",
        "Desempeño insatisfactorio",
    ], dtype=int)
    etiquetas = pd.cut(
        df_colab["puntaje"],
        bins=[-0.01, 69.99, 79.99, 89.99, 100.0],
        labels=["Desempeño insatisfactorio", "Bajo desempeño", "Desempeño satisfactorio", "Alto Desempeño"],
    )
    conteos = etiquetas.value_counts().reindex(escala.index, fill_value=0)
    colores = {
        "Alto Desempeño": "#1f66d1",
        "Desempeño satisfactorio": "#00b050",
        "Bajo desempeño": "#ffc000",
        "Desempeño insatisfactorio": "#ff0000",
    }
    html = '<div style="overflow-x:auto"><table class="ev-table">'
    html += "<thead><tr><th>Escala de objetivos</th><th style='text-align:right'>Colaboradores</th></tr></thead><tbody>"
    for etiqueta, conteo in conteos.items():
        html += (
            "<tr>"
            f"<td style='font-weight:600;color:{colores[etiqueta]}'>{etiqueta}</td>"
            f"<td style='text-align:right'>{int(conteo)}</td>"
            "</tr>"
        )
    html += (
        "<tr style='font-weight:700;background:#f8f7fc'>"
        f"<td>Total general</td><td style='text-align:right'>{int(conteos.sum())}</td>"
        "</tr></tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def preparar_resultado_integrado(
    df_360_global: pd.DataFrame,
    df_obj_colab: pd.DataFrame,
    df_potencial: pd.DataFrame,
    df_obj_fuente: pd.DataFrame,
) -> pd.DataFrame:
    base_360 = df_360_global[["colaborador", "global"]].rename(
        columns={"colaborador": "colaborador_360", "global": "evd_360"}
    ).copy()
    base_obj = df_obj_colab[["colaborador", "puntaje", "cargo_objetivo", "jefe"]].rename(
        columns={"colaborador": "colaborador_obj", "puntaje": "objetivos"}
    ).copy()
    base_pot = df_potencial[
        [col for col in ["colaborador", "evaluacion_potencial", "empresa", "pais", "grupo"] if col in df_potencial.columns]
    ].rename(columns={"colaborador": "colaborador_pot", "evaluacion_potencial": "potencial"}).copy()

    for df, col_nombre in [
        (base_360, "colaborador_360"),
        (base_obj, "colaborador_obj"),
        (base_pot, "colaborador_pot"),
    ]:
        df["match_nombre"] = df[col_nombre].map(normalizar_nombre_match)
        df.drop_duplicates("match_nombre", inplace=True)

    integrado = base_360.merge(base_obj, on="match_nombre", how="outer")
    integrado = integrado.merge(base_pot, on="match_nombre", how="outer")
    integrado["colaborador"] = integrado["colaborador_360"].combine_first(integrado["colaborador_obj"])
    integrado["colaborador"] = integrado["colaborador"].combine_first(integrado["colaborador_pot"])

    evaluadores = set(df_obj_fuente["nombre_evaluador"].dropna().map(normalizar_nombre_match)) if not df_obj_fuente.empty else set()
    integrado["gente_a_cargo"] = integrado["colaborador"].map(
        lambda nombre: "SI" if normalizar_nombre_match(nombre) in evaluadores else "NO"
    )

    def etiqueta(row):
        tiene_360 = pd.notna(row.get("evd_360")) and row.get("evd_360") > 0
        tiene_obj = pd.notna(row.get("objetivos")) and row.get("objetivos") > 0
        tiene_pot = pd.notna(row.get("potencial")) and row.get("potencial") > 0
        if tiene_360 and tiene_obj and tiene_pot:
            return "Completa"
        if tiene_360 and tiene_obj:
            return "360+obj"
        if tiene_360 and tiene_pot:
            return "360+pot"
        if tiene_obj and tiene_pot:
            return "obj+pot"
        if tiene_360:
            return "Solo 360"
        if tiene_obj:
            return "Solo obj"
        if tiene_pot:
            return "Solo pot"
        return ""

    integrado["etiqueta_integrada"] = integrado.apply(etiqueta, axis=1)

    def calcular_integrada(row):
        etiqueta_val = row["etiqueta_integrada"]
        if etiqueta_val == "Completa":
            return round(row["evd_360"] * 0.30 + row["objetivos"] * 0.30 + row["potencial"] * 0.40, 0)
        if etiqueta_val == "360+obj":
            return round(row["evd_360"] * 0.50 + row["objetivos"] * 0.50, 0)
        if etiqueta_val == "360+pot":
            return round(row["evd_360"] * 0.60 + row["potencial"] * 0.40, 0)
        if etiqueta_val == "obj+pot":
            return round(row["objetivos"] * 0.60 + row["potencial"] * 0.40, 0)
        return np.nan

    integrado["integrada"] = integrado.apply(calcular_integrada, axis=1)
    integrado["escala_integrada"] = integrado["integrada"].apply(
        lambda valor: escala_objetivos_label(valor) if pd.notna(valor) else ""
    )
    for col in ["empresa", "pais", "grupo", "cargo_objetivo", "jefe"]:
        if col not in integrado.columns:
            integrado[col] = "Sin dato"
        integrado[col] = integrado[col].fillna("Sin dato").replace("", "Sin dato")
    return integrado.sort_values("integrada", ascending=False, na_position="last")


def resumen_dimension_integrada(df: pd.DataFrame, dimension: str, valor_col: str = "integrada") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[dimension, "puntaje", "colaboradores", "participacion"])
    total = max(1, df["colaborador"].nunique())
    resumen = (
        df.groupby(dimension, dropna=False)
        .agg(
            puntaje=(valor_col, "mean"),
            colaboradores=("colaborador", "nunique"),
        )
        .reset_index()
    )
    resumen["participacion"] = resumen["colaboradores"] / total
    return resumen.sort_values(["puntaje", "colaboradores"], ascending=[False, False])


def fig_integrada_bullet(promedio: float, titulo: str) -> go.Figure:
    fig = fig_objetivos_bullet(promedio)
    fig.update_traces(title={"text": titulo, "font": {"size": 15}})
    return fig


def fig_integrada_escala(df: pd.DataFrame) -> go.Figure:
    orden = ["Alto Desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"]
    colores = ["#1f66d1", "#00b050", "#ffc000", "#ff0000"]
    conteos = df["escala_integrada"].value_counts().reindex(orden, fill_value=0)
    fig = go.Figure(go.Bar(
        x=orden,
        y=conteos.values,
        marker_color=colores,
        text=conteos.values,
        textposition="outside",
        hovertemplate="%{x}<br>%{y} colaboradores<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=330,
        showlegend=False,
        xaxis=dict(tickfont_size=10),
        yaxis=dict(title="Colaboradores", gridcolor="#f0eef8", rangemode="tozero"),
    )
    return fig


CONFIG_INTEGRADO = {
    "Completa": {
        "tab": "360 + Objetivos + Potencial",
        "titulo": "Resultados integrados 360 + Objetivos + Potencial",
        "promedio": "Promedio Completa",
        "colaboradores": "Colaboradores Completa",
        "sub": "360 30% · Objetivos 30% · Potencial 40%",
        "detalle": [("evd_360", "360"), ("objetivos", "Obj."), ("potencial", "Pot.")],
    },
    "360+obj": {
        "tab": "360 + Objetivos",
        "titulo": "Resultados integrados 360 + Objetivos",
        "promedio": "Promedio 360+obj",
        "colaboradores": "Colaboradores 360+obj",
        "sub": "360 50% · Objetivos 50%",
        "detalle": [("evd_360", "360"), ("objetivos", "Obj.")],
    },
    "360+pot": {
        "tab": "360 + Potencial",
        "titulo": "Resultados integrados 360 + Potencial",
        "promedio": "Promedio 360+pot",
        "colaboradores": "Colaboradores 360+pot",
        "sub": "360 60% · Potencial 40%",
        "detalle": [("evd_360", "360"), ("potencial", "Pot.")],
    },
    "obj+pot": {
        "tab": "Objetivos + Potencial",
        "titulo": "Resultados integrados Objetivos + Potencial",
        "promedio": "Promedio obj+pot",
        "colaboradores": "Colaboradores obj+pot",
        "sub": "Objetivos 60% · Potencial 40%",
        "detalle": [("objetivos", "Obj."), ("potencial", "Pot.")],
    },
}


def render_tabla_escala_integrada(df: pd.DataFrame, titulo: str) -> None:
    orden = ["Alto Desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"]
    colores = {
        "Alto Desempeño": "#1f66d1",
        "Desempeño satisfactorio": "#00b050",
        "Bajo desempeño": "#ffc000",
        "Desempeño insatisfactorio": "#ff0000",
    }
    conteos = df["escala_integrada"].value_counts().reindex(orden, fill_value=0)
    html = '<div style="overflow-x:auto"><table class="ev-table">'
    html += f"<thead><tr><th>{html_lib.escape(titulo)}</th><th style='text-align:right'>Colaboradores</th></tr></thead><tbody>"
    for etiqueta, conteo in conteos.items():
        html += (
            "<tr>"
            f"<td style='font-weight:600;color:{colores[etiqueta]}'>{etiqueta}</td>"
            f"<td style='text-align:right'>{int(conteo)}</td>"
            "</tr>"
        )
    html += (
        "<tr style='font-weight:700;background:#f8f7fc'>"
        f"<td>Total general</td><td style='text-align:right'>{int(conteos.sum())}</td>"
        "</tr></tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def dimension_disponible(df: pd.DataFrame, candidatas: list[str]) -> list[str]:
    disponibles = []
    for col in candidatas:
        if col in df.columns and df[col].fillna("Sin dato").ne("Sin dato").any():
            disponibles.append(col)
    return disponibles


def render_resultado_integrado_tipo(
    df_base: pd.DataFrame,
    etiqueta: str,
    universo_total: int,
) -> None:
    config = CONFIG_INTEGRADO[etiqueta]
    df_tipo_base = df_base[df_base["etiqueta_integrada"] == etiqueta].copy()
    if df_tipo_base.empty:
        st.info(f"No hay colaboradores para {config['tab']} con la base actual.")
        return

    key_base = etiqueta.replace("+", "_").replace(" ", "_").lower()
    filtro_1, filtro_2, filtro_3 = st.columns(3)
    with filtro_1:
        filtro_colabs = st.multiselect(
            "Colaboradores",
            sorted(df_tipo_base["colaborador"].dropna().unique().tolist()),
            key=f"filtro_integrado_{key_base}_colabs",
            placeholder=f"Todos los colaboradores {config['tab']}",
        )
    with filtro_2:
        filtro_gente = st.multiselect(
            "Gente a cargo",
            sorted(df_tipo_base["gente_a_cargo"].dropna().unique().tolist()),
            key=f"filtro_integrado_{key_base}_gente",
            placeholder="Todos",
        )
    with filtro_3:
        filtro_escala = st.multiselect(
            "Escala integrada",
            ["Alto Desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"],
            key=f"filtro_integrado_{key_base}_escala",
            placeholder="Todas las escalas",
        )

    df_tipo = df_tipo_base.copy()
    if filtro_colabs:
        df_tipo = df_tipo[df_tipo["colaborador"].isin(filtro_colabs)]
    if filtro_gente:
        df_tipo = df_tipo[df_tipo["gente_a_cargo"].isin(filtro_gente)]
    if filtro_escala:
        df_tipo = df_tipo[df_tipo["escala_integrada"].isin(filtro_escala)]

    promedio = float(df_tipo["integrada"].mean()) if len(df_tipo) else 0.0
    total = len(df_tipo)
    alto = int((df_tipo["integrada"] >= 90).sum())

    kpi_i1, kpi_i2, kpi_i3, kpi_i4 = st.columns(4)
    with kpi_i1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{config['promedio']}</div>
            <div class="kpi-value gradient">{promedio:.0f}</div>
            <div class="kpi-sub">{config['sub']}</div>
        </div>""", unsafe_allow_html=True)
    with kpi_i2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{config['colaboradores']}</div>
            <div class="kpi-value">{total}</div>
            <div class="kpi-sub">con fuentes disponibles</div>
        </div>""", unsafe_allow_html=True)
    with kpi_i3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Alto desempeño</div>
            <div class="kpi-value green">{alto}</div>
            <div class="kpi-sub">integrada >= 90</div>
        </div>""", unsafe_allow_html=True)
    with kpi_i4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Participación</div>
            <div class="kpi-value">{(total / max(1, universo_total)):.0%}</div>
            <div class="kpi-sub">sobre universo integrado</div>
        </div>""", unsafe_allow_html=True)

    dimensiones = dimension_disponible(df_tipo, ["grupo", "cargo_objetivo", "pais", "empresa", "gente_a_cargo"])
    principal_dim = dimensiones[0] if dimensiones else "gente_a_cargo"
    df_principal = resumen_dimension_integrada(df_tipo, principal_dim)

    panel_izq, panel_centro, panel_der = st.columns([0.9, 1.55, 1.1])
    with panel_izq:
        render_tabla_escala_integrada(df_tipo, f"Escala {config['tab']}")
        for dim in dimensiones[:1]:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            render_tabla_dimension_objetivos(
                dim.replace("_", " ").title(),
                resumen_dimension_integrada(df_tipo, dim),
                dim,
                total,
                promedio,
            )
    with panel_centro:
        st.markdown(f"**{config['titulo']}**")
        st.plotly_chart(
            fig_integrada_bullet(promedio, config["titulo"]),
            use_container_width=True,
            key=f"integrado_bullet_{key_base}",
        )
        st.markdown(f"**Resultado por {principal_dim.replace('_', ' ')}**")
        st.plotly_chart(
            fig_objetivos_dimension(df_principal, principal_dim),
            use_container_width=True,
            key=f"integrado_dimension_{key_base}",
        )
        st.markdown("**Escala integrada**")
        st.plotly_chart(
            fig_integrada_escala(df_tipo),
            use_container_width=True,
            key=f"integrado_escala_{key_base}",
        )
    with panel_der:
        for dim in dimensiones[:3]:
            render_tabla_dimension_objetivos(
                dim.replace("_", " ").title(),
                resumen_dimension_integrada(df_tipo, dim),
                dim,
                total,
                promedio,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown(f"**Colaboradores {config['tab']}**")
        html = '<div class="ev-scroll-table"><table class="ev-table">'
        html += "<thead><tr><th>Colaborador</th>"
        for _, label in config["detalle"]:
            html += f"<th style='text-align:right'>{label}</th>"
        html += "<th>Nivel</th><th style='text-align:right'>Integrada</th></tr></thead><tbody>"
        for _, fila in df_tipo.sort_values("integrada", ascending=False).iterrows():
            html += "<tr>"
            html += f"<td style='font-weight:600'>{html_lib.escape(str(fila['colaborador']))}</td>"
            for col, _ in config["detalle"]:
                valor = fila.get(col)
                html += f"<td style='text-align:right'>{valor:.0f}</td>" if pd.notna(valor) else "<td style='text-align:right'>-</td>"
            html += f"<td>{html_lib.escape(str(fila['escala_integrada']))}</td>"
            html += f"<td style='text-align:right'>{chip_html(fila['integrada'])}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SIDEBAR
requerir_login()

try:
    res, res_potencial, res_objetivos, fuente_datos = cargar_datos_dashboard()
except Exception as exc:
    st.error(f"No se pudo cargar la base del dashboard: {exc}")
    st.stop()

with st.sidebar:
    # Logo: leer SVG y embeber como HTML para que funcione sobre fondo oscuro
    try:
        with open("brand_evaluar_on_dark.svg", "r", encoding="utf-8") as f:
            svg_content = f.read()
        st.markdown(
            f'<div style="padding:16px 8px 0">{svg_content}</div>',
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        # Fallback si el SVG no estÃ¡ en la misma carpeta
        st.markdown("""
        <div style="padding:16px 8px 0;text-align:center">
            <span style="font-size:26px;font-weight:700;color:white;letter-spacing:-0.5px">
                e<span style="background:linear-gradient(90deg,#c13bc4,#f47c3c);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text">v</span>aluar
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Linea decorativa degradada
    st.markdown('<div class="ev-sidebar-accent"></div>', unsafe_allow_html=True)

    st.markdown("**Fuente de datos**")
    st.markdown(
        f'<div style="font-size:11px;color:rgba(255,255,255,0.65);line-height:1.4">'
        f'{html_lib.escape(fuente_datos["nombre"])}<br>{html_lib.escape(fuente_datos["detalle"])}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ev-sidebar-accent"></div>', unsafe_allow_html=True)

    # Pesos activos - solo lectura
    st.markdown("**Pesos de ponderaci\u00f3n activos**")
    for tipo, peso in PESOS_PONDERACION.items():
        label = TIPO_LABEL.get(tipo, tipo)
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:12px;'
            f'color:rgba(255,255,255,0.6);padding:3px 0">'
            f'<span>{label}</span>'
            f'<span style="font-weight:600;color:rgba(255,255,255,0.9)">{int(peso*100)}%</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="ev-sidebar-accent"></div>', unsafe_allow_html=True)


# DASHBOARD
resumen_fuente = res.get("resumen_fuente", {})

try:
    with open("brand_evaluar_on_dark.svg", "r", encoding="utf-8") as f:
        _svg = f.read()
    _svg = _svg.replace("<svg ", '<svg style="height:32px;width:auto;display:block" ', 1)
    logo_html = _svg
except FileNotFoundError:
    logo_html = (
        '<span style="font-size:22px;font-weight:700;color:white;letter-spacing:-0.5px">'
        'e<span style="background:linear-gradient(90deg,#c13bc4,#f47c3c);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        'background-clip:text">v</span>aluar</span>'
    )

ciclo_limpio = str(res.get("ciclo", ""))

st.markdown(f"""
<div class="ev-topbar">
    <div style="display:flex;align-items:center">{logo_html}</div>
    <span class="ev-cycle">Fase I - Evaluaci\u00f3n 360 - {ciclo_limpio}</span>
</div>
""", unsafe_allow_html=True)

if resumen_fuente:
    etiqueta_fuente_resumen = (
        "Neon PostgreSQL"
        if fuente_datos.get("tipo") == "neon"
        else "exportacion original de Evaluar.com"
    )
    st.caption(
        f"Fuente: {etiqueta_fuente_resumen} - "
        f"{resumen_fuente['filas']} respuestas - "
        f"{resumen_fuente['colaboradores']} colaboradores - "
        f"{resumen_fuente['items']} items"
    )

FASES = [
    ("fase1", "Fase I - Evaluaci\u00f3n 360"),
    ("fase2", "Fase II - Potencial"),
    ("fase3", "Fase III - Objetivos"),
    ("res_int", "Resultado Integrado"),
    ("ninebox", "Ninebox"),
]

if "fase_activa" not in st.session_state:
    st.session_state.fase_activa = "fase1"

with st.container(key="sticky_phase_nav"):
    cols = st.columns(len(FASES))
    for col, (key, label) in zip(cols, FASES):
        with col:
            activa = st.session_state.fase_activa == key
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if activa else "secondary",
            ):
                st.session_state.fase_activa = key
                st.rerun()

fase_activa = st.session_state.fase_activa
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

if fase_activa == "fase1":
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    todos_colaboradores = sorted(res["df_global"]["colaborador"].tolist())
    with st.container(key="sticky_filtros_desempeno"):
        st.markdown("""
        <div class="ev-filter-container">
            <div class="ev-filter-header">
                <span class="ev-filter-icon"></span>
                <span class="ev-filter-title">Filtros de desempeño</span>
                <span class="ev-filter-hint">Aplican a toda la Fase I</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        filtro_f1, limpiar_f1 = st.columns([5, 1])
        with filtro_f1:
            filtro_colaboradores = st.multiselect(
                "Colaboradores",
                options=todos_colaboradores,
                placeholder="Todos los colaboradores",
                key="filtro_desempeno_colaboradores",
            )
        with limpiar_f1:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if filtro_colaboradores and st.button(
                "Limpiar", key="limpiar_filtro_desempeno", use_container_width=True
            ):
                st.session_state.filtro_desempeno_colaboradores = []
                st.rerun()
    st.markdown('<div class="sticky-controls-spacer"></div>', unsafe_allow_html=True)

    colabs_activos = filtro_colaboradores if filtro_colaboradores else todos_colaboradores
    df_global_f = res["df_global"][res["df_global"]["colaborador"].isin(colabs_activos)].copy()
    df_comp_f = res["df_comp"][res["df_comp"]["colaborador"].isin(colabs_activos)].copy()
    df_fuente_f = res["df_fuente"][
        res["df_fuente"]["nombre_colaborador"].isin(colabs_activos)
    ].copy()
    df_items_f = motor_360.calcular_items(df_fuente_f, PESOS_PONDERACION)

    if len(df_comp_f):
        df_global_f = (
            df_comp_f.groupby("colaborador")["puntaje"]
            .mean()
            .reset_index()
            .rename(columns={"puntaje": "global"})
            .sort_values("global", ascending=False)
        )
        df_global_f["escala_idx"] = df_global_f["global"].apply(motor_360._idx_escala)
        df_global_f["escala"] = df_global_f["escala_idx"].apply(lambda i: ESCALA_LABELS[i])

        df_comp_prom_f = (
            df_comp_f.groupby("competencia")["puntaje"]
            .mean().reset_index()
            .rename(columns={"puntaje": "prom_comp"})
            .sort_values("prom_comp", ascending=False)
        )
        rel_prom_f = {}
        comp_rel_f = {}
        for tipo in res["tipos_activos"]:
            col_t = f"tipo_{tipo}"
            if col_t in df_comp_f.columns:
                valores_tipo = df_comp_f[col_t].dropna()
                if len(valores_tipo):
                    rel_prom_f[tipo] = valores_tipo.mean()
                comp_rel_f[tipo] = (
                    df_comp_f.groupby("competencia")[col_t].mean().dropna().to_dict()
                )
        tipo_labels_pesos_f = etiquetas_tipo_con_pesos(df_comp_f, list(res["tipos_activos"].keys()))
    else:
        df_comp_prom_f = res["df_comp_prom"]
        rel_prom_f = res["rel_prom"]
        comp_rel_f = res["comp_rel"]
        tipo_labels_pesos_f = TIPO_LABEL

    # KPIs de Fase I
    total_colab = len(df_global_f)
    prom_global = df_global_f["global"].mean() if len(df_global_f) else 0
    n_alto      = len(df_global_f[df_global_f["global"] >= 90])
    n_comp      = len(df_comp_prom_f)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Promedio global 360</div>
            <div class="kpi-value gradient">{prom_global:.2f}</div>
            <div class="kpi-sub">{escala_label(prom_global)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Colaboradores</div>
            <div class="kpi-value">{total_colab}</div>
            <div class="kpi-sub">{"seleccionado" if total_colab == 1 else "evaluados"}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Competencias</div>
            <div class="kpi-value">{n_comp}</div>
            <div class="kpi-sub">evaluadas</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Alto desempeño</div>
            <div class="kpi-value green">{n_alto}</div>
            <div class="kpi-sub">colaboradores >= 90</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Subtabs de Fase I
    sub_res, sub_comp, sub_rel, sub_colab, sub_items = st.tabs([
        "Resumen",
        "Competencias",
        "Por relaci\u00f3n",
        "Colaboradores",
        "\u00cdtems",
    ])

    # â”€â”€ Subtab: Resumen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with sub_res:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Distribución por escala de desempeño**")
            st.plotly_chart(fig_escala(df_global_f), use_container_width=True, key="res_escala")
        with col_b:
            st.markdown("**Promedio por tipo de relaci\u00f3n**")
            st.plotly_chart(fig_relaciones(rel_prom_f), use_container_width=True, key="res_relaciones")

        col_c, col_d = st.columns(2)
        comp_sorted = df_comp_prom_f.sort_values("prom_comp", ascending=False)
        with col_c:
            st.markdown("**Top competencias**")
            for _, row in comp_sorted.head(4).iterrows():
                v = row["prom_comp"]
                pct = int((v - 65) / 35 * 100)
                color = score_color(v)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                    <span style="font-size:12px;color:#6b6b8a;flex:1;min-width:0;overflow:hidden;
                        text-overflow:ellipsis;white-space:nowrap" title="{row['competencia']}">{row['competencia']}</span>
                    <div style="width:100px;height:6px;background:#e8e4f4;border-radius:3px;overflow:hidden">
                        <div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>
                    </div>
                    <span style="font-size:13px;font-weight:600;color:{color};min-width:38px">{v:.2f}</span>
                </div>""", unsafe_allow_html=True)
        with col_d:
            st.markdown("**Competencias a fortalecer**")
            for _, row in comp_sorted.tail(4).sort_values("prom_comp").iterrows():
                v = row["prom_comp"]
                pct = int((v - 65) / 35 * 100)
                color = score_color(v)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                    <span style="font-size:12px;color:#6b6b8a;flex:1;min-width:0;overflow:hidden;
                        text-overflow:ellipsis;white-space:nowrap" title="{row['competencia']}">{row['competencia']}</span>
                    <div style="width:100px;height:6px;background:#e8e4f4;border-radius:3px;overflow:hidden">
                        <div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>
                    </div>
                    <span style="font-size:13px;font-weight:600;color:{color};min-width:38px">{v:.2f}</span>
                </div>""", unsafe_allow_html=True)

    # â”€â”€ Subtab: Competencias â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with sub_comp:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Puntaje por competencia**")
            st.plotly_chart(fig_comp_barras(df_comp_prom_f), use_container_width=True, key="comp_barras")
        with col_b:
            st.markdown("**Radar de competencias**")
            st.plotly_chart(fig_radar(df_comp_prom_f), use_container_width=True, key="comp_radar")

        st.markdown("**Detalle por colaborador x competencia**")
        df_pivot = df_comp_f.pivot_table(index="colaborador", columns="competencia", values="puntaje").reset_index()
        df_pivot["__g"] = df_pivot.iloc[:, 1:].mean(axis=1, numeric_only=True)
        df_pivot = df_pivot.sort_values("__g", ascending=False).drop(columns="__g")
        comp_cols = [c for c in df_pivot.columns if c != "colaborador"]
        html  = '<div style="overflow-x:auto"><table class="ev-table"><thead><tr>'
        html += '<th>Colaborador</th><th>Global</th>' + "".join(f"<th>{c}</th>" for c in comp_cols) + "</tr></thead><tbody>"
        for _, row in df_pivot.iterrows():
            html += f'<tr><td style="font-weight:500">{row["colaborador"]}</td><td>{chip_html(row[comp_cols].mean())}</td>'
            for c in comp_cols:
                v = row[c]
                html += f"<td>{chip_html(v)}</td>" if pd.notna(v) else "<td style='color:#aaa;text-align:center'>&mdash;</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)

    # â”€â”€ Subtab: Por relaciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with sub_rel:
        col_a, col_b = st.columns(2)
        competencias_f = df_comp_prom_f["competencia"].tolist()
        with col_a:
            st.markdown("**Promedio global por tipo de relaci\u00f3n**")
            st.plotly_chart(fig_relaciones(rel_prom_f), use_container_width=True, key="rel_relaciones")
        with col_b:
            st.markdown("**Competencias x relaci\u00f3n**")
            st.plotly_chart(
                fig_rel_comp(comp_rel_f, competencias_f, tipo_labels_pesos_f),
                use_container_width=True,
                key="rel_comp",
            )

        st.markdown("**Tabla: promedio por competencia y relaci\u00f3n**")
        tipos_con_datos = [t for t in TIPO_LABEL if t in comp_rel_f]
        html  = '<div style="overflow-x:auto"><table class="ev-table"><thead><tr><th>Competencia</th>'
        html += "".join(f"<th>{tipo_labels_pesos_f.get(t, TIPO_LABEL[t])}</th>" for t in tipos_con_datos) + "</tr></thead><tbody>"
        for comp in competencias_f:
            html += f'<tr><td style="font-weight:500">{comp}</td>'
            for t in tipos_con_datos:
                v = comp_rel_f.get(t, {}).get(comp)
                html += f"<td>{chip_html(v)}</td>" if v is not None else "<td style='color:#aaa;text-align:center'>&mdash;</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)

    # â”€â”€ Subtab: Colaboradores â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with sub_colab:
        opciones_colab = df_global_f.sort_values("global", ascending=False)["colaborador"].tolist()
        if opciones_colab:
            control_colab, control_top = st.columns([3, 1])
            with control_colab:
                colaborador_sel = st.selectbox(
                    "Detalle individual",
                    options=opciones_colab,
                    key="colaborador_detalle_fase1",
                )
            with control_top:
                top_n = st.selectbox(
                    "Ranking visible",
                    options=[15, 25, 50],
                    index=1,
                    format_func=lambda n: f"Top {n}",
                    key="ranking_visible_fase1",
                )

            df_colab = df_comp_f[df_comp_f["colaborador"] == colaborador_sel]
            g = df_global_f[df_global_f["colaborador"] == colaborador_sel]["global"].values[0]

            df_rank_base = df_global_f.sort_values("global", ascending=False).copy()
            df_rank = df_rank_base.head(top_n).copy()
            seleccionado_fuera_top = colaborador_sel not in df_rank["colaborador"].tolist()
            if seleccionado_fuera_top:
                df_rank = pd.concat([
                    df_rank,
                    df_rank_base[df_rank_base["colaborador"] == colaborador_sel],
                ], ignore_index=True)

            rank_col, detail_col = st.columns([1.05, 0.95])
            with rank_col:
                st.markdown("**Ranking de colaboradores**")
                nota_extra = " Incluye el colaborador seleccionado fuera del Top." if seleccionado_fuera_top else ""
                st.markdown(
                    f'<div class="ev-mini-note">Mostrando {len(df_rank)} de {len(df_rank_base)} colaboradores.{nota_extra}</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    fig_colab_ranking(df_rank, height=420, colaborador_sel=colaborador_sel),
                    use_container_width=True,
                    key="colab_ranking",
                )

                with st.expander("Ver ranking completo en tabla", expanded=False):
                    html = '<div class="ev-scroll-table"><table class="ev-table">'
                    html += "<thead><tr><th>#</th><th>Colaborador</th><th>Puntaje</th><th>Escala</th></tr></thead><tbody>"
                    for pos, (_, row) in enumerate(df_rank_base.iterrows(), start=1):
                        es_sel = row["colaborador"] == colaborador_sel
                        estilo = ' style="background:#f5f0ff;font-weight:600"' if es_sel else ""
                        nombre = html_lib.escape(str(row["colaborador"]))
                        html += f"<tr{estilo}><td>{pos}</td><td>{nombre}</td><td>{chip_html(row['global'])}</td><td>{escala_label(row['global'])}</td></tr>"
                    html += "</tbody></table></div>"
                    st.markdown(html, unsafe_allow_html=True)

            with detail_col:
                st.markdown("**Detalle individual**")
                st.markdown(f"""
                <div style="background:white;border:0.5px solid #e8e4f4;border-radius:10px;padding:16px">
                    <div style="font-size:16px;font-weight:600;color:#1a1a3e;margin-bottom:4px">{colaborador_sel}</div>
                    <div style="font-size:24px;font-weight:700;color:{score_color(g)};margin-bottom:4px">{g:.2f}</div>
                    <div style="font-size:12px;color:#6b6b8a;margin-bottom:16px">{escala_label(g)}</div>
                """, unsafe_allow_html=True)
                for _, row in df_colab.sort_values("puntaje", ascending=False).iterrows():
                    v = row["puntaje"]
                    pct = int((v - 65) / 35 * 100)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                        <span style="font-size:11px;color:#6b6b8a;flex:1;white-space:nowrap;overflow:hidden;
                            text-overflow:ellipsis" title="{row['competencia']}">{row['competencia']}</span>
                        <div style="width:80px;height:5px;background:#e8e4f4;border-radius:3px;overflow:hidden">
                            <div style="width:{pct}%;height:100%;background:{score_color(v)};border-radius:3px"></div>
                        </div>
                        <span style="font-size:12px;font-weight:600;color:{score_color(v)};min-width:36px">{v:.2f}</span>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown("**Radar individual**")
                st.plotly_chart(fig_colab_radar(df_comp_f, colaborador_sel), use_container_width=True, key="colab_radar")

            st.markdown("**Desglose por relaci\u00f3n**")
            tipos_disp = [t for t in TIPO_LABEL if f"tipo_{t}" in df_colab.columns]
            if tipos_disp:
                tipo_labels_colab = etiquetas_tipo_con_pesos(df_colab, tipos_disp)
                html  = '<div style="overflow-x:auto"><table class="ev-table"><thead><tr><th>Competencia</th>'
                html += "".join(f"<th>{tipo_labels_colab.get(t, TIPO_LABEL[t])}</th>" for t in tipos_disp) + "</tr></thead><tbody>"
                for _, row in df_colab.sort_values("puntaje", ascending=False).iterrows():
                    html += f'<tr><td style="font-weight:500">{row["competencia"]}</td>'
                    for t in tipos_disp:
                        v = row.get(f"tipo_{t}")
                        html += f"<td>{chip_html(v)}</td>" if pd.notna(v) else "<td style='color:#aaa;text-align:center'>&mdash;</td>"
                    html += "</tr>"
                html += "</tbody></table></div>"
                st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No hay colaboradores con los filtros aplicados.")

    # â”€â”€ Subtab: Ãtems â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with sub_items:
        st.markdown("**Puntaje por \u00edtem (promedio ponderado)**")
        comp_options = ["Todas las competencias"] + sorted(df_items_f["competencia"].unique().tolist())
        filtro_comp  = st.selectbox("Competencia", comp_options, label_visibility="collapsed")
        df_items_show = df_items_f.copy()
        if filtro_comp != "Todas las competencias":
            df_items_show = df_items_show[df_items_show["competencia"] == filtro_comp]
        html  = '<div style="overflow-x:auto"><table class="ev-table ev-items-table">'
        html += "<thead><tr><th>Item</th><th>Puntaje</th></tr></thead><tbody>"
        for competencia, df_grupo in df_items_show.groupby("competencia", sort=True):
            promedio = df_grupo["puntaje"].mean()
            cantidad = len(df_grupo)
            nombre = html_lib.escape(str(competencia))
            etiqueta_items = "\u00edtem" if cantidad == 1 else "\u00edtems"
            html += (
                '<tr class="ev-items-group"><td colspan="2">'
                '<div class="ev-items-group-content">'
                f'<span class="ev-items-group-name">{nombre}</span>'
                f'<span class="ev-items-group-meta">{cantidad} {etiqueta_items} &middot; Promedio {promedio:.2f}</span>'
                "</div></td></tr>"
            )
            for _, row in df_grupo.sort_values("puntaje", ascending=False).iterrows():
                item = html_lib.escape(str(row["item"]))
                html += f'<tr><td>{item}</td><td>{chip_html(row["puntaje"])}</td></tr>'
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FASE II - POTENCIAL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def _proximamente(fase: str):
    st.markdown(f"""
    <div style="text-align:center;padding:60px 20px">
        <div style="font-size:12px;letter-spacing:0.18em;text-transform:uppercase;color:#7b6fb0;margin-bottom:12px">Pr\u00f3ximamente</div>
        <div style="font-size:18px;font-weight:600;color:#1a1a3e;margin-bottom:6px">{fase}</div>
        <div style="font-size:13px;color:#6b6b8a">
            Esta secci\u00f3n se habilitar\u00e1 cuando se cargue el archivo correspondiente.
        </div>
    </div>
    """, unsafe_allow_html=True)

if fase_activa == "fase2":
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    resumen_potencial = res_potencial["resumen"]
    df_potencial = res_potencial["df_personas"].copy()

    with st.container(key="sticky_filtros_potencial"):
        st.markdown("""
        <div class="ev-filter-container">
            <div class="ev-filter-header">
                <span class="ev-filter-icon"></span>
                <span class="ev-filter-title">Filtros de potencial</span>
                <span class="ev-filter-hint">Aplican a toda la Fase II</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        filtro_pot_1, filtro_pot_2 = st.columns(2)
        with filtro_pot_1:
            nombres_potencial = st.multiselect(
                "Colaboradores",
                options=sorted(df_potencial["colaborador"].dropna().unique().tolist()),
                placeholder="Todos los colaboradores",
                key="filtro_potencial_colaboradores",
            )
        with filtro_pot_2:
            jefes_disponibles = sorted(
                jefe for jefe in df_potencial["jefe"].dropna().unique().tolist()
                if jefe and not jefe.upper().startswith("N/A")
            )
            jefes_potencial = st.multiselect(
                "Jefes",
                options=jefes_disponibles,
                placeholder="Todos los jefes",
                key="filtro_potencial_jefes",
            )
    st.markdown('<div class="sticky-controls-spacer"></div>', unsafe_allow_html=True)

    if nombres_potencial:
        df_potencial = df_potencial[df_potencial["colaborador"].isin(nombres_potencial)]
    if jefes_potencial:
        df_potencial = df_potencial[df_potencial["jefe"].isin(jefes_potencial)]

    df_potencial_evaluado = df_potencial[df_potencial["evaluacion_potencial"].notna()].copy()
    df_valores_potencial = res_potencial["df_competencias"].copy()
    if nombres_potencial:
        df_valores_potencial = df_valores_potencial[
            df_valores_potencial["colaborador"].isin(nombres_potencial)
        ]
    if jefes_potencial:
        df_valores_potencial = df_valores_potencial[
            df_valores_potencial["jefe"].isin(jefes_potencial)
        ]

    sub_f2_res, sub_f2_pot, sub_f2_disc, sub_f2_iq, sub_f2_curvas = st.tabs([
        "Resumen", "Valores", "DISC / Arquetipos", "IQ Inteligencia", "Curvas de Desarrollo",
    ])
    with sub_f2_res:
        total_potencial = len(df_potencial_evaluado)
        promedio_potencial = df_potencial_evaluado["evaluacion_potencial"].mean()
        kpi_pot_1, kpi_pot_2 = st.columns(2)
        with kpi_pot_1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Colaboradores</div>
                <div class="kpi-value">{total_potencial}</div>
                <div class="kpi-sub">con evaluaci\u00f3n de potencial</div>
            </div>""", unsafe_allow_html=True)
        with kpi_pot_2:
            promedio_texto = f"{promedio_potencial:.2f}" if pd.notna(promedio_potencial) else "&mdash;"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Evaluaci\u00f3n de potencial</div>
                <div class="kpi-value green">{promedio_texto}</div>
                <div class="kpi-sub">promedio 2026</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if df_potencial_evaluado.empty:
            st.info("No hay colaboradores con evaluaci\u00f3n de potencial para los filtros seleccionados.")
        else:
            medidor_1, medidor_2 = st.columns(2)
            with medidor_1:
                st.markdown("**Escala benchmark externo**")
                st.plotly_chart(
                    fig_medidor_potencial(promedio_potencial, (70, 85)),
                    use_container_width=True,
                    key="potencial_medidor_benchmark",
                )
            with medidor_2:
                st.markdown("**Escala propia**")
                st.plotly_chart(
                    fig_medidor_potencial(promedio_potencial, (82, 98)),
                    use_container_width=True,
                    key="potencial_medidor_propio",
                )

            escala_1, escala_2 = st.columns(2)
            with escala_1:
                st.markdown("**Distribucion benchmark externo**")
                st.plotly_chart(
                    fig_escala_potencial(df_potencial_evaluado, "escala_benchmark"),
                    use_container_width=True,
                    key="potencial_escala_benchmark",
                )
            with escala_2:
                st.markdown("**Distribucion escala propia**")
                st.plotly_chart(
                    fig_escala_potencial(df_potencial_evaluado, "escala_potencial"),
                    use_container_width=True,
                    key="potencial_escala_propia",
                )

            graf_1, graf_2, graf_3 = st.columns(3)
            with graf_1:
                st.markdown("**Colaboradores por empresa**")
                st.plotly_chart(
                    fig_distribucion_potencial(df_potencial, "empresa"),
                    use_container_width=True,
                    key="potencial_empresa",
                )
            with graf_2:
                st.markdown("**Colaboradores por pais**")
                st.plotly_chart(
                    fig_distribucion_potencial(df_potencial, "pais"),
                    use_container_width=True,
                    key="potencial_pais",
                )
            with graf_3:
                st.markdown("**Comparativo de potencial 2025-2026**")
                st.plotly_chart(
                    fig_comparativo_potencial(df_potencial),
                    use_container_width=True,
                    key="potencial_comparativo",
                )
    with sub_f2_pot:
        escala_valores = st.segmented_control(
            "Escala de referencia",
            options=["Benchmark externo", "Escala propia"],
            default="Benchmark externo",
            key="escala_valores_potencial",
        )
        limites_valores = (70, 85) if escala_valores == "Benchmark externo" else (82, 98)

        if not df_valores_potencial.empty:
            df_valores_mapeo = df_valores_potencial.copy()
            df_valores_mapeo["competencia_limpia"] = df_valores_mapeo["competencia"].map(reparar_texto)
            df_valores_mapeo["clave_competencia"] = df_valores_mapeo["competencia_limpia"].map(clave_texto)
            promedios_valores = df_valores_mapeo.groupby("clave_competencia")["ajuste"].mean().mul(100)
        else:
            promedios_valores = pd.Series(dtype=float)
        tabla_valores = pd.DataFrame({"competencia": ORDEN_VALORES_POTENCIAL})
        tabla_valores["clave_competencia"] = tabla_valores["competencia"].map(clave_texto)
        tabla_valores["puntaje"] = tabla_valores["clave_competencia"].map(promedios_valores)

        tabla_col, grafico_col = st.columns([1, 3])
        with tabla_col:
            st.markdown("**Valores**")
            html = '<div style="overflow-x:auto"><table class="ev-table"><thead><tr>'
            html += '<th>Competencia</th><th style="text-align:right">Promedio</th></tr></thead><tbody>'
            for _, fila in tabla_valores.iterrows():
                competencia = html_lib.escape(reparar_texto(fila["competencia"]))
                fondo, texto = color_valor_potencial(fila["puntaje"], limites_valores)
                valor = f"{fila['puntaje']:.2f}%" if pd.notna(fila["puntaje"]) else "&mdash;"
                html += (
                    f'<tr><td>{competencia}</td>'
                    f'<td style="text-align:right;background:{fondo};color:{texto};font-weight:600">'
                    f'{valor}</td></tr>'
                )
            html += "</tbody></table></div>"
            st.markdown(html, unsafe_allow_html=True)

        with grafico_col:
            st.markdown("**Promedio por valor**")
            if tabla_valores["puntaje"].notna().any():
                st.plotly_chart(
                    fig_valores_potencial(tabla_valores, limites_valores),
                    use_container_width=True,
                    key="valores_potencial_grafico",
                )
            else:
                st.info("No hay valores disponibles para los filtros seleccionados.")
    with sub_f2_disc:
        tabla_disc = contar_arquetipos_disc(df_potencial)
        total_disc = int(tabla_disc["colaboradores"].sum()) if not tabla_disc.empty else 0
        total_base_disc = len(df_potencial)
        cobertura_disc = total_disc / total_base_disc if total_base_disc else np.nan
        arquetipo_lider = tabla_disc.iloc[0] if not tabla_disc.empty else None

        disc_kpi_1, disc_kpi_2, disc_kpi_3 = st.columns(3)
        with disc_kpi_1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Colaboradores con DISC</div>
                <div class="kpi-value">{total_disc}</div>
                <div class="kpi-sub">de {total_base_disc} colaboradores filtrados</div>
            </div>""", unsafe_allow_html=True)
        with disc_kpi_2:
            cobertura_txt = f"{cobertura_disc:.1%}" if pd.notna(cobertura_disc) else "&mdash;"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Cobertura DISC</div>
                <div class="kpi-value green">{cobertura_txt}</div>
                <div class="kpi-sub">personas con arquetipo asignado</div>
            </div>""", unsafe_allow_html=True)
        with disc_kpi_3:
            lider_nombre = html_lib.escape(str(arquetipo_lider["arquetipo"])) if arquetipo_lider is not None else "&mdash;"
            lider_valor = int(arquetipo_lider["colaboradores"]) if arquetipo_lider is not None else 0
            lider_part = f"{arquetipo_lider['participacion']:.1%}" if arquetipo_lider is not None else "&mdash;"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Arquetipo dominante</div>
                <div class="kpi-value" style="font-size:22px">{lider_nombre}</div>
                <div class="kpi-sub">{lider_valor} colaboradores &middot; {lider_part}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if tabla_disc.empty:
            st.info("No hay arquetipos DISC disponibles para los filtros seleccionados.")
        else:
            tabla_col, radar_col = st.columns([0.9, 1.5])
            with tabla_col:
                st.markdown("**Arquetipos**")
                html = '<div class="ev-scroll-table"><table class="ev-table">'
                html += "<thead><tr><th>Arquetipo</th><th style='text-align:right'>Colaboradores</th><th style='text-align:right'>%</th></tr></thead><tbody>"
                max_disc = tabla_disc["colaboradores"].max()
                for idx, fila in tabla_disc.iterrows():
                    color = DISC_PALETA[idx % len(DISC_PALETA)]
                    arquetipo = html_lib.escape(str(fila["arquetipo"]))
                    colaboradores = int(fila["colaboradores"])
                    participacion = f"{fila['participacion']:.1%}"
                    ancho = int(colaboradores / max_disc * 100) if max_disc else 0
                    html += (
                        "<tr>"
                        f"<td><div style='font-weight:600;color:#1a1a3e'>{arquetipo}</div>"
                        "<div style='height:5px;background:#f0eef8;border-radius:5px;overflow:hidden;margin-top:5px'>"
                        f"<div style='width:{ancho}%;height:100%;background:{color};border-radius:5px'></div>"
                        "</div></td>"
                        f"<td style='text-align:right;font-weight:700;color:{color}'>{colaboradores}</td>"
                        f"<td style='text-align:right;color:#6b6b8a'>{participacion}</td>"
                        "</tr>"
                    )
                html += (
                    "<tr style='font-weight:700;background:#f8f7fc'>"
                    f"<td>Total general</td><td style='text-align:right'>{total_disc}</td><td style='text-align:right'>100.0%</td>"
                    "</tr></tbody></table></div>"
                )
                st.markdown(html, unsafe_allow_html=True)

            with radar_col:
                st.markdown("**Mapa radial de arquetipos**")
                st.plotly_chart(
                    fig_disc_arquetipos(tabla_disc),
                    use_container_width=True,
                    key="disc_arquetipos_radial",
                )

            st.markdown("**Arquetipos con mayor presencia**")
            st.plotly_chart(
                fig_disc_top_barras(tabla_disc, top_n=min(8, len(tabla_disc))),
                use_container_width=True,
                key="disc_arquetipos_top",
            )

    with sub_f2_iq:
        tabla_iq = contar_iq(df_potencial)
        total_iq = int(tabla_iq["colaboradores"].sum()) if not tabla_iq.empty else 0
        total_base_iq = len(df_potencial)
        cobertura_iq = total_iq / total_base_iq if total_base_iq else np.nan
        promedio_iq = (
            np.average(tabla_iq["puntaje"], weights=tabla_iq["colaboradores"])
            if not tabla_iq.empty and tabla_iq["puntaje"].notna().any()
            else np.nan
        )
        rango_lider_iq = (
            tabla_iq.sort_values(["colaboradores", "puntaje"], ascending=[False, True]).iloc[0]
            if not tabla_iq.empty else None
        )

        iq_kpi_1, iq_kpi_2, iq_kpi_3 = st.columns(3)
        with iq_kpi_1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Colaboradores con IQ</div>
                <div class="kpi-value">{total_iq}</div>
                <div class="kpi-sub">de {total_base_iq} colaboradores filtrados</div>
            </div>""", unsafe_allow_html=True)
        with iq_kpi_2:
            promedio_txt = f"{promedio_iq:.1f}" if pd.notna(promedio_iq) else "&mdash;"
            cobertura_txt = f"{cobertura_iq:.1%}" if pd.notna(cobertura_iq) else "&mdash;"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Promedio IQ</div>
                <div class="kpi-value green">{promedio_txt}</div>
                <div class="kpi-sub">cobertura {cobertura_txt}</div>
            </div>""", unsafe_allow_html=True)
        with iq_kpi_3:
            rango_nombre = html_lib.escape(str(rango_lider_iq["iq"])) if rango_lider_iq is not None else "&mdash;"
            rango_valor = int(rango_lider_iq["colaboradores"]) if rango_lider_iq is not None else 0
            rango_part = f"{rango_lider_iq['participacion']:.1%}" if rango_lider_iq is not None else "&mdash;"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Rango mas frecuente</div>
                <div class="kpi-value" style="font-size:22px">{rango_nombre}</div>
                <div class="kpi-sub">{rango_valor} colaboradores &middot; {rango_part}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if tabla_iq.empty:
            st.info("No hay datos de IQ para los filtros seleccionados.")
        else:
            graf_iq, tabla_iq_col = st.columns([1.5, 0.9])
            with graf_iq:
                st.markdown("**Distribucion por factor Inteligencia**")
                st.plotly_chart(
                    fig_iq_distribucion(tabla_iq),
                    use_container_width=True,
                    key="iq_inteligencia_distribucion",
                )
            with tabla_iq_col:
                st.markdown("**Detalle IQ**")
                html = '<div class="ev-scroll-table"><table class="ev-table">'
                html += "<thead><tr><th>Factor Inteligencia</th><th style='text-align:right'>Puntaje</th><th style='text-align:right'>Colab.</th><th style='text-align:right'>%</th></tr></thead><tbody>"
                for _, fila in tabla_iq.iterrows():
                    etiqueta = html_lib.escape(str(fila["iq"]))
                    puntaje = f"{fila['puntaje']:.0f}" if pd.notna(fila["puntaje"]) else "&mdash;"
                    html += (
                        "<tr>"
                        f"<td style='font-weight:600'>{etiqueta}</td>"
                        f"<td style='text-align:right'>{puntaje}</td>"
                        f"<td style='text-align:right;font-weight:700;color:#185fa5'>{int(fila['colaboradores'])}</td>"
                        f"<td style='text-align:right;color:#6b6b8a'>{fila['participacion']:.1%}</td>"
                        "</tr>"
                    )
                html += (
                    "<tr style='font-weight:700;background:#f8f7fc'>"
                    f"<td>Total general</td><td></td><td style='text-align:right'>{total_iq}</td><td style='text-align:right'>100.0%</td>"
                    "</tr></tbody></table></div>"
                )
                st.markdown(html, unsafe_allow_html=True)
    with sub_f2_curvas:
        competencias_curva = [
            comp for comp in ORDEN_VALORES_POTENCIAL
            if comp in set(df_valores_potencial["competencia"].dropna().unique())
        ]
        if not competencias_curva:
            st.info("No hay competencias disponibles para construir curvas de desarrollo con los filtros seleccionados.")
        else:
            selector_curva, resumen_curva = st.columns([2.2, 1])
            with selector_curva:
                competencia_curva = st.selectbox(
                    "Competencia",
                    options=competencias_curva,
                    key="curva_desarrollo_competencia",
                )

            tabla_curva = preparar_curva_desarrollo(df_valores_potencial, competencia_curva)
            total_curva = int(tabla_curva["colaboradores"].sum()) if not tabla_curva.empty else 0
            puntaje_promedio_curva = (
                np.average(tabla_curva["puntaje"], weights=tabla_curva["colaboradores"])
                if total_curva else np.nan
            )
            moda_curva = (
                tabla_curva.sort_values(["colaboradores", "puntaje"], ascending=[False, True]).iloc[0]
                if total_curva else None
            )
            with resumen_curva:
                promedio_txt = f"{puntaje_promedio_curva:.1f}" if pd.notna(puntaje_promedio_curva) else "&mdash;"
                moda_txt = (
                    f"{int(moda_curva['puntaje'])} &middot; {html_lib.escape(str(moda_curva['descripcion']))}"
                    if moda_curva is not None else "&mdash;"
                )
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Distribucion seleccionada</div>
                    <div class="kpi-value">{promedio_txt}</div>
                    <div class="kpi-sub">{total_curva} registros &middot; moda {moda_txt}</div>
                </div>""", unsafe_allow_html=True)

            if tabla_curva.empty:
                st.info("La competencia seleccionada no tiene puntajes disponibles para los filtros actuales.")
            else:
                graf_curva, tabla_curva_col = st.columns([1.55, 0.85])
                with graf_curva:
                    st.markdown("**Curva de desarrollo**")
                    st.plotly_chart(
                        fig_curva_desarrollo(tabla_curva, competencia_curva),
                        use_container_width=True,
                        key="curva_desarrollo_grafico",
                    )
                with tabla_curva_col:
                    st.markdown("**Escala y frecuencia**")
                    html = '<div class="ev-scroll-table"><table class="ev-table">'
                    html += "<thead><tr><th>Descripcion</th><th style='text-align:right'>Escala</th><th style='text-align:right'>Colab.</th><th style='text-align:right'>%</th></tr></thead><tbody>"
                    for _, fila in tabla_curva.sort_values("puntaje", ascending=False).iterrows():
                        descripcion = html_lib.escape(str(fila["descripcion"]))
                        html += (
                            "<tr>"
                            f"<td style='font-weight:600'>{descripcion}</td>"
                            f"<td style='text-align:right'>{int(fila['puntaje'])}</td>"
                            f"<td style='text-align:right;font-weight:700;color:#185fa5'>{int(fila['colaboradores'])}</td>"
                            f"<td style='text-align:right;color:#6b6b8a'>{fila['participacion']:.1%}</td>"
                            "</tr>"
                        )
                    html += (
                        "<tr style='font-weight:700;background:#f8f7fc'>"
                        f"<td>Total general</td><td></td><td style='text-align:right'>{total_curva}</td><td style='text-align:right'>100.0%</td>"
                        "</tr></tbody></table></div>"
                    )
                    st.markdown(html, unsafe_allow_html=True)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FASE III - EVALUACION DE OBJETIVOS
if fase_activa == "fase3":
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    df_obj_colab_base = res_objetivos["df_colaboradores"].copy()
    df_obj_fuente_base = res_objetivos["df_fuente"].copy()

    if df_obj_colab_base.empty:
        _proximamente("Fase III - Evaluacion de Objetivos")
    else:
        filtro_obj_1, filtro_obj_2, filtro_obj_3 = st.columns(3)
        with filtro_obj_1:
            filtro_obj_colabs = st.multiselect(
                "Colaboradores",
                sorted(df_obj_colab_base["colaborador"].dropna().unique().tolist()),
                key="filtro_objetivos_colaboradores",
                placeholder="Todos los colaboradores",
            )
        with filtro_obj_2:
            filtro_obj_jefes = st.multiselect(
                "Jefes",
                sorted(df_obj_colab_base["jefe"].dropna().unique().tolist()),
                key="filtro_objetivos_jefes",
                placeholder="Todos los jefes",
            )
        with filtro_obj_3:
            filtro_obj_escala = st.multiselect(
                "Nivel de desempeño",
                ["Alto Desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"],
                key="filtro_objetivos_escala",
                placeholder="Todos los niveles",
            )

        df_obj_colab = df_obj_colab_base.copy()
        if filtro_obj_colabs:
            df_obj_colab = df_obj_colab[df_obj_colab["colaborador"].isin(filtro_obj_colabs)]
        if filtro_obj_jefes:
            df_obj_colab = df_obj_colab[df_obj_colab["jefe"].isin(filtro_obj_jefes)]
        df_obj_colab["nivel_desempeno"] = df_obj_colab["puntaje"].map(escala_objetivos_label)
        if filtro_obj_escala:
            df_obj_colab = df_obj_colab[df_obj_colab["nivel_desempeno"].isin(filtro_obj_escala)]

        colabs_obj_activos = df_obj_colab["colaborador"].dropna().unique().tolist()
        df_obj_fuente = df_obj_fuente_base[df_obj_fuente_base["nombre_colaborador"].isin(colabs_obj_activos)].copy()
        evaluadores_obj = set(df_obj_fuente_base["nombre_evaluador"].dropna().map(normalizar_nombre_match))
        df_obj_colab["gente_a_cargo"] = df_obj_colab["colaborador"].map(
            lambda nombre: "SI" if normalizar_nombre_match(nombre) in evaluadores_obj else "NO"
        )

        df_obj_cargos = (
            df_obj_fuente.groupby("cargo_objetivo", dropna=False)
            .agg(
                puntaje=("puntaje", "mean"),
                colaboradores=("nombre_colaborador", "nunique"),
                objetivos=("objetivo", "nunique"),
            )
            .reset_index()
            .sort_values("puntaje", ascending=False)
        )
        df_obj_items = (
            df_obj_fuente.groupby(["cargo_objetivo", "objetivo"], dropna=False)
            .agg(
                puntaje=("puntaje", "mean"),
                colaboradores=("nombre_colaborador", "nunique"),
            )
            .reset_index()
            .sort_values("puntaje", ascending=False)
        )

        promedio_obj = float(df_obj_colab["puntaje"].mean()) if len(df_obj_colab) else 0.0
        alto_obj = int((df_obj_colab["puntaje"] >= 90).sum()) if len(df_obj_colab) else 0
        total_obj_colab = len(df_obj_colab)
        total_obj_items = int(df_obj_fuente["objetivo"].nunique()) if len(df_obj_fuente) else 0
        df_obj_gente = resumen_dimension_objetivos(df_obj_colab, "gente_a_cargo")

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Promedio objetivos</div>
                <div class="kpi-value gradient">{promedio_obj:.2f}</div>
                <div class="kpi-sub">{escala_label(promedio_obj)}</div>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Colaboradores</div>
                <div class="kpi-value">{total_obj_colab}</div>
                <div class="kpi-sub">con objetivos evaluados</div>
            </div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Objetivos</div>
                <div class="kpi-value">{total_obj_items}</div>
                <div class="kpi-sub">unicos evaluados</div>
            </div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Alto cumplimiento</div>
                <div class="kpi-value green">{alto_obj}</div>
                <div class="kpi-sub">colaboradores >= 90</div>
            </div>""", unsafe_allow_html=True)

        sub_f3_res, sub_f3_obj, sub_f3_colab = st.tabs([
            "Resumen", "Objetivos", "Colaboradores",
        ])
        with sub_f3_res:
            graf_a, graf_b = st.columns(2)
            with graf_a:
                st.markdown("**Escala de evaluación de objetivos**")
                st.plotly_chart(
                    fig_objetivos_distribucion(df_obj_colab),
                    use_container_width=True,
                    key="obj_distribucion",
                )
            with graf_b:
                st.markdown("**Cargos con mejor cumplimiento**")
                st.plotly_chart(
                    fig_objetivos_cargos(df_obj_cargos),
                    use_container_width=True,
                    key="obj_cargos",
                )

            tabla_a, tabla_b = st.columns([0.85, 1.15])
            with tabla_a:
                render_tabla_escala_objetivos(df_obj_colab)
                render_tabla_dimension_objetivos(
                    "Gente a cargo",
                    df_obj_gente,
                    "gente_a_cargo",
                    total_obj_colab,
                    promedio_obj,
                )
            with tabla_b:
                st.markdown("**Cargos / puestos**")
                st.markdown(
                    f'<div class="ev-mini-note">Mostrando {len(df_obj_cargos)} cargos/puestos con los filtros aplicados.</div>',
                    unsafe_allow_html=True,
                )
                html = '<div class="ev-scroll-table"><table class="ev-table">'
                html += "<thead><tr><th>Cargo</th><th style='text-align:right'>Promedio</th><th style='text-align:right'>Colab.</th><th style='text-align:right'>Objetivos</th></tr></thead><tbody>"
                for _, fila in df_obj_cargos.sort_values("puntaje", ascending=False).iterrows():
                    html += (
                        "<tr>"
                        f"<td style='font-weight:600'>{html_lib.escape(str(fila['cargo_objetivo']))}</td>"
                        f"<td style='text-align:right'>{chip_html(fila['puntaje'])}</td>"
                        f"<td style='text-align:right'>{int(fila['colaboradores'])}</td>"
                        f"<td style='text-align:right'>{int(fila['objetivos'])}</td>"
                        "</tr>"
                    )
                html += "</tbody></table></div>"
                st.markdown(html, unsafe_allow_html=True)

        with sub_f3_obj:
            cargos_opciones = ["Todos los cargos"] + sorted(df_obj_items["cargo_objetivo"].dropna().unique().tolist())
            cargo_sel_obj = st.selectbox("Cargo", cargos_opciones, key="objetivos_cargo_selector")
            df_items_show = df_obj_items.copy()
            if cargo_sel_obj != "Todos los cargos":
                df_items_show = df_items_show[df_items_show["cargo_objetivo"] == cargo_sel_obj]

            st.markdown("**Cumplimiento por objetivo**")
            html = '<div class="ev-scroll-table"><table class="ev-table">'
            html += "<thead><tr><th>Cargo</th><th>Objetivo</th><th style='text-align:right'>Colab.</th><th style='text-align:right'>Puntaje</th></tr></thead><tbody>"
            for _, fila in df_items_show.sort_values("puntaje", ascending=False).iterrows():
                html += (
                    "<tr>"
                    f"<td style='font-weight:600'>{html_lib.escape(str(fila['cargo_objetivo']))}</td>"
                    f"<td>{html_lib.escape(str(fila['objetivo']))}</td>"
                    f"<td style='text-align:right'>{int(fila['colaboradores'])}</td>"
                    f"<td style='text-align:right'>{chip_html(fila['puntaje'])}</td>"
                    "</tr>"
                )
            html += "</tbody></table></div>"
            st.markdown(html, unsafe_allow_html=True)

        with sub_f3_colab:
            graf_col, tabla_col = st.columns([1.1, 1.2])
            with graf_col:
                st.markdown("**Ranking de colaboradores**")
                st.plotly_chart(
                    fig_objetivos_colaboradores(df_obj_colab),
                    use_container_width=True,
                    key="obj_colaboradores",
                )
            with tabla_col:
                st.markdown("**Detalle por colaborador**")
                html = '<div class="ev-scroll-table"><table class="ev-table">'
                html += "<thead><tr><th>Colaborador</th><th>Cargo</th><th>Jefe</th><th>Nivel</th><th>Gente a cargo</th><th style='text-align:right'>Objetivos</th><th style='text-align:right'>Puntaje</th></tr></thead><tbody>"
                for _, fila in df_obj_colab.sort_values("puntaje", ascending=False).iterrows():
                    html += (
                        "<tr>"
                        f"<td style='font-weight:600'>{html_lib.escape(str(fila['colaborador']))}</td>"
                        f"<td>{html_lib.escape(str(fila['cargo_objetivo']))}</td>"
                        f"<td>{html_lib.escape(str(fila['jefe']))}</td>"
                        f"<td>{html_lib.escape(str(fila['nivel_desempeno']))}</td>"
                        f"<td>{html_lib.escape(str(fila['gente_a_cargo']))}</td>"
                        f"<td style='text-align:right'>{int(fila['objetivos'])}</td>"
                        f"<td style='text-align:right'>{chip_html(fila['puntaje'])}</td>"
                        "</tr>"
                    )
                html += "</tbody></table></div>"
                st.markdown(html, unsafe_allow_html=True)

# RESULTADO INTEGRADO
if fase_activa == "res_int":
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    df_integrado_base = preparar_resultado_integrado(
        res["df_global"],
        res_objetivos["df_colaboradores"],
        res_potencial["df_personas"],
        res_objetivos["df_fuente"],
    )

    sub_ri_completa, sub_ri_360_obj, sub_ri_360_pot, sub_ri_obj_pot, sub_ri_colab = st.tabs([
        "360 + Objetivos + Potencial",
        "360 + Objetivos",
        "360 + Potencial",
        "Objetivos + Potencial",
        "Colaboradores",
    ])

    with sub_ri_completa:
        render_resultado_integrado_tipo(df_integrado_base, "Completa", len(df_integrado_base))

    with sub_ri_360_obj:
        render_resultado_integrado_tipo(df_integrado_base, "360+obj", len(df_integrado_base))
    with sub_ri_360_pot:
        render_resultado_integrado_tipo(df_integrado_base, "360+pot", len(df_integrado_base))
    with sub_ri_obj_pot:
        render_resultado_integrado_tipo(df_integrado_base, "obj+pot", len(df_integrado_base))
    with sub_ri_colab:
        df_colab_integrado = df_integrado_base[pd.notna(df_integrado_base["integrada"])].copy()
        if df_colab_integrado.empty:
            st.info("No hay colaboradores con resultado integrado calculable.")
        else:
            filtros_colab_1, filtros_colab_2, filtros_colab_3 = st.columns(3)
            with filtros_colab_1:
                filtro_colab_integrado = st.multiselect(
                    "Colaboradores",
                    sorted(df_colab_integrado["colaborador"].dropna().unique().tolist()),
                    key="filtro_integrado_detalle_colabs",
                    placeholder="Todos los colaboradores integrados",
                )
            with filtros_colab_2:
                filtro_tipo_integrado = st.multiselect(
                    "Tipo de integración",
                    [cfg for cfg in CONFIG_INTEGRADO.keys() if cfg in df_colab_integrado["etiqueta_integrada"].unique()],
                    key="filtro_integrado_detalle_tipo",
                    placeholder="Todos los tipos",
                    format_func=lambda valor: CONFIG_INTEGRADO.get(valor, {}).get("tab", valor),
                )
            with filtros_colab_3:
                filtro_nivel_integrado = st.multiselect(
                    "Escala integrada",
                    ["Alto Desempeño", "Desempeño satisfactorio", "Bajo desempeño", "Desempeño insatisfactorio"],
                    key="filtro_integrado_detalle_nivel",
                    placeholder="Todas las escalas",
                )

            if filtro_colab_integrado:
                df_colab_integrado = df_colab_integrado[df_colab_integrado["colaborador"].isin(filtro_colab_integrado)]
            if filtro_tipo_integrado:
                df_colab_integrado = df_colab_integrado[df_colab_integrado["etiqueta_integrada"].isin(filtro_tipo_integrado)]
            if filtro_nivel_integrado:
                df_colab_integrado = df_colab_integrado[df_colab_integrado["escala_integrada"].isin(filtro_nivel_integrado)]

            st.markdown("**Detalle general de colaboradores integrados**")
            html = '<div class="ev-scroll-table"><table class="ev-table">'
            html += "<thead><tr><th>Colaborador</th><th>Tipo</th><th>Nivel</th><th>Grupo</th><th>Empresa</th><th>País</th><th style='text-align:right'>360</th><th style='text-align:right'>Obj.</th><th style='text-align:right'>Pot.</th><th style='text-align:right'>Integrada</th></tr></thead><tbody>"
            for _, fila in df_colab_integrado.sort_values("integrada", ascending=False).iterrows():
                tipo_label = CONFIG_INTEGRADO.get(fila["etiqueta_integrada"], {}).get("tab", fila["etiqueta_integrada"])
                html += (
                    "<tr>"
                    f"<td style='font-weight:600'>{html_lib.escape(str(fila['colaborador']))}</td>"
                    f"<td>{html_lib.escape(str(tipo_label))}</td>"
                    f"<td>{html_lib.escape(str(fila['escala_integrada']))}</td>"
                    f"<td>{html_lib.escape(str(fila['grupo']))}</td>"
                    f"<td>{html_lib.escape(str(fila['empresa']))}</td>"
                    f"<td>{html_lib.escape(str(fila['pais']))}</td>"
                    f"<td style='text-align:right'>{fila['evd_360']:.0f}</td>" if pd.notna(fila.get("evd_360")) else "<td style='text-align:right'>-</td>"
                )
                html += f"<td style='text-align:right'>{fila['objetivos']:.0f}</td>" if pd.notna(fila.get("objetivos")) else "<td style='text-align:right'>-</td>"
                html += f"<td style='text-align:right'>{fila['potencial']:.0f}</td>" if pd.notna(fila.get("potencial")) else "<td style='text-align:right'>-</td>"
                html += f"<td style='text-align:right'>{chip_html(fila['integrada'])}</td></tr>"
            html += "</tbody></table></div>"
            st.markdown(html, unsafe_allow_html=True)

# NINEBOX
if fase_activa == "ninebox":
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    df_ninebox_base = preparar_ninebox(res["df_global"], res_potencial["df_personas"])

    if df_ninebox_base.empty:
        st.info("No hay colaboradores con datos emparejados de desempeño 360 y potencial.")
    else:
        nombres_ninebox = sorted(df_ninebox_base["colaborador"].dropna().unique().tolist())
        seleccion_ninebox = st.session_state.get("filtro_ninebox_colaboradores", [])
        df_ninebox_kpi = df_ninebox_base.copy()
        if seleccion_ninebox:
            df_ninebox_kpi = df_ninebox_kpi[df_ninebox_kpi["colaborador"].isin(seleccion_ninebox)]

        kpi_conteos = pd.Series(dtype=int)
        if len(df_ninebox_kpi) >= 2:
            cortes_kpi = cortes_ninebox(df_ninebox_kpi)
            df_ninebox_kpi = clasificar_ninebox(df_ninebox_kpi, cortes_kpi)
            kpi_conteos = df_ninebox_kpi["cuadrante"].value_counts()

        kpi_total = len(df_ninebox_kpi)
        kpi_alto_alto = int(kpi_conteos.get(1, 0))
        kpi_medio_medio = int(kpi_conteos.get(5, 0))
        kpi_bajo_bajo = int(kpi_conteos.get(9, 0))

        kpi_cols = st.columns(4)
        kpi_datos = [
            ("Personas", kpi_total, "con desempeño 360 y potencial"),
            ("Alto-Alto", kpi_alto_alto, "alto potencial y alto desempeño"),
            ("Medio-Medio", kpi_medio_medio, "zona central del ninebox"),
            ("Bajo-Bajo", kpi_bajo_bajo, "bajo potencial y bajo desempeño"),
        ]
        for col, (titulo, valor, subtitulo) in zip(kpi_cols, kpi_datos):
            with col:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">{titulo}</div>
                        <div class="kpi-value">{valor}</div>
                        <div class="kpi-sub">{subtitulo}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        filtro_ninebox = st.multiselect(
            "Colaboradores",
            options=nombres_ninebox,
            placeholder="Todos los colaboradores emparejados",
            key="filtro_ninebox_colaboradores",
        )
        df_ninebox = df_ninebox_base.copy()
        if filtro_ninebox:
            df_ninebox = df_ninebox[df_ninebox["colaborador"].isin(filtro_ninebox)]

        if df_ninebox.empty or len(df_ninebox) < 2:
            st.info("Selecciona al menos dos colaboradores con desempeño y potencial para construir la matriz.")
        else:
            cortes = cortes_ninebox(df_ninebox)
            df_ninebox_clasificado = clasificar_ninebox(df_ninebox, cortes)

            st.markdown("**Puntos de corte**")
            cortes_html = '<div style="overflow-x:auto"><table class="ev-table"><thead><tr>'
            cortes_html += "<th></th><th>Promedio</th><th>Desviación</th><th>Rango sup</th><th>Rango inf</th></tr></thead><tbody>"
            cortes_html += (
                "<tr><td style='font-weight:700'>Potencial</td>"
                f"<td>{cortes['potencial_prom']:.1f}</td><td>{cortes['potencial_std']:.1f}</td>"
                f"<td>{cortes['potencial_sup']:.1f}</td><td>{cortes['potencial_inf']:.1f}</td></tr>"
            )
            cortes_html += (
                "<tr><td style='font-weight:700'>Evd 360</td>"
                f"<td>{cortes['desempeno_prom']:.1f}</td><td>{cortes['desempeno_std']:.1f}</td>"
                f"<td>{cortes['desempeno_sup']:.1f}</td><td>{cortes['desempeno_inf']:.1f}</td></tr>"
            )
            cortes_html += "</tbody></table></div>"
            st.markdown(cortes_html, unsafe_allow_html=True)

            matriz_col, tabla_col = st.columns([1.05, 1.15])
            with matriz_col:
                st.markdown("**Matriz Ninebox**")
                st.plotly_chart(
                    fig_ninebox(df_ninebox_clasificado),
                    use_container_width=True,
                    key="ninebox_matriz",
                )
                st.markdown(
                    f"<div class='ev-mini-note'><b>Muestra:</b> {len(df_ninebox_clasificado)} colaboradores emparejados</div>",
                    unsafe_allow_html=True,
                )

            with tabla_col:
                st.markdown("**Colaboradores por cuadrante**")
                tabla = df_ninebox_clasificado.sort_values(
                    ["cuadrante", "potencial", "desempeno_360"],
                    ascending=[True, False, False],
                )
                html = '<div class="ev-scroll-table" style="max-height:520px"><table class="ev-table">'
                html += (
                    "<thead><tr><th>Nombres</th><th style='text-align:right'># cuadrante</th>"
                    "<th>Colaboradores</th><th style='text-align:right'>POTENCIAL</th>"
                    "<th style='text-align:right'>360</th></tr></thead><tbody>"
                )
                for cuadrante, grupo in tabla.groupby("cuadrante", sort=True):
                    color = NINEBOX_COLORES.get(int(cuadrante), "#f8f7fc")
                    nombre_cuadrante = html_lib.escape(NINEBOX_LABELS.get(int(cuadrante), f"Cuadrante {cuadrante}"))
                    html += (
                        f"<tr style='background:{color};font-weight:700'>"
                        f"<td>{nombre_cuadrante}</td><td style='text-align:right'>{int(cuadrante)}</td>"
                        f"<td style='text-align:right'>{len(grupo)}</td><td></td><td></td></tr>"
                    )
                    for _, fila in grupo.iterrows():
                        nombre = html_lib.escape(str(fila["colaborador"]))
                        html += (
                            "<tr>"
                            f"<td>{nombre}</td>"
                            f"<td style='text-align:right'>{int(fila['cuadrante'])}</td>"
                            "<td style='text-align:right'>1</td>"
                            f"<td style='text-align:right'>{fila['potencial']:.1f}</td>"
                            f"<td style='text-align:right'>{fila['desempeno_360']:.1f}</td>"
                            "</tr>"
                        )
                html += "</tbody></table></div>"
                st.markdown(html, unsafe_allow_html=True)



# Activa el modo fijo solo cuando filtros y pestaÃ±as alcanzan el borde superior.
components.html(
    """
    <script>
    (() => {
        const hostWindow = window.parent;
        const doc = hostWindow.document;

        if (hostWindow.__phaseControlsCleanup) {
            hostWindow.__phaseControlsCleanup();
        }

        const setup = () => {
            const filter = doc.querySelector(
                '.st-key-sticky_filtros_desempeno, .st-key-sticky_filtros_potencial'
            );
            const tabs = doc.querySelector(
                '[data-testid="stTabs"] [data-baseweb="tab-list"]'
            );

            if (!filter || !tabs) {
                doc.body.classList.remove('phase-controls-pinned');
                doc.body.style.removeProperty('--phase-filter-height');
                return;
            }

            let scroller = filter.parentElement;
            while (scroller && scroller !== doc.body) {
                const style = hostWindow.getComputedStyle(scroller);
                const scrollable = /(auto|scroll)/.test(style.overflowY)
                    && scroller.scrollHeight > scroller.clientHeight;
                if (scrollable) break;
                scroller = scroller.parentElement;
            }

            const usesWindow = !scroller || scroller === doc.body;
            const target = usesWindow ? hostWindow : scroller;
            const getScrollTop = () => usesWindow
                ? (hostWindow.scrollY || doc.documentElement.scrollTop)
                : scroller.scrollTop;
            const getViewportTop = () => usesWindow ? 0 : scroller.getBoundingClientRect().top;
            const trigger = filter.getBoundingClientRect().top
                - getViewportTop() + getScrollTop();

            const update = () => {
                const pinned = getScrollTop() >= trigger - 2;
                doc.body.classList.toggle('phase-controls-pinned', pinned);
                if (pinned) {
                    doc.body.style.setProperty(
                        '--phase-filter-height', `${filter.offsetHeight}px`
                    );
                }
            };

            target.addEventListener('scroll', update, { passive: true });
            hostWindow.addEventListener('resize', update, { passive: true });
            update();

            hostWindow.__phaseControlsCleanup = () => {
                target.removeEventListener('scroll', update);
                hostWindow.removeEventListener('resize', update);
                doc.body.classList.remove('phase-controls-pinned');
                doc.body.style.removeProperty('--phase-filter-height');
                hostWindow.__phaseControlsCleanup = null;
            };
        };

        hostWindow.setTimeout(setup, 250);
    })();
    </script>
    """,
    height=0,
    width=0,
)
