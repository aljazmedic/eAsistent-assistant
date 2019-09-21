import pip._internal
import pip


def install_requirements():
    if hasattr(pip, 'main'):
        pip.main(["install", "--user", "--upgrade", "pip==9.0.3"])
        pip.main(['install', '-r', 'requirements.txt'])
    else:
        pip._internal.main(["install", "--user", "--upgrade", "pip==9.0.3"])
        pip._internal.main(['install', '-r', 'requirements.txt'])


# Example
if __name__ == '__main__':
    install_requirements()
