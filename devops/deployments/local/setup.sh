#!/bin/bash
cd "$(dirname "$0")/../../../"
echo $(pwd)
export PYTHONPATH=$(pwd)
source venv/Scripts/activate
pip install -r requirements.txt