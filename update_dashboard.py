import os

dashboard_content = """{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="row mb-5 align-items-center">
    <div class="col-md-7">
        <h2 class="mb-1 fw-bold text-dark" style="letter-spacing: -0.5px;">Dashboard</h2>
        <p class="text-secondary mb-0 fs-6">Welcome back, <span class="fw-semibold">{{ user.get_full_name|default:user.username }}</span> ({{ user.get_role_display }})</p>
    </div>
    {% if user.is_technician or user.is_superuser %}
    <div class="col-md-5 text-md-end mt-3 mt-md-0">
        <a href="{% url 'jobcard_create' %}" class="btn btn-primary shadow rounded-pill px-4 py-2" style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); border: none;">
            <i class="bi bi-plus-lg me-2"></i>Create New Jobcard
        </a>
    </div>
    {% endif %}
</div>

<!-- Stat Cards Row (New addition for premium feel) -->
<div class="row mb-4">
    {% if user.is_technician or user.is_superuser %}
    <div class="col-md-4 mb-3">
        <div class="card border-0 p-4 h-100" style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="text-muted text-uppercase mb-2" style="font-size: 0.75rem; letter-spacing: 1px;">Active Jobs</h6>
                    <h2 class="fw-bold mb-0 text-dark">{{ active_jobcards.count|default:"0" }}</h2>
                </div>
                <div class="p-3 rounded-circle text-primary" style="background-color: rgba(59, 130, 246, 0.1);">
                    <i class="bi bi-tools fs-4"></i>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    {% if user.is_manager or user.is_superuser %}
    <div class="col-md-4 mb-3">
         <div class="card border-0 p-4 h-100" style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="text-muted text-uppercase mb-2" style="font-size: 0.75rem; letter-spacing: 1px;">Pending Approval</h6>
                    <h2 class="fw-bold mb-0 text-warning">{{ pending_approval.count|default:"0" }}</h2>
                </div>
                <div class="p-3 rounded-circle text-warning" style="background-color: rgba(245, 158, 11, 0.1);">
                    <i class="bi bi-exclamation-circle fs-4"></i>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    {% if user.is_admin_role or user.is_custom_superuser %}
    <div class="col-md-4 mb-3">
         <div class="card border-0 p-4 h-100" style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="text-muted text-uppercase mb-2" style="font-size: 0.75rem; letter-spacing: 1px;">Ready To Invoice</h6>
                    <h2 class="fw-bold mb-0 text-success">{{ ready_for_invoice.count|default:"0" }}</h2>
                </div>
                <div class="p-3 rounded-circle text-success" style="background-color: rgba(16, 185, 129, 0.1);">
                    <i class="bi bi-currency-dollar fs-4"></i>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>

{% if user.is_technician or user.is_superuser %}
<div class="row">
    <div class="col-md-12 mb-5">
        <div class="card border-0">
            <div class="card-header bg-transparent py-3 d-flex align-items-center">
                <i class="bi bi-clock-history text-primary fs-5 me-2"></i>
                <h5 class="mb-0 fw-semibold">Active Jobcards</h5>
            </div>
            <div class="card-body p-0">
                {% if active_jobcards %}
                <div class="table-responsive">
                    <table class="table align-middle mb-0">
                        <thead>
                            <tr>
                                <th class="ps-4">JC Number</th>
                                <th>Company</th>
                                <th>Category</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th class="text-end pe-4">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for jc in active_jobcards %}
                            <tr>
                                <td class="ps-4 fw-medium text-dark">{{ jc.jobcard_number }}</td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="bg-light rounded p-2 me-3 text-secondary"><i class="bi bi-building"></i></div>
                                        <span class="fw-medium">{{ jc.company.name }}</span>
                                    </div>
                                </td>
                                <td><span class="badge" style="background-color: #f1f5f9; color: #475569;">{{ jc.get_category_display }}</span></td>
                                <td>
                                    {% if jc.status == 'DRAFT' %}
                                        <span class="badge" style="background-color: #e2e8f0; color: #475569;"><i class="bi bi-pencil me-1"></i>Draft</span>
                                    {% else %}
                                        <span class="badge" style="background-color: #dbeafe; color: #1e40af;"><i class="bi bi-send me-1"></i>Submitted</span>
                                    {% endif %}
                                </td>
                                <td class="text-muted">{{ jc.created_at|date:"M d, Y" }}</td>
                                <td class="text-end pe-4">
                                    {% if jc.status == 'DRAFT' %}
                                        <a href="{% url 'jobcard_update' jc.pk %}" class="btn btn-sm btn-outline-primary rounded-pill px-3 py-1 fw-bold">Continue <i class="bi bi-arrow-right ms-1"></i></a>
                                    {% else %}
                                        <a href="{% url 'jobcard_pdf' jc.pk %}" class="btn btn-sm btn-light border rounded-pill px-3 py-1 text-danger fw-bold"><i class="bi bi-file-pdf me-1"></i>PDF</a>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <div class="d-inline-flex justify-content-center align-items-center bg-light rounded-circle mb-3 border shadow-sm" style="width: 80px; height: 80px;">
                        <i class="bi bi-inbox fs-1 text-muted"></i>
                    </div>
                    <h5 class="fw-medium text-dark">No active jobcards</h5>
                    <p class="text-muted">You're all caught up! Create a new jobcard to get started.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endif %}

{% if user.is_manager or user.is_superuser %}
<div class="row">
    <div class="col-md-12 mb-5">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-transparent py-3 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-circle text-warning fs-5 me-2"></i>
                    <h5 class="mb-0 fw-semibold text-dark">Pending Approval</h5>
                </div>
                <span class="badge bg-warning text-dark rounded-pill">{{ pending_approval.count }}</span>
            </div>
            <div class="card-body p-0">
                {% if pending_approval %}
                <div class="table-responsive">
                    <table class="table align-middle mb-0">
                         <thead>
                            <tr>
                                <th class="ps-4">JC Number</th>
                                <th>Technician</th>
                                <th>Company</th>
                                <th>Date Submitted</th>
                                <th class="text-end pe-4">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for jc in pending_approval %}
                            <tr>
                                <td class="ps-4 fw-medium text-dark">{{ jc.jobcard_number }}</td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="bg-light rounded-circle p-2 me-2 text-primary shadow-sm"><i class="bi bi-person"></i></div>
                                        <span class="fw-medium">{{ jc.technician.get_full_name|default:jc.technician.username }}</span>
                                    </div>
                                </td>
                                <td>{{ jc.company.name }}</td>
                                <td class="text-muted">{{ jc.updated_at|date:"M d, Y H:i" }}</td>
                                <td class="text-end pe-4">
                                    <a href="{% url 'manager_approve' jc.pk %}" class="btn btn-sm btn-warning text-dark fw-bold rounded-pill px-3 py-1 shadow-sm"><i class="bi bi-check2-square me-1"></i>Review</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <div class="d-inline-flex justify-content-center align-items-center bg-light rounded-circle mb-3 border shadow-sm" style="width: 80px; height: 80px;">
                        <i class="bi bi-check-circle fs-1 text-success"></i>
                    </div>
                    <h5 class="fw-medium text-dark">All Caught Up</h5>
                    <p class="text-muted">No jobcards currently pending approval.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endif %}

{% if user.is_admin_role or user.is_custom_superuser %}
<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-transparent py-3 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <i class="bi bi-currency-dollar text-success fs-5 me-2"></i>
                    <h5 class="mb-0 fw-semibold text-dark">Ready for Invoicing</h5>
                </div>
                <span class="badge bg-success rounded-pill px-3">{{ ready_for_invoice.count }}</span>
            </div>
            <div class="card-body p-0">
                {% if ready_for_invoice %}
                <div class="table-responsive">
                    <table class="table align-middle mb-0">
                         <thead>
                            <tr>
                                <th class="ps-4">JC Number</th>
                                <th>Company</th>
                                <th>Approved By</th>
                                <th>Date Approved</th>
                                <th class="text-end pe-4">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for jc in ready_for_invoice %}
                            <tr>
                                <td class="ps-4 fw-medium text-dark">{{ jc.jobcard_number }}</td>
                                <td>{{ jc.company.name }}</td>
                                <td><i class="bi bi-shield-check text-success me-1"></i><span class="fw-medium">{{ jc.manager_name }}</span></td>
                                <td class="text-muted">{{ jc.updated_at|date:"M d, Y" }}</td>
                                <td class="text-end pe-4">
                                    <div class="btn-group shadow-sm rounded-pill" role="group">
                                        <a href="{% url 'jobcard_pdf' jc.pk %}" class="btn btn-sm btn-light border-end text-danger fw-bold"><i class="bi bi-file-pdf"></i> View</a>
                                        <a href="{% url 'admin_invoice' jc.pk %}" class="btn btn-sm btn-success fw-bold"><i class="bi bi-receipt me-1"></i>Process</a>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <div class="d-inline-flex justify-content-center align-items-center bg-light rounded-circle mb-3 border shadow-sm" style="width: 80px; height: 80px;">
                        <i class="bi bi-inbox fs-1 text-muted"></i>
                    </div>
                    <h5 class="fw-medium text-dark">No Pending Invoices</h5>
                    <p class="text-muted">There are no jobcards waiting to be invoiced.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}
"""

with open(r"c:\Apps_Dev\FITSJCDEV\templates\dashboard.html", "w", encoding="utf-8") as f:
    f.write(dashboard_content)
print("dashboard.html updated")
