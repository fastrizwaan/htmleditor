import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio, GObject

import os
import sys
import json
import socket
import subprocess
import threading
import time
import random
import tempfile
import websocket
import requests
import uuid

class ChromeBridge:
    """Bridge to communicate with Chrome/Chromium via Chrome DevTools Protocol"""
    
    def __init__(self, chrome_path=None, debug_port=None):
        self.chrome_path = chrome_path or self._find_chrome_executable()
        self.debug_port = debug_port or random.randint(9222, 9999)
        self.user_data_dir = tempfile.mkdtemp(prefix="chrome-")
        self.process = None
        self.ws = None
        self.target_id = None
        self.session_id = None
        self.message_id = 0
        self.callbacks = {}
        self.connected = False
        
    def _find_chrome_executable(self):
        """Find Chrome or Chromium executable on the system."""
        possible_paths = [
            # Linux
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            # macOS
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            # Windows
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise Exception("Could not find Chrome or Chromium executable. Please specify the path manually.")
    
    def start(self):
        """Start Chrome in headless mode with remote debugging enabled."""
        if self.process:
            return
        
        args = [
            self.chrome_path,
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.user_data_dir}",
            "--headless=new",  # New headless mode
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions"
        ]
        
        self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for Chrome to start and the debugging port to be available
        max_retries = 10
        for i in range(max_retries):
            try:
                time.sleep(0.5)
                response = requests.get(f"http://localhost:{self.debug_port}/json/version")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                if i == max_retries - 1:
                    raise Exception("Failed to connect to Chrome DevTools")
                continue
        
        # Create a blank target/page
        response = requests.get(f"http://localhost:{self.debug_port}/json/new")
        if response.status_code != 200:
            raise Exception("Failed to create a new target")
        
        target_info = response.json()
        self.target_id = target_info["id"]
        
        # Connect to the WebSocket endpoint
        self.ws = websocket.create_connection(target_info["webSocketDebuggerUrl"])
        self.connected = True
        
        # Start the message handling thread
        threading.Thread(target=self._message_loop, daemon=True).start()
        
        # Create a new session
        response = self._send_message({
            "method": "Target.attachToTarget",
            "params": {
                "targetId": self.target_id,
                "flatten": True
            }
        })
        self.session_id = response["result"]["sessionId"]
    
    def _message_loop(self):
        """Background thread to handle incoming WebSocket messages."""
        while self.connected:
            try:
                message = self.ws.recv()
                data = json.loads(message)
                
                if "id" in data and data["id"] in self.callbacks:
                    callback = self.callbacks.pop(data["id"])
                    callback(data)
            except (websocket.WebSocketConnectionClosedException, json.JSONDecodeError):
                self.connected = False
                break
    
    def _send_message(self, message):
        """Send a message to Chrome and wait for a response."""
        if not self.connected:
            raise Exception("Not connected to Chrome")
        
        message_id = self.message_id
        self.message_id += 1
        message["id"] = message_id
        
        result = {"done": False, "response": None}
        event = threading.Event()
        
        def callback(response):
            result["response"] = response
            result["done"] = True
            event.set()
        
        self.callbacks[message_id] = callback
        self.ws.send(json.dumps(message))
        event.wait(timeout=5.0)
        
        if not result["done"]:
            raise Exception("Timeout waiting for response from Chrome")
        
        return result["response"]
    
    def navigate(self, url):
        """Navigate to a URL."""
        return self._send_message({
            "sessionId": self.session_id,
            "method": "Page.navigate",
            "params": {"url": url}
        })
    
    def get_document_html(self):
        """Get the HTML content of the document."""
        # First, get the document node ID
        response = self._send_message({
            "sessionId": self.session_id,
            "method": "DOM.getDocument",
            "params": {}
        })
        
        root_node_id = response["result"]["root"]["nodeId"]
        
        # Get outer HTML of the document
        response = self._send_message({
            "sessionId": self.session_id,
            "method": "DOM.getOuterHTML",
            "params": {"nodeId": root_node_id}
        })
        
        return response["result"]["outerHTML"]
    
    def evaluate_javascript(self, script):
        """Evaluate JavaScript in the current page."""
        response = self._send_message({
            "sessionId": self.session_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": script,
                "returnByValue": True
            }
        })
        
        if "result" in response and "result" in response["result"]:
            return response["result"]["result"].get("value")
        return None
    
    def load_html(self, html_content):
        """Load HTML content into the page."""
        # First, navigate to a blank page
        self.navigate("about:blank")
        
        # Then set the HTML content
        html_script = f"""
        document.open();
        document.write(`{html_content.replace('`', '\\`')}`);
        document.close();
        """
        self.evaluate_javascript(html_script)
    
    def capture_screenshot(self, path=None):
        """Capture a screenshot of the current page."""
        response = self._send_message({
            "sessionId": self.session_id,
            "method": "Page.captureScreenshot",
            "params": {}
        })
        
        screenshot_data = response["result"]["data"]
        
        if path:
            import base64
            with open(path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))
        
        return screenshot_data
    
    def close(self):
        """Close the connection and terminate Chrome."""
        if self.connected:
            try:
                self.ws.close()
            except:
                pass
            self.connected = False
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            
            self.process = None

