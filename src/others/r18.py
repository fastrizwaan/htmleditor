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
        self.win = Adw.ApplicationWindow(application=app, default_width=800, default_height=600)
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
        
        # Create WebView with proper settings
        context = WebKit.WebContext.get_default()
        
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Enable developer tools for debugging
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(True)
        
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paginated Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            overflow-x: hidden;
            background-color: #f5f5f5;
        }
        
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            padding: 20px;
            min-height: 100vh;
        }
        
        .page {
            width: 300px;
            min-height: 200px;
            border: 1px solid #ccc;
            padding: 15px;
            line-height: 1.5;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            background-color: white;
            white-space: pre-wrap;
            word-wrap: break-word;
            position: relative;
            font-size: 16px;
        }
        
        .page:focus {
            outline: 2px solid #0078D7;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Make caret more visible */
        [contenteditable=true] {
            caret-color: black;
        }
        
        /* Debug outline - uncomment if needed */
        /*.page { outline: 1px solid red; }*/
    </style>
</head>
<body>
    <div id="editor-container"></div>

    <script>
        // Simple implementation first to ensure basic functionality works
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.getElementById('editor-container');
            
            // Create a single editable page to start
            const page = document.createElement('div');
            page.className = 'page';
            page.contentEditable = true;
            page.setAttribute('data-page-index', '0');
            page.textContent = ''; // Start with empty content
            
            // Log when element gets focus to help debugging
            page.addEventListener('focus', function() {
                console.log('Page focused');
            });
            
            // Handle input on the page
            page.addEventListener('input', function(e) {
                console.log('Input detected:', e.target.textContent);
                notifyContentChanged();
            });
            
            // Handle enter key specially to ensure proper line breaks
            page.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    // Don't prevent default - allow normal line break insertion
                    console.log('Enter key pressed');
                }
                
                // Handle Ctrl+S for save
                if (e.ctrlKey && e.key === 's') {
                    e.preventDefault();
                    requestSave();
                }
            });
            
            // Add the page to the container
            container.appendChild(page);
            
            // Focus the page immediately so user can start typing
            setTimeout(() => {
                page.focus();
                console.log('Initial focus set');
            }, 100);
            
            // Helper function to notify Python about content changes
            function notifyContentChanged() {
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.contentChanged) {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } else {
                    console.log('ContentChanged handler not available');
                }
            }
            
            // Helper function to request save
            function requestSave() {
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.saveRequested) {
                    window.webkit.messageHandlers.saveRequested.postMessage('save');
                } else {
                    console.log('SaveRequested handler not available');
                }
            }
            
            // Expose functions for Python to call
            window.getContentAsHtml = function() {
                console.log('Getting content as HTML');
                const pages = document.querySelectorAll('.page');
                let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Saved Document</title>';
                html += '<style>body{margin:20px;font-family:sans-serif;}.page{width:300px;min-height:200px;border:1px solid #ccc;';
                html += 'padding:15px;line-height:1.5;background-color:white;white-space:pre-wrap;word-wrap:break-word;';
                html += 'margin-bottom:20px;page-break-after:always;}</style></head><body>';
                
                html += '<div class="container">';
                pages.forEach(page => {
                    html += `<div class="page">${page.innerHTML}</div>`;
                });
                html += '</div></body></html>';
                
                return html;
            };
            
            window.getContentAsText = function() {
                console.log('Getting content as text');
                let text = '';
                document.querySelectorAll('.page').forEach(page => {
                    text += page.textContent;
                });
                return text;
            };
            
            // Debug function
            window.checkEditorState = function() {
                const page = document.querySelector('.page');
                console.log({
                    pageExists: !!page,
                    contentEditable: page ? page.contentEditable : 'N/A',
                    innerHTML: page ? page.innerHTML : 'N/A',
                    textContent: page ? page.textContent : 'N/A',
                    isFocused: document.activeElement === page
                });
            };
            
            // Run debug check after a delay
            setTimeout(window.checkEditorState, 500);
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
            
            # Check editor state after a delay
            GLib.timeout_add(1000, self.check_editor_state)
    
    def check_editor_state(self):
        self.webview.evaluate_javascript(
            "window.checkEditorState();", 
            -1, None, None, None, None, None, None
        )
        return False  # Don't repeat the timeout
    
    def on_content_changed(self, manager, message):
        self.content_changed = True
        print("Content changed")
    
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
