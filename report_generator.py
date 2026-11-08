import io
import re
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def agregar_fondo_beige(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#f5f2eb')) # Fondo marfil cálido antideslumbrante
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.restoreState()

def crear_tabla_resumen_desde_texto(texto_informe, estilo_celda, estilo_header):
    """Extrae las métricas del texto y construye una tabla estructurada de nivel ejecutivo."""
    datos = [["Región / Categoría analizada", "Métrica / Variación"]]
    
    for linea in texto_informe.split("\n"):
        match = re.search(r"[•\-]?\s*([A-Za-zÁÉÍÓÚáéíóúñ\s()]+):\s*([0-9]+[.,][0-9]+\s*pp|[0-9]+[.,][0-9]+)", linea)
        if match:
            reg = match.group(1).strip()
            val = match.group(2).strip()
            # Evitamos duplicados y títulos largos
            if len(reg) < 25 and [reg, val] not in datos:
                datos.append([reg, val])
                
    # Si encontramos suficientes filas de datos, armamos una tabla prolija
    if len(datos) > 1:
        # Tomamos hasta 6 filas principales para que quede estético
        filas_tabla = [datos[0]] + datos[1:7]
        t = Table([[Paragraph(cell, estilo_header) if i == 0 else Paragraph(cell, estilo_celda) for cell in fila] for i, fila in enumerate(filas_tabla)], colWidths=[320, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')), # Encabezado azul profesional
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        return t
    return None

def generar_pdf_ejecutivo(tipo_reporte, texto_informe, img_bytes=None, img_bytes_extra=None):
    buffer = io.BytesIO()
    # Mantenemos márgenes profesionales pero permitimos que el documento crezca dinámicamente en páginas
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    styles = getSampleStyleSheet()
    
    color_fondo_caja = colors.HexColor('#ffffff')
    color_borde = colors.HexColor('#cbd5e1')
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.white, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0369a1'), spaceBefore=10, spaceAfter=4, keepWithNext=True)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=5)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#cbd5e1'))
    estilo_th = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)
    estilo_td = ParagraphStyle('TD', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#334155'))

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
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # 2. Gráfico principal compacto
    if img_bytes:
        chart_table = Table([[RLImage(io.BytesIO(img_bytes), width=500, height=130)]], colWidths=[540])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_fondo_caja),
            ('BOX', (0, 0), (-1, -1), 0.5, color_borde),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 6))

    # 2.1 Tabla Resumen Ejecutiva automática (captura más filas para aprovechar el espacio)
    datos = [["Región / Categoria analizada", "Métrica / Variación"]]
    for linea in texto_informe.split("\n"):
        match = re.search(r"[•\-]?\s*([A-Za-zÁÉÍÓÚáéíóúñ\s()]+):\s*([0-9]+[.,][0-9]+\s*pp|[0-9]+[.,][0-9]+)", linea)
        if match:
            reg = match.group(1).strip()
            val = match.group(2).strip()
            if len(reg) < 25 and [reg, val] not in datos:
                datos.append([reg, val])
                
    if len(datos) > 1:
        # Permitimos hasta 12 filas para mostrar todo el desglose regional en la tabla
        filas_tabla = [datos[0]] + datos[1:13]
        t = Table([[Paragraph(cell, estilo_header) if i == 0 else Paragraph(cell, estilo_td) for cell in fila] for i, fila in enumerate(filas_tabla)], colWidths=[320, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # 3. Procesamiento completo del texto sin recortes
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

    # Compilación con soporte para múltiples páginas fluidas (fondos aplicados a todas las hojas)
    doc.build(story, onFirstPage=agregar_fondo_beige, onLaterPages=agregar_fondo_beige)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
