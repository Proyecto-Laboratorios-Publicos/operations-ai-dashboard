import io
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_ejecutivo(tipo_reporte, texto_informe, img_bytes=None):
    buffer = io.BytesIO()
    # Márgenes reducidos para aprovechar mejor el espacio de la hoja (menos blanco)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=35, 
        leftMargin=35, 
        topMargin=35, 
        bottomMargin=35
    )
    
    styles = getSampleStyleSheet()
    
    # Paleta corporativa moderna
    color_primario = colors.HexColor('#0f172a')   # Slate oscuro profesional
    color_secundario = colors.HexColor('#2563eb') # Azul vibrante
    color_fondo_caja = colors.HexColor('#f1f5f9') # Gris muy suave para bloques
    color_borde = colors.HexColor('#cbd5e1')      # Borde sutil
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, textColor=color_primario, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10.5, textColor=color_secundario, spaceBefore=6, spaceAfter=4)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#334155'), spaceAfter=4)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#64748b'))

    story = []
    
    # --- 1. CABECERA TIPO TARJETA GERENCIAL (Elimina el blanco superior) ---
    header_data = [
        [Paragraph("<b>REPORTE EJECUTIVO OFICIAL - INDEC</b>", estilo_titulo)],
        [Paragraph(f"<b>Enfoque analítico:</b> {tipo_reporte}", estilo_meta)]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_fondo_caja),
        ('BOX', (0, 0), (-1, -1), 1, color_borde),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # --- 2. GRÁFICO INTEGRADO EN BLOQUE ---
    if img_bytes:
        # Contenedor visual para el gráfico
        chart_table = Table([[RLImage(io.BytesIO(img_bytes), width=520, height=170)]], colWidths=[540])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, color_borde),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 10))

    # --- 3. CUERPO DEL INFORME ESTRUCTURADO ---
    lineas = texto_informe.split("\n")
    for linea in lineas:
        linea_limpia = linea.strip()
        if linea_limpia:
            if "|" in linea_limpia or "---" in linea_limpia:
                continue
            
            if linea_limpia.startswith("###") or linea_limpia.startswith("##"):
                sub_txt = linea_limpia.replace("#", "").strip()
                story.append(Paragraph(f"<b>{html.escape(sub_txt)}</b>", estilo_subtitulo))
            else:
                formateado = linea_limpia.replace("**", "<b>", 1).replace("**", "</b>", 1)
                formateado = formateado.replace("*", "•")
                texto_seguro = html.escape(formateado).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
                story.append(Paragraph(texto_seguro, estilo_cuerpo))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
