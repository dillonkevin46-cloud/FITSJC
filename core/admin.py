from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CompanyProfile, JobCard, JobDetail

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

class JobDetailInline(admin.TabularInline):
    model = JobDetail
    extra = 1

class JobCardAdmin(admin.ModelAdmin):
    list_display = ('jobcard_id', 'client_name', 'status', 'created_at')
    list_filter = ('status', 'technician', 'created_at')
    inlines = [JobDetailInline]
    search_fields = ('jobcard_id', 'client_name', 'company_name')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CompanyProfile)
admin.site.register(JobCard, JobCardAdmin)
admin.site.register(JobDetail)
