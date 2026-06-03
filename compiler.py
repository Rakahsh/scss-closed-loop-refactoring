# -*- coding: utf-8 -*-
import os
import sass
import config
import diagnostics

def build_scss_tree():
    try:
        diagnostics.log_info("Initializing SCSS Compilation with Auto-Injection...")

        # Self-Healing: Ensure directories exist
        os.makedirs(config.SOURCE_DIR, exist_ok=True)

        # Check if the global variable file exists to inject
        global_var_file = "_variable.scss"
        global_var_path = os.path.join(config.SCSS_DIR, global_var_file)
        has_globals = os.path.exists(global_var_path)

        for file in os.listdir(config.SCSS_DIR):
            if file.endswith('.scss') and not file.startswith('_'):
                src_path = os.path.join(config.SCSS_DIR, file)
                out_path = os.path.join(config.SOURCE_DIR, file.replace('.scss', '.css'))

                with open(src_path, 'r', encoding='utf-8') as src:
                    scss_string = src.read()

                # --- AUTO-INJECTOR ---
                # Prepend the variables file directly into memory if it exists
                if has_globals and "@import 'variable'" not in scss_string and '@import "_variable"' not in scss_string:
                    scss_string = "@import '" + global_var_file + "';\n" + scss_string

                # Compile from the in-memory string (Source Maps removed: Legacy dependency)
                compiled_css = sass.compile(
                    string=scss_string,
                    include_paths=[config.SCSS_DIR],
                    output_style='expanded'
                )

                with open(out_path, 'w', encoding='utf-8') as out:
                    out.write(compiled_css)

        diagnostics.log_info("SCSS Compilation successful. CSS generated via Auto-Injector.")
        return True

    except sass.CompileError as e:
        diagnostics.log_error(f"SCSS Syntax Error: {e}")
        return False
    except Exception as e:
        diagnostics.log_error(f"Compiler System Error: {e}")
        return False