@echo off

pip install --upgrade pip==19.0.1
pip install -r requirements.txt

python run_service.py %*