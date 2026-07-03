"""
generar_pdf.py — sistema de diseño fiel al HTML de referencia Evaluar.com
"""

import io, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable,
)

W, H = A4

# Paleta fiel al CSS del HTML
INK       = colors.HexColor("#22194e")
INK2      = colors.HexColor("#3a3170")
INK_SOFT  = colors.HexColor("#6b638f")
PAPER     = colors.HexColor("#faf8f3")
PAPER2    = colors.HexColor("#f3efe6")
LINE      = colors.HexColor("#e4dfd3")
LINE_STR  = colors.HexColor("#c9c2b3")
MAGENTA   = colors.HexColor("#ff4298")
AMBER     = colors.HexColor("#ffab48")
GOOD      = colors.HexColor("#2f7d5e")
WARN      = colors.HexColor("#b45a1f")
BAD       = colors.HexColor("#a32a4d")
WHITE     = colors.white

BANDA_COLOR = {
    "Alto Desempeño":  {"fg": GOOD, "hex_fg": "#2f7d5e", "hex_bg": "#eaf4ef"},
    "Satisfactorio":   {"fg": WARN, "hex_fg": "#b45a1f", "hex_bg": "#fdf3ea"},
    "Bajo Desempeño":  {"fg": WARN, "hex_fg": "#b45a1f", "hex_bg": "#fdf3ea"},
    "Insatisfactorio": {"fg": BAD,  "hex_fg": "#a32a4d", "hex_bg": "#fbeaef"},
}

TIPOS_ORDEN = ["Autoevaluación", "Jefe", "Subordinado", "Pares", "Cliente Interno"]

PAD_TOP = 1.97*cm
PAD_LAT = 2.26*cm
PAD_BOT = 2.54*cm

TOTAL_PAGES = 4

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def spacer(h): return Spacer(1, h*cm)
def hr(color=LINE, t=0.5, sb=6, sa=6):
    return HRFlowable(width="100%", thickness=t, color=color,
                      spaceBefore=sb, spaceAfter=sa)

def banda_desde_pts(p):
    if p >= 90: return "Alto Desempeño"
    if p >= 80: return "Satisfactorio"
    if p >= 70: return "Bajo Desempeño"
    return "Insatisfactorio"

def bc(banda, campo):
    return BANDA_COLOR.get(banda,
        {"fg":INK_SOFT,"hex_fg":"#6b638f","hex_bg":"#f5f5f5"})[campo]

def sty(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10, textColor=INK2,
                leading=15, spaceAfter=0, spaceBefore=0)
    return ParagraphStyle(name, **{**base, **kw})

def E():
    return {
        "eyebrow":     sty("ey", fontName="Helvetica", fontSize=8,
                           textColor=MAGENTA, leading=12),
        "section_id":  sty("sid", fontName="Helvetica", fontSize=8,
                           textColor=INK_SOFT, leading=12),
        "section_h":   sty("sh", fontName="Helvetica-Bold", fontSize=22,
                           textColor=INK, leading=28),
        "h3":          sty("h3", fontName="Helvetica-Bold", fontSize=14,
                           textColor=INK, leading=20),
        "th":          sty("th", fontName="Helvetica-Bold", fontSize=8,
                           textColor=INK_SOFT, leading=11),
        "td":          sty("td", fontName="Helvetica", fontSize=10,
                           textColor=INK, leading=14),
        "td_comp":     sty("tdc", fontName="Helvetica-Bold", fontSize=10,
                           textColor=INK, leading=14),
        "td_num":      sty("tdn", fontName="Helvetica-Bold", fontSize=10,
                           textColor=INK, leading=14, alignment=TA_RIGHT),
        "nota":        sty("nota", fontName="Helvetica-Oblique", fontSize=8,
                           textColor=INK_SOFT, leading=12),
        "body":        sty("body", fontName="Helvetica", fontSize=10,
                           textColor=INK2, leading=16, alignment=TA_JUSTIFY),
    }

# ---------------------------------------------------------------------------
# Gráficos matplotlib
# ---------------------------------------------------------------------------

