# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import time
import threading
import config
import re

# --- PROGRESS INDICATOR UTILITY ---
class Spinner:
    def __init__(self, message="Processing..."):
        self.spinner_chars = ['|', '/', '-', '\\']
        self.delay = 0.1
        self.message = message
        self.running = False
        self.thread = None

    def spin(self):
        while self.running:
            for char in self.spinner_chars:
                if not self.running: break
                sys.stdout.write(f'\r[ {char} ] {self.message}')
                sys.stdout.flush()
                time.sleep(self.delay)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 6) + '\r')
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
# ---------------------------------

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

    new_vars_to_append = {}
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

    if not global_var_file and len(args) > 0:
        global_var_file = args[0]

    if global_var_file:
        global_path = os.path.join(config.SCSS_DIR, global_var_file)
        if os.path.exists(global_path):
            with open(global_path, 'r', encoding='utf-8') as f:
                global_content = f.read()

            appended_count = 0
            with open(global_path, 'a', encoding='utf-8') as f:
                for var_name, var_value in new_vars_to_append.items():
                    if f"{var_name}:" not in global_content.replace(' ', ''):
                        if appended_count == 0:
                            f.write("\n\n// --- Auto-Appended by SCSS Copilot ---\n")
                        f.write(f"{var_name}: {var_value};\n")
                        appended_count += 1
                        global_content += f"\n{var_name}: {var_value};\n"

            if appended_count > 0:
                print(f"[REWRITER] Auto-Appended {appended_count} new variables to {global_var_file}")
    else:
        print("[WARNING] No global variable file detected to auto-append new tokens.")

    # Start Progress Indicator
    spinner = Spinner(f"Mutating {len(mapping)} AST tokens across {len(file_mutations)} components...")
    spinner.start()

    boundary_chars = r'[a-zA-Z0-9\.\-%_#]'
    total_mutations_applied = 0

    for filename, mutations in file_mutations.items():
        src_path = os.path.join(config.SCSS_DIR, filename)
        out_path = os.path.join(config.APPLIED_DIR, filename)

        if not os.path.exists(src_path):
            continue

        with open(src_path, 'r', encoding='utf-8') as src:
            lines = src.readlines()

        for mut in mutations:
            line_num = mut.get('line')
            old_raw = mut.get('raw')
            new_token = mut.get('mapped')

            if line_num and 1 <= line_num <= len(lines):
                idx = line_num - 1
                pattern = re.compile(fr"(?<!{boundary_chars}){re.escape(old_raw)}(?!{boundary_chars})", re.IGNORECASE)
                if pattern.search(lines[idx]):
                    lines[idx] = pattern.sub(new_token, lines[idx])
                    total_mutations_applied += 1

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, 'w', encoding='utf-8') as out:
            out.writelines(lines)

        try:
            shutil.copy2(out_path, src_path)
        except Exception as e:
            spinner.stop()
            print(f"    [ERROR] Sync promotion failed for {filename}: {e}")
            spinner.start()

    # Stop Progress Indicator
    spinner.stop()
    print(f"[SUCCESS] AST Rewrite Complete: {total_mutations_applied} mutations successfully applied and promoted!")
    return True