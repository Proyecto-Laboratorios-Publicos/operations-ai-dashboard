import io
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_ejecutivo(tipo_reporte, texto_informe, img_bytes=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=40, 
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Paleta corporativa elegante
    color_primario = colors.HexColor('#1e3a8a') # Azul oscuro formal
    color_secundario = colors.HexColor('#3b82f6') # Azul acento
    color_texto = colors.HexColor('#1f2937')
    color_fondo_caja = colors.HexColor('#f8fafc')
    
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, spaceAfter=2, textColor=color_primario)
    estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, spaceAfter=6, spaceBefore=10, textColor=color_secundario)
    estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=6, textColor=color_texto)
    estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, leading=12, spaceAfter=10, textColor=colors.HexColor('#6b7280'))

    story = []
    
    # Encabezado con bloque estilizado (Caja resumen superior)
    story.append(Paragraph("<b>INFORME TÉCNICO OFICIAL - INDEC</b>", estilo_titulo))
    story.append(Paragraph(f"<b>Enfoque del análisis:</b> {tipo_reporte}", estilo_meta))
    story.append(Spacer(1, 4))

    # Incrustar gráfico si está disponible dentro de una estructura visual limpia
    if img_bytes:
        story.append(RLImage(io.BytesIO(img_bytes), width=510, height=190))
        story.append(Spacer(1, 12))

    # Procesamiento y estructuración del texto del informe
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
