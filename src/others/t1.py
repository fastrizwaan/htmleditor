#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, Adw, WebKit, GLib, Gdk

class PageEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.pageeditor")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        # Create main window
        self.window = Adw.ApplicationWindow(application=app)
        self.window.set_default_size(400, 500)
        self.window.set_title("Tiny Page Editor")

        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # WebKit WebView for editing
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)

        # Create and apply the stylesheet
        style_manager = self.webview.get_settings()
        style_manager.set_enable_javascript(True)
        
        # Create a scrolled window to contain the webview
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(self.webview)
        main_box.append(scrolled_window)

        # Load the HTML content with CSS for pagination
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Page Editor</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    line-height: 1.2;
                    background-color: #f0f0f0;
                }
                
                #editor {
                    width: 100px;
                    height: 30px;
                    padding: 5px;
                    margin: 10px auto;
                    background-color: white;
                    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
                    box-sizing: border-box;
                    overflow: hidden;
                    position: relative;
                }
                
                .page {
                    width: 100px;
                    height: 30px;
                    padding: 5px;
                    margin: 10px auto;
                    background-color: white;
                    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
                    box-sizing: border-box;
                    overflow: hidden;
                    page-break-after: always;
                    position: relative;
                }
                
                @media print {
                    body {
                        background-color: white;
                    }
                    
                    .page {
                        margin: 0;
                        box-shadow: none;
                        page-break-after: always;
                    }
                }
            </style>
        </head>
        <body>
            <div id="container">
                <div id="page-1" class="page" contenteditable="true">
                    Type here...
                </div>
            </div>
            
            <script>
                // Track current page
                let pageCount = 1;
                
                // Function to check content overflow and create a new page if needed
                function checkOverflow() {
                    const currentPage = document.querySelector(`#page-${pageCount}`);
                    
                    // Check if content overflows the current page
                    if (currentPage.scrollHeight > currentPage.clientHeight) {
                        // Create a new page
                        pageCount++;
                        const newPage = document.createElement('div');
                        newPage.id = `page-${pageCount}`;
                        newPage.className = 'page';
                        newPage.contentEditable = true;
                        
                        // Move overflowing content to the new page
                        const range = document.createRange();
                        const selection = window.getSelection();
                        
                        // Try to find a good breaking point (paragraph or line)
                        let breakFound = false;
                        const nodes = Array.from(currentPage.childNodes);
                        
                        // Start from the end and find a suitable break point
                        for (let i = nodes.length - 1; i >= 0; i--) {
                            const node = nodes[i];
                            const nodeRect = node.getBoundingClientRect();
                            const pageRect = currentPage.getBoundingClientRect();
                            
                            // If this node is partially outside the page, move it
                            if (nodeRect.bottom > pageRect.bottom) {
                                // Found a node that overflows
                                newPage.appendChild(node);
                                breakFound = true;
                            }
                        }
                        
                        // If we couldn't find a good break, just cut at a character level
                        if (!breakFound && currentPage.textContent.length > 0) {
                            // Start with half the text as a guess
                            let startCut = Math.floor(currentPage.textContent.length / 2);
                            let endCut = currentPage.textContent.length;
                            let midCut;
                            
                            // Binary search to find the overflow point
                            while (startCut < endCut) {
                                midCut = Math.floor((startCut + endCut) / 2);
                                
                                // Create a range from the start to midCut
                                range.setStart(currentPage.firstChild, 0);
                                range.setEnd(currentPage.firstChild, midCut);
                                
                                const tempDiv = document.createElement('div');
                                tempDiv.appendChild(range.cloneContents());
                                document.body.appendChild(tempDiv);
                                
                                const tempHeight = tempDiv.scrollHeight;
                                document.body.removeChild(tempDiv);
                                
                                if (tempHeight > currentPage.clientHeight) {
                                    endCut = midCut - 1;
                                } else {
                                    startCut = midCut + 1;
                                }
                            }
                            
                            // Split the text at the found position
                            const textNode = currentPage.firstChild;
                            const secondPart = textNode.splitText(startCut);
                            newPage.appendChild(document.createTextNode(secondPart.textContent));
                            secondPart.remove();
                        }
                        
                        // Append the new page to the container
                        document.getElementById('container').appendChild(newPage);
                        
                        // Focus on the new page
                        newPage.focus();
                    }
                }
                
                // Monitor content changes to check for overflow
                let observer = new MutationObserver(function(mutations) {
                    checkOverflow();
                });
                
                // Start observing the container for changes
                observer.observe(document.getElementById('container'), { 
                    childList: true, 
                    subtree: true, 
                    characterData: true 
                });
                
                // Set up keyboard event listeners for better handling
                document.addEventListener('keydown', function(e) {
                    // Add special handling for Enter, Backspace, Delete keys if needed
                    setTimeout(checkOverflow, 0);
                });
                
                // Initial check
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(checkOverflow, 0);
                });
                
                // Listen for paste events
                document.addEventListener('paste', function() {
                    setTimeout(checkOverflow, 0);
                });
            </script>
        </body>
        </html>
        """
        
        self.webview.load_html(html_content, "file:///")
        
        # Show the window
        self.window.present()

if __name__ == "__main__":
    app = PageEditor()
    app.run(None)
