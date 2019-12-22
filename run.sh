#!/bin/bash
if workon school_venv; then
	echo "Using virtualenvwrapper"
elif source venv/Scripts/activate; then
	echo "Using virtualenv"
else
	echo "Using default environment"
fi

python run_service.py $@
if deactivate; then
	echo "Unable to deactivate";
else
	echo "Done";
fi
