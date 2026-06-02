# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - Closed-Loop Application Release

### Added
- [Added] Created the `rewriter.py` daemon module. The engine now applies SCSS token mappings back onto original structural files (`.scss`) and cross-compiles CSS custom properties natively onto HTML templates in `/output_applied/`.
- [Added] Created `html_parser.py` capable of crawling the `/src_html/` directory and injecting raw structural components into the interactive visual Sandbox.
- [Added] Integrated the "Resolution Studio" UI into the Visual Audit HTML template. It automatically parses extracted drift states and allows click-to-map binding against the Brand Guide.

### Fixed
- [Fixed] Categorization Bugs in JavaScript visualizer. Upgraded generic regex constraints via `.includes()` logic, ensuring complex Python extraction strings (`$typography-extracted-12`) correctly populate contrast matrices and radii tabs.

### Changed
- [Changed] Altered execution state in `main.py` daemon loop. Process now pauses and allows structural 'Hot Keys' (`o` to open UI, `r` to rewrite codebase).