#!/bin/bash
{
	# try activating through /venv/scripts/activate
	source venv/Scripts/activate
	echo "Using virtualenv"
} || {
	workon school_venv
	echo "Using virtualenvwrapper"
} || {
	echo "Using default environment"
}

python run_service.py $@
{
	deactivate
} || {
	echo "Unable to deactivate"
}
echo "Done"