class ChromeEditWindow(Gtk.ApplicationWindow):
    """GTK4 window that embeds Chrome via IPC for editing content."""
    
    def __init__(self, app, *args, **kwargs):
        super().__init__(application=app, *args, **kwargs)
        
        # Set up window
        self.set_default_size(900, 700)
        self.set_title("Chrome Editor (IPC)")
        
        # Create Chrome bridge
        self.chrome = ChromeBridge()
        
        # Create UI
        self.setup_ui()
        
        # Start Chrome and initialize the editor
        GLib.idle_add(self.initialize_chrome)
    
    def setup_ui(self):
        """Set up the GTK4 user interface."""
        # Main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_child(self.main_box)
        
        # HeaderBar
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        # Controls in header
        self.refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        self.header.pack_start(self.refresh_button)
        
        self.save_button = Gtk.Button.new_from_icon_name("document-save-symbolic")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.header.pack_end(self.save_button)
        
        # Format buttons
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        format_box.set_margin_start(8)
        format_box.set_margin_end(8)
        format_box.set_margin_top(8)
        format_box.set_margin_bottom(8)
        
        self.bold_button = Gtk.Button.new_with_label("Bold")
        self.bold_button.connect("clicked", self.on_format_clicked, "bold")
        format_box.append(self.bold_button)
        
        self.italic_button = Gtk.Button.new_with_label("Italic")
        self.italic_button.connect("clicked", self.on_format_clicked, "italic")
        format_box.append(self.italic_button)
        
        self.underline_button = Gtk.Button.new_with_label("Underline")
        self.underline_button.connect("clicked", self.on_format_clicked, "underline")
        format_box.append(self.underline_button)
        
        self.main_box.append(format_box)
        
        # Content preview 
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        
        self.preview = Gtk.Label()
        self.preview.set_markup("<i>Loading Chrome...</i>")
        self.preview.set_wrap(True)
        self.preview.set_xalign(0)
        self.preview.set_yalign(0)
        self.preview.set_margin_start(10)
        self.preview.set_margin_end(10)
        
        self.scrolled.set_child(self.preview)
        self.main_box.append(self.scrolled)
        
        # Status bar
        self.status_bar = Gtk.Label()
        self.status_bar.set_markup("<i>Starting Chrome...</i>")
        self.status_bar.set_xalign(0)
        self.status_bar.set_margin_start(10)
        self.status_bar.set_margin_end(10)
        self.status_bar.set_margin_top(5)
        self.status_bar.set_margin_bottom(5)
        self.main_box.append(self.status_bar)
        
        # Connect window close signal
        self.connect("close-request", self.on_window_close)
    
    def initialize_chrome(self):
        """Initialize Chrome and load the editor."""
        try:
            self.chrome.start()
            
            # Load editable content
            editable_html = """
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
                        min-height: 300px;
                        border: 1px solid #ccc;
                        padding: 10px;
                        box-sizing: border-box;
                        overflow: auto;
                        outline: none;
                    }
                </style>
            </head>
            <body>
                <div id="editor" contenteditable="true">Start typing here...</div>
                <script>
                    // Simple script to track changes
                    let lastContent = "";
                    const editor = document.getElementById('editor');
                    
                    editor.addEventListener('input', function() {
                        lastContent = editor.innerHTML;
                    });
                    
                    // Function to allow GTK app to get content
                    function getContent() {
                        return editor.innerHTML;
                    }
                    
                    // Function to allow GTK app to set content
                    function setContent(html) {
                        editor.innerHTML = html;
                        lastContent = html;
                    }
                    
                    // Function to apply formatting
                    function applyFormat(command) {
                        document.execCommand(command, false, null);
                        editor.focus();
                    }
                </script>
            </body>
            </html>
            """
            
            self.chrome.load_html(editable_html)
            
            # Take a screenshot to use as preview
            self.update_preview()
            
            # Set up timer to update preview regularly
            GLib.timeout_add(1000, self.update_preview)
            
            self.status_bar.set_markup("<i>Chrome ready. Editing in headless browser.</i>")
        except Exception as e:
            self.status_bar.set_markup(f"<span foreground='red'>Error: {str(e)}</span>")
            return False
        
        return False  # Don't call again
    
    def update_preview(self):
        """Update the content preview."""
        if not self.chrome.connected:
            return False
        
        try:
            # Get content from Chrome
            content = self.chrome.evaluate_javascript("getContent()")
            
            # Update preview (with some basic sanitization)
            safe_content = content.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
            self.preview.set_markup(f"<span>{safe_content}</span>")
            
            # Take screenshot periodically (optional, can be resource intensive)
            # screenshot_data = self.chrome.capture_screenshot()
            # TODO: Display screenshot in an image widget if needed
            
            return True  # Continue updating
        except Exception as e:
            self.status_bar.set_markup(f"<span foreground='red'>Error updating preview: {str(e)}</span>")
            return False
    
    def on_refresh_clicked(self, button):
        """Refresh the preview."""
        self.update_preview()
    
    def on_save_clicked(self, button):
        """Save the content."""
        try:
            content = self.chrome.evaluate_javascript("getContent()")
            
            # Create a file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Save HTML Content",
                parent=self,
                action=Gtk.FileChooserAction.SAVE
            )
            
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Save", Gtk.ResponseType.ACCEPT)
            
            dialog.set_current_name("editor_content.html")
            
            # Connect to the response signal
            dialog.connect("response", self.on_save_dialog_response, content)
            
            # Show the dialog
            dialog.show()
            
        except Exception as e:
            self.status_bar.set_markup(f"<span foreground='red'>Error saving: {str(e)}</span>")
    
    def on_save_dialog_response(self, dialog, response_id, content):
        """Handle the file chooser dialog response."""
        if response_id == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_bar.set_markup(f"<i>Content saved to {file_path}</i>")
            except Exception as e:
                self.status_bar.set_markup(f"<span foreground='red'>Error saving file: {str(e)}</span>")
        
        dialog.destroy()
    
    def on_format_clicked(self, button, format_type):
        """Apply formatting to the content."""
        try:
            self.chrome.evaluate_javascript(f"applyFormat('{format_type}')")
            self.update_preview()
        except Exception as e:
            self.status_bar.set_markup(f"<span foreground='red'>Error applying format: {str(e)}</span>")
    
    def on_window_close(self, *args):
        """Handle window closing."""
        # Close Chrome
        if hasattr(self, 'chrome'):
            self.chrome.close()
        return False

class ChromeEditorApp(Adw.Application):
    """GTK4 application with Libadwaita styling."""
    
    def __init__(self):
        super().__init__(application_id="com.example.ChromeEditor")
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        """Create and show the main window."""
        win = ChromeEditWindow(app)
        win.present()

if __name__ == "__main__":
    # Make sure required modules are installed
    missing_modules = []
    
    try:
        import websocket
    except ImportError:
        missing_modules.append('websocket-client')
    
    try:
        import requests
    except ImportError:
        missing_modules.append('requests')
    
    if missing_modules:
        print(f"Missing required modules: {', '.join(missing_modules)}")
        print("Please install them with:")
        print(f"pip install {' '.join(missing_modules)}")
        sys.exit(1)
    
    app = ChromeEditorApp()
    app.run(sys.argv)
