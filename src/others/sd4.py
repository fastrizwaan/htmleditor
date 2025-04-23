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
        self.window.set_default_size(400, 400)
        self.window.set_title("Page Editor")
        
        # Create a box to hold our content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create WebKit WebView for the editor
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Just add a simple page indicator at the bottom
        self.page_label = Gtk.Label(label="Page: 1")
        self.page_label.set_margin_top(10)
        self.page_label.set_margin_bottom(10)
        self.page_label.set_halign(Gtk.Align.CENTER)
        
        # Add components to the main box
        main_box.append(self.webview)
        main_box.append(self.page_label)
        
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
            padding: 0;
            font-family: monospace;
            overflow: auto;
        }
        #editor-container {
            padding: 20px;
        }
        .page {
            border: 1px solid #ccc;
            margin-bottom: 20px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            position: relative;
            width: 340px;
            box-sizing: border-box;
            margin-left: auto;
            margin-right: auto;
        }
        .page-content {
            padding: 10px;
            min-height: 2em;
            max-height: 2em;
            line-height: 1em;
            overflow: hidden;
            outline: none;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 16px;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }
        .page-number {
            position: absolute;
            bottom: -16px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            padding: 2px 8px;
            border-radius: 10px;
            border: 1px solid #ddd;
            font-size: 12px;
            color: #888;
        }
    </style>
