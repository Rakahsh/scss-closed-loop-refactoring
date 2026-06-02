# -*- coding: utf-8 -*-
import os
import json
import config

def apply_resolution_map():
    print("\n[REWRITER] Initializing AST Line-Level codebase rewrite...")

    if not os.path.exists(config.RESOLUTION_MAP_FILE):
        print(f"[ERROR] Could not find {config.RESOLUTION_MAP_FILE}.")
        return False

    with open(config.RESOLUTION_MAP_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    if not mapping or not isinstance(mapping, list):
        print("[ERROR] Resolution map is empty or not in the required Array format.")
        return False

    print(f"[REWRITER] Processing {len(mapping)} specific AST line mutations...")

    # Group mutations by file to avoid opening/closing files multiple times
    file_mutations = {}
    for mut in mapping:
        f_name = mut['file']
        if f_name not in file_mutations:
            file_mutations[f_name] = []
        file_mutations[f_name].append(mut)

    for filename, mutations in file_mutations.items():
        src_path = os.path.join(config.SCSS_DIR, filename)
        out_path = os.path.join(config.APPLIED_DIR, filename)

        if not os.path.exists(src_path):
            print(f"[WARNING] Source file missing: {filename}")
            continue

        with open(src_path, 'r', encoding='utf-8') as src:
            lines = src.readlines()

        # Apply mutations line by line
        for mut in mutations:
            line_num = mut.get('line')
            old_raw = mut.get('raw')
            new_token = mut.get('mapped')

            if line_num and line_num <= len(lines):
                idx = line_num - 1
                # Target the specific line and replace the raw hardcoded value
                lines[idx] = lines[idx].replace(old_raw, new_token)

        with open(out_path, 'w', encoding='utf-8') as out:
            out.writelines(lines)

    print(f"[SUCCESS] AST Rewrites successfully applied to {config.APPLIED_DIR}/")
    return True
