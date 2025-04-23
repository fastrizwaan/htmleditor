import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')  # Using WebKit 6.0 for GTK4
from gi.repository import Gtk, Adw, WebKit, GLib
import os
import sys
import webview  # PyWebView

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up window
        self.set_default_size(900, 700)
        self.set_title("PyWebView in GTK4/Libadwaita")
        
        # Create main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        
        # Add header bar with Libadwaita styling
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        # Add URL entry
        self.url_entry = Gtk.Entry()
        self.url_entry.set_hexpand(True)
        self.url_entry.set_text("data:text/html,<html><body contenteditable style='height:100%; padding:20px; font-family:sans-serif;'>Start typing here...</body></html>")
        self.url_entry.connect("activate", self.on_url_activate)
        self.header.set_title_widget(self.url_entry)
        
        # Add navigation buttons
        self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back_button.connect("clicked", self.on_back_clicked)
        self.header.pack_start(self.back_button)
        
        self.forward_button = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.forward_button.connect("clicked", self.on_forward_clicked)
        self.header.pack_start(self.forward_button)
        
        self.refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        self.header.pack_start(self.refresh_button)
        
        # Create WebView
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.main_box.append(self.webview)
        
        # Connect signals
        self.connect("close-request", self.on_window_destroy)
        
        # Initialize browser
        self.init_browser()
    
    def init_browser(self):
        """Initialize the browser with default URL."""
        url = self.url_entry.get_text()
        self.webview.load_uri(url)
    
    def on_url_activate(self, entry):
        """Navigate to URL when Enter is pressed in the URL bar."""
        self.webview.load_uri(entry.get_text())
    
    def on_back_clicked(self, button):
        """Navigate back."""
        if self.webview.can_go_back():
            self.webview.go_back()
    
    def on_forward_clicked(self, button):
        """Navigate forward."""
        if self.webview.can_go_forward():
            self.webview.go_forward()
    
    def on_refresh_clicked(self, button):
        """Refresh the current page."""
        self.webview.reload()
    
    def on_window_destroy(self, *args):
        """Handle window closing."""
        return False

class EditorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        # Create and show the window
        win = MainWindow(application=app)
        win.present()

# Alternative implementation using only PyWebView
def run_pywebview_only():
    """
    Launch a window using only PyWebView (without GTK4/Libadwaita).
    This is a simpler alternative if GTK4 integration is giving trouble.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                margin: 0;
                padding: 20px;
                height: 100vh;
                box-sizing: border-box;
            }
            #editor {
                width: 100%;
                height: 90%;
                border: 1px solid #ccc;
                padding: 10px;
                box-sizing: border-box;
                overflow: auto;
                outline: none;
            }
            .toolbar {
                margin-bottom: 10px;
                display: flex;
                gap: 10px;
            }
            button {
                padding: 5px 10px;
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background: #e0e0e0;
            }
        </style>
    </head>
    <body>
        <div class="toolbar">
            <button id="saveBtn">Save</button>
            <button id="boldBtn">Bold</button>
            <button id="italicBtn">Italic</button>
            <button id="underlineBtn">Underline</button>
        </div>
        <div id="editor" contenteditable="true">Start typing here...</div>
        
        <script>
            document.getElementById('saveBtn').addEventListener('click', function() {
                const content = document.getElementById('editor').innerHTML;
                alert('Content would be saved:\n' + content);
            });
            
            document.getElementById('boldBtn').addEventListener('click', function() {
                document.execCommand('bold', false, null);
                document.getElementById('editor').focus();
            });
            
            document.getElementById('italicBtn').addEventListener('click', function() {
                document.execCommand('italic', false, null);
                document.getElementById('editor').focus();
            });
            
            document.getElementById('underlineBtn').addEventListener('click', function() {
                document.execCommand('underline', false, null);
                document.getElementById('editor').focus();
            });
        </script>
    </body>
    </html>
    """
    
    webview.create_window('Editable Content', html=html_content)
    webview.start()

# Main entry point
if __name__ == "__main__":
    # Uncomment the preferred method:
    
    # Method 1: Full GTK4/Libadwaita with WebKit
    app = EditorApp(application_id="com.example.WebViewEditor")
    app.run(sys.argv)
    
    # Method 2: PyWebView only (simpler, fewer dependencies)
    # run_pywebview_only()
