#!/usr/bin/env python3
import gi
import tempfile
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit

class FlowingPaginatedEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.FlowingPaginatedEditor")
        self.connect('activate', self.on_activate)
        self.tempdir = tempfile.mkdtemp()
        self.editor_html_path = os.path.join(self.tempdir, "editor.html")
        
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
    <title>Flowing Paginated Editor</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: sans-serif;
            background-color: #E0E0E0;
        }
        
        #editor-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            margin-bottom: 50px;
            position: relative;
        }
        
        /* Hide the main content editor */
        #main-editor {
            position: absolute;
            left: -9999px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }
        
        .page {
            width: 300px;
            height: 120px;
            background-color: white;
            border: 3px solid #0066CC;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow: hidden;
            position: relative;
            user-select: text;
            /* Make uneditable but selectable */
            -webkit-user-modify: read-only;
        }
        
        .page:focus {
            outline: none;
            border-color: #CC0066;
            box-shadow: 0 0 12px rgba(0, 102, 204, 0.5);
        }
        
        .page-number {
            position: absolute;
            bottom: 2px;
            right: 5px;
            font-size: 10px;
            color: #999;
            user-select: none;
            pointer-events: none;
        }
        
        /* Style for the true editor */
        #visible-editor {
            width: 300px;
            min-height: 120px;
            background-color: white;
            border: 3px solid #00CC66;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-top: 20px;
        }
        
        #visible-editor:focus {
            outline: none;
            border-color: #CC0066;
        }
    </style>
</head>
<body>
    <!-- Hidden editor that stores the true content -->
    <div id="main-editor" contenteditable="true"></div>
    
    <!-- Container for page displays -->
    <div id="editor-wrap"></div>
    
    <!-- Visible editor for actual editing -->
    <div id="visible-editor" contenteditable="true">Start typing here. The text will automatically flow into pages as you type.</div>

    <script>
        // Main elements
        const mainEditor = document.getElementById('main-editor');
        const editorWrap = document.getElementById('editor-wrap');
        const visibleEditor = document.getElementById('visible-editor');
        
        // Configuration
        const pageWidth = 300;
        const pageHeight = 120;
        const pagePadding = 15;
        const effectiveWidth = pageWidth - (pagePadding * 2);
        const effectiveHeight = pageHeight - (pagePadding * 2);
        
        // Initialize
        let allText = '';
        let isUpdating = false;
        
        // Create a measurement div for text fitting
        const measureDiv = document.createElement('div');
        measureDiv.style.position = 'absolute';
        measureDiv.style.visibility = 'hidden';
        measureDiv.style.width = effectiveWidth + 'px';
        measureDiv.style.whiteSpace = 'pre-wrap';
        measureDiv.style.wordWrap = 'break-word';
        document.body.appendChild(measureDiv);
        
        // Handle input in the visible editor
        visibleEditor.addEventListener('input', function() {
            if (isUpdating) return;
            
            allText = visibleEditor.innerText;
            updatePages();
        });
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl+A to select all text
            if (e.ctrlKey && e.key === 'a') {
                e.preventDefault();
                
                // Select all text in the visible editor
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(visibleEditor);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        });
        
        // Function to update the page displays
        function updatePages() {
            if (isUpdating) return;
            isUpdating = true;
            
            // Store text from the visible editor
            allText = visibleEditor.innerText;
            
            // Clear the pages
            editorWrap.innerHTML = '';
            
            // If no text, show nothing
            if (!allText.trim()) {
                isUpdating = false;
                return;
            }
            
            // Split text into pages
            const pages = splitIntoPages(allText);
            
            // Create display pages
            pages.forEach((pageText, index) => {
                createPageDisplay(pageText, index);
            });
            
            isUpdating = false;
        }
        
        // Function to split text into pages by content length
        function splitIntoPages(text) {
            const pages = [];
            let remainingText = text;
            
            while (remainingText.length > 0) {
                // Measure how much text fits on a page
                const fitLength = findFittingTextLength(remainingText);
                
                // Add page
                pages.push(remainingText.substring(0, fitLength));
                
                // Update remaining text
                remainingText = remainingText.substring(fitLength);
            }
            
            return pages;
        }
        
        // Function to find how much text fits on a page
        function findFittingTextLength(text) {
            // If text is empty, return 0
            if (!text) return 0;
            
            measureDiv.innerHTML = '';
            
            // If text is short enough to fit, return its length
            measureDiv.textContent = text;
            if (measureDiv.clientHeight <= effectiveHeight) {
                return text.length;
            }
            
            // Binary search to find the fitting text length
            let min = 0;
            let max = text.length;
            let mid;
            let bestFit = 0;
            
            while (min <= max) {
                mid = Math.floor((min + max) / 2);
                measureDiv.textContent = text.substring(0, mid);
                
                if (measureDiv.clientHeight <= effectiveHeight) {
                    bestFit = mid;
                    min = mid + 1;
                } else {
                    max = mid - 1;
                }
            }
            
            // If we couldn't fit anything, take at least one character
            if (bestFit === 0 && text.length > 0) {
                return 1;
            }
            
            return bestFit;
        }
        
        // Function to create a display page
        function createPageDisplay(text, index) {
            const page = document.createElement('div');
            page.className = 'page';
            page.textContent = text;
            
            const pageNumber = document.createElement('div');
            pageNumber.className = 'page-number';
            pageNumber.textContent = 'Page ' + (index + 1);
            page.appendChild(pageNumber);
            
            // Make page selectable but not directly editable
            page.addEventListener('mousedown', function() {
                // When clicking a page, focus the editor
                visibleEditor.focus();
            });
            
            editorWrap.appendChild(page);
        }
        
        // Function to get content for saving
        function getContent() {
            return allText;
        }
        
        // Initial setup
        updatePages();
        
        // Focus the editor on start
        visibleEditor.focus();
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            print("Page loaded completely")
    
    def on_save_clicked(self, button):
        self.webview.evaluate_javascript(
            "getContent();",
            -1, None, None, None, None, self.on_get_content, None
        )
    
    def on_get_content(self, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                content = js_result.get_js_value().to_string()
                print(f"Content: {content}")
                # Here you would handle saving the content
                self.show_save_dialog(content)
        except Exception as e:
            print(f"Error getting content: {e}")
    
    def show_save_dialog(self, content):
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self.win,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.ACCEPT
        )
        dialog.set_current_name("document.txt")
        
        dialog.connect("response", self.on_save_dialog_response, content)
        dialog.present()
    
    def on_save_dialog_response(self, dialog, response, content):
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"File saved to {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")
        
        dialog.destroy()
    
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
    app = FlowingPaginatedEditor()
    app.run(None)
