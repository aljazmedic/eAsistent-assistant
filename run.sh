#!/bin/bash

pip install --upgrade pip
pip install -r requirements.txt

shift # removes first arg
python run_service.py "$@"