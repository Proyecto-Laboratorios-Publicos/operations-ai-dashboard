import io
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def agregar_fondo_beige(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#f7f5f0')) # Beige cálido no invasivo
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.restoreState()

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
    
    color_primario = colors.HexColor('#1e293b')
    color_secundario = colors.HexColor('#0284c7')
    color_fondo_caja = colors.HexColor('#ffffff')
    color_borde = colors.HexColor('#e2e8f0')
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=color_primario, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, textColor=color_secundario, spaceBefore=8, spaceAfter=4)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=4)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#64748b'))

    story = []
    
   # 1. Cabecera tipo tarjeta gerencial con fondo azul marino y texto blanco
    header_data = [
        [Paragraph("<b>REPORTE EJECUTIVO OFICIAL - INDEC</b>", ParagraphStyle('TitBlanco', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.white, spaceAfter=2))],
        [Paragraph(f"<b>Enfoque analítico:</b> {tipo_reporte}", ParagraphStyle('MetaBlanco', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#e2e8f0')))]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1e3a8a')), # Azul marino formal
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e293b')),
        ('PADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # 2. Gráfico integrado en bloque
    if img_bytes:
        chart_table = Table([[RLImage(io.BytesIO(img_bytes), width=520, height=160)]], colWidths=[540])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_fondo_caja),
            ('BOX', (0, 0), (-1, -1), 0.5, color_borde),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 8))

    # 3. Procesamiento y limpieza total del texto (Adiós asteriscos y cuadrados)
    lineas = texto_informe.split("\n")
    for linea in lineas:
        linea_limpia = linea.strip()
        if linea_limpia:
            if "|" in linea_limpia or "---" in linea_limpia:
                continue
            
            # Limpieza profunda de caracteres conflictivos
            reemplazos = {"—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "■": " "}
            for char_malo, char_bueno in reemplazos.items():
                linea_limpia = linea_limpia.replace(char_malo, char_bueno)
            
            # Detectar y limpiar títulos con hashes (###)
            if linea_limpia.startswith("#"):
                sub_txt = linea_limpia.replace("#", "").strip()
                story.append(Paragraph(f"<b>{html.escape(sub_txt)}</b>", estilo_subtitulo))
            else:
                # Quitamos los asteriscos sueltos de markdown feos y dejamos negritas limpias si las hay
                texto_limpio = linea_limpia.replace("**", "")
                
                # Formatear viñetas prolijas
                if texto_limpio.startswith("-") or texto_limpio.startswith("*"):
                    texto_limpio = "• " + texto_limpio[1:].strip()
                
                story.append(Paragraph(html.escape(texto_limpio), estilo_cuerpo))

    doc.build(story, onFirstPage=agregar_fondo_beige, onLaterPages=agregar_fondo_beige)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
