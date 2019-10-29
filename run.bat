@echo off

pip install --upgrade -q pip
pip install -q -r requirements.txt

python run_service.py %*