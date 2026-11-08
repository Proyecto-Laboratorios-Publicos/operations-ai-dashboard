import io
import re
import html
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def agregar_fondo_beige(canvas, doc):
    canvas.saveState()
    # Fondo marfil cálido antideslumbrante (cero flash bomb)
    canvas.setFillColor(colors.HexColor('#f5f2eb'))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.restoreState()

def crear_grafico_plotly_desde_texto(texto_informe):
    """Extrae métricas del texto del informe y genera un gráfico ejecutivo con Plotly."""
    regiones = []
    valores = []
    
    for linea in texto_informe.split("\n"):
        match = re.search(r"[•\-]?\s*([A-Za-zÁÉÍÓÚáéíóúñ\s()]+):\s*([0-9]+[.,][0-9]+)\s*pp", linea)
        if match:
            regiones.append(match.group(1).strip())
            valores.append(float(match.group(2).replace(",", ".")))
            
    if len(regiones) < 3:
        for linea in texto_informe.split("\n"):
            match_gen = re.search(r"[•\-]?\s*([A-Za-zÁÉÍÓÚáéíóúñ\s()]+):\s*([0-9]+[.,][0-9]+)", linea)
            if match_gen and match_gen.group(1).strip() not in regiones:
                regiones.append(match_gen.group(1).strip())
                try:
                    valores.append(float(match_gen.group(2).replace(",", ".")))
                except ValueError:
                    pass

    if regiones and valores and len(regiones) == len(valores):
        df_auto = pd.DataFrame({"Categoria": regiones[-7:], "Valor": valores[-7:]})
        
        fig = px.bar(
            df_auto, x="Valor", y="Categoria", orientation="h",
            title="<b>Incidencia Regional Reciente (Extraída del Análisis)</b>",
            labels={"Valor": "Puntaje / Variación", "Categoria": ""}
        )
        fig.update_layout(
            width=650, height=210,
            margin=dict(l=20, r=20, t=35, b=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=9, color="#334155")
        )
        try:
            return fig.to_image(format="png", scale=2)
        except Exception:
            return None
    return None

def generar_pdf_ejecutivo(tipo_reporte, texto_informe, img_bytes=None, img_bytes_extra=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=35, 
        leftMargin=35, 
        topMargin=35, 
        bottomMargin=35
    )
    
    styles = getSampleStyleSheet()
    color_fondo_caja = colors.HexColor('#ffffff')
    color_borde = colors.HexColor('#cbd5e1')
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.white, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0369a1'), spaceBefore=8, spaceAfter=4)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=4)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#cbd5e1'))

    story = []
    
    # 1. Cabecera azul metalizado oscuro (anti-flash)
    header_data = [
        [Paragraph("<b>REPORTE EJECUTIVO OFICIAL - INDEC</b>", estilo_titulo)],
        [Paragraph(f"<b>Enfoque analítico:</b> {tipo_reporte}", estilo_meta)]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#020617')),
        ('LINEBELOW', (0, 1), (-1, 1), 2, colors.HexColor('#000000')),
        ('PADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # 2. Gráfico principal de la app (si viene)
    if img_bytes:
        chart_table = Table([[RLImage(io.BytesIO(img_bytes), width=520, height=150)]], colWidths=[540])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_fondo_caja),
            ('BOX', (0, 0), (-1, -1), 0.5, color_borde),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 6))

    # 2.1 Gráfico automático generado con Plotly desde el texto del informe
    img_bytes_auto = crear_grafico_plotly_desde_texto(texto_informe)
    if img_bytes_auto:
        chart_table_auto = Table([[RLImage(io.BytesIO(img_bytes_auto), width=520, height=140)]], colWidths=[540])
        chart_table_auto.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_fondo_caja),
            ('BOX', (0, 0), (-1, -1), 0.5, color_borde),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table_auto)
        story.append(Spacer(1, 6))

    # 3. Procesamiento y limpieza del texto
    lineas = texto_informe.split("\n")
    for linea in lineas:
        linea_limpia = linea.strip()
        if linea_limpia:
            if "|" in linea_limpia or "---" in linea_limpia:
                continue
            
            reemplazos = {"—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "■": " "}
            for char_malo, char_bueno in reemplazos.items():
                linea_limpia = linea_limpia.replace(char_malo, char_bueno)
            
            if linea_limpia.startswith("#"):
                sub_txt = linea_limpia.replace("#", "").strip()
                story.append(Paragraph(f"<b>{html.escape(sub_txt)}</b>", estilo_subtitulo))
            else:
                texto_limpio = linea_limpia.replace("**", "")
                if texto_limpio.startswith("-") or texto_limpio.startswith("*"):
                    texto_limpio = "• " + texto_limpio[1:].strip()
                story.append(Paragraph(html.escape(texto_limpio), estilo_cuerpo))

    doc.build(story, onFirstPage=agregar_fondo_beige, onLaterPages=agregar_fondo_beige)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
