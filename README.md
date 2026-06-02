# Autonomous SCSS Refactoring Copilot - v2.0.0

High-performance modular AST-parsing workbench and real-time codebase rewriter designed to consolidate styling footprints completely.

## Core Closed-Loop Workflow
1. Run `pip install -r requirements.txt`.
2. Define your master design tokens inside `/config_data/brand_guide.json`.
3. Drop your target `.scss` entry points into `/src_scss/`.
4. Drop your component `.html` files into `/src_html/`.
5. Run `python main.py` and press `o` to open the Visual Audit Dashboard.
6. Use the **Resolution Studio** tab to visually map all unbranded tokens to your JSON Brand Guide. Click "Export Resolution Map".
7. Save the downloaded `resolution_map.json` into the `/config_data/` directory.
8. Press `r` in the Python terminal. The engine will parse your entire framework and write the fully consolidated code into `/output_applied/`.