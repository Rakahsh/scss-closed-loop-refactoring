# -*- coding: utf-8 -*-
import os
import config
import base64
import json

def build_visual_dashboard(scss_content, iteration, timestamp, html_snippets, global_scss_content=""):
    html_path = os.path.join(config.REPORT_DIR, "index.html")

    brand_guide_json = {}
    if os.path.exists(config.BRAND_GUIDE_FILE):
        with open(config.BRAND_GUIDE_FILE, 'r', encoding='utf-8') as f:
            try:
                brand_guide_json = json.load(f)
            except:
                pass

    # Read the pure HTML template
    with open(config.TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()

    # Encode payload as Base64 to prevent ALL syntax errors in the browser
    b64_bg = base64.b64encode(json.dumps(brand_guide_json).encode('utf-8')).decode('utf-8')
    b64_scss = base64.b64encode(scss_content.encode('utf-8')).decode('utf-8')
    b64_global = base64.b64encode(global_scss_content.encode('utf-8')).decode('utf-8') if global_scss_content else base64.b64encode(b"// No global _variables.scss detected.").decode('utf-8')
    b64_html = base64.b64encode(html_snippets.encode('utf-8')).decode('utf-8') if html_snippets else base64.b64encode(b"<div class='empty-state'>Drop your .html files into /src_html/ to see them rendered here with live tokens.</div>").decode('utf-8')

    # Safe Replacement using the Template Engine concept
    final_html = template.replace("__INJECT_BG_B64__", b64_bg)
    final_html = final_html.replace("__INJECT_SCSS_B64__", b64_scss)
    final_html = final_html.replace("__INJECT_GLOBAL_B64__", b64_global)
    final_html = final_html.replace("__INJECT_HTML_B64__", b64_html)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    return html_path
