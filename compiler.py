import sass
import os
import config
import diagnostics

def build_scss_tree():
    try:
        success = False
        for f in os.listdir(config.SCSS_DIR):
            if f.endswith('.scss') and not f.startswith('_'):
                in_file = os.path.join(config.SCSS_DIR, f)
                out_file = os.path.join(config.SOURCE_DIR, f.replace('.scss', '.css'))
                map_file = out_file + '.map'

                with open(out_file, 'w', encoding='utf-8') as css_out, open(map_file, 'w', encoding='utf-8') as map_out:
                    css, smap = sass.compile(filename=in_file, output_style='expanded', source_map_filename=f.replace('.scss', '.css.map'))
                    css_out.write(css)
                    map_out.write(smap)
                success = True

        if success:
            diagnostics.log_info("SCSS Compilation successful. AST Source Maps explicitly generated.")
            return True
        else:
            diagnostics.log_warning("No root SCSS files found in /src_scss/ to compile.")
            return False

    except sass.CompileError as e:
        diagnostics.log_error(f"SCSS Syntax Error: {e}")
        return False
