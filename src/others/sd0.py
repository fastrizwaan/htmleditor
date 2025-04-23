#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, Adw, GLib, WebKit, Gdk

class PageEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.pageeditor")
        self.connect('activate', self.on_activate)
        
    def on_activate(self, app):
        # Create main window
        self.window = Adw.ApplicationWindow(application=app)
        self.window.set_default_size(500, 400)
        self.window.set_title("Page Editor")
        
        # Create a box to hold our content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create WebKit WebView for the editor
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Create page navigation buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        nav_box.set_spacing(10)
        nav_box.set_margin_top(10)
        nav_box.set_margin_bottom(10)
        nav_box.set_margin_start(10)
        nav_box.set_margin_end(10)
        
        self.prev_button = Gtk.Button(label="Previous Page")
        self.next_button = Gtk.Button(label="Next Page")
        self.page_label = Gtk.Label(label="Page: 1")
        
        self.prev_button.connect("clicked", self.go_to_prev_page)
        self.next_button.connect("clicked", self.go_to_next_page)
        
        nav_box.append(self.prev_button)
        nav_box.append(self.page_label)
        nav_box.append(self.next_button)
        nav_box.set_halign(Gtk.Align.CENTER)
        
        # Add components to the main box
        main_box.append(self.webview)
        main_box.append(nav_box)
        
        # Set the content
        self.window.set_content(main_box)
        
        # Load the HTML with the editor
        self.load_editor()
        
        # Show the window
        self.window.present()
    
    def load_editor(self):
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Paginated Editor</title>
    <style>
        body {
            margin: 0;
            padding: 10px;
            font-family: sans-serif;
            overflow: hidden;
        }
        #editor {
            width: 100%;
            height: 100%;
            outline: none;
            white-space: pre-wrap;
            overflow: hidden;
        }
        .page {
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 10px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            height: calc(4em + 10px); /* Height for 4 lines + some padding */
            overflow: hidden;
        }
        #pages-container {
            position: relative;
            height: 100%;
        }
        #current-page {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: calc(4em + 20px); /* match page height + padding */
        }
        /* Hide other pages */
        .page:not(:first-child) {
            display: none;
        }
    </style>
