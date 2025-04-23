#!/usr/bin/env python3
import gi
import tempfile
import os
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, GLib, WebKit, Gio

class PaginatedEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.PaginatedEditor")
        self.connect('activate', self.on_activate)
        self.tempdir = tempfile.mkdtemp()
        self.editor_html_path = os.path.join(self.tempdir, "editor.html")
        self.content_changed = False
        
    def on_activate(self, app):
        # Create the application window
        self.win = Adw.ApplicationWindow(application=app, default_width=600, default_height=800)
        self.win.set_title("Paginated Editor")
        
        # Main box layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_content(main_box)
        
        # Create the header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Add save button
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        header.pack_end(save_button)
        
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
        
        # Create editor HTML file
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
    <title>Paginated Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            overflow-x: hidden;
        }
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            padding: 20px;
        }
        .page {
            width: 10ch;
            height: 2em;
            border: 1px solid #000;
            padding: 10px;
            line-height: 1em;
            overflow: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            position: relative;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            background-color: white;
            user-select: text;
            cursor: text;
        }
    </style>
</head>
<body>
    <div id="editor-container"></div>
    <textarea id="hidden-input" spellcheck="false"></textarea>

    <script>
        // Editor state
        let text = '';
        const pageWidth = 10; // characters
        const pageHeight = 2; // lines
        const charsPerPage = pageWidth * pageHeight;
        const container = document.getElementById('editor-container');
        const hiddenInput = document.getElementById('hidden-input');
        
        // Focus the hidden input on page load
        window.addEventListener('load', () => {
            hiddenInput.focus();
        });
        
        // Keep focus on the hidden input
        document.addEventListener('click', () => {
            hiddenInput.focus();
        });
        
        // Handle input events
        hiddenInput.addEventListener('input', (e) => {
            text = hiddenInput.value;
            updatePages();
            
            // Notify the Python app that content has changed
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        });
        
        // Function to update pages based on text content
        function updatePages() {
            // Clear the container
            container.innerHTML = '';
            
            // Calculate how many pages we need
            const totalChars = text.length;
            const numPages = Math.max(1, Math.ceil(totalChars / charsPerPage));
            
            // Create pages
            for (let i = 0; i < numPages; i++) {
                const startChar = i * charsPerPage;
                const endChar = Math.min(startChar + charsPerPage, totalChars);
                const pageText = text.substring(startChar, endChar);
                
                const page = document.createElement('div');
                page.className = 'page';
                page.textContent = pageText;
                page.dataset.pageIndex = i;
                
                container.appendChild(page);
            }
        }
        
        // Initialize with one empty page
        updatePages();
        
        // Function to get all content as HTML
        function getContentAsHtml() {
            const pages = document.querySelectorAll('.page');
            let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Saved Document</title>';
            html += '<style>body{margin:20px;font-family:sans-serif;}.page{width:10ch;height:2em;border:1px solid #000;';
            html += 'padding:10px;line-height:1em;overflow:hidden;white-space:pre-wrap;word-wrap:break-word;';
            html += 'margin-bottom:20px;page-break-after:always;}</style></head><body>';
            
            html += '<div class="container">';
            pages.forEach(page => {
                html += `<div class="page">${page.textContent}</div>`;
            });
            html += '</div></body></html>';
            
            return html;
        }
        
        // Function to get all content as text
        function getContentAsText() {
            return text;
        }
        
        // Enable keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+S to save
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                window.webkit.messageHandlers.saveRequested.postMessage('save');
            }
        });
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Register message handlers for communication between JS and Python
            user_content_manager = self.webview.get_user_content_manager()
            
            # Handler for content changes
            content_changed_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "contentChanged")
            if content_changed_handler:
                user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            
            # Handler for save requests
            save_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "saveRequested")
            if save_handler:
                user_content_manager.connect("script-message-received::saveRequested", self.on_save_requested)
    
    def on_content_changed(self, manager, message):
        self.content_changed = True
    
    def on_save_requested(self, manager, message):
        self.on_save_clicked(None)
    
    def on_save_clicked(self, button):
        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self.win,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.ACCEPT
        )
        dialog.set_current_name("document.html")
        
        # Set up filters
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        dialog.add_filter(filter_html)
        
        dialog.connect("response", self.on_save_dialog_response)
        dialog.present()
    
    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            
            # Get content from WebView
            self.webview.evaluate_javascript("getContentAsHtml();", -1, None, None, None, None, self.save_html_callback, file_path)
        
        dialog.destroy()
    
    def save_html_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                html_content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    f.write(html_content)
                
                self.show_notification("Document saved successfully")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")
    
    def show_notification(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        # In GTK4/libadwaita, we need a ToastOverlay to show toasts
        # For simplicity in this example, we'll just print the message
        print(message)
    
    def do_shutdown(self):
        # Clean up temporary files
        if os.path.exists(self.tempdir):
            for file in os.listdir(self.tempdir):
                os.unlink(os.path.join(self.tempdir, file))
            os.rmdir(self.tempdir)
        
        Adw.Application.do_shutdown(self)

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
