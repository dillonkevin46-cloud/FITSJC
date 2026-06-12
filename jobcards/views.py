import base64
import uuid
import io
import json
from html import escape
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, View, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage

# ReportLab imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether, BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from .models import User, Jobcard, JobcardItem, Company, GlobalSettings, PDFTemplateElement
from .forms import (
    UserLoginForm, CustomUserCreationForm, ManagerUserEditForm, CompanyForm, GlobalSettingsForm,
    JobcardForm, JobcardItemFormSet, ManagerActionForm, AdminActionForm
)

# --- Helper Functions ---
def save_signature_image(base64_data):
    if not base64_data:
        return None
    try:
        if ';base64,' in base64_data:
            format, imgstr = base64_data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            return ContentFile(base64.b64decode(imgstr), name=filename)
        return None
    except Exception as e:
        print(f"Error saving signature: {e}")
        return None

def setup_default_template_elements():
    defaults = [
        {'element_name': 'header_logo', 'pos_x': 40, 'pos_y': 40, 'width': 120, 'height': 60, 'font_size': 0},
        {'element_name': 'company_info', 'pos_x': 200, 'pos_y': 40, 'width': 350, 'height': 60, 'font_size': 12},
        {'element_name': 'jobcard_meta', 'pos_x': 400, 'pos_y': 110, 'width': 150, 'height': 50, 'font_size': 10},
        {'element_name': 'client_details', 'pos_x': 40, 'pos_y': 110, 'width': 200, 'height': 40, 'font_size': 10},
        {'element_name': 'start_stop_times', 'pos_x': 300, 'pos_y': 150, 'width': 250, 'height': 40, 'font_size': 10},
        {'element_name': 'items_table', 'pos_x': 40, 'pos_y': 210, 'width': 515, 'height': 300, 'font_size': 10},
        {'element_name': 'manager_notes', 'pos_x': 40, 'pos_y': 530, 'width': 515, 'height': 60, 'font_size': 10},
        {'element_name': 'admin_notes', 'pos_x': 40, 'pos_y': 600, 'width': 515, 'height': 60, 'font_size': 10},
        {'element_name': 'signatures', 'pos_x': 40, 'pos_y': 680, 'width': 515, 'height': 100, 'font_size': 10},
    ]
    if not PDFTemplateElement.objects.exists():
        for d in defaults:
            PDFTemplateElement.objects.create(**d)

# --- PDF GENERATOR ---

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
            if is_dummy and not c_addr: c_addr = "123 Fake Street\nCity, Country"
            text = f"<b><font size={fs+4}>{escape(c_name)}</font></b><br/>" + escape(c_addr).replace('\n', '<br/>')
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

def generate_dummy_pdf_buffer():
    return generate_pdf_buffer(None, is_dummy=True)


# --- VIEWS ---

class CustomLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = 'registration/login.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_technician():
            context['active_jobcards'] = Jobcard.objects.filter(technician=user, status__in=[Jobcard.Status.DRAFT, Jobcard.Status.SUBMITTED])
            context['archived_jobcards'] = Jobcard.objects.filter(technician=user).exclude(status__in=[Jobcard.Status.DRAFT, Jobcard.Status.SUBMITTED])
        elif user.is_manager():
            context['pending_approval'] = Jobcard.objects.filter(status=Jobcard.Status.SUBMITTED)
            context['approved_jobcards'] = Jobcard.objects.filter(status=Jobcard.Status.APPROVED)
        elif user.is_admin_role() or user.is_custom_superuser():
             context['ready_for_invoice'] = Jobcard.objects.filter(status=Jobcard.Status.APPROVED)
             context['invoiced_jobcards'] = Jobcard.objects.filter(status=Jobcard.Status.INVOICED)

        return context

class JobcardCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Jobcard
    form_class = JobcardForm
    template_name = 'jobcard_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_technician() or self.request.user.is_superuser

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        initial['tech_name'] = user.get_full_name() or user.username
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['item_formset'] = JobcardItemFormSet(self.request.POST)
        else:
            data['item_formset'] = JobcardItemFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['item_formset']

        action = self.request.POST.get('action')

        if action == 'submit':
            valid = True

            if not form.cleaned_data.get('time_stop'):
                messages.error(self.request, "You must Stop the timer before submitting.")
                valid = False

            has_items = False
            if items.is_valid():
                for item_form in items.cleaned_data:
                    if item_form and not item_form.get('DELETE', False):
                        if item_form.get('description'):
                            has_items = True
                            break
            else:
                valid = False

            if not has_items and valid:
                messages.error(self.request, "You must add at least one Job Detail before submitting.")
                valid = False

            if not valid:
                return self.render_to_response(self.get_context_data(form=form, item_formset=items))

        self.object = form.save(commit=False)
        self.object.technician = self.request.user

        tech_sig = form.cleaned_data.get('tech_signature_data')
        client_sig = form.cleaned_data.get('client_signature_data')

        if tech_sig:
            self.object.tech_signature = save_signature_image(tech_sig)
        if client_sig:
            self.object.client_signature = save_signature_image(client_sig)

        if action == 'submit':
            self.object.status = Jobcard.Status.SUBMITTED

        self.object.save()

        if items.is_valid():
            items.instance = self.object
            items.save()

            if action == 'submit':
                try:
                    pdf_buffer = generate_pdf_buffer(self.object)

                    to_email = None
                    if self.object.company and self.object.company.email:
                        to_email = self.object.company.email

                    if to_email:
                        email = EmailMessage(
                            subject=f'Jobcard Submitted: {self.object.jobcard_number}',
                            body=f'Please find attached the jobcard.',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[to_email]
                        )
                        email.attach(f'{self.object.jobcard_number}.pdf', pdf_buffer.read(), 'application/pdf')
                        email.send(fail_silently=True)
                        messages.success(self.request, "Jobcard submitted and emailed!")
                    else:
                        messages.success(self.request, "Jobcard submitted successfully! (No email sent, company email missing).")
                except Exception as e:
                    messages.warning(self.request, f"Jobcard submitted but email/PDF failed: {e}")
            else:
                 messages.success(self.request, "Jobcard draft saved!")

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form, item_formset=items))

class JobcardUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Jobcard
    form_class = JobcardForm
    template_name = 'jobcard_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        obj = self.get_object()
        if self.request.user.is_technician():
             return obj.technician == self.request.user and obj.status == Jobcard.Status.DRAFT
        return False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['item_formset'] = JobcardItemFormSet(self.request.POST, instance=self.object)
        else:
            data['item_formset'] = JobcardItemFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['item_formset']

        action = self.request.POST.get('action')

        if action == 'submit':
            valid = True

            if not form.cleaned_data.get('time_stop'):
                messages.error(self.request, "You must Stop the timer before submitting.")
                valid = False

            has_items = False
            if items.is_valid():
                for item_form in items.cleaned_data:
                    if item_form and not item_form.get('DELETE', False):
                        if item_form.get('description'):
                            has_items = True
                            break
            else:
                valid = False

            if not has_items and valid:
                messages.error(self.request, "You must add at least one Job Detail before submitting.")
                valid = False

            if not valid:
                return self.render_to_response(self.get_context_data(form=form, item_formset=items))

        self.object = form.save(commit=False)

        tech_sig = form.cleaned_data.get('tech_signature_data')
        client_sig = form.cleaned_data.get('client_signature_data')

        if tech_sig:
            self.object.tech_signature = save_signature_image(tech_sig)
        if client_sig:
            self.object.client_signature = save_signature_image(client_sig)

        if action == 'submit':
            self.object.status = Jobcard.Status.SUBMITTED

        self.object.save()

        if items.is_valid():
            items.save()

            if action == 'submit':
                try:
                    pdf_buffer = generate_pdf_buffer(self.object)
                    to_email = None
                    if self.object.company and self.object.company.email:
                        to_email = self.object.company.email

                    if to_email:
                        email = EmailMessage(
                            subject=f'Jobcard Submitted: {self.object.jobcard_number}',
                            body=f'Please find attached the jobcard.',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[to_email]
                        )
                        email.attach(f'{self.object.jobcard_number}.pdf', pdf_buffer.read(), 'application/pdf')
                        email.send(fail_silently=True)
                        messages.success(self.request, "Jobcard submitted and emailed!")
                    else:
                        messages.success(self.request, "Jobcard submitted successfully! (No email sent).")
                except Exception as e:
                    messages.warning(self.request, f"Jobcard submitted but email/PDF failed: {e}")
            else:
                 messages.success(self.request, "Jobcard updated successfully!")

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form, item_formset=items))

class JobcardAutosaveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        jobcard = get_object_or_404(Jobcard, pk=pk)
        if jobcard.technician != request.user and not request.user.is_superuser:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        form = JobcardForm(request.POST, instance=jobcard, user=request.user)
        if form.is_valid():
            jobcard = form.save(commit=False)

            tech_sig = form.cleaned_data.get('tech_signature_data')
            client_sig = form.cleaned_data.get('client_signature_data')

            if tech_sig:
                jobcard.tech_signature = save_signature_image(tech_sig)
            if client_sig:
                jobcard.client_signature = save_signature_image(client_sig)

            jobcard.save()

            items = JobcardItemFormSet(request.POST, instance=jobcard)
            if items.is_valid():
                items.save()

            return JsonResponse({'status': 'saved'})
        return JsonResponse({'error': form.errors}, status=400)

