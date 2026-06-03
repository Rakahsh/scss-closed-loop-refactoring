# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import sass
import config
import diagnostics

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
        diagnostics.log_info("Initializing SCSS Compilation with Auto-Injection...")

        # Self-Healing: Ensure directories exist
        os.makedirs(config.SOURCE_DIR, exist_ok=True)

        # Check if the global variable file exists to inject
        global_var_file = "_variable.scss"
        global_var_path = os.path.join(config.SCSS_DIR, global_var_file)
        has_globals = os.path.exists(global_var_path)

        files_to_compile = [f for f in os.listdir(config.SCSS_DIR) if f.endswith('.scss') and not f.startswith('_')]

        # Start Progress Indicator
        spinner = Spinner(f"Compiling {len(files_to_compile)} SCSS components...")
        spinner.start()

        for file in files_to_compile:
            src_path = os.path.join(config.SCSS_DIR, file)
            out_path = os.path.join(config.SOURCE_DIR, file.replace('.scss', '.css'))

            with open(src_path, 'r', encoding='utf-8') as src:
                scss_string = src.read()

            # --- AUTO-INJECTOR ---
            if has_globals and "@import 'variable'" not in scss_string and '@import "_variable"' not in scss_string:
                scss_string = "@import '" + global_var_file + "';\n" + scss_string

            # Compile from the in-memory string
            compiled_css = sass.compile(
                string=scss_string,
                include_paths=[config.SCSS_DIR],
                output_style='expanded'
            )

            with open(out_path, 'w', encoding='utf-8') as out:
                out.write(compiled_css)

        # Stop Progress Indicator
        spinner.stop()
        diagnostics.log_info(f"SCSS Compilation successful. ({len(files_to_compile)} files generated via Auto-Injector)")
        return True

    except sass.CompileError as e:
        if 'spinner' in locals(): spinner.stop()
        diagnostics.log_error(f"SCSS Syntax Error: {e}")
        return False
    except Exception as e:
        if 'spinner' in locals(): spinner.stop()
        diagnostics.log_error(f"Compiler System Error: {e}")
        return False