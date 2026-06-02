import os
import sys
import config

def run_system_checks():
    try:
        import cssutils
        import sass
    except ImportError as e:
        sys.exit(f"[FATAL] Missing module: {e}. Run pip install -r requirements.txt")

    for path in [config.SCSS_DIR, config.HTML_DIR, config.SOURCE_DIR, config.REPORT_DIR, config.OUTPUT_DIR, config.CONFIG_DATA_DIR, config.APPLIED_DIR]:
        os.makedirs(path, exist_ok=True)
