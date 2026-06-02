import os
import json
import re
import config
import diagnostics

def apply_resolution_map(global_var_file_hint=None):
    diagnostics.log_info("\n[REWRITER] Initializing codebase rewrite sequence...")

    if not os.path.exists(config.RESOLUTION_MAP_FILE):
        diagnostics.log_error(f"Could not find {config.RESOLUTION_MAP_FILE}. Export it from the Dashboard first.")
        return False

    with open(config.RESOLUTION_MAP_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    if not mapping:
        diagnostics.log_warning("Resolution map is empty. Cancelling rewrite.")
        return False

    diagnostics.log_info(f"Loaded {len(mapping)} value mappings to apply.")

    for file in os.listdir(config.SCSS_DIR):
        if not file.endswith('.scss'):
            continue

        file_path = os.path.join(config.SCSS_DIR, file)
        out_path = os.path.join(config.APPLIED_DIR, file)

        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()

        # FUZZY MATCH SAFE-LOCK
        is_global = False
        if global_var_file_hint and file == global_var_file_hint:
            is_global = True
        elif 'var' in file.lower() or 'global' in file.lower():
            is_global = True

        if is_global:
            diagnostics.log_info(f"[SAFE-LOCK] Identified {file} as GLOBAL variables file. Appending only.")
            appends = "\n// --- NEW RESOLVED TOKENS ---\n"
            for raw_val, new_token in mapping.items():
                if new_token not in content:
                    appends += f"{new_token}: {raw_val};\n"
            content += appends
        else:
            diagnostics.log_info(f"[REGEX] Applying overrides to structural file: {file}")
            for raw_val, new_token in mapping.items():
                escaped_val = re.escape(raw_val)
                pattern = r"(:\s*)" + escaped_val + r"(\s*;)"
                content = re.sub(pattern, r"\g<1>" + new_token + r"\g<2>", content)

        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(content)

    if os.path.exists(config.HTML_DIR):
        for file in os.listdir(config.HTML_DIR):
            if file.endswith('.html'):
                with open(os.path.join(config.HTML_DIR, file), 'r', encoding='utf-8') as src:
                    content = src.read()

                for raw_val, new_token in mapping.items():
                    escaped_val = re.escape(raw_val)
                    pattern = r"(:\s*)" + escaped_val + r"(\s*;)"
                    css_var = f"var(--{new_token.replace('$', '')})"
                    content = re.sub(pattern, r"\g<1>" + css_var + r"\g<2>", content)

                with open(os.path.join(config.APPLIED_DIR, file), 'w', encoding='utf-8') as out:
                    out.write(content)

    diagnostics.log_info(f"[SUCCESS] Codebase successfully rewritten to {config.APPLIED_DIR}/")
    return True
