# -*- coding: utf-8 -*-
import os
import re
import ast
import json
import config
import diagnostics
import classifier

def get_value_variations(val):
    val = str(val).strip().lower()
    variations = {val}
    no_space = val.replace(" ", "")
    variations.add(no_space)
    if 'rgba' in no_space:
        variations.add(no_space.replace("0.", "."))
        variations.add(val.replace("0.", "."))

    if val.startswith('#'):
        if len(val) == 7 and val[1] == val[2] and val[3] == val[4] and val[5] == val[6]:
            variations.add(f"#{val[1]}{val[3]}{val[5]}")
        elif len(val) == 4:
            variations.add(f"#{val[1]}{val[1]}{val[2]}{val[2]}{val[3]}{val[3]}")

    named_reverse = {"#ffffff": "white", "#000000": "black", "#ff0000": "red", "#0000ff": "blue", "#008000": "green", "transparent": "transparent"}
    if val in named_reverse:
        variations.add(named_reverse[val])
    return list(variations)

def find_all_raw_value_lines(scss_file_path, compiled_value, engine, expected_category):
    variations = get_value_variations(compiled_value)
    hits = []
    has_any_match = False

    # Boundary constraints: Prevent matching partial values (e.g. 1.2 matching 1.25)
    boundary_chars = r'[a-zA-Z0-9\.\-%_#]'

    try:
        with open(scss_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            line_lower = line.lower()

            # Strip comments to prevent false positives
            line_lower = re.sub(r'/\*.*?\*/', '', line_lower)
            line_lower = re.sub(r'(?<!:)//.*', '', line_lower)

            if not line_lower.strip(): continue
            if line_lower.strip().startswith('$') and ':' in line_lower and '{' not in line_lower:
                continue

            for v in variations:
                pattern = re.compile(fr"(?<!{boundary_chars}){re.escape(v)}(?!{boundary_chars})", re.IGNORECASE)
                if pattern.search(line_lower):

                    # CONTEXT ISOLATION: Smart extraction handling nested {} and mixins
                    raw_prop = line_lower.strip() # Default to whole line if no colon is present

                    if ':' in line_lower:
                        parts = line_lower.split(':')
                        prop_chunk = parts[0]
                        for char in ['{', ';', '}']:
                            if char in prop_chunk:
                                prop_chunk = prop_chunk.split(char)[-1]
                        raw_prop = prop_chunk.strip()

                    line_cat = engine.determine_category(raw_prop, compiled_value)

                    # Exact match ensures cross-contamination is eliminated
                    if line_cat == expected_category:
                        hits.append(idx + 1)
                        has_any_match = True
                    break

        return hits, has_any_match
    except Exception as e:
        diagnostics.log_error(f"AST Verification Failed on {scss_file_path}: {e}")
        return [], False

def is_junk_value(val):
    val_clean = val.strip().lower()
    if val_clean in getattr(config, 'JUNK_VALUES', []): return True
    if val_clean.isalpha() and val_clean not in ['red', 'blue', 'green', 'black', 'white', 'gray']: return True
    return False

def execute_automated_extraction(metrics_list):
    shared_rules = []
    taxonomy = {"colors": {}, "typography": {}, "spacing": {}, "borders": {}, "shadows": {}, "sizing": {}, "misc": {}}
    counters = {k: 1 for k in taxonomy.keys()}
    lineage_hooks = {}
    engine = classifier.PropertyClassifier()

    scss_files = [f for f in os.listdir(config.SCSS_DIR) if f.endswith('.scss') and not ('var' in f.lower() or 'global' in f.lower())]

    for row in metrics_list:
        context_dict = ast.literal_eval(row["Context"])
        css_selector = row["Selector"]

        if row["Status"] == "Identical Match (Ready)":
            rule_body = "  " + ";\n  ".join([f"{k}: {v}" for k, v in context_dict.items()]) + ";"
            shared_rules.append(f"// Lineage: Ready for mapping\n{css_selector} {{\n{rule_body}\n}}")

        if config.CRAWL_SETTINGS["semantic_token_grouping"]:
            for prop, val in context_dict.items():
                if is_junk_value(val) or 'var(' in val.lower():
                    continue

                category = engine.determine_category(prop, val)

                exact_origins = []
                is_hardcoded = False
                for s_file in scss_files:
                    full_path = os.path.join(config.SCSS_DIR, s_file)
                    hits, file_has_match = find_all_raw_value_lines(full_path, val, engine, category)
                    if file_has_match: is_hardcoded = True
                    for h in hits: exact_origins.append(f"{s_file}:{h}")

                if not is_hardcoded:
                    continue

                if category == "colors":
                    hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}', str(val))
                    if hex_matches and config.CRAWL_SETTINGS["auto_extract_hex"]:
                        for h_val in hex_matches:
                            existing_var_name = None
                            for k, v in taxonomy["colors"].items():
                                if v.split(';')[0] == h_val:
                                    existing_var_name = k
                                    break

                            if existing_var_name:
                                lineage_hooks[existing_var_name].extend(exact_origins)
                            else:
                                var_name = f"$color-extracted-{counters['colors']}"
                                taxonomy["colors"][var_name] = h_val
                                lineage_hooks[var_name] = exact_origins
                                counters["colors"] += 1
                    else:
                        existing_var_name = None
                        for k, v in taxonomy["colors"].items():
                            if v.split(';')[0] == val:
                                existing_var_name = k
                                break

                        if existing_var_name:
                            lineage_hooks[existing_var_name].extend(exact_origins)
                        else:
                            var_name = f"$color-extracted-{counters['colors']}"
                            taxonomy["colors"][var_name] = val
                            lineage_hooks[var_name] = exact_origins
                            counters["colors"] += 1
                else:
                    existing_var_name = None
                    for k, v in taxonomy[category].items():
                        if v.split(';')[0] == val:
                            existing_var_name = k
                            break

                    if existing_var_name:
                        lineage_hooks[existing_var_name].extend(exact_origins)
                    else:
                        var_name = f"${category}-extracted-{counters[category]}"
                        taxonomy[category][var_name] = val
                        lineage_hooks[var_name] = exact_origins
                        counters[category] += 1

    var_file = os.path.join(config.OUTPUT_DIR, "_variables_generated.scss")
    with open(var_file, 'w', encoding='utf-8') as f:
        f.write("// Automatically Isolated Global Tokens\n\n")
        for cat, tokens in taxonomy.items():
            if tokens:
                f.write(f"// --- {cat.upper()} ---\n")
                for k, v in tokens.items():
                    val_str = v if ';' in v else f"{v};"
                    f.write(f"{k}: {val_str}\n")
                f.write("\n")

    shared_file = os.path.join(config.OUTPUT_DIR, "_shared_generated.scss")
    with open(shared_file, 'w', encoding='utf-8') as f:
        f.write("@import 'variables_generated';\n\n")
        f.write("\n\n".join(shared_rules))

    lineage_export = {k: list(set(v)) for k, v in lineage_hooks.items() if v}
    with open(os.path.join(config.OUTPUT_DIR, "lineage.json"), 'w', encoding='utf-8') as f:
        json.dump(lineage_export, f)

    return var_file
