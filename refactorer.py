import os
import re
import ast
import json
import config
import diagnostics

def get_value_variations(val):
    val = str(val).strip().lower()
    variations = {val}
    # Add spacing-stripped variations for functions like rgba(255, 255, 255)
    variations.add(val.replace(" ", ""))

    if val.startswith('#'):
        if len(val) == 7 and val[1] == val[2] and val[3] == val[4] and val[5] == val[6]:
            variations.add(f"#{val[1]}{val[3]}{val[5]}")
        elif len(val) == 4:
            variations.add(f"#{val[1]}{val[1]}{val[2]}{val[2]}{val[3]}{val[3]}")

    named_reverse = {"#ffffff": "white", "#000000": "black", "#ff0000": "red", "#0000ff": "blue", "#008000": "green", "transparent": "transparent"}
    if val in named_reverse:
        variations.add(named_reverse[val])
    return list(variations)

def find_all_raw_value_lines(scss_file_path, compiled_value):
    # Nesting-Agnostic Scanner: Ignores CSS selector boundaries.
    # Simply finds every line where the raw value was explicitly typed.
    variations = get_value_variations(compiled_value)
    hits = []
    try:
        with open(scss_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            line_lower = line.lower()
            if line_lower.strip().startswith('//'):
                continue

            for v in variations:
                if v in line_lower:
                    # Prevent False Positives (e.g. matching #fff inside #ffffff)
                    if v.startswith('#'):
                        v_idx = line_lower.find(v)
                        end_idx = v_idx + len(v)
                        if end_idx < len(line_lower) and line_lower[end_idx] in '0123456789abcdef':
                            continue

                    hits.append(idx + 1)
                    break # Move to next line after finding a hit
        return hits
    except Exception as e:
        diagnostics.log_error(f"AST Verification Failed on {scss_file_path}: {e}")
        return []

def is_junk_value(val):
    val_clean = val.strip().lower()
    if val_clean in config.JUNK_VALUES: return True
    if val_clean.isalpha() and val_clean not in ['red', 'blue', 'green', 'black', 'white', 'gray']: return True
    return False

def classify_property_intent(prop, val):
    prop, val = prop.lower(), str(val).lower()
    if any(k in prop for k in ['color', 'fill', 'stroke']) or re.search(r'#[0-9a-f]{3,8}|rgba?\(', val): return "colors"
    if any(k in prop for k in ['font', 'line-height', 'letter-spacing', 'text-transform', 'text-decoration']): return "typography"
    if any(k in prop for k in ['padding', 'margin', 'gap', 'top', 'bottom', 'left', 'right']): return "spacing"
    if 'border-radius' in prop or 'border-width' in prop: return "borders"
    if 'shadow' in prop: return "shadows"
    if any(k in prop for k in ['width', 'height', 'max-', 'min-']): return "sizing"
    return "misc"

def execute_automated_extraction(metrics_list):
    shared_rules = []
    taxonomy = {"colors": {}, "typography": {}, "spacing": {}, "borders": {}, "shadows": {}, "sizing": {}, "misc": {}}
    counters = {k: 1 for k in taxonomy.keys()}
    lineage_hooks = {}

    scss_files = [f for f in os.listdir(config.SCSS_DIR) if f.endswith('.scss') and not ('var' in f.lower() or 'global' in f.lower())]

    for row in metrics_list:
        context_dict = ast.literal_eval(row["Context"])
        source_css = row["Source"]
        css_selector = row["Selector"]

        if row["Status"] == "Identical Match (Ready)":
            rule_body = "  " + ";\n  ".join([f"{k}: {v}" for k, v in context_dict.items()]) + ";"
            shared_rules.append(f"// Lineage: Ready for mapping\n{css_selector} {{\n{rule_body}\n}}")

        if config.CRAWL_SETTINGS["semantic_token_grouping"]:
            for prop, val in context_dict.items():
                if is_junk_value(val) or 'var(' in val.lower():
                    continue

                exact_origins = []
                for s_file in scss_files:
                    full_path = os.path.join(config.SCSS_DIR, s_file)
                    hits = find_all_raw_value_lines(full_path, val)
                    for h in hits:
                        exact_origins.append(f"{s_file}:{h}")

                # Skip if dynamically generated (no hardcoded string found)
                if not exact_origins:
                    continue

                category = classify_property_intent(prop, val)

                if val not in [v.split(';')[0] for v in taxonomy[category].values()]:
                    if category == "colors" and config.CRAWL_SETTINGS["auto_extract_hex"]:
                        hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}', str(val))
                        for h_val in hex_matches:
                            if h_val not in [v.split(';')[0] for v in taxonomy["colors"].values()]:
                                taxonomy["colors"][f"$color-extracted-{counters['colors']}"] = h_val
                                if h_val not in lineage_hooks: lineage_hooks[h_val] = []
                                lineage_hooks[h_val].extend(exact_origins)
                                counters["colors"] += 1
                    else:
                        taxonomy[category][f"${category}-extracted-{counters[category]}"] = val
                        if val not in lineage_hooks: lineage_hooks[val] = []
                        lineage_hooks[val].extend(exact_origins)
                        counters[category] += 1

    var_file = os.path.join(config.OUTPUT_DIR, "_variables_generated.scss")
    with open(var_file, 'w', encoding='utf-8') as f:
        f.write("// Automatically Isolated Global Tokens\n\n")
        for category, tokens in taxonomy.items():
            if tokens:
                f.write(f"// --- {category.upper()} ---\n")
                for k, v in tokens.items():
                    val_str = v if ';' in v else f"{v};"
                    f.write(f"{k}: {val_str}\n")
                f.write("\n")

    shared_file = os.path.join(config.OUTPUT_DIR, "_shared_generated.scss")
    with open(shared_file, 'w', encoding='utf-8') as f:
        f.write("@import 'variables_generated';\n\n")
        f.write("\n\n".join(shared_rules))

    lineage_export = {k: " | ".join(set(v)) for k, v in lineage_hooks.items()}
    with open(os.path.join(config.OUTPUT_DIR, "lineage.json"), 'w', encoding='utf-8') as f:
        json.dump(lineage_export, f)

    return var_file
