import io
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def agregar_fondo_beige(canvas, doc):
    canvas.saveState()
    # Fondo beige/marfil suave y cálido (cero reflejos molestos)
    canvas.setFillColor(colors.HexColor('#f5f2eb'))
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
    
    color_primario = colors.HexColor('#0f172a')   # Slate muy oscuro
    color_secundario = colors.HexColor('#0369a1') # Azul corporativo sobrio
    color_fondo_caja = colors.HexColor('#ffffff') # Tarjetas interiores limpias
    color_borde = colors.HexColor('#cbd5e1')      # Borde sutil
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.white, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, textColor=color_secundario, spaceBefore=8, spaceAfter=4)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=4)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#cbd5e1'))

    story = []
    
    # 1. Cabecera con Azul Metalizado Oscuro y bordes inferiores profundos (Efecto oscurecido anti-flash)
    header_data = [
        [Paragraph("<b>REPORTE EJECUTIVO OFICIAL - INDEC</b>", estilo_titulo)],
        [Paragraph(f"<b>Enfoque analítico:</b> {tipo_reporte}", estilo_meta)]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')), # Azul marino metalizado / casi negro
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#020617')),    # Borde oscuro profundo
        ('LINEBELOW', (0, 1), (-1, 1), 2, colors.HexColor('#000000')), # Sombra inferior acentuada
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

    # 3. Procesamiento y limpieza total del texto
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