</head>
<body>
    <div id="editor-container"></div>

    <script>
        // DOM References
        const editorContainer = document.getElementById('editor-container');
        
        // State variables
        let pages = [];
        let currentPage = 0;
        
        // Create initial page on load
        window.addEventListener('DOMContentLoaded', function() {
            createPage();
            updatePageCounter(1);
        });
        
        // Create a new page
        function createPage(content = '') {
            // Create page elements
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'page-content';
            contentDiv.contentEditable = true;
            contentDiv.innerHTML = content || '';
            contentDiv.dataset.pageIndex = pages.length;
            
            const pageNumberDiv = document.createElement('div');
            pageNumberDiv.className = 'page-number';
            pageNumberDiv.textContent = `Page ${pages.length + 1}`;
            
            // Assemble page
            pageDiv.appendChild(contentDiv);
            pageDiv.appendChild(pageNumberDiv);
            
            // Add to container
            editorContainer.appendChild(pageDiv);
            
            // Add listeners
            contentDiv.addEventListener('input', handleInput);
            contentDiv.addEventListener('keydown', handleKeydown);
            contentDiv.addEventListener('focus', function() {
                currentPage = parseInt(this.dataset.pageIndex);
                updatePageCounter(currentPage + 1);
            });
            
            // Add to pages array
            pages.push(contentDiv);
            
            // Return the page content element
            return contentDiv;
        }
        
        // Handle input in a page
        function handleInput(event) {
            const pageContent = event.target;
            const pageIndex = parseInt(pageContent.dataset.pageIndex);
            
            // Check if content exceeds 2 lines
            if (pageContent.scrollHeight > pageContent.clientHeight) {
                // Content overflow - move excess to next page
                const overflowText = getOverflowText(pageContent);
                
                // First remove overflow from current page
                removeOverflow(pageContent);
                
                // Now handle the overflow text
                if (pageIndex + 1 < pages.length) {
                    // Next page exists - prepend overflow to it
                    const nextPage = pages[pageIndex + 1];
                    nextPage.innerHTML = overflowText + nextPage.innerHTML;
                    
                    // If the next page now overflows, handle it recursively
                    if (nextPage.scrollHeight > nextPage.clientHeight) {
                        handleInput({ target: nextPage });
                    }
                } else {
                    // Create a new page with overflow text
                    createPage(overflowText);
                }
                
                // Move cursor to next page if it was in overflow area
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    if (isInOverflow(range.startContainer, range.startOffset, pageContent)) {
                        if (pageIndex + 1 < pages.length) {
                            const nextPage = pages[pageIndex + 1];
                            nextPage.focus();
                            const newRange = document.createRange();
                            newRange.setStart(nextPage, 0);
                            selection.removeAllRanges();
                            selection.addRange(newRange);
                        }
                    }
                }
            }
            
            // Update current page indicator
            currentPage = pageIndex;
            updatePageCounter(currentPage + 1);
        }
        
        // Handle keyboard events
        function handleKeydown(event) {
            const pageContent = event.target;
            const pageIndex = parseInt(pageContent.dataset.pageIndex);
            
            // Handle backspace at beginning of a page
            if (event.key === 'Backspace' && isAtBeginning(pageContent) && pageIndex > 0) {
                event.preventDefault();
                
                // Move cursor to end of previous page
                const prevPage = pages[pageIndex - 1];
                const prevContent = prevPage.innerHTML;
                const currentContent = pageContent.innerHTML;
                
                // Check if current page is empty
                if (currentContent.trim() === '') {
                    // Just remove the empty page
                    pageContent.parentNode.remove();
                    pages.splice(pageIndex, 1);
                    
                    // Update page indices and numbers
                    updatePageIndices();
                    
                    // Focus previous page
                    prevPage.focus();
                    placeCursorAtEnd(prevPage);
                } else {
                    // Try to merge content with previous page
                    prevPage.innerHTML = prevContent + currentContent;
                    
                    // Check if merged content fits
                    if (prevPage.scrollHeight <= prevPage.clientHeight) {
                        // Content fits - remove current page
                        pageContent.parentNode.remove();
                        pages.splice(pageIndex, 1);
                        
                        // Update page indices and numbers
                        updatePageIndices();
                        
                        // Focus previous page
                        prevPage.focus();
                        placeCursorAtEnd(prevPage);
                    } else {
                        // Content doesn't fit - handle overflow
                        const overflowText = getOverflowText(prevPage);
                        removeOverflow(prevPage);
                        
                        // Update current page with overflow
                        pageContent.innerHTML = overflowText + pageContent.innerHTML;
                        
                        // Focus previous page
                        prevPage.focus();
                        placeCursorAtEnd(prevPage);
                    }
                }
                
                // Update current page indicator
                currentPage = pageIndex - 1;
                updatePageCounter(currentPage + 1);
                return;
            }
            
            // Navigate between pages with arrow keys
            if (event.key === 'ArrowUp' && isAtBeginning(pageContent) && pageIndex > 0) {
                event.preventDefault();
                pages[pageIndex - 1].focus();
                placeCursorAtEnd(pages[pageIndex - 1]);
                currentPage = pageIndex - 1;
                updatePageCounter(currentPage + 1);
            } else if (event.key === 'ArrowDown' && isAtEnd(pageContent) && pageIndex < pages.length - 1) {
                event.preventDefault();
                pages[pageIndex + 1].focus();
                placeCursorAtBeginning(pages[pageIndex + 1]);
                currentPage = pageIndex + 1;
                updatePageCounter(currentPage + 1);
            }
        }
        
        // Get overflow text (content that doesn't fit in 2 lines)
        function getOverflowText(element) {
            // Create a clone for testing
            const clone = element.cloneNode(true);
            const temp = document.createElement('div');
            temp.style.position = 'absolute';
            temp.style.left = '-9999px';
            temp.style.width = element.clientWidth + 'px';
            temp.style.maxHeight = element.clientHeight + 'px';
            temp.style.overflow = 'hidden';
            temp.appendChild(clone);
            document.body.appendChild(temp);
            
            // Get the content that fits within 2 lines
            const visibleContent = getVisibleContent(clone);
            
            // Clean up
            document.body.removeChild(temp);
            
            // Return the overflow content
            const fullContent = element.innerText;
            return fullContent.substring(visibleContent.length);
        }
        
        // Get the content that's visible within an element
        function getVisibleContent(element) {
            // Split into lines
            const fullText = element.innerText;
            const lines = fullText.split('\\n');
            
            // Only keep first 2 lines
            const visibleLines = lines.slice(0, 2);
            return visibleLines.join('\\n');
        }
        
        // Remove overflow content from an element
        function removeOverflow(element) {
            const visibleContent = getVisibleContent(element);
            element.innerText = visibleContent;
        }
        
        // Check if selection is in overflow area
        function isInOverflow(node, offset, element) {
            // Get content up to cursor position
            const range = document.createRange();
            range.setStart(element, 0);
            range.setEnd(node, offset);
            const textToCursor = range.toString();
            
            // Count lines up to cursor
            const linesToCursor = (textToCursor.match(/\\n/g) || []).length;
            
            // If more than 1 line break, cursor is beyond 2 lines
            return linesToCursor > 1;
        }
        
        // Check if cursor is at beginning of element
        function isAtBeginning(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            
            // At beginning of element
            if (range.startContainer === element && range.startOffset === 0) return true;
            
            // At beginning of first text node
            if (element.firstChild && 
                range.startContainer === element.firstChild && 
                range.startOffset === 0) return true;
            
            return false;
        }
        
        // Check if cursor is at end of element
        function isAtEnd(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            
            // Get the last text node
            const lastNode = getLastTextNode(element);
            
            // At end of the last text node
            if (lastNode && 
                range.startContainer === lastNode && 
                range.startOffset === lastNode.length) return true;
            
            // At end of element with no children
            if (!element.hasChildNodes() && 
                range.startContainer === element && 
                range.startOffset === 0) return true;
            
            return false;
        }
        
        // Get the last text node in an element
        function getLastTextNode(element) {
            if (element.nodeType === Node.TEXT_NODE) return element;
            
            for (let i = element.childNodes.length - 1; i >= 0; i--) {
                const lastNode = getLastTextNode(element.childNodes[i]);
                if (lastNode) return lastNode;
            }
            
            return null;
        }
        
        // Place cursor at beginning of element
        function placeCursorAtBeginning(element) {
            const range = document.createRange();
            const selection = window.getSelection();
            
            if (element.firstChild && element.firstChild.nodeType === Node.TEXT_NODE) {
                range.setStart(element.firstChild, 0);
            } else {
                range.setStart(element, 0);
            }
            
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        // Place cursor at end of element
        function placeCursorAtEnd(element) {
            const range = document.createRange();
            const selection = window.getSelection();
            
            const lastNode = getLastTextNode(element);
            
            if (lastNode) {
                range.setStart(lastNode, lastNode.length);
            } else {
                range.selectNodeContents(element);
                range.collapse(false);
            }
            
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        // Update page indices and numbers after page removal
        function updatePageIndices() {
            pages.forEach((page, index) => {
                page.dataset.pageIndex = index;
                const pageNumber = page.parentNode.querySelector('.page-number');
                if (pageNumber) pageNumber.textContent = `Page ${index + 1}`;
            });
        }
        
        // Update page counter in GTK app
        function updatePageCounter(pageNum) {
            try {
                window.webkit.messageHandlers.pageChanged.postMessage("Page:" + pageNum);
            } catch (e) {
                console.error("Failed to update page counter:", e);
            }
        }
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
        try:
            # Extract page number using regex
            import re
            text = str(message)
            matches = re.findall(r'\d+', text)
            if matches:
                page_num = int(matches[0])
                self.page_label.set_text(f"Page: {page_num}")
            else:
                self.page_label.set_text("Page: 1")
        except Exception as e:
            print(f"Error updating page label: {e}")
            self.page_label.set_text("Page: 1")

if __name__ == "__main__":
    app = PageEditor()
    app.run(None)
