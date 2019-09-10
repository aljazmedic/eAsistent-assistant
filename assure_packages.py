import pip

def install_requirements():
    pip.main(["install", "--user", "--upgrade", "pip==9.0.3"]) 
    if hasattr(pip, 'main'):
        pip.main(['requirements.txt'])
    else:
        pip._internal.main(['install', package])

# Example
if __name__ == '__main__':
    install_requirements()