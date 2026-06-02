import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCSS_DIR = os.path.join(BASE_DIR, "src_scss")
HTML_DIR = os.path.join(BASE_DIR, "src_html")
SOURCE_DIR = os.path.join(BASE_DIR, "source_files")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
OUTPUT_DIR = os.path.join(BASE_DIR, "consolidated_output")
CONFIG_DATA_DIR = os.path.join(BASE_DIR, "config_data")
APPLIED_DIR = os.path.join(BASE_DIR, "output_applied")

BRAND_GUIDE_FILE = os.path.join(CONFIG_DATA_DIR, "brand_guide.json")
RESOLUTION_MAP_FILE = os.path.join(CONFIG_DATA_DIR, "resolution_map.json")
LOG_FILE = os.path.join(REPORT_DIR, "system_diagnostics.log")
API_PORT = 8080

CRAWL_SETTINGS = {
    "strip_comments": True,
    "lowercase_selectors": True,
    "auto_extract_hex": True,
    "semantic_token_grouping": True,
    "color_match_threshold_percent": 95.0
}

# The Exclusion Blacklist for v8.3.0
JUNK_VALUES = {
    "transparent", "inherit", "initial", "unset", "none", "auto",
    "0", "0px", "0%", "0em", "0rem", "100%", "100vw", "100vh",
    "normal", "bold", "italic", "underline", "hidden", "visible",
    "absolute", "relative", "fixed", "sticky", "static", "block", "inline", "flex", "grid"
}