def crear_gauge(puntaje, banda, ancho_cm=6.5, alto_cm=4.8):
    fig, ax = plt.subplots(figsize=(ancho_cm/2.54, alto_cm/2.54),
                           subplot_kw=dict(aspect="equal"))
    ax.set_xlim(-1.4, 1.4); ax.set_ylim(-0.65, 1.4); ax.axis("off")
    fig.patch.set_facecolor("#faf8f3")

    for lo, hi, col in [(0,70,"#fbeaef"),(70,80,"#fdf3ea"),
                        (80,90,"#fdf3ea"),(90,100,"#eaf4ef")]:
        t1 = 180-(lo/100)*180; t2 = 180-(hi/100)*180
        ax.add_patch(mpatches.Wedge((0,0),1.05,t2,t1,width=0.30,
                     facecolor=col, edgecolor="#faf8f3", linewidth=2))

    fg = bc(banda, "hex_fg")
    ang = math.radians(180-(puntaje/100)*180)
    ax.plot([0,0.74*math.cos(ang)],[0,0.74*math.sin(ang)],
            color=fg, lw=2.5, solid_capstyle="round", zorder=5)
    ax.add_patch(plt.Circle((0,0),0.065,color=fg,zorder=6))

    ax.text(0,-0.22,f"{puntaje:.1f}",ha="center",va="center",
            fontsize=26,fontweight="bold",color=fg,fontfamily="DejaVu Sans")
    ax.text(0,-0.46,banda,ha="center",va="center",
            fontsize=7.5,color="#6b638f",fontfamily="DejaVu Sans")

    for val,lbl in [(0,"0"),(70,"70"),(80,"80"),(90,"90"),(100,"100")]:
        a = math.radians(180-(val/100)*180)
        ax.text(1.22*math.cos(a),1.22*math.sin(a),lbl,
                ha="center",va="center",fontsize=6,
                color="#c9c2b3",fontfamily="DejaVu Sans")

    buf = io.BytesIO()
    plt.savefig(buf,format="png",dpi=160,bbox_inches="tight",
                facecolor="#faf8f3")
    plt.close(fig); buf.seek(0)
    return Image(buf, width=ancho_cm*cm, height=alto_cm*cm)


