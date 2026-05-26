#!/bin/bash
set -e

echo "========================================"
echo "  Running ETL pipeline..."
echo "========================================"
python etl.py

echo "========================================"
echo "  Starting Streamlit dashboard..."
echo "========================================"
streamlit run dashboard.py
