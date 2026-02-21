import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import JobCard, JobDetail, CompanyProfile, CustomUser
from .forms import (
    JobCardForm, JobDetailFormSet, SignatureSubmissionForm, 
    ManagerReviewForm, CompanyProfileForm, CustomUserCreationForm, CustomUserChangeForm
)
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse

def is_technician(user):
    return user.is_technician()

def is_manager(user):
    return user.is_manager()

def is_admin(user):
    return user.is_admin()

@login_required
def dashboard(request):
    if request.user.is_admin():
        return redirect('admin_dashboard')
    elif request.user.is_manager():
        return redirect('manager_dashboard')
    else:
        return redirect('technician_dashboard')

@login_required
@user_passes_test(is_technician)
def technician_dashboard(request):
    jobcards = JobCard.objects.filter(technician=request.user).exclude(status='archived').order_by('-created_at')
    return render(request, 'core/dashboard.html', {'jobcards': jobcards, 'role': 'Technician'})

@login_required
@user_passes_test(is_technician)
def create_jobcard(request):
    if request.method == 'POST':
        form = JobCardForm(request.POST)
        if form.is_valid():
            jobcard = form.save(commit=False)
            jobcard.technician = request.user
            jobcard.save()
            return redirect('technician_job_detail', job_id=jobcard.id)
    else:
        form = JobCardForm()
    return render(request, 'core/jobcard_create.html', {'form': form})

@login_required
@user_passes_test(is_technician)
def technician_job_detail(request, job_id):
    jobcard = get_object_or_404(JobCard, id=job_id, technician=request.user)
    
    if jobcard.status != 'draft':
         # Prevent editing if submitted
         return render(request, 'core/jobcard_readonly.html', {'jobcard': jobcard})

    formset = JobDetailFormSet(request.POST or None, instance=jobcard, prefix='details')
    signature_form = SignatureSubmissionForm(request.POST or None)

    if request.method == 'POST':
        if 'start_job' in request.POST:
            if not jobcard.start_time:
                jobcard.start_time = timezone.now()
                jobcard.save()
            return redirect('technician_job_detail', job_id=jobcard.id)
            
        elif 'stop_job' in request.POST:
            if not jobcard.end_time:
                jobcard.end_time = timezone.now()
                jobcard.save()
            return redirect('technician_job_detail', job_id=jobcard.id)
            
        elif 'save_details' in request.POST:
            if formset.is_valid():
                formset.save()
            return redirect('technician_job_detail', job_id=jobcard.id)

        elif 'submit_job' in request.POST:
            # Save details first if any changes
            if formset.is_valid():
                formset.save()
            
            if signature_form.is_valid():
                jobcard.technician_signature = signature_form.cleaned_data['technician_signature']
                jobcard.client_signature = signature_form.cleaned_data['client_signature']
                jobcard.status = 'submitted'
                jobcard.save()
                return redirect('technician_dashboard')
            else:
                # Handle signature errors or missing signatures
                # For now, we assume frontend validation or just reload with errors
                pass
    
    return render(request, 'core/jobcard_detail_technician.html', {
        'jobcard': jobcard,
        'formset': formset,
        'signature_form': signature_form
    })

# Try to import xhtml2pdf, but handle failure gracefully for dev environment
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    jobcards = JobCard.objects.filter(status='submitted').order_by('-updated_at')
    return render(request, 'core/dashboard.html', {'jobcards': jobcards, 'role': 'Manager'})

@login_required
@user_passes_test(is_manager)
def manager_job_review(request, job_id):
    jobcard = get_object_or_404(JobCard, id=job_id, status='submitted')
    
    if request.method == 'POST':
        form = ManagerReviewForm(request.POST, instance=jobcard)
        if form.is_valid():
            jobcard = form.save(commit=False)
            
            if 'sign_off' in request.POST:
                signature_data = form.cleaned_data.get('manager_signature_data')
                if signature_data:
                    jobcard.manager_signature = signature_data
                    jobcard.status = 'signed_off'
                    jobcard.save()
                    
                    # Generate PDF and Email
                    try:
                        send_jobcard_email(jobcard)
                        # Optionally archive automatically or let admin do it
                        jobcard.status = 'archived' 
                        jobcard.save()
                    except Exception as e:
                        # Log error, maybe notify user
                        print(f"Error sending email: {e}")
                        
                    return redirect('manager_dashboard')
            
            jobcard.save()
            return redirect('manager_dashboard')
    else:
        form = ManagerReviewForm(instance=jobcard)
    
    return render(request, 'core/jobcard_review.html', {'jobcard': jobcard, 'form': form})

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    jobcards = JobCard.objects.filter(status='archived').order_by('-updated_at')
    return render(request, 'core/dashboard.html', {'jobcards': jobcards, 'role': 'Admin'})

def generate_pdf(jobcard):
    template_path = 'core/jobcard_pdf.html'
    context = {'jobcard': jobcard}
    html = render_to_string(template_path, context)
    
    if pisa is None:
        print("xhtml2pdf not installed")
        return None

    from io import BytesIO
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def send_jobcard_email(jobcard):
    subject = f'Job Card Completed - {jobcard.jobcard_id}'
    message = f'Dear {jobcard.client_name},\n\nPlease find attached the completed job card {jobcard.jobcard_id}.\n\nBest regards,\n{jobcard.company_name}'
    
    company_profile = CompanyProfile.objects.first()
    from_email = company_profile.default_email if company_profile and company_profile.default_email else settings.DEFAULT_FROM_EMAIL
    
    # Send to the client's email if available, otherwise fallback to default
    recipient_list = [jobcard.client_email] if jobcard.client_email else [settings.DEFAULT_FROM_EMAIL]
    
    email = EmailMessage(subject, message, from_email, recipient_list)
    
    pdf_content = generate_pdf(jobcard)
    if pdf_content:
        email.attach(f'{jobcard.jobcard_id}.pdf', pdf_content, 'application/pdf')
        email.send()
    else:
        print("PDF generation failed, email not sent.")

# --- NEW MANAGER VIEWS ---

@login_required
@user_passes_test(is_manager)
def manager_settings(request):
    company_profile = CompanyProfile.objects.first()
    if not company_profile:
        company_profile = CompanyProfile.objects.create()

    if request.method == 'POST':
        form = CompanyProfileForm(request.POST, request.FILES, instance=company_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            extra_fields_json = form.cleaned_data.get('extra_fields')
            if extra_fields_json:
                try:
                    profile.extra_fields = json.loads(extra_fields_json)
                except json.JSONDecodeError:
                    pass # Or add error
            profile.save()
            return redirect('manager_settings')
    else:
        initial_data = {}
        if company_profile.extra_fields:
            initial_data['extra_fields'] = json.dumps(company_profile.extra_fields)
        form = CompanyProfileForm(instance=company_profile, initial=initial_data)

    return render(request, 'core/manager_settings.html', {'form': form, 'company_profile': company_profile})

@login_required
@user_passes_test(is_manager)
def manager_user_list(request):
    users = CustomUser.objects.all().order_by('username')
    return render(request, 'core/manager_user_list.html', {'users': users})

@login_required
@user_passes_test(is_manager)
def manager_user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manager_user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/manager_user_form.html', {'form': form, 'title': 'Add New User'})

@login_required
@user_passes_test(is_manager)
def manager_user_edit(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manager_user_list')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'core/manager_user_form.html', {'form': form, 'title': f'Edit User: {user.username}'})
