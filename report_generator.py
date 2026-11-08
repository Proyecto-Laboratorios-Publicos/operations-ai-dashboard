import io
import re
import html
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def agregar_fondo_beige(canvas, doc):
    canvas.saveState()
    # Fondo beige/marfil cálido y suave (cero reflejos/flash bomb)
    canvas.setFillColor(colors.HexColor('#f5f2eb'))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.restoreState()

def crear_grafico_desde_texto(texto_informe):
    """Extrae métricas numéricas del texto del informe y genera un gráfico ejecutivo automático."""
    regiones = []
    valores = []
    
    # Patrón para buscar líneas como "• Noreste: 8,70 pp" o similares
    for linea in texto_informe.split("\n"):
        match = re.search(r"[•\-]?\s*([A-Za-zÁÉÍÓÚáéíóúñ\s()]+):\s*([0-9]+[.,][0-9]+)\s*pp", linea)
        if match:
            regiones.append(match.group(1).strip())
            valores.append(float(match.group(2).replace(",", ".")))
            
    # Si no encuentra suficientes datos con 'pp', busca formato general
    if len(regiones) < 3:
        for linea in texto_informe.split("\n"):
            match_gen = re.search(r"[•\-]?\s*([A-Za-zÁÉÍÓÚáéíóúñ\s()]+):\s*([0-9]+[.,][0-9]+)", linea)
            if match_gen and match_gen.group(1).strip() not in regiones:
                regiones.append(match_gen.group(1).strip())
                try:
                    valores.append(float(match_gen.group(2).replace(",", ".")))
                except ValueError:
                    pass

    # Si encontramos datos válidos, armamos un gráfico limpio y profesional con Matplotlib
    if regiones and valores and len(regiones) == len(valores):
        # Tomamos los últimos o primeros 6-8 valores para que no se sature el gráfico
        regiones = regiones[-7:]
        valores = valores[-7:]
        
        fig, ax = plt.subplots(figsize=(6, 2.2))
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#ffffff')
        
        bars = ax.barh(regiones, valores, color='#0284c7', height=0.6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['bottom'].set_color('#cbd5e1')
        
        ax.tick_params(axis='both', labelsize=8, colors='#334155')
        ax.set_title("Incidencia Regional Reciente (Extraída del Análisis)", fontsize=9, fontweight='bold', color='#0f172a', pad=10)
        
        # Añadir las etiquetas de valor al lado de cada barra
        for bar in bars:
            width = bar.get_width()
            ax.annotate(f'{width:.2f} pp',
                        xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0), textcoords="offset points",
                        ha='left', va='center', fontsize=7, color='#334155', fontweight='bold')

        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        img_buffer.seek(0)
        return img_buffer.read()
        
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

    # 2.1 NUEVO GRÁFICO AUTOMÁTICO EXTRAÍDO DEL TEXTO DEL INFORME
    img_bytes_auto = crear_grafico_desde_texto(texto_informe)
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
