# -*- coding: utf-8 -*-
import os
import sys
import csv
import webbrowser
from datetime import datetime
import config
import diagnostics
import compiler
import analyzer
import refactorer
import visualizer_api
import html_parser
import rewriter
import server

def generate_report_file(data, current_iteration, stamp):
    filepath = os.path.join(config.REPORT_DIR, f"copilot_drift_v{current_iteration}_{stamp}.csv")
    fields = ["Selector", "Status", "Source", "Context", "Drift Count", "Session Aging (s)"]
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)
    diagnostics.log_info(f"CSV Drift Report exported to {filepath}")
    return filepath

def get_global_file_name():
    files = [f for f in os.listdir(config.SCSS_DIR) if f.endswith('.scss')]
    for f in files:
        if 'var' in f.lower() or 'global' in f.lower():
            return f
    return None

def main():
    diagnostics.start_session()
    print("======================================================================")
    print("SCSS Dynamic Copilot Engine - v8.16.2 (Closed-Loop Edition)")
    print("======================================================================")

    import preflight
    preflight.run_system_checks()

    try:
        server.start_server(8080)
    except Exception as e:
        diagnostics.log_error(f"Failed to start local server: {e}")

    session_start = datetime.now()
    iteration = 1

    while True:
        print(f"\n--- [RUNNING REFACTOR ITERATION: {iteration}] ---")

        global_file = get_global_file_name()
        if global_file:
            diagnostics.log_info(f"Fuzzy Match: Registered '{global_file}' as the Global Variable Target.")
        else:
            diagnostics.log_warning("No global '_variables.scss' found. Dashboard previews may be limited.")

        if not compiler.build_scss_tree():
            action = input("Press [ENTER] to retry compile, or [q] to abort: ").strip().lower()
            if action == 'q': break
            continue

        compiled_targets = [f for f in os.listdir(config.SOURCE_DIR) if f.endswith('.css')]
        if len(compiled_targets) < 2:
            print(f"[HALT] Need at least 2 SCSS files in '{config.SCSS_DIR}'.")
            break

        session_aging = round((datetime.now() - session_start).total_seconds(), 2)

        results = analyzer.compute_discrepancies(
            os.path.join(config.SOURCE_DIR, compiled_targets[0]),
            os.path.join(config.SOURCE_DIR, compiled_targets[1]),
            session_aging
        )

        # --- THE FIX: Capture the generated _variables_generated.scss file path ---
        var_file_path = refactorer.execute_automated_extraction(results)

        html_snippets = html_parser.get_html_snippets()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Read the generated extracted tokens for the UI feed
        visualizer_scss_feed = ""
        if var_file_path and os.path.exists(var_file_path):
            with open(var_file_path, 'r', encoding='utf-8') as vf:
                visualizer_scss_feed = vf.read()

        global_scss_content = ""
        if global_file:
            with open(os.path.join(config.SCSS_DIR, global_file), 'r', encoding='utf-8') as f:
                global_scss_content = f.read()

        compiled_css_inject = ""
        for cf in compiled_targets:
            with open(os.path.join(config.SOURCE_DIR, cf), 'r', encoding='utf-8') as f:
                compiled_css_inject += f.read() + "\n"

        # Send data securely to API
        visualizer_api.update_api_payload(visualizer_scss_feed, html_snippets, compiled_css_inject, global_scss_content)
        csv_report = generate_report_file(results, iteration, stamp)

        print("\n[DAEMON CYCLE PAUSED] Engine awaits.")
        print(" [ENTER] Run next scan iteration")
        print(" [o]     Open Visual HUD in browser (http://localhost:8080/index.html)")
        print(" [r]     Rewrite codebase using resolution_map.json")
        print(" [c]     Open CSV Drift Report")
        print(" [q]     Quit")

        action = input("Selection: ").strip().lower()

        if action == 'q':
            break
        elif action == 'o':
            webbrowser.open('http://localhost:8080/index.html')
        elif action == 'c':
            if sys.platform == "win32": os.startfile(csv_report)
            elif sys.platform == "darwin": os.system(f"open '{csv_report}'")
            else: os.system(f"xdg-open '{csv_report}'")
        elif action == 'r':
            target_global = get_global_file_name()
            if not target_global:
                target_global = input("Enter global variable file name (e.g. _variable.scss): ").strip()
            rewriter.apply_resolution_map(target_global)

        iteration += 1

if __name__ == "__main__":
    main()