</head>
<body>
    <div id="pages-container">
        <div id="current-page" class="page" contenteditable="true"></div>
    </div>

    <script>
        // Store references
        const pagesContainer = document.getElementById('pages-container');
        const currentPageElem = document.getElementById('current-page');
        
        // Initialize content storage
        let pages = [''];
        let currentPageIndex = 0;
        
        // Function to update displayed page
        function showCurrentPage() {
            currentPageElem.innerHTML = pages[currentPageIndex];
            window.webkit.messageHandlers.pageChanged.postMessage(currentPageIndex + 1);
            
            // Set cursor at the end of the content
            setCaretAtEnd(currentPageElem);
        }
        
        // Helper to set caret at the end of an element
        function setCaretAtEnd(element) {
            const range = document.createRange();
            const selection = window.getSelection();
            
            if (element.childNodes.length > 0) {
                range.setStartAfter(element.childNodes[element.childNodes.length - 1]);
            } else {
                range.setStart(element, 0);
            }
            
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
            element.focus();
        }
        
        // Detect when content needs to flow to next page
        currentPageElem.addEventListener('input', function() {
            // Save current content
            pages[currentPageIndex] = currentPageElem.innerHTML;
            
            // Check if we need to split to a new page
            const lineHeight = parseInt(getComputedStyle(currentPageElem).lineHeight);
            const maxLines = 4;
            
            // Use scrollHeight to determine if content overflows
            if (currentPageElem.scrollHeight > currentPageElem.clientHeight) {
                // Content overflows, need to move text to next page
                const textNodes = getTextNodesIn(currentPageElem);
                if (textNodes.length === 0) return;
                
                // Split on a reasonable boundary
                splitContentToNextPage();
            }
        });
        
        // Get all text nodes in an element
        function getTextNodesIn(node) {
            var textNodes = [];
            if (node.nodeType == 3) {
                textNodes.push(node);
            } else {
                var children = node.childNodes;
                for (var i = 0; i < children.length; i++) {
                    textNodes.push.apply(textNodes, getTextNodesIn(children[i]));
                }
            }
            return textNodes;
        }
        
        // Split content when it overflows current page
        function splitContentToNextPage() {
            // First try to preserve whole paragraphs
            const paragraphs = Array.from(currentPageElem.childNodes);
            if (paragraphs.length > 1) {
                // For simplicity, move the last paragraph to the next page
                const lastParagraph = paragraphs[paragraphs.length - 1];
                const lastParagraphHTML = lastParagraph.outerHTML || lastParagraph.textContent;
                
                // Remove from current page
                lastParagraph.remove();
                
                // Update current page content
                pages[currentPageIndex] = currentPageElem.innerHTML;
                
                // Add to next page
                if (currentPageIndex + 1 >= pages.length) {
                    pages.push(lastParagraphHTML);
                } else {
                    pages[currentPageIndex + 1] = lastParagraphHTML + pages[currentPageIndex + 1];
                }
                
                // Go to next page automatically
                currentPageIndex++;
                showCurrentPage();
                return;
            }
            
            // If only one paragraph or text node, try to split at a word boundary
            const selection = window.getSelection();
            const range = document.createRange();
            
            // Start at the approximate position that would be the 4th line
            // This is a simplification - in a real app you'd need more sophisticated text measuring
            const text = currentPageElem.innerText;
            const approxCharsPerLine = 40; // Estimate
            const splitPoint = approxCharsPerLine * 4;
            
            if (text.length <= splitPoint) return;
            
            // Find nearest word boundary after the split point
            let wordBoundary = text.indexOf(' ', splitPoint);
            if (wordBoundary === -1) wordBoundary = text.length;
            
            // Split content
            const remainingText = text.substring(wordBoundary).trim();
            
            // Update current page (truncate)
            currentPageElem.innerText = text.substring(0, wordBoundary);
            pages[currentPageIndex] = currentPageElem.innerHTML;
            
            // Add to next page
            if (currentPageIndex + 1 >= pages.length) {
                pages.push(remainingText);
            } else {
                pages[currentPageIndex + 1] = remainingText + pages[currentPageIndex + 1];
            }
            
            // Go to next page automatically
            currentPageIndex++;
            showCurrentPage();
        }
        
        // Navigate to previous page
        function goToPrevPage() {
            if (currentPageIndex > 0) {
                // Save current content
                pages[currentPageIndex] = currentPageElem.innerHTML;
                
                // Move to previous page
                currentPageIndex--;
                showCurrentPage();
            }
        }
        
        // Navigate to next page
        function goToNextPage() {
            // Save current content
            pages[currentPageIndex] = currentPageElem.innerHTML;
            
            // Move to next page or create one
            if (currentPageIndex + 1 < pages.length) {
                currentPageIndex++;
            } else {
                pages.push('');
                currentPageIndex++;
            }
            showCurrentPage();
        }
        
        // Initialize
        showCurrentPage();
        
        // Expose functions for Python to call
        window.goToPrevPage = goToPrevPage;
        window.goToNextPage = goToNextPage;
    </script>
</body>
</html>
        """
        self.webview.load_html(html_content, None)
        
        # Set up message handlers for communication between WebKit and GTK
        self.webview.connect('load-changed', self.on_load_changed)
    
    def on_load_changed(self, web_view, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Register message handler for page changes
            user_content_manager = self.webview.get_user_content_manager()
            user_content_manager.register_script_message_handler("pageChanged")
            user_content_manager.connect("script-message-received::pageChanged", 
                                         self.on_page_changed)
    
    def on_page_changed(self, manager, message):
        # Update the page label
        page_num = message.get_js_value().to_int32()
        self.page_label.set_text(f"Page: {page_num}")
    
    def go_to_prev_page(self, button):
        self.webview.evaluate_javascript("window.goToPrevPage()", -1, None, None, None, None, None)
    
    def go_to_next_page(self, button):
        self.webview.evaluate_javascript("window.goToNextPage()", -1, None, None, None, None, None)

if __name__ == "__main__":
    app = PageEditor()
    app.run(None)
