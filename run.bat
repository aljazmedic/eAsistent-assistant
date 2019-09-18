@echo off

pip install --upgrade pip
pip install -r requirements.txt

python run_service.py %*