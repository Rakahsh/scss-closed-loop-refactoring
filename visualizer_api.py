import os
import json
import config
import diagnostics

def get_lineage_data():
    path = os.path.join(config.OUTPUT_DIR, "lineage.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: pass
    return {}

def get_compiled_data():
    compiled_data = {}
    for f in os.listdir(config.SOURCE_DIR):
        if f.endswith('.css'):
            css_path = os.path.join(config.SOURCE_DIR, f)
            with open(css_path, 'r', encoding='utf-8') as cf:
                css = cf.read()
            compiled_data[f] = {"css": css}
    return compiled_data

def get_source_scss_files():
    scss_files = {}
    if not os.path.exists(config.SCSS_DIR): return scss_files
    for f in os.listdir(config.SCSS_DIR):
        if f.endswith('.scss') and not ('var' in f.lower() or 'global' in f.lower()):
            with open(os.path.join(config.SCSS_DIR, f), 'r', encoding='utf-8') as file:
                scss_files[f] = file.read()
    return scss_files

# --- NEW MODULE FOR TRACEABILITY ---
def get_selector_map():
    path = os.path.join(config.OUTPUT_DIR, "selector_map.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: pass
    return {}
# -----------------------------------

def update_api_payload(scss_content, html_snippets, _, global_scss_content=""):
    brand_guide_json = {}
    if os.path.exists(config.BRAND_GUIDE_FILE):
        with open(config.BRAND_GUIDE_FILE, 'r', encoding='utf-8') as f:
            try: brand_guide_json = json.load(f)
            except: pass

    payload = {
        "brand_guide": brand_guide_json,
        "scss": scss_content,
        "global_scss": global_scss_content if global_scss_content else "// No global variable file detected.",
        "html_snippets": html_snippets if html_snippets else "<div class='empty-state'>Drop your .html files into /src_html/ to see them rendered here.</div>",
        "compiled_css_data": get_compiled_data(),
        "lineage": get_lineage_data(),
        "source_scss_files": get_source_scss_files(),
        "selector_map": get_selector_map() # Safely injected here
    }

    data_path = os.path.join(config.REPORT_DIR, "api_data.json")
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f)

    template_path = os.path.join(config.BASE_DIR, "template.html")
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as src:
            with open(os.path.join(config.REPORT_DIR, "index.html"), 'w', encoding='utf-8') as out:
                out.write(src.read())
    return data_path
