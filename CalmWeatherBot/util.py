import os

def get_variable(variable):
    try:
        return os.getenv(variable)
    except KeyError:
        print("Varaible '%s' not found." %variable)

