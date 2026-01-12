#!/usr/bin/env bash
set -euo pipefail
python tools/validate_requirements.py
python tools/build_traceability.py
python tools/export_matrix_csv.py
python tools/export_graphviz.py
python tools/export_html.py
