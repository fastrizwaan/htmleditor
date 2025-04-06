# methods/__init__.py
from .show_error_dialog import show_error_dialog
from .on_quit import on_quit
from .setup_keyboard_shortcuts import setup_keyboard_shortcuts
from .save_preferences import save_preferences


# Define __all__ to control what gets imported with "import *"
__all__ = [
'show_error_dialog',
'on_quit',
'setup_keyboard_shortcuts',
'save_preferences']
