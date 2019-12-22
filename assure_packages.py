import subprocess
import sys, logging

LEVELS = {
	logging.INFO: None,
	logging.DEBUG: None,
	logging.WARNING: "-q"
}


def install_requirements(level=logging.INFO):
	lvl = LEVELS[level]
	lvl = [] if lvl is None else [lvl]
	subprocess.check_call([sys.executable, "-m", "pip", "install"] + lvl + ['-r', 'requirements.txt'])


def install_pip(version=None, level=logging.INFO):
	lvl = LEVELS[level]
	lvl = [] if lvl is None else [lvl]
	if version is None:
		subprocess.check_call([sys.executable, "-m", "pip", "install"] + lvl + ["--upgrade", "pip"])
	else:
		subprocess.check_call([sys.executable, "-m", "pip", "install"] + lvl + ["--upgrade", f"pip=={version}"])


# Example
if __name__ == '__main__':
	install_pip()
	install_requirements()
