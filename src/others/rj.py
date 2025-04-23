import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, WebKit, GLib, Gio
import json

class ReactGtkApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.ReactGtkApp")
        self.connect("activate", self.on_activate)
        self.webview = None
        
    def on_activate(self, app):
        # Create main window
        window = Gtk.ApplicationWindow(application=app, title="React GTK App")
        window.set_default_size(800, 600)
        
        # Create WebKit WebView
        self.webview = WebKit.WebView()
        
        # Set up JavaScript to Python bridge
        settings = self.webview.get_settings()
        settings.set_enable_javascript(True)
        
        self.webview.connect("load-changed", self.on_load_changed)
        
        # Get absolute path to index.html in the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "index.html")
        
        # Format the file URI correctly
        file_uri = f"file://{html_path}"
        print(f"Loading HTML from: {file_uri}")
        
        # Load React app with proper file URI
        self.webview.load_uri(file_uri)
        
        # Add WebView to window
        window.set_child(self.webview)
        window.present()
        
    # Rest of your code remains the same...
