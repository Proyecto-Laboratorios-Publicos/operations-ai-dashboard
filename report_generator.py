import io
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Función para pintar el fondo de la página de color beige suave en cada hoja generada
def agregar_fondo_beige(canvas, doc):
    canvas.saveState()
    # Color beige cálido / marfil muy suave (no invasivo a la vista)
    canvas.setFillColor(colors.HexColor('#f7f5f0'))
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
    
    # Paleta corporativa armónica con el fondo beige
    color_primario = colors.HexColor('#1e293b')   # Slate oscuro sobrio
    color_secundario = colors.HexColor('#0284c7') # Azul profesional
    color_fondo_caja = colors.HexColor('#ffffff') # Blanco puro para contraste en las tarjetas
    color_borde = colors.HexColor('#e2e8f0')      # Borde sutil
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=color_primario, spaceAfter=2)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, textColor=color_secundario, spaceBefore=6, spaceAfter=3)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=4)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#64748b'))

    story = []
    
    # --- 1. CABECERA TIPO TARJETA SOBRE FONDO BEIGE ---
    header_data = [
        [Paragraph("<b>REPORTE EJECUTIVO OFICIAL - INDEC</b>", estilo_titulo)],
        [Paragraph(f"<b>Enfoque analítico:</b> {tipo_reporte}", estilo_meta)]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_fondo_caja),
        ('BOX', (0, 0), (-1, -1), 1, color_borde),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # --- 2. GRÁFICOS VISUALES EN BLOQUE ---
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

    # --- 3. CUERPO DEL INFORME ESTRUCTURADO Y BLINDAJE CONTRA CARACTERES ---
    lineas = texto_informe.split("\n")
    for linea in lineas:
        linea_limpia = linea.strip()
        if linea_limpia:
            if "|" in linea_limpia or "---" in linea_limpia:
                continue
            
            # Limpieza total de caracteres que confunden al parser de ReportLab
            linea_limpia = linea_limpia.replace("=", " - ").replace("$", "").replace("■", " ")
            
            if linea_limpia.startswith("###") or linea_limpia.startswith("##"):
                sub_txt = linea_limpia.replace("#", "").strip()
                story.append(Paragraph(f"<b>{html.escape(sub_txt)}</b>", estilo_subtitulo))
            else:
                # Primero escapamos todo el texto de forma segura para HTML
                texto_escapado = html.escape(linea_limpia)
                # Luego reemplazamos las negritas de markdown por etiquetas <b> de ReportLab
                texto_escapado = texto_escapado.replace("**", "<b>", 1).replace("**", "</b>", 1)
                texto_escapado = texto_escapado.replace("*", "•")
                
                story.append(Paragraph(texto_escapado, estilo_cuerpo))
    
    # Compilamos el documento aplicando la función de fondo beige en cada página
    doc.build(story, onFirstPage=agregar_fondo_beige, onLaterPages=agregar_fondo_beige)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
