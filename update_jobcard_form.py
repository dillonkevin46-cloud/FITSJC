import re

template_path = r"c:\Apps_Dev\FITSJCDEV\templates\jobcard_form.html"
with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

new_styles = """
<style>
    .jobcard-container {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    .jobcard-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #fff;
        margin: -40px -40px 40px -40px;
        padding: 30px 40px;
        border-radius: 16px 16px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .jobcard-header h3 { color: #fff !important; font-weight: 700; letter-spacing: -0.5px; }
    .signature-pad-wrapper {
        border-radius: 12px !important;
        overflow: hidden;
        border: 2px dashed #cbd5e1 !important;
        transition: border 0.2s ease;
    }
    .signature-pad-wrapper:hover { border-color: #94a3b8 !important; }
    .signature-pad-wrapper canvas { cursor: crosshair; }
    .formset-row {
        background-color: #fff;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .formset-row:hover {
        background-color: #f8fafc;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .table-input input {
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        border-radius: 8px;
        padding: 8px 12px;
        width: 100%;
        transition: all 0.2s ease;
    }
    .table-input input:focus, .table-input input:hover {
        border: 1px solid #3b82f6;
        background: #fff;
        outline: none;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    /* Hide crispy labels in table */
    #items-table label { display: none; }
    #items-table .mb-3 { margin-bottom: 0 !important; }
    
    /* Enhance inputs */
    input.form-control, select.form-control, select.form-select, textarea.form-control {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease;
    }
    input.form-control:focus, select.form-control:focus, select.form-select:focus, textarea.form-control:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }
</style>
"""

content = re.sub(r"<style>.*?</style>", new_styles, content, flags=re.DOTALL)
content = content.replace('bg-dark', 'bg-white text-dark')

with open(template_path, "w", encoding="utf-8") as f:
    f.write(content)

print("jobcard_form.html updated")
