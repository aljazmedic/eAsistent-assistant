#!/bin/bash

python -m pip install -q pip
pip install -q -r requirements.txt

python run_service.py $@