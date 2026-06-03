# -*- coding: utf-8 -*-
import os
import json
import shutil
import config

# Accept the global_var_file argument passed by main.py
def apply_resolution_map(global_var_file=None, *args, **kwargs):
    print("\n[REWRITER] Initializing AST Line-Level codebase rewrite...")

    if not os.path.exists(config.RESOLUTION_MAP_FILE):
        print(f"[ERROR] Could not find {config.RESOLUTION_MAP_FILE}. Export it from the Visual Dashboard first.")
        return False

    with open(config.RESOLUTION_MAP_FILE, 'r', encoding='utf-8') as f:
        try:
            mapping = json.load(f)
        except json.JSONDecodeError:
            print("[ERROR] resolution_map.json is corrupted or malformed.")
            return False

    if not mapping or not isinstance(mapping, list):
        print("[ERROR] Resolution map is empty or not in the required AST Array format.")
        return False

    print(f"[REWRITER] Processing {len(mapping)} specific AST line mutations...")

    # 1. Gather all variables to dynamically append to global vars
    new_vars_to_append = {}

    # Group mutations by file to optimize I/O operations
    file_mutations = {}
    for mut in mapping:
        f_name = mut.get('file')
        mapped_var = mut.get('mapped')
        raw_val = mut.get('raw')

        if mapped_var and raw_val:
            new_vars_to_append[mapped_var] = raw_val

        if not f_name:
            continue
        if f_name not in file_mutations:
            file_mutations[f_name] = []
        file_mutations[f_name].append(mut)

    # --- GLOBAL VARIABLE AUTO-DECLARATION ---
    if global_var_file:
        global_path = os.path.join(config.SCSS_DIR, global_var_file)
        if os.path.exists(global_path):
            with open(global_path, 'r', encoding='utf-8') as f:
                global_content = f.read()

            appended_count = 0
            with open(global_path, 'a', encoding='utf-8') as f:
                for var_name, var_value in new_vars_to_append.items():
                    # If the user mapped to a custom token that isn't declared yet, append it.
                    if f"{var_name}:" not in global_content.replace(' ', ''):
                        if appended_count == 0:
                            f.write("\n\n// --- Auto-Appended by SCSS Copilot ---\n")
                        f.write(f"{var_name}: {var_value};\n")
                        appended_count += 1

            if appended_count > 0:
                print(f"[REWRITER] Auto-Appended {appended_count} new variables to {global_var_file}")
    else:
        print("[WARNING] No global variable file detected to auto-append new tokens.")
    # ----------------------------------------

    for filename, mutations in file_mutations.items():
        src_path = os.path.join(config.SCSS_DIR, filename)
        out_path = os.path.join(config.APPLIED_DIR, filename)

        if not os.path.exists(src_path):
            print(f"[WARNING] Source file missing: {filename}")
            continue

        with open(src_path, 'r', encoding='utf-8') as src:
            lines = src.readlines()

        # Apply mutations line by line
        mutations_applied = 0
        for mut in mutations:
            line_num = mut.get('line')
            old_raw = mut.get('raw')
            new_token = mut.get('mapped')

            if line_num and 1 <= line_num <= len(lines):
                idx = line_num - 1
                if old_raw in lines[idx]:
                    lines[idx] = lines[idx].replace(old_raw, new_token)
                    mutations_applied += 1

        # Ensure output staging directory exists
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, 'w', encoding='utf-8') as out:
            out.writelines(lines)

        print(f" -> Staged {filename}: {mutations_applied} mutations applied.")

        # Closed-Loop Promotion: Safely back-sync from staging directly to src_scss
        try:
            shutil.copy2(out_path, src_path)
            print(f"    [SYNC] Promoted staged changes back to source folder: {src_path}")
        except Exception as e:
            print(f"    [ERROR] Sync promotion failed for {filename}: {e}")

    print(f"\n[SUCCESS] AST Rewrites successfully applied and promoted to production source!")
    return True