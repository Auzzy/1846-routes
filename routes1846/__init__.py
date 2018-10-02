import os.path

_DIR_NAME = "data"

def get_data_file(filename):
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    return os.path.join(root_dir, _DIR_NAME, filename)


from routes1846.find_best_routes import find_best_routes