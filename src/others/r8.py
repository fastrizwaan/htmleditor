#!/usr/bin/env python3
import gi
import tempfile
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit

class SimpleEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.SimpleEditor")
        self.connect('activate', self.on_activate)
        self.tempdir = tempfile.mkdtemp()
        self.editor_html_path = os.path.join(self.tempdir, "editor.html")
        
    def on_activate(self, app):
        # Create the application window
        self.win = Adw.ApplicationWindow(application=app, default_width=600, default_height=800)
        self.win.set_title("Simple Editor")
        
        # Main box layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_content(main_box)
        
        # Create the header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Add a button for testing
        test_button = Gtk.Button(label="Test Button")
        test_button.connect("clicked", self.on_test_clicked)
        header.pack_end(test_button)
        
        # Create WebView
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Connect to signals
        self.webview.connect("load-changed", self.on_load_changed)
        
        # Create scrolled window for the webview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.webview)
        main_box.append(scrolled)
        
        # Create editor HTML file with absolute minimal code
        self.create_editor_html()
        
        # Load the editor
        self.webview.load_uri(f"file://{self.editor_html_path}")
        
        # Show the window
        self.win.present()
    
    def create_editor_html(self):
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Basic Editor</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: sans-serif;
            background-color: #E0E0E0;
            display: flex;
            justify-content: center;
        }
        
        #editor {
            width: 400px;
            height: 300px;
            background-color: white;
            border: 5px solid #0066CC;
            padding: 20px;
            margin-top: 20px;
            font-size: 16px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <!-- Super simple editable div with pre-populated text -->
    <div id="editor" contenteditable="true">This is a test. You should be able to edit this text.

Try pressing Enter to create a new line.

The background should be white with a blue border.</div>

    <script>
        // Super simple - just track when the div is clicked to verify it works
        document.getElementById('editor').addEventListener('click', function() {
            console.log('Editor clicked');
        });
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            print("Page loaded completely")
    
    def on_test_clicked(self, button):
        print("Test button clicked")
        # Try to execute a simple JavaScript to check if editor exists
        self.webview.evaluate_javascript(
            "document.getElementById('editor') ? 'Editor exists' : 'Editor not found'",
            -1, None, None, None, None, self.on_js_finished, None
        )
    
    def on_js_finished(self, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                print(f"JavaScript result: {js_result.get_js_value().to_string()}")
        except Exception as e:
            print(f"JavaScript error: {e}")
    
    def do_shutdown(self):
        # Clean up temporary files
        if os.path.exists(self.tempdir):
            for file in os.listdir(self.tempdir):
                try:
                    os.unlink(os.path.join(self.tempdir, file))
                except:
                    pass
            try:
                os.rmdir(self.tempdir)
            except:
                pass
        
        Adw.Application.do_shutdown(self)

if __name__ == "__main__":
    app = SimpleEditor()
    app.run(None)
