from pip import _internal
import pip

import subprocess
import sys, os


def install_requirements():
	subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", '-r', 'requirements.txt'])


def install_pip(version=None):
	if version is None:
		subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--user", "--upgrade", "pip"])
	else:
		subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--user", "--upgrade", f"pip=={version}"])


# Example
if __name__ == '__main__':
	install_pip()
	install_requirements()
