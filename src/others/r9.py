#!/usr/bin/env python3
import gi
import tempfile
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit

class PaginatedEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.PaginatedEditor")
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
        
        # Add new page button
        new_page_button = Gtk.Button(label="New Page")
        new_page_button.connect("clicked", self.on_new_page_clicked)
        header.pack_end(new_page_button)
        
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
            padding: 20px;
            font-family: sans-serif;
            background-color: #E0E0E0;
        }
        
        #container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
        }
        
        .page {
            width: 300px;
            height: 100px;
            background-color: white;
            border: 3px solid #0066CC;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow: hidden;
            position: relative;
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
        }
    </style>
</head>
<body>
    <div id="container"></div>

    <script>
        // Get the container
        const container = document.getElementById('container');
        
        // Text content
        let text = '';
        
        // Create a page with given index and content
        function createPage(index, content = '') {
            const page = document.createElement('div');
            page.className = 'page';
            page.setAttribute('contenteditable', 'true');
            page.dataset.pageIndex = index;
            page.textContent = content;
            
            // Add page number indicator
            const pageNumber = document.createElement('div');
            pageNumber.className = 'page-number';
            pageNumber.textContent = 'Page ' + (index + 1);
            page.appendChild(pageNumber);
            
            // Add event listeners
            page.addEventListener('input', onPageInput);
            page.addEventListener('keydown', onPageKeyDown);
            
            container.appendChild(page);
            return page;
        }
        
        // Handle page input
        function onPageInput(e) {
            updateContent();
            checkPagination();
        }
        
        // Handle special keys
        function onPageKeyDown(e) {
            // Handle Enter key
            if (e.key === 'Enter') {
                e.preventDefault();
                document.execCommand('insertText', false, '\\n');
                return;
            }
            
            // Handle navigation between pages
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                const currentPage = e.target;
                const currentIndex = parseInt(currentPage.dataset.pageIndex);
                const pages = document.querySelectorAll('.page');
                
                if (e.key === 'ArrowDown' && currentIndex < pages.length - 1) {
                    e.preventDefault();
                    pages[currentIndex + 1].focus();
                } else if (e.key === 'ArrowUp' && currentIndex > 0) {
                    e.preventDefault();
                    pages[currentIndex - 1].focus();
                }
            }
        }
        
        // Update the content variable from all pages
        function updateContent() {
            text = '';
            document.querySelectorAll('.page').forEach(page => {
                // We need to exclude the page number text
                const pageContent = page.childNodes[0] ? page.childNodes[0].textContent : '';
                text += pageContent;
            });
        }
        
        // Check if pages need to be split or merged
        function checkPagination() {
            const pages = document.querySelectorAll('.page');
            let isOverflowing = false;
            
            // Check for overflow in each page
            pages.forEach(page => {
                if (page.scrollHeight > page.clientHeight) {
                    isOverflowing = true;
                }
            });
            
            if (isOverflowing) {
                redistributeContent();
            }
        }
        
        // Redistribute content among pages or create new ones as needed
        function redistributeContent() {
            // Create a temporary measurement div
            const testDiv = document.createElement('div');
            testDiv.className = 'page';
            testDiv.style.visibility = 'hidden';
            testDiv.style.position = 'absolute';
            document.body.appendChild(testDiv);
            
            // Get all text content
            updateContent();
            
            // Clear all pages
            container.innerHTML = '';
            
            // Break text into pages
            let remainingText = text;
            let pageIndex = 0;
            
            while (remainingText.length > 0) {
                // Create a new page
                const page = createPage(pageIndex);
                
                // Find how much text fits
                testDiv.textContent = remainingText;
                
                // If it all fits
                if (testDiv.scrollHeight <= testDiv.clientHeight) {
                    page.textContent = remainingText;
                    remainingText = '';
                } else {
                    // Need to determine how much text fits
                    let end = remainingText.length;
                    let start = 0;
                    let mid;
                    let lastGoodAmount = 0;
                    
                    // Binary search to find max amount of text that fits
                    while (start < end) {
                        mid = Math.floor((start + end) / 2);
                        testDiv.textContent = remainingText.substring(0, mid);
                        
                        if (testDiv.scrollHeight <= testDiv.clientHeight) {
                            lastGoodAmount = mid;
                            start = mid + 1;
                        } else {
                            end = mid;
                        }
                    }
                    
                    // If we couldn't fit even a single character, take at least one
                    if (lastGoodAmount === 0 && remainingText.length > 0) {
                        lastGoodAmount = 1;
                    }
                    
                    // Set page content and update remaining text
                    page.textContent = remainingText.substring(0, lastGoodAmount);
                    remainingText = remainingText.substring(lastGoodAmount);
                }
                
                // Re-add page number since textContent replaced it
                const pageNumber = document.createElement('div');
                pageNumber.className = 'page-number';
                pageNumber.textContent = 'Page ' + (pageIndex + 1);
                page.appendChild(pageNumber);
                
                pageIndex++;
            }
            
            // Clean up
            document.body.removeChild(testDiv);
            
            // Focus on the first page if none are focused
            if (document.activeElement.tagName !== 'DIV' || !document.activeElement.classList.contains('page')) {
                const firstPage = document.querySelector('.page');
                if (firstPage) firstPage.focus();
            }
        }
        
        // Function to add a new empty page at the end
        function addNewPage() {
            const pages = document.querySelectorAll('.page');
            const newIndex = pages.length;
            const newPage = createPage(newIndex);
            newPage.focus();
        }
        
        // Function to save content
        function getContent() {
            return text;
        }
        
        // Create initial page
        createPage(0, 'Start typing here. Press Enter for new lines, up/down arrows to navigate between pages.');
        
        // Focus on it
        document.querySelector('.page').focus();
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
    
    def on_new_page_clicked(self, button):
        self.webview.evaluate_javascript(
            "addNewPage();",
            -1, None, None, None, None, None, None
        )
    
    def on_get_content(self, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                content = js_result.get_js_value().to_string()
                print(f"Content: {content}")
                # Here you would save the content to a file
        except Exception as e:
            print(f"Error getting content: {e}")
    
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
    app = PaginatedEditor()
    app.run(None)