def crear_radar(competencias, banda, ancho_cm=13, alto_cm=10):
    etiq = list(competencias.keys())
    vals = [competencias[c]["puntaje"] for c in etiq]
    n = len(etiq)
    if n < 3:
        return _barras_fallback(competencias, ancho_cm, alto_cm)

    angles = np.linspace(0,2*np.pi,n,endpoint=False).tolist()
    vc = vals+[vals[0]]; ac = angles+[angles[0]]

    fg = bc(banda,"hex_fg"); bg = bc(banda,"hex_bg")

    fig, ax = plt.subplots(figsize=(ancho_cm/2.54,alto_cm/2.54),
                           subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#ffffff"); ax.set_facecolor("#ffffff")

    theta = np.linspace(0,2*np.pi,300)
    for lo,hi,col in [(65,70,"#fbeaef"),(70,80,"#fdf3ea"),
                      (80,90,"#fdf3ea"),(90,100,"#eaf4ef")]:
        ax.fill_between(theta,lo,hi,color=col,alpha=0.28,zorder=0)

    ax.plot(ac,vc,color=fg,linewidth=2,zorder=3)
    ax.fill(ac,vc,color=bg,alpha=0.50,zorder=2)
    ax.scatter(angles,vals,color=fg,s=25,zorder=4)

    etiq_c = [e if len(e)<=18 else e[:16]+"…" for e in etiq]
    ax.set_xticks(angles)
    ax.set_xticklabels(etiq_c,fontsize=8,color="#22194e",
                       fontfamily="DejaVu Sans")
    ax.tick_params(axis="x",pad=10)
    ax.set_ylim(60,100)
    ax.set_yticks([70,80,90,100])
    ax.set_yticklabels(["70","80","90","100"],
                       fontsize=6.5,color="#c9c2b3",fontfamily="DejaVu Sans")
    ax.grid(color="#e4dfd3",linewidth=0.6)
    ax.spines["polar"].set_color("#e4dfd3")

    buf = io.BytesIO()
    plt.savefig(buf,format="png",dpi=160,bbox_inches="tight",
                facecolor="#ffffff")
    plt.close(fig); buf.seek(0)
    return Image(buf, width=ancho_cm*cm, height=alto_cm*cm)


def _barras_fallback(competencias, ancho_cm, alto_cm):
    etiq = list(competencias.keys())
    vals = [competencias[c]["puntaje"] for c in etiq]
    fig, ax = plt.subplots(figsize=(ancho_cm/2.54, alto_cm/2.54))
    ax.barh(etiq, vals, color="#ff4298", height=0.5)
    ax.set_xlim(60,105)
    buf = io.BytesIO()
    plt.savefig(buf,format="png",dpi=160,bbox_inches="tight",facecolor="#fff")
    plt.close(fig); buf.seek(0)
    return Image(buf, width=ancho_cm*cm, height=alto_cm*cm)

# ---------------------------------------------------------------------------
# Header / Footer
# ---------------------------------------------------------------------------

def _header(c, nombre, proceso, page_num):
    y = H - PAD_TOP + 0.1*cm
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.line(PAD_LAT, y-0.70*cm, W-PAD_LAT, y-0.70*cm)

    c.setFont("Helvetica-Bold",8); c.setFillColor(MAGENTA)
    c.drawString(PAD_LAT, y-0.44*cm, "evaluar.com")

    c.setStrokeColor(LINE_STR); c.setLineWidth(0.5)
    c.line(PAD_LAT+1.8*cm, y-0.14*cm, PAD_LAT+1.8*cm, y-0.60*cm)

    c.setFont("Helvetica",8); c.setFillColor(INK_SOFT)
    c.drawString(PAD_LAT+2.0*cm, y-0.44*cm, proceso)
    c.drawRightString(W-PAD_LAT, y-0.44*cm,
                      f"{nombre}  ·  {page_num:02d} / {TOTAL_PAGES:02d}")


def _footer(c, proceso, page_num):
    y = PAD_BOT - 0.4*cm
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.line(PAD_LAT, y+0.55*cm, W-PAD_LAT, y+0.55*cm)
    c.setFont("Helvetica",7.5); c.setFillColor(INK_SOFT)
    c.drawString(PAD_LAT, y+0.25*cm, f"evaluar.com  ·  {proceso}")
    c.drawRightString(W-PAD_LAT, y+0.25*cm,
                      f"{page_num:02d} / {TOTAL_PAGES:02d}")

# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------

def _portada(c, nombre, proceso, cliente, fecha, cargo="", area=""):
    c.setFillColor(PAPER); c.rect(0,0,W,H,fill=1,stroke=0)

    # Acento decorativo esquina superior derecha
    c.setFillColorRGB(1,0.259,0.596,alpha=0.07)
    c.circle(W+30, H+10, 190, fill=1, stroke=0)
    c.setFillColorRGB(1,0.671,0.282,alpha=0.05)
    c.circle(W, H+40, 140, fill=1, stroke=0)

    # Header
    y = H - PAD_TOP
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.line(PAD_LAT, y-0.70*cm, W-PAD_LAT, y-0.70*cm)
    c.setFont("Helvetica-Bold",9); c.setFillColor(MAGENTA)
    c.drawString(PAD_LAT, y-0.44*cm, "evaluar.com")
    c.setStrokeColor(LINE_STR); c.setLineWidth(0.5)
    c.line(PAD_LAT+1.9*cm, y-0.14*cm, PAD_LAT+1.9*cm, y-0.62*cm)
    c.setFont("Helvetica",8.5); c.setFillColor(INK_SOFT)
    c.drawString(PAD_LAT+2.1*cm, y-0.44*cm, cliente)
    c.setFont("Helvetica",8); c.setFillColor(INK_SOFT)
    c.drawRightString(W-PAD_LAT, y-0.44*cm, fecha)

    # Hero: eyebrow
    y_hero = H*0.60
    c.setFont("Helvetica-Bold",7.5); c.setFillColor(MAGENTA)
    c.drawString(PAD_LAT, y_hero+1.1*cm, proceso.upper())
    c.setStrokeColor(MAGENTA); c.setLineWidth(1.5)
    c.line(PAD_LAT, y_hero+0.82*cm, PAD_LAT+1.1*cm, y_hero+0.82*cm)

    # Nombre (dividido en dos líneas)
    partes = nombre.split()
    mitad  = max(1, len(partes)//2)
    l1 = " ".join(partes[:mitad])
    l2 = " ".join(partes[mitad:])

    c.setFont("Helvetica-Bold",42); c.setFillColor(INK)
    c.drawString(PAD_LAT, y_hero, l1)
    if l2:
        c.setFont("Helvetica-BoldOblique",42); c.setFillColor(INK2)
        c.drawString(PAD_LAT, y_hero-1.65*cm, l2)

    y_sep = y_hero - (2.55*cm if l2 else 1.30*cm)
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.line(PAD_LAT, y_sep, W-PAD_LAT, y_sep)

    # Ficha en grid 2 col
    campos = [("Proceso", proceso), ("Empresa", cliente)]
    if cargo: campos.insert(0, ("Rol / Puesto", cargo))
    if area:  campos.append(("Área", area))

    col_w = (W - 2*PAD_LAT) / 2
    y_fi  = y_sep - 0.55*cm

    for i, (k, v) in enumerate(campos):
        x = PAD_LAT + (i%2)*col_w
        y = y_fi - (i//2)*1.35*cm
        c.setFont("Helvetica",7.5); c.setFillColor(INK_SOFT)
        c.drawString(x, y, k.upper())
        c.setFont("Helvetica-Bold",12); c.setFillColor(INK)
        v2 = v if len(v) <= 34 else v[:32]+"…"
        c.drawString(x, y-0.42*cm, v2)

    # Footer portada
    yf = PAD_BOT
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.line(PAD_LAT, yf+0.55*cm, W-PAD_LAT, yf+0.55*cm)
    c.setFont("Helvetica",8); c.setFillColor(INK_SOFT)
    c.drawString(PAD_LAT, yf+0.25*cm,
                 "Reporte Individual  ·  Confidencial · Uso interno de RRHH")
    c.drawRightString(W-PAD_LAT, yf+0.25*cm, f"01 / {TOTAL_PAGES:02d}")

# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

def _tabla_tipos(desglose, pesos, ancho, estilos):
    tipos = [t for t in TIPOS_ORDEN if t in desglose]
    enc = [Paragraph(x, estilos["th"]) for x in
           ["TIPO DE EVALUADOR","PESO","PUNTAJE","BANDA"]]
    filas = [enc]
    for t in tipos:
        pts = desglose[t]; peso = pesos.get(t,0)
        banda = banda_desde_pts(pts); fg = bc(banda,"fg")
        filas.append([
            Paragraph(t, estilos["td_comp"]),
            Paragraph(f"{peso:.0f}%",
                      ParagraphStyle("p",fontName="Helvetica",fontSize=10,
                                     textColor=INK_SOFT,leading=14,
                                     alignment=TA_RIGHT)),
            Paragraph(f"<b>{pts:.1f}</b>",
                      ParagraphStyle("n",fontName="Helvetica-Bold",fontSize=10,
                                     textColor=fg,leading=14,alignment=TA_RIGHT)),
            Paragraph(banda,
                      ParagraphStyle("b",fontName="Helvetica-Bold",fontSize=8,
                                     textColor=fg,leading=12)),
        ])

    t = Table(filas, colWidths=[ancho*.38,ancho*.12,ancho*.18,ancho*.32],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,0),7),("BOTTOMPADDING",(0,0),(-1,0),5),
        ("LINEBELOW",     (0,0),(-1,0),0.8,LINE_STR),
        ("TOPPADDING",    (0,1),(-1,-1),7),("BOTTOMPADDING",(0,1),(-1,-1),7),
        ("LINEBELOW",     (0,1),(-1,-1),0.4,LINE),
        ("LEFTPADDING",   (0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",         (1,0),(2,-1),"RIGHT"),
    ]))
    return t


def _tabla_competencias(competencias, ancho, estilos):
    tipos = []
    for d in competencias.values():
        for t in TIPOS_ORDEN:
            if t in d["desglose_tipo"] and t not in tipos:
                tipos.append(t)

    primer = next(iter(competencias.values()))

    enc1 = [Paragraph("COMPETENCIA", estilos["th"])]
    for t in tipos:
        enc1.append(Paragraph(t.upper(), estilos["th"]))
    enc1.append(Paragraph("PONDERADO", estilos["th"]))

    enc2 = [Paragraph("", estilos["th"])]
    for t in tipos:
        p = primer["pesos_aplicados"].get(t, 0)
        enc2.append(Paragraph(f"{p:.0f}%",
                    ParagraphStyle("pw",fontName="Helvetica",fontSize=8,
                                   textColor=MAGENTA,leading=11,
                                   alignment=TA_CENTER)))
    enc2.append(Paragraph("", estilos["th"]))

    filas = [enc1, enc2]
    for nom, d in competencias.items():
        banda = d["clasificacion"]["etiqueta"]; fg = bc(banda,"fg")
        fila = [Paragraph(nom, estilos["td_comp"])]
        for t in tipos:
            pts = d["desglose_tipo"].get(t)
            if pts is not None:
                fila.append(Paragraph(f"{pts:.1f}", estilos["td_num"]))
            else:
                fila.append(Paragraph("—",
                            ParagraphStyle("dash",fontName="Helvetica",
                                           fontSize=9,textColor=INK_SOFT,
                                           leading=13,alignment=TA_RIGHT)))
        fila.append(Paragraph(f"<b>{d['puntaje']:.1f}</b>",
                    ParagraphStyle("pond",fontName="Helvetica-Bold",fontSize=11,
                                   textColor=fg,leading=14,alignment=TA_RIGHT)))
        filas.append(fila)

    n = len(tipos)
    cw = [ancho*.30] + [(ancho*.50)/max(n,1)]*n + [ancho*.20]
    t  = Table(filas, colWidths=cw, repeatRows=2)

    style = [
        ("TOPPADDING",    (0,0),(-1,1),6),
        ("BOTTOMPADDING", (0,0),(-1,0),4),("BOTTOMPADDING",(0,1),(-1,1),6),
        ("LINEBELOW",     (0,0),(-1,0),0.5,LINE_STR),
        ("LINEBELOW",     (0,1),(-1,1),0.8,LINE_STR),
        ("TOPPADDING",    (0,2),(-1,-1),8),("BOTTOMPADDING",(0,2),(-1,-1),8),
        ("LINEBELOW",     (0,2),(-1,-1),0.4,LINE),
        ("LEFTPADDING",   (0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",         (1,0),(-1,-1),"RIGHT"),
        ("ALIGN",         (0,0),(0,-1),"LEFT"),
    ]
    for i in range(len(competencias)):
        if i%2==0:
            style.append(("BACKGROUND",(0,i+2),(-2,i+2),PAPER2))
    t.setStyle(TableStyle(style))
    return t


def _leyenda_bandas(ancho, estilos):
    items = [
        ("Alto Desempeño","≥ 90","#eaf4ef","#2f7d5e"),
        ("Satisfactorio","80–89","#fdf3ea","#b45a1f"),
        ("Bajo Desempeño","70–79","#fdf3ea","#b45a1f"),
        ("Insatisfactorio","< 70","#fbeaef","#a32a4d"),
    ]
    celdas = []
    for etiq, rng, bg, fg in items:
        inner = Table([[Paragraph(
            f"<b>{etiq}</b>   {rng}",
            ParagraphStyle("ley",fontName="Helvetica-Bold",fontSize=8.5,
                           textColor=colors.HexColor(fg),leading=13),
        )]], colWidths=[ancho/4 - 0.4*cm])
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1),colors.HexColor(bg)),
            ("TOPPADDING",    (0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",   (0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ]))
        celdas.append(inner)

    t = Table([celdas], colWidths=[ancho/4]*4)
    t.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",   (0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
        ("VALIGN",       (0,0),(-1,-1),"TOP"),
    ]))
    return t

