#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD
python3 insights/api/insight_api.py
