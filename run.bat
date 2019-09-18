@echo off

pip install --user --upgrade pip==9.0.3
pip install -r requirements.txt

python run_service.py %*