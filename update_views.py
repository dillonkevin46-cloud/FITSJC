import os
import re

views_path = r"c:\Apps_Dev\FITSJCDEV\jobcards\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update imports
content = content.replace("from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether", 
                          "from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether, BaseDocTemplate, PageTemplate, Frame")

# 2. Extract PDF GENERATOR section
start_marker = "# --- PDF GENERATOR ---"
end_marker = "def generate_dummy_pdf_buffer():"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_pdf_logic = """# --- PDF GENERATOR ---

def draw_static_elements(canvas, doc, elements_dict, jobcard, is_dummy, tech_only):
    canvas.saveState()
    width, height = A4

    canvas.setStrokeColorRGB(0.2, 0.2, 0.2)
    canvas.setLineWidth(1)
    canvas.rect(20, 20, width - 40, height - 40)

    settings_obj = GlobalSettings.objects.first()
    watermark_img = None
    if settings_obj:
        if settings_obj.watermark:
            watermark_img = settings_obj.watermark.path
        elif settings_obj.company_logo:
            watermark_img = settings_obj.company_logo.path

    if watermark_img:
        try:
            canvas.saveState()
            canvas.setFillAlpha(0.05)
            img = ImageReader(watermark_img)
            img_w, img_h = img.getSize()
            aspect = img_h / float(img_w)
            target_w = width * 0.6
            target_h = target_w * aspect
            x = (width - target_w) / 2
            y = (height - target_h) / 2
            canvas.drawImage(watermark_img, x, y, width=target_w, height=target_h, preserveAspectRatio=True, mask='auto')
            canvas.restoreState()
        except Exception:
            canvas.restoreState()

    canvas.setFont("Helvetica", 9)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.drawRightString(width - 30, 30, f"Page {doc.page}")

    def get_pdf_y(web_y, element_h):
        return height - web_y - element_h

    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_bold = ParagraphStyle('Bold', parent=style_normal, fontName='Helvetica-Bold')

    def draw_paragraph(text, x, y, w, h, style):
        p = Paragraph(text, style)
        p.wrapOn(canvas, w, h)
        p.drawOn(canvas, x, y + h - p.height)

    for name, el in elements_dict.items():
        if name == 'items_table': continue

        ex, ey, ew, eh = el.pos_x, el.pos_y, el.width, el.height
        pdf_y = get_pdf_y(ey, eh)
        fs = el.font_size or 10

        if name == 'header_logo':
            if settings_obj and settings_obj.company_logo:
                try:
                    canvas.drawImage(settings_obj.company_logo.path, ex, pdf_y, width=ew, height=eh, preserveAspectRatio=True, mask='auto')
                except:
                    pass
            elif is_dummy:
                draw_paragraph("<b>[LOGO]</b>", ex, pdf_y, ew, eh, style_bold)

        elif name == 'company_info':
            c_name = settings_obj.company_name if settings_obj else "Company Name"
            if is_dummy and not settings_obj: c_name = "Acme Corp"
            c_addr = settings_obj.company_address if settings_obj else ""
            if is_dummy and not c_addr: c_addr = "123 Fake Street\\nCity, Country"
            text = f"<b><font size={fs+4}>{escape(c_name)}</font></b><br/>" + escape(c_addr).replace('\\n', '<br/>')
            draw_paragraph(text, ex, pdf_y, ew, eh, style_normal)

        elif name == 'jobcard_meta':
            jc_num = "JC-PREVIEW-123" if is_dummy else jobcard.jobcard_number
            jc_date = "2023-10-27" if is_dummy else (jobcard.created_at.strftime('%Y-%m-%d') if jobcard else "")
            jc_stat = "APPROVED" if is_dummy else (jobcard.get_status_display() if jobcard else "")
            jc_cat = "Call Out" if is_dummy else (jobcard.get_category_display() if jobcard else "")
            text = f"<b>Jobcard No:</b> {escape(jc_num)}<br/><b>Date:</b> {escape(jc_date)}<br/><b>Status:</b> {escape(jc_stat)}<br/><b>Category:</b> {escape(jc_cat)}"
            style_meta = ParagraphStyle('Meta', parent=style_normal, fontSize=fs, leading=fs*1.2)
            draw_paragraph(text, ex, pdf_y, ew, eh, style_meta)

        elif name == 'client_details':
            c_name = "Acme Corp" if is_dummy else (jobcard.client_name if jobcard else "N/A")
            if not is_dummy and jobcard:
                if jobcard.company:
                    c_name = jobcard.company.name
                elif jobcard.client_name:
                    c_name = jobcard.client_name
                else:
                    c_name = "N/A"
            tech_user = jobcard.technician if jobcard and not is_dummy else None
            tech_name = "John Doe" if is_dummy else (tech_user.get_full_name() or tech_user.username if tech_user else 'N/A')
            text = f"<b>Client:</b> {escape(c_name)}<br/><b>Technician:</b> {escape(tech_name)}"
            style_det = ParagraphStyle('Det', parent=style_normal, fontSize=fs, leading=fs*1.2)
            draw_paragraph(text, ex, pdf_y, ew, eh, style_det)

        elif name == 'start_stop_times':
            start_str = "2023-10-27 09:00" if is_dummy else ((jobcard.time_start.strftime('%Y-%m-%d %H:%M') if jobcard.time_start else '-') if jobcard else '-')
            stop_str = "2023-10-27 11:30" if is_dummy else ((jobcard.time_stop.strftime('%Y-%m-%d %H:%M') if jobcard.time_stop else '-') if jobcard else '-')
            text = f"<b>Start Time:</b> {escape(start_str)}<br/><b>Stop Time:</b> {escape(stop_str)}"
            style_time = ParagraphStyle('Time', parent=style_normal, fontSize=fs, leading=fs*1.2)
            draw_paragraph(text, ex, pdf_y, ew, eh, style_time)

        elif name == 'manager_notes':
            if not is_dummy and tech_only: continue
            notes = "Approved. Good work." if is_dummy else (jobcard.manager_notes if jobcard else "N/A")
            text = f"<b>Manager Notes:</b><br/>{escape(notes) or 'N/A'}"
            style_notes = ParagraphStyle('Notes', parent=style_normal, fontSize=fs, leading=fs*1.2)
            draw_paragraph(text, ex, pdf_y, ew, eh, style_notes)

        elif name == 'admin_notes':
            if not is_dummy and tech_only: continue
            status = "INVOICED" if is_dummy else (jobcard.status if jobcard else "")
            if status == 'INVOICED' or is_dummy:
                notes = "Invoiced #INV-999" if is_dummy else (jobcard.admin_notes if jobcard else "N/A")
                text = f"<b>Admin Notes:</b><br/>{escape(notes) or 'N/A'}"
                style_notes = ParagraphStyle('Notes', parent=style_normal, fontSize=fs, leading=fs*1.2)
                draw_paragraph(text, ex, pdf_y, ew, eh, style_notes)

        elif name == 'signatures':
            tech_user = jobcard.technician if jobcard and not is_dummy else None
            tech_name = "John Doe" if is_dummy else (tech_user.get_full_name() or tech_user.username if tech_user else 'N/A')
            c_name = "Acme Corp" if is_dummy else ((jobcard.company.name if jobcard.company else jobcard.client_name) if jobcard else 'N/A')
            manager_name = "Boss Man" if is_dummy else (jobcard.manager_name if jobcard else 'N/A')
            
            tech_sig = None if is_dummy else (jobcard.tech_signature if jobcard else None)
            client_sig = None if is_dummy else (jobcard.client_signature if jobcard else None)
            manager_sig = None if is_dummy else (jobcard.manager_signature if jobcard else None)
            
            jobcard_status = jobcard.status if jobcard else ""
            show_manager = (is_dummy or jobcard_status in ['APPROVED', 'INVOICED']) and not tech_only
            cols = 3 if show_manager else 2
            col_w = ew / cols
            
            def draw_sig_box(title, title_name, sig_img, col_idx):
                cx = ex + (col_idx * col_w)
                canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
                canvas.rect(cx, pdf_y, col_w - 10, eh)
                canvas.setFillColorRGB(0, 0, 0)
                canvas.setFont("Helvetica-Bold", fs)
                canvas.drawString(cx + 5, pdf_y + eh - 15, title)
                canvas.setFont("Helvetica", fs)
                canvas.drawString(cx + 5, pdf_y + eh - 30, title_name or "")
                if sig_img:
                    try:
                        canvas.drawImage(sig_img.path, cx + 5, pdf_y + 5, width=col_w-20, height=eh-40, preserveAspectRatio=True, mask='auto')
                    except: pass
            
            draw_sig_box("Tech Sign", tech_name, tech_sig, 0)
            draw_sig_box("Client Sign", c_name, client_sig, 1)
            if show_manager:
                draw_sig_box("Manager Sign", manager_name, manager_sig, 2)

    canvas.restoreState()

def build_pdf_items_table(jobcard, is_dummy=False):
    table_data = [['Description', 'Parts Used', 'Qty', 'Person Helped']]

    if is_dummy:
        dummy_items = [
            ("Diagnosed network issue", "Cat6 Cable", "10", "Jane Smith"),
            ("Replaced Switch", "24-Port Switch", "1", "Jane Smith"),
            ("Configured VLANs", "-", "1", "IT Manager"),
        ] * 2
        table_data.extend(dummy_items)
    else:
        styles = getSampleStyleSheet()
        style_normal = styles['Normal']
        if jobcard:
            for item in jobcard.items.all():
                table_data.append([
                    Paragraph(escape(item.description), style_normal),
                    Paragraph(escape(item.parts_used), style_normal),
                    escape(str(item.qty)),
                    Paragraph(escape(item.person_helped), style_normal)
                ])

    items_table = Table(table_data, colWidths=[200, 160, 40, 110], repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4f6f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return items_table

def generate_pdf_buffer(jobcard, is_dummy=False, tech_only=False):
    buffer = io.BytesIO()
    
    elements = PDFTemplateElement.objects.all()
    elements_dict = {el.element_name: el for el in elements}
    
    tab_el = elements_dict.get('items_table')
    if tab_el:
        tab_x = tab_el.pos_x
        tab_y = tab_el.pos_y
        tab_w = tab_el.width
        tab_h = tab_el.height
    else:
        tab_x, tab_y, tab_w, tab_h = 40, 210, 515, 300

    pdf_y = A4[1] - tab_y - tab_h

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=50
    )
    
    frame = Frame(tab_x, pdf_y, tab_w, tab_h, id='normal')
    
    def draw_bg_callback(canvas, doc):
        draw_static_elements(canvas, doc, elements_dict, jobcard, is_dummy, tech_only)

    template = PageTemplate(id='base', frames=frame, onPage=draw_bg_callback)
    doc.addPageTemplates([template])
    
    flowables = [build_pdf_items_table(jobcard, is_dummy)]
    doc.build(flowables)
    
    buffer.seek(0)
    return buffer

"""
    content = content[:start_idx] + new_pdf_logic + content[end_idx:]

    with open(views_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully updated views.py")
else:
    print("Could not find markers")
