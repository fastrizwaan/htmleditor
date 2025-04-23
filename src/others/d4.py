#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, Adw, WebKit, GLib, Gdk

class PageEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.pageeditor")
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        # Create the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("Page Editor")
        self.win.set_default_size(850, 1100)  # Slightly larger than US Letter to show margins

        # Create a WebKit web view which will host our editor
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)

        # US Letter dimensions in points (1/72 inch) but with reduced height for testing
        page_width = 612
        page_height = 200  # Reduced height to make testing easier
        
        # HTML content with CSS for page layout
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #f0f0f0;
                    font-family: sans-serif;
                }}
                
                @page {{
                    size: {page_width}pt {page_height}pt;
                    margin: 0;
                }}
                
                .editor-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px;
                    min-height: 100vh;
                }}
                
                .page {{
                    width: {page_width}pt;
                    height: {page_height}pt;
                    background-color: white;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                    margin-bottom: 20px;
                    position: relative;
                    overflow: hidden;
                }}
                
                .page-content {{
                    position: absolute;
                    top: 72pt;      /* 1 inch margin top */
                    left: 72pt;     /* 1 inch margin left */
                    right: 72pt;    /* 1 inch margin right */
                    bottom: 72pt;   /* 1 inch margin bottom */
                    overflow: hidden;
                }}
                
                #content-editable {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    outline: none;
                    line-height: 1.5;
                    overflow: visible;
                }}
                
                /* Style for the overflow indicator */
                .overflow-container {{
                    display: none;
                }}
            </style>
        </head>
        <body>
            <div class="editor-container">
                <div id="page-container"></div>
            </div>
            
            <script>
                // Main document that will contain all text
                const mainDocument = document.createElement('div');
                mainDocument.id = 'main-document';
                mainDocument.contentEditable = true;
                mainDocument.spellcheck = true;
                mainDocument.style.position = 'absolute';
                mainDocument.style.top = '0';
                mainDocument.style.left = '0';
                mainDocument.style.width = '100%';
                mainDocument.style.outline = 'none';
                document.body.appendChild(mainDocument);
                
                // Track pages and content
                let pages = [];
                let pageContents = [];
                
                // Function to create a new page
                function createPage() {{
                    const pageContainer = document.getElementById('page-container');
                    const pageNumber = pageContainer.children.length + 1;
                    
                    const page = document.createElement('div');
                    page.className = 'page';
                    page.id = 'page-' + pageNumber;
                    
                    const pageContent = document.createElement('div');
                    pageContent.className = 'page-content';
                    pageContent.id = 'page-content-' + pageNumber;
                    
                    page.appendChild(pageContent);
                    pageContainer.appendChild(page);
                    
                    pages.push(page);
                    pageContents.push(pageContent);
                    
                    return {{page, pageContent}};
                }}
                
                // Create the first page
                const firstPage = createPage();
                
                // Function to update page content
                function updatePages() {{
                    const text = mainDocument.innerHTML;
                    
                    // Clear all page contents
                    pageContents.forEach(content => content.innerHTML = '');
                    
                    // Temporary element to measure text
                    const tempElement = document.createElement('div');
                    tempElement.style.position = 'absolute';
                    tempElement.style.visibility = 'hidden';
                    tempElement.style.width = (pageContents[0].clientWidth) + 'px';
                    tempElement.style.lineHeight = '1.5';
                    tempElement.style.fontSize = '16px';
                    tempElement.style.fontFamily = 'sans-serif';
                    document.body.appendChild(tempElement);
                    
                    // Get the exact line height in pixels for accurate calculations
                    const computedLineHeight = 24; // 1.5 * 16px font size
                    
                    // Get maximum content height per page (4 lines)
                    const maxLinesPerPage = 4;
                    const maxContentHeight = maxLinesPerPage * computedLineHeight;
                    
                    // Process the text character by character to ensure precise line breaks
                    let allText = text.replace(/<br>|<div>|<\/div>|<p>|<\/p>/g, '\n').replace(/&nbsp;/g, ' ');
                    allText = allText.replace(/<[^>]*>/g, ''); // Remove any remaining HTML tags
                    
                    // Split text into lines (we'll rebuild it properly)
                    const lines = [];
                    let currentLine = '';
                    
                    // Function to measure text width
                    function measureTextWidth(text) {
                        tempElement.textContent = text;
                        return tempElement.clientWidth;
                    }
                    
                    // Build lines based on text content and available width
                    const words = allText.split(/\s+/);
                    for (let i = 0; i < words.length; i++) {
                        const word = words[i];
                        const testLine = currentLine + (currentLine ? ' ' : '') + word;
                        
                        // Check if we're at a line break
                        if (word.includes('\n')) {
                            const parts = word.split('\n');
                            // Add the first part to current line and push it
                            currentLine += (currentLine ? ' ' : '') + parts[0];
                            lines.push(currentLine);
                            
                            // Start new lines with remaining parts
                            for (let j = 1; j < parts.length - 1; j++) {
                                lines.push(parts[j]);
                            }
                            
                            // Start new current line with the last part
                            currentLine = parts[parts.length - 1] || '';
                        }
                        // Otherwise check if the word fits
                        else if (measureTextWidth(testLine) <= pageContents[0].clientWidth) {
                            currentLine = testLine;
                        } else {
                            // Word doesn't fit, push current line and start a new one
                            lines.push(currentLine);
                            currentLine = word;
                        }
                    }
                    
                    // Push the last line if there's anything left
                    if (currentLine) {
                        lines.push(currentLine);
                    }
                    
                    // Now distribute lines across pages
                    let currentPage = 0;
                    let currentPageLineCount = 0;
                    
                    for (let i = 0; i < lines.length; i++) {
                        // Check if we need a new page
                        if (currentPageLineCount >= maxLinesPerPage) {
                            // Move to next page
                            currentPage++;
                            currentPageLineCount = 0;
                            
                            // Create new page if needed
                            if (currentPage >= pages.length) {
                                createPage();
                            }
                        }
                        
                        // Add line to current page
                        const line = lines[i];
                        pageContents[currentPage].innerHTML += 
                            (pageContents[currentPage].innerHTML ? '<br>' : '') + 
                            line;
                        
                        currentPageLineCount++;
                    }
                    
                    // Clean up
                    document.body.removeChild(tempElement);
                    
                    // Make sure all created pages are visible
                    for (let i = 0; i <= currentPage; i++) {
                        pages[i].style.display = 'block';
                    }
                    
                    // Hide any excess pages
                    for (let i = currentPage + 1; i < pages.length; i++) {
                        pages[i].style.display = 'none';
                    }
                }}
                
                // Position the main document over the first page content initially
                function positionEditor() {{
                    const firstPageContent = document.getElementById('page-content-1');
                    const rect = firstPageContent.getBoundingClientRect();
                    
                    mainDocument.style.top = rect.top + 'px';
                    mainDocument.style.left = rect.left + 'px';
                    mainDocument.style.width = rect.width + 'px';
                    mainDocument.style.height = rect.height + 'px';
                    mainDocument.focus();
                }}
                
                // Listen for input events
                mainDocument.addEventListener('input', function() {{
                    updatePages();
                }});
                
                // Initial setup
                window.addEventListener('load', function() {{
                    positionEditor();
                    mainDocument.focus();
                }});
            </script>
        </body>
        </html>
        """

        # Load the HTML content
        self.webview.load_html(html_content, None)

        # Create a scrolled window to contain the webview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.webview)

        # Set the main window content
        self.win.set_content(scrolled)
        
        # Show the window
        self.win.present()

if __name__ == "__main__":
    app = PageEditor()
    app.run(None)