# ---------------------------------------------------------------------------
# Texto descriptivo por banda
# ---------------------------------------------------------------------------

def _desc_banda(banda):
    return {
        "Alto Desempeño": (
            "El colaborador demuestra un desempeño que supera las expectativas "
            "de manera consistente. Sus resultados reflejan dominio sólido de "
            "las competencias evaluadas y lo posicionan como referente positivo "
            "dentro del equipo."
        ),
        "Satisfactorio": (
            "El colaborador cumple con las expectativas del rol de forma adecuada. "
            "Las competencias evaluadas están en el nivel esperado, con oportunidades "
            "puntuales de mejora para alcanzar un desempeño destacado."
        ),
        "Bajo Desempeño": (
            "El colaborador cumple parcialmente con las expectativas. Se identifican "
            "brechas en varias competencias que requieren atención y un plan de "
            "desarrollo estructurado para alcanzar el nivel requerido."
        ),
        "Insatisfactorio": (
            "El colaborador no alcanza las expectativas mínimas del rol. Se requiere "
            "intervención inmediata con acompañamiento continuo y seguimiento "
            "estrecho para revertir esta situación."
        ),
    }.get(banda, "")

# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def generar_pdf(nombre, resultado, proceso, cliente, fecha,
                cargo="", area="", ruta_salida="informe.pdf"):

    estilos = E()
    ancho_cont = W - 2*PAD_LAT

    frame_y = PAD_BOT + 0.85*cm
    frame_h = H - PAD_TOP - 1.0*cm - frame_y
    frame   = Frame(PAD_LAT, frame_y, ancho_cont, frame_h,
                    leftPadding=0, rightPadding=0,
                    topPadding=0, bottomPadding=0, showBoundary=0)

    def on_first(canvas, doc):
        canvas.saveState()
        _portada(canvas, nombre, proceso, cliente, fecha, cargo, area)
        canvas.restoreState()

    def on_later(canvas, doc):
        canvas.saveState()
        _header(canvas, nombre, proceso, doc.page)
        _footer(canvas, proceso, doc.page)
        canvas.restoreState()

    doc = BaseDocTemplate(ruta_salida, pagesize=A4,
                          leftMargin=0, rightMargin=0,
                          topMargin=0, bottomMargin=0)
    doc.addPageTemplates([
        PageTemplate(id="portada",   frames=[Frame(0,0,W,H)], onPage=on_first),
        PageTemplate(id="contenido", frames=[frame],           onPage=on_later),
    ])

    puntaje_global = resultado["puntaje_global"]
    banda_global   = resultado["clasificacion"]["etiqueta"]
    competencias   = resultado["competencias"]
    desglose       = resultado["desglose_global"]
    pesos          = resultado["pesos_aplicados"]

    story = [PageBreak()]   # saltar portada

    # PÁG 2 — Resultado general
    story += [
        Paragraph("SECCIÓN 01  ·  RESUMEN GENERAL", estilos["section_id"]),
        spacer(0.15),
        Paragraph("Resultado de la<br/>Evaluación 360°", estilos["section_h"]),
        hr(LINE, sb=8, sa=8),
    ]

    gauge  = crear_gauge(puntaje_global, banda_global)
    fg_hex = bc(banda_global,"hex_fg")

    celda_izq = [gauge]
    celda_der = [
        spacer(0.5),
        Paragraph(f"{puntaje_global:.1f}",
                  ParagraphStyle("gn",fontName="Helvetica-Bold",fontSize=52,
                                 textColor=colors.HexColor(fg_hex),leading=52)),
        Paragraph(banda_global.upper(),
                  ParagraphStyle("gp",fontName="Helvetica-Bold",fontSize=9,
                                 textColor=colors.HexColor(fg_hex),leading=14)),
        spacer(0.3),
        Paragraph(_desc_banda(banda_global),
                  ParagraphStyle("gd",fontName="Helvetica",fontSize=10,
                                 textColor=INK2,leading=16,
                                 alignment=TA_JUSTIFY)),
    ]

    layout = Table([[celda_izq, celda_der]],
                   colWidths=[7*cm, ancho_cont-7*cm])
    layout.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(layout)
    story += [hr(LINE, sb=10, sa=8),
              Paragraph("Puntaje por tipo de evaluador", estilos["h3"]),
              spacer(0.2),
              _tabla_tipos(desglose, pesos, ancho_cont, estilos),
              spacer(0.3),
              Paragraph(
                  "Los pesos se redistribuyen proporcionalmente cuando algún "
                  "tipo de evaluador no participa en la evaluación.",
                  estilos["nota"])]

    # PÁG 3 — Detalle por competencia
    story += [
        PageBreak(),
        Paragraph("SECCIÓN 02  ·  COMPETENCIAS", estilos["section_id"]),
        spacer(0.15),
        Paragraph("Detalle por<br/>Competencia", estilos["section_h"]),
        hr(LINE, sb=8, sa=8),
        _tabla_competencias(competencias, ancho_cont, estilos),
        spacer(0.35),
        Paragraph(
            "Cada valor refleja el promedio de todos los ítems evaluados dentro "
            "de esa competencia para ese tipo de evaluador. El puntaje ponderado "
            "aplica los pesos según los evaluadores presentes.",
            estilos["nota"]),
    ]

    # PÁG 4 — Radar
    story += [
        PageBreak(),
        Paragraph("SECCIÓN 03  ·  MAPA DE COMPETENCIAS", estilos["section_id"]),
        spacer(0.15),
        Paragraph("Perfil de<br/>Competencias", estilos["section_h"]),
        hr(LINE, sb=8, sa=4),
    ]
    radar = crear_radar(competencias, banda_global)
    t_radar = Table([[radar]], colWidths=[ancho_cont])
    t_radar.setStyle(TableStyle([
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(t_radar)
    story += [spacer(0.4), _leyenda_bandas(ancho_cont, estilos)]

    doc.build(story)
    print(f"  ✓  {ruta_salida}")