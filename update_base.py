import re

base_path = r"c:\Apps_Dev\FITSJCDEV\templates\base.html"
with open(base_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace Styles
new_styles = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body { 
            background-color: #f4f7f6; /* Premium soft gray */
            font-family: 'Inter', system-ui, sans-serif;
            color: #1e293b;
            overflow-x: hidden;
        } 
        
        /* Modern Glassmorphism Sidebar */
        .sidebar { 
            background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
            color: #f8fafc; 
            min-height: 100vh; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1050; 
            box-shadow: 4px 0 24px rgba(17, 24, 39, 0.15);
        }
        
        .sidebar .sidebar-header {
            padding: 24px 20px;
            background-color: rgba(17, 24, 39, 0.4);
            backdrop-filter: blur(10px);
            font-size: 1.25rem;
            font-weight: 700;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            letter-spacing: 0.5px;
        }

        .sidebar .sidebar-header img {
            max-height: 40px;
            max-width: 100%;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }

        .sidebar .nav-link { 
            color: #9ca3af; 
            border-radius: 0.5rem; 
            margin: 0.35rem 0.75rem; 
            padding: 0.75rem 1.15rem; 
            font-weight: 500;
            transition: all 0.25s ease;
        }
        
        .sidebar .nav-link:hover, .sidebar .nav-link.active, .sidebar a[aria-expanded="true"] { 
            color: #ffffff; 
            background-color: rgba(255,255,255,0.08); 
            transform: translateX(4px);
        }
        
        .sidebar .nav-link i { margin-right: 12px; font-size: 1.25rem; width: 20px; text-align: center; }
        .sidebar .dropdown-menu { background-color: rgba(0,0,0,0.15); border: none; padding: 0.5rem 0; margin: 0; }
        .sidebar .dropdown-item { color: #9ca3af; padding: 0.65rem 1rem 0.65rem 3.5rem; font-size: 0.875rem; font-weight: 500; transition: color 0.2s; }
        .sidebar .dropdown-item:hover { color: #ffffff; background-color: transparent; }

        /* Top Navbar */
        .top-navbar { 
            background-color: #ffffff !important; 
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            border-bottom: 1px solid rgba(226, 232, 240, 0.8);
            padding: 1rem 1.5rem;
            backdrop-filter: blur(8px);
        } 
        #menu-toggle { color: #475569; transition: color 0.2s; }
        #menu-toggle:hover { color: #0f172a; }

        /* Premium Components */
        .card { 
            border: 1px solid rgba(226, 232, 240, 0.8); 
            border-radius: 1rem; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02); 
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            background-color: #ffffff;
            overflow: hidden;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        }
        .card-header {
            border-bottom: 1px solid #f1f5f9;
            background-color: #ffffff;
            padding: 1.25rem 1.5rem;
            font-weight: 600;
            color: #0f172a;
        }
        .btn { font-weight: 500; border-radius: 0.5rem; padding: 0.5rem 1.25rem; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); letter-spacing: 0.025em; }
        .btn-primary { 
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
            color: #fff;
        }
        .btn-primary:hover { 
            box-shadow: 0 6px 15px rgba(59, 130, 246, 0.4);
            transform: translateY(-1px);
        }
        .table { margin-bottom: 0; }
        .table thead th { 
            background-color: #f8fafc !important; 
            color: #64748b; 
            font-weight: 600; 
            text-transform: uppercase; 
            font-size: 0.7rem; 
            letter-spacing: 0.05em;
            border-bottom: 2px solid #e2e8f0;
            padding: 1rem;
        }
        .table tbody td { vertical-align: middle; padding: 1rem; color: #334155; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
        .table tbody tr:hover { background-color: #f8fafc; }
        
        .badge { font-weight: 600; padding: 0.4em 0.8em; border-radius: 999px; letter-spacing: 0.025em; }

        /* Layout Structure CSS */
        #wrapper {
            display: flex;
            min-height: 100vh;
            width: 100vw;
            overflow-x: hidden;
        }

        .sidebar {
            width: 260px;
            display: flex;
            flex-direction: column;
        }

        .sidebar.collapsed { margin-left: -260px; }

        /* Main Content Styling */
        #page-content-wrapper {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
            transition: margin-left 0.3s ease-in-out;
        }

        #top-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 1000;
            position: sticky;
            top: 0;
        }

        #menu-toggle {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
        }

        #menu-toggle:hover { background-color: #f1f5f9; }

        #main-body {
            flex-grow: 1;
            padding: 2rem;
            animation: fadeIn 0.4s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Mobile Backdrop Overlay */
        #sidebar-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(15, 23, 42, 0.4);
            z-index: 1040;
            backdrop-filter: blur(4px);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        /* Responsive Logic */
        @media (max-width: 768px) {
            .sidebar { position: fixed; height: 100vh; transform: translateX(-100%); }
            .sidebar.mobile-show { transform: translateX(0); }
            #sidebar-overlay.mobile-show { display: block; opacity: 1; }
            #main-body { padding: 1.25rem; }
            .card { border-radius: 0.75rem; }
        }

        @media (min-width: 769px) {
            .sidebar.collapsed { margin-left: -260px; }
        }
    </style>"""

content = re.sub(r"<style>.*?</style>", new_styles, content, flags=re.DOTALL)
content = content.replace('text-white', 'text-dark')

with open(base_path, "w", encoding="utf-8") as f:
    f.write(content)

print("base.html updated")
