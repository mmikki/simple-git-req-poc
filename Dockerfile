# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Graphviz optional; used for rendering PNG from .dot
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates graphviz \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

RUN pip install --no-cache-dir pyyaml

# Copy the new tools set
COPY tools /opt/req-tools

# Default command runs all tools in sequence
CMD ["bash", "-lc", "\
  python /opt/req-tools/validate_requirements.py && \
  python /opt/req-tools/build_traceability.py && \
  python /opt/req-tools/export_matrix_csv.py && \
  python /opt/req-tools/export_graphviz.py && \
  python /opt/req-tools/export_html.py && \
  python /opt/req-tools/export_html_expandable.py && \
  ( dot -Tpng outputs/requirements.dot -o outputs/requirements.png || true )"]