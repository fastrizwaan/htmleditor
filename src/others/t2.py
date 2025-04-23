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

        # Configure WebView settings
        settings = self.webview.get_settings()
        settings.set_enable_javascript(True)
        settings.set_javascript_can_access_clipboard(True)
        
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
            <title>Tiny Page Editor</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    font-size: 8px;
                    line-height: 1.2;
                    background-color: #f0f0f0;
                    overflow-x: hidden;
                }
                
                #editor-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px;
                    min-height: 100vh;
                }
                
                .page {
                    width: 100px;
                    height: 30px;
                    padding: 5px;
                    margin: 10px auto;
                    background-color: white;
                    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
                    box-sizing: border-box;
                    position: relative;
                    border: 1px solid #ccc;
                    overflow: hidden;
                }
                
                .page:focus {
                    outline: 2px solid #0078d7;
                }
                
                /* Hide page number while editing but show on print */
                .page::after {
                    content: attr(data-page-number);
                    position: absolute;
                    bottom: 2px;
                    right: 2px;
                    font-size: 6px;
                    color: #999;
                    pointer-events: none;
                }
                
                @media print {
                    body {
                        background-color: white;
                    }
                    
                    .page {
                        margin: 0;
                        box-shadow: none;
                        page-break-after: always;
                        border: none;
                    }
                    
                    .page::after {
                        display: block;
                    }
                }
                
                #hidden-measurer {
                    position: absolute;
                    top: -9999px;
                    left: -9999px;
                    visibility: hidden;
                    width: 100px;
                    padding: 5px;
                    box-sizing: border-box;
                    font-family: Arial, sans-serif;
                    font-size: 8px;
                    line-height: 1.2;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
            </style>
        </head>
        <body>
            <div id="editor-container"></div>
            <div id="hidden-measurer"></div>
            
            <script>
                class TinyDocumentEditor {
                    constructor() {
                        this.container = document.getElementById('editor-container');
                        this.measurer = document.getElementById('hidden-measurer');
                        this.pages = [];
                        this.currentPage = null;
                        this.pageWidth = 100;
                        this.pageHeight = 30;
                        this.contentPadding = 5;
                        this.pageCount = 0;
                        this.isUpdating = false;
                        
                        // Create initial page
                        this.addPage();
                        
                        // Set up event listeners
                        this.setupEvents();
                    }
                    
                    addPage() {
                        this.pageCount++;
                        
                        const page = document.createElement('div');
                        page.className = 'page';
                        page.contentEditable = true;
                        page.dataset.pageNumber = this.pageCount;
                        page.dataset.pageIndex = this.pages.length;
                        
                        if (this.pages.length === 0) {
                            page.textContent = "Type here...";
                        }
                        
                        this.container.appendChild(page);
                        this.pages.push(page);
                        this.currentPage = page;
                        
                        return page;
                    }
                    
                    measureText(text) {
                        this.measurer.textContent = text;
                        return {
                            width: this.measurer.scrollWidth,
                            height: this.measurer.scrollHeight
                        };
                    }
                    
                    getPageContentHeight(page) {
                        return this.pageHeight - (this.contentPadding * 2);
                    }
                    
                    getPageContentWidth(page) {
                        return this.pageWidth - (this.contentPadding * 2);
                    }
                    
                    getTextUpToOverflow(text) {
                        // If text is empty, return empty
                        if (!text) return "";
                        
                        // Start with a binary search approach
                        let low = 0;
                        let high = text.length;
                        let result = "";
                        
                        while (low < high) {
                            const mid = Math.floor((low + high) / 2);
                            const testText = text.substring(0, mid);
                            const metrics = this.measureText(testText);
                            
                            if (metrics.height <= this.getPageContentHeight()) {
                                low = mid + 1;
                                result = testText;
                            } else {
                                high = mid;
                            }
                        }
                        
                        // Fine-tune: add characters one by one until overflow
                        for (let i = result.length; i <= text.length; i++) {
                            const testText = text.substring(0, i);
                            const metrics = this.measureText(testText);
                            
                            if (metrics.height > this.getPageContentHeight()) {
                                return text.substring(0, i - 1);
                            }
                        }
                        
                        return text;
                    }
                    
                    redistributeContent() {
                        if (this.isUpdating) return;
                        this.isUpdating = true;
                        
                        try {
                            // Collect all text content
                            let allContent = "";
                            this.pages.forEach(page => {
                                allContent += page.textContent;
                            });
                            
                            // Clear all pages except the first one
                            while (this.pages.length > 1) {
                                const lastPage = this.pages.pop();
                                this.container.removeChild(lastPage);
                            }
                            
                            // Start with first page
                            let currentPage = this.pages[0];
                            let remainingText = allContent;
                            let pageIndex = 0;
                            
                            while (remainingText.length > 0) {
                                // Determine how much text fits on current page
                                const fittingText = this.getTextUpToOverflow(remainingText);
                                
                                // Set content for current page
                                currentPage.textContent = fittingText;
                                
                                // Remove processed text from remaining text
                                remainingText = remainingText.substring(fittingText.length);
                                
                                // If more text remains, create a new page
                                if (remainingText.length > 0) {
                                    currentPage = this.addPage();
                                    pageIndex++;
                                }
                            }
                            
                            // Ensure there's always at least one page
                            if (this.pages.length === 0) {
                                this.addPage();
                            }
                            
                            // Update current page if needed
                            if (!this.currentPage || !this.container.contains(this.currentPage)) {
                                this.currentPage = this.pages[this.pages.length - 1];
                            }
                            
                            // Set focus to current page
                            this.setFocusToEnd(this.currentPage);
                        } finally {
                            this.isUpdating = false;
                        }
                    }
                    
                    setFocusToEnd(element) {
                        if (!element) return;
                        
                        element.focus();
                        
                        // Create a range and set the selection to the end
                        const range = document.createRange();
                        const selection = window.getSelection();
                        
                        if (element.childNodes.length > 0) {
                            const lastNode = element.childNodes[element.childNodes.length - 1];
                            if (lastNode.nodeType === Node.TEXT_NODE) {
                                range.setStart(lastNode, lastNode.length);
                                range.collapse(true);
                            } else {
                                range.selectNodeContents(element);
                                range.collapse(false);
                            }
                        } else {
                            range.selectNodeContents(element);
                            range.collapse(false);
                        }
                        
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                    
                    setupEvents() {
                        // Use input event to detect content changes
                        this.container.addEventListener('input', () => {
                            setTimeout(() => this.redistributeContent(), 0);
                        });
                        
                        // Handle keydown for special keys
                        this.container.addEventListener('keydown', (e) => {
                            // Special handling for page navigation
                            if (e.key === 'ArrowDown' && e.ctrlKey) {
                                e.preventDefault();
                                const currentIndex = parseInt(document.activeElement.dataset.pageIndex, 10);
                                if (currentIndex < this.pages.length - 1) {
                                    this.pages[currentIndex + 1].focus();
                                }
                            } else if (e.key === 'ArrowUp' && e.ctrlKey) {
                                e.preventDefault();
                                const currentIndex = parseInt(document.activeElement.dataset.pageIndex, 10);
                                if (currentIndex > 0) {
                                    this.pages[currentIndex - 1].focus();
                                }
                            }
                        });
                        
                        // Handle focus to track current page
                        this.container.addEventListener('focusin', (e) => {
                            if (e.target.classList.contains('page')) {
                                this.currentPage = e.target;
                            }
                        });
                        
                        // Handle paste events
                        this.container.addEventListener('paste', (e) => {
                            setTimeout(() => this.redistributeContent(), 0);
                        });
                        
                        // Initial distribution (if needed)
                        setTimeout(() => this.redistributeContent(), 100);
                    }
                }
                
                // Initialize the editor when the document is ready
                document.addEventListener('DOMContentLoaded', () => {
                    window.editor = new TinyDocumentEditor();
                });
                
                // Initialize immediately if document is already loaded
                if (document.readyState === 'complete' || document.readyState === 'interactive') {
                    window.editor = new TinyDocumentEditor();
                }
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
