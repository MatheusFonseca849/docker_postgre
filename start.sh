#!/bin/bash
set -e

echo "========================================"
echo "  Running ETL pipeline..."
echo "========================================"
python etl.py

echo "========================================"
echo "  Starting Streamlit on port ${PORT:-8501}..."
echo "========================================"
streamlit run dashboard.py --server.port=${PORT:-8501} --server.address=0.0.0.0
