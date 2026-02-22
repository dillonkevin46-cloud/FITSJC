from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('technician', 'Technician'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='technician')

    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_technician(self):
        return self.role == 'technician'

class CompanyProfile(models.Model):
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    address = models.TextField(blank=True)
    default_email = models.EmailField(blank=True, null=True)
    extra_fields = models.JSONField(default=list, blank=True)

    def __str__(self):
        return "Company Profile"

    class Meta:
        verbose_name_plural = "Company Profile"

class JobCard(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('signed_off', 'Signed Off'),
        ('archived', 'Archived'),
    )

    jobcard_id = models.CharField(max_length=20, unique=True, editable=False)
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    technician = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='jobcards')
    
    # Signatures stored as Base64 strings
    technician_signature = models.TextField(blank=True, null=True) 
    client_signature = models.TextField(blank=True, null=True)
    manager_signature = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    manager_notes = models.TextField(blank=True)
    custom_fields_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.jobcard_id:
            now = timezone.now()
            year = now.year
            # Find the last jobcard created this year to increment the sequence
            last_job = JobCard.objects.filter(jobcard_id__startswith=f"JC-{year}-").order_by('jobcard_id').last()
            if last_job:
                try:
                    last_id = int(last_job.jobcard_id.split('-')[-1])
                    new_id = last_id + 1
                except ValueError:
                    new_id = 1
            else:
                new_id = 1
            self.jobcard_id = f"JC-{year}-{new_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.jobcard_id

class JobDetail(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='details')
    description = models.CharField(max_length=255)
    hardware_replaced = models.CharField(max_length=255, blank=True)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.job_card.jobcard_id} - {self.description}"