class ManagerJobcardView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Jobcard
    form_class = ManagerActionForm
    template_name = 'jobcard_manager.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def form_valid(self, form):
        self.object = form.save(commit=False)
        manager_sig = form.cleaned_data.get('manager_signature_data')
        if manager_sig:
             self.object.manager_signature = save_signature_image(manager_sig)

        if 'approve' in self.request.POST:
            self.object.status = Jobcard.Status.APPROVED

        self.object.save()
        messages.success(self.request, "Jobcard reviewed successfully!")
        return redirect(self.success_url)

class AdminJobcardView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Jobcard
    form_class = AdminActionForm
    template_name = 'jobcard_admin.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_admin_role() or self.request.user.is_superuser

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.status = Jobcard.Status.INVOICED
        self.object.admin_capture_name = self.request.user.get_full_name() or self.request.user.username
        self.object.admin_capture_date = timezone.now()
        self.object.save()
        messages.success(self.request, "Jobcard marked as Invoiced!")
        return redirect(self.success_url)

class AdminArchiveListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobcard
    template_name = 'jobcard_archive.html'
    context_object_name = 'archived_jobcards'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_admin_role() or self.request.user.is_superuser

    def get_queryset(self):
        qs = Jobcard.objects.filter(status=Jobcard.Status.INVOICED).order_by('-created_at')

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(jobcard_number__icontains=query) |
                Q(company__name__icontains=query) |
                Q(technician__username__icontains=query)
            )

        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = Jobcard.Category.choices
        return context

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'user_list.html'

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'user_form.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = ManagerUserEditForm
    template_name = 'user_form.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, "User deleted successfully.")
        return super().form_valid(form)

class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

class CompanyCreateAJAXView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({'success': False, 'message': 'Company name is required.'}, status=400)

            company = Company.objects.create(
                name=name,
                address=data.get('address', ''),
                contact_number=data.get('contact_number', ''),
                email=data.get('email', '')
            )
            return JsonResponse({'success': True, 'id': company.id, 'name': company.name})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

class SettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'settings_form.html'

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def get(self, request):
        settings_obj = GlobalSettings.objects.first()
        form = GlobalSettingsForm(instance=settings_obj)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        settings_obj = GlobalSettings.objects.first()
        form = GlobalSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated.")
            return redirect('dashboard')
        return render(request, self.template_name, {'form': form})

class JobcardPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        jobcard = get_object_or_404(Jobcard, pk=pk)

        try:
            buffer = generate_pdf_buffer(jobcard)
        except Exception as e:
            return HttpResponse(f"Error generating PDF: {e}", status=500)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{jobcard.jobcard_number}.pdf"'
        return response

class FormDesignerView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'form_designer.html'

    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def get(self, request):
        setup_default_template_elements()
        elements = PDFTemplateElement.objects.all()
        return render(request, self.template_name, {'elements': elements})

class SaveTemplateLayoutView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def post(self, request):
        try:
            data = json.loads(request.body)
            elements_data = data.get('elements', [])

            for item in elements_data:
                name = item.get('name')
                if name:
                    element, created = PDFTemplateElement.objects.get_or_create(element_name=name)
                    element.pos_x = float(item.get('x', 0))
                    element.pos_y = float(item.get('y', 0))
                    element.width = float(item.get('width', 100))
                    element.height = float(item.get('height', 50))
                    element.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class PreviewPDFTemplateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_manager() or self.request.user.is_superuser

    def get(self, request):
        try:
            buffer = generate_dummy_pdf_buffer()
        except Exception as e:
            return HttpResponse(f"Error generating Preview PDF: {e}", status=500)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="jobcard_preview.pdf"'
        return response

class ResendJobcardEmailView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_admin_role() or self.request.user.is_superuser

    def post(self, request, pk):
        jobcard = get_object_or_404(Jobcard, pk=pk)

        to_email = None
        if jobcard.company and jobcard.company.email:
            to_email = jobcard.company.email

        if not to_email:
            messages.error(request, "Cannot resend: No company email associated with this jobcard.")
            return redirect('dashboard')

        try:
            pdf_buffer = generate_pdf_buffer(jobcard, tech_only=True)
            email = EmailMessage(
                subject=f'Jobcard Copy (Tech Version): {jobcard.jobcard_number}',
                body=f'Please find attached a copy of the jobcard for {jobcard.company.name}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )
            email.attach(f'{jobcard.jobcard_number}_tech.pdf', pdf_buffer.read(), 'application/pdf')
            email.send(fail_silently=False)
            messages.success(request, "Tech-only jobcard successfully sent to client!")
        except Exception as e:
            messages.error(request, f"Failed to send email: {e}")

        return redirect('dashboard')
