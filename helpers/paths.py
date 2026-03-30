import os
import sys

def get_base_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return base_path

def get_config_path(filename):
    """
    Get path to config file.
    If running in frozen mode (PyInstaller), looking in the same directory as executable.
    If running in dev mode, looking in project root.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        application_path = os.path.dirname(sys.executable)
    else:
        # Running from source
        application_path = os.path.abspath(".")
        
    return os.path.join(application_path, filename)

def get_asset_path(filename):
    """
    Get path to asset file.
    """
    return os.path.join(get_base_path(), filename)
