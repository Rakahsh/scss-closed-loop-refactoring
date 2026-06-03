# -*- coding: utf-8 -*-
import os
import sass
import config
import diagnostics
import json
import re
import sys
import time
import threading

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

def build_scss_tree():
    try:
        diagnostics.log_info("Initializing SCSS Compilation with Auto-Injection & Shadow Mapping...")

        # Self-Healing: Ensure directories exist
        os.makedirs(config.SOURCE_DIR, exist_ok=True)
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        # Check if the global variable file exists to inject
        global_var_file = "_variable.scss"
        global_var_path = os.path.join(config.SCSS_DIR, global_var_file)
        has_globals = os.path.exists(global_var_path)

        selector_map = {}

        spinner = Spinner("Compiling & Shadow-Mapping SCSS components...")
        spinner.start()

        for file in os.listdir(config.SCSS_DIR):
            if file.endswith('.scss') and not file.startswith('_'):
                src_path = os.path.join(config.SCSS_DIR, file)
                out_path = os.path.join(config.SOURCE_DIR, file.replace('.scss', '.css'))

                with open(src_path, 'r', encoding='utf-8') as src:
                    scss_string = src.read()

                injected_offset = 0
                # --- AUTO-INJECTOR ---
                # Prepend the variables file directly into memory if it exists
                if has_globals and "@import 'variable'" not in scss_string and '@import "_variable"' not in scss_string:
                    scss_string = "@import '" + global_var_file + "';\n" + scss_string
                    injected_offset = 1

                # Compile from the in-memory string (Source Maps removed: Legacy dependency)
                compiled_css = sass.compile(
                    string=scss_string,
                    include_paths=[config.SCSS_DIR],
                    output_style='expanded'
                )

                with open(out_path, 'w', encoding='utf-8') as out:
                    out.write(compiled_css)

                # --- SHADOW COMPILER FOR FULL-STACK TRACEABILITY ---
                # Runs an isolated compile step to map SCSS lines to compiled CSS selectors safely
                try:
                    map_css = sass.compile(
                        string=scss_string,
                        include_paths=[config.SCSS_DIR],
                        output_style='expanded',
                        source_comments=True
                    )
                    pattern = re.compile(r'/\*\s*line\s+(\d+).*?\*/\s*([^{]+)\s*{', re.MULTILINE)
                    file_map = {}
                    for match in pattern.finditer(map_css):
                        line_num = int(match.group(1)) - injected_offset
                        if line_num > 0:
                            selector = match.group(2).strip().replace('\n', ' ')
                            file_map[str(line_num)] = selector
                    selector_map[file] = file_map
                except Exception:
                    pass # Fail silently, preserving primary production build

        with open(os.path.join(config.OUTPUT_DIR, "selector_map.json"), "w", encoding='utf-8') as f:
            json.dump(selector_map, f)

        spinner.stop()
        diagnostics.log_info("SCSS Compilation successful. CSS & Maps generated via Auto-Injector.")
        return True

    except sass.CompileError as e:
        if 'spinner' in locals(): spinner.stop()
        diagnostics.log_error(f"SCSS Syntax Error: {e}")
        return False
    except Exception as e:
        if 'spinner' in locals(): spinner.stop()
        diagnostics.log_error(f"Compiler System Error: {e}")
        return False
