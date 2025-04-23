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
            display: block !important; /* Force display */
        }
        
        /* Remove blue outline on focus and selection */
        .page:focus {
            outline: none;
        }
        
        /* Modify selection color to be more subtle or transparent */
        ::selection {
            background-color: rgba(200, 200, 200, 0.3);
        }
        
        /* Make text caret visible but remove other visual indicators */
        .page[contenteditable=true] {
            caret-color: black;
        }
    </style>
</head>
<body>
    <div id="editor-container" contenteditable="false" spellcheck="false"></div>

    <script>
        // Editor state
        let text = '';
        const container = document.getElementById('editor-container');
        
        // For debouncing updates
        let updateTimer = null;
        
        // Function to update pages based on text content
        function updatePages() {
            // Don't update if we're in the middle of a selection operation
            if (window.getSelection().type === 'Range') {
                return;
            }
            
            // Save cursor position
            const selection = window.getSelection();
            const range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
            let selectionPageIndex = -1;
            let selectionOffset = 0;
            
            if (range && range.startContainer) {
                // Find which page and what offset we're at
                const node = range.startContainer;
                const pageElement = node.nodeType === 3 ? 
                    node.parentElement.closest('.page') : 
                    node.closest('.page');
                
                if (pageElement) {
                    selectionPageIndex = parseInt(pageElement.dataset.pageIndex);
                    selectionOffset = range.startOffset;
                    
                    // Add offsets from previous pages
                    for (let i = 0; i < selectionPageIndex; i++) {
                        const prevPage = document.querySelector(`.page[data-page-index="${i}"]`);
                        if (prevPage) {
                            selectionOffset += prevPage.textContent.length;
                        }
                    }
                }
            }
            
            // Temporarily remove input handlers
            const pages = document.querySelectorAll('.page');
            pages.forEach(page => {
                page.removeEventListener('input', pageInputHandler);
                page.removeEventListener('keydown', keyDownHandler);
            });
            
            // Remember active element
            const activeElement = document.activeElement;
            const isFocused = activeElement && activeElement.classList && activeElement.classList.contains('page');
            
            // Clear the container
            container.innerHTML = '';
            
            // Always create at least one page
            if (text.length === 0) {
                const page = document.createElement('div');
                page.className = 'page';
                page.textContent = '';
                page.dataset.pageIndex = 0;
                page.setAttribute('contenteditable', 'true');
                
                page.addEventListener('input', pageInputHandler);
                page.addEventListener('keydown', keyDownHandler);
                
                container.appendChild(page);
            } else {
                // Create pages based on page size
                // First, create a hidden page to measure content
                const testDiv = document.createElement('div');
                testDiv.className = 'page';
                testDiv.style.visibility = 'hidden';
                testDiv.style.position = 'absolute';
                document.body.appendChild(testDiv);
                
                // Instead of character-by-character, we'll try to fit multiple characters at once
                // and use binary search to find the optimal break point
                let pageIndex = 0;
                let remainingText = text;
                
                while (remainingText.length > 0) {
                    // Find how much text will fit on this page
                    let start = 0;
                    let end = remainingText.length;
                    let mid = end;
                    let lastGoodFit = 0;
                    
                    // Try with chunks of text to find the breaking point faster
                    // First try fitting the entire text
                    testDiv.textContent = remainingText;
                    
                    // If it all fits, use it all
                    if (testDiv.scrollHeight <= testDiv.clientHeight && 
                        testDiv.scrollWidth <= testDiv.clientWidth) {
                        lastGoodFit = remainingText.length;
                    } else {
                        // Binary search to find the maximum amount of text that fits
                        while (start < end) {
                            mid = Math.floor((start + end) / 2);
                            testDiv.textContent = remainingText.substring(0, mid);
                            
                            if (testDiv.scrollHeight <= testDiv.clientHeight && 
                                testDiv.scrollWidth <= testDiv.clientWidth) {
                                // This chunk fits, try a larger one
                                lastGoodFit = mid;
                                start = mid + 1;
                            } else {
                                // This chunk is too big, try a smaller one
                                end = mid;
                            }
                        }
                        
                        // If we couldn't fit anything, take at least one character
                        if (lastGoodFit === 0 && remainingText.length > 0) {
                            lastGoodFit = 1;
                        }
                    }
                    
                    // Create a page with the content that fits
                    const page = document.createElement('div');
                    page.className = 'page';
                    page.textContent = remainingText.substring(0, lastGoodFit);
                    page.dataset.pageIndex = pageIndex++;
                    page.setAttribute('contenteditable', 'true');
                    
                    // Add event listeners
                    page.addEventListener('input', pageInputHandler);
                    page.addEventListener('keydown', keyDownHandler);
                    
                    container.appendChild(page);
                    
                    // Update remaining text
                    remainingText = remainingText.substring(lastGoodFit);
                }
                
                // Clean up
                document.body.removeChild(testDiv);
            }
            
            // Restore selection if possible
            if (selectionPageIndex !== -1 && selectionOffset >= 0) {
                try {
                    // Calculate new page and offset
                    let remainingOffset = selectionOffset;
                    let newPageIndex = 0;
                    
                    // Find the correct page and offset
                    const allPages = document.querySelectorAll('.page');
                    while (newPageIndex < allPages.length) {
                        const pageLength = allPages[newPageIndex].textContent.length;
                        if (remainingOffset <= pageLength) {
                            break;
                        }
                        remainingOffset -= pageLength;
                        newPageIndex++;
                    }
                    
                    // Make sure we don't exceed available pages
                    if (newPageIndex < allPages.length) {
                        const page = allPages[newPageIndex];
                        const textNode = page.firstChild;
                        
                        // Set selection
                        const newRange = document.createRange();
                        
                        if (textNode) {
                            // Make sure we don't exceed the text length
                            const actualOffset = Math.min(remainingOffset, textNode.textContent.length);
                            newRange.setStart(textNode, actualOffset);
                        } else {
                            newRange.setStart(page, 0);
                        }
                        
                        // Apply the selection
                        setTimeout(() => {
                            selection.removeAllRanges();
                            selection.addRange(newRange);
                            page.focus();
                        }, 0);
                    }
                } catch (e) {
                    console.error('Error restoring selection:', e);
                }
            } else if (isFocused) {
                // Just focus the first page if we were focused before
                setTimeout(() => {
                    const firstPage = document.querySelector('.page');
                    if (firstPage) {
                        firstPage.focus();
                    }
                }, 0);
            }
        }
        
        // Page input handler function
        function pageInputHandler(e) {
            // Extract text from all pages
            text = '';
            document.querySelectorAll('.page').forEach((p) => {
                text += p.textContent;
            });
            
            // Debounce the update to avoid interrupting typing
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => {
                updatePages();
            }, 100);
        }
        
        // Handle key events
        function keyDownHandler(e) {
            // Handle Enter key for newlines
            if (e.key === 'Enter') {
                e.preventDefault();
                
                // Insert a newline character
                document.execCommand('insertText', false, '\\n');
                
                // Update the text content
                text = '';
                document.querySelectorAll('.page').forEach((p) => {
                    text += p.textContent;
                });
                
                // Debounce the update
                clearTimeout(updateTimer);
                updateTimer = setTimeout(() => {
                    updatePages();
                }, 100);
                
                return false;
            }
            
            // Handle navigation between pages with arrow keys
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                const currentPage = e.target;
                const currentIndex = parseInt(currentPage.dataset.pageIndex);
                const pages = document.querySelectorAll('.page');
                
                if (e.key === 'ArrowDown') {
                    const nextIndex = currentIndex + 1;
                    if (nextIndex < pages.length) {
                        e.preventDefault();
                        pages[nextIndex].focus();
                        
                        // Place cursor at the beginning of the next page
                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.setStart(pages[nextIndex].firstChild || pages[nextIndex], 0);
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                } else if (e.key === 'ArrowUp') {
                    const prevIndex = currentIndex - 1;
                    if (prevIndex >= 0) {
                        e.preventDefault();
                        pages[prevIndex].focus();
                        
                        // Place cursor at the end of the previous page
                        const selection = window.getSelection();
                        const range = document.createRange();
                        const textNode = pages[prevIndex].firstChild;
                        
                        if (textNode) {
                            range.setStart(textNode, textNode.textContent.length);
                        } else {
                            range.setStart(pages[prevIndex], 0);
                        }
                        
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                }
            }
        }
        
        // Initialize with one empty page
        function initEditor() {
            // Create first page
            const page = document.createElement('div');
            page.className = 'page';
            page.textContent = '';
            page.dataset.pageIndex = 0;
            page.setAttribute('contenteditable', 'true');
            container.appendChild(page);
            
            // Add event listeners
            page.addEventListener('input', pageInputHandler);
            page.addEventListener('keydown', keyDownHandler);
            
            // Focus it
            page.focus();
        }
        
        // Initialize the editor
        initEditor();
        
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
