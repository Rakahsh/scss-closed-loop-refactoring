import os
import config
import diagnostics

def get_html_snippets():
    snippets = ""
    if not os.path.exists(config.HTML_DIR):
        diagnostics.log_warning("HTML Directory not found. Sandbox will be empty.", echo=False)
        return snippets

    files = [f for f in os.listdir(config.HTML_DIR) if f.endswith('.html')]
    diagnostics.log_info(f"Crawled src_html: Found {len(files)} components.", echo=False)

    for file in files:
        with open(os.path.join(config.HTML_DIR, file), 'r', encoding='utf-8') as f:
            snippets += f"\n" + f.read() + "\n<hr style='border-color: #444; margin: 40px 0;'>\n"
    return snippets
