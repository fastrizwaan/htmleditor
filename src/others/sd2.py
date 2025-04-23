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
            font-family: sans-serif;
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
            width: 100%;
            box-sizing: border-box;
        }
        .page-content {
            padding: 10px;
            min-height: 4em;
            max-height: 4em;
            line-height: 1em;
            overflow: hidden;
            outline: none;
            white-space: pre-wrap;
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
            z-index: 10;
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
        let currentFocusedPageIndex = 0;
        
        // Create initial page on load
        window.addEventListener('DOMContentLoaded', function() {
            createPage();
            updatePageNumbers();
        });
        
        // Create a new page
        function createPage(content = '', insertAfterIndex = null) {
            // Create page elements
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'page-content';
            contentDiv.contentEditable = true;
            contentDiv.innerHTML = content;
            
            const pageNumberDiv = document.createElement('div');
            pageNumberDiv.className = 'page-number';
            
            // Assemble page
            pageDiv.appendChild(contentDiv);
            pageDiv.appendChild(pageNumberDiv);
            
            // Insert at specific position or at the end
            if (insertAfterIndex !== null && insertAfterIndex < pages.length) {
                const nextPage = pages[insertAfterIndex].parentNode.nextSibling;
                if (nextPage) {
                    editorContainer.insertBefore(pageDiv, nextPage);
                } else {
                    editorContainer.appendChild(pageDiv);
                }
                // Update our pages array
                pages.splice(insertAfterIndex + 1, 0, contentDiv);
            } else {
                editorContainer.appendChild(pageDiv);
                pages.push(contentDiv);
            }
            
            // Set up event listeners
            contentDiv.addEventListener('input', handlePageInput);
            contentDiv.addEventListener('keydown', handlePageKeydown);
            contentDiv.addEventListener('focus', function() {
                currentFocusedPageIndex = pages.indexOf(this);
                notifyPageChange(currentFocusedPageIndex + 1);
            });
            
            // Return the content div reference
            return contentDiv;
        }
        
        // Handle input events on a page
        function handlePageInput(event) {
            const pageContent = event.target;
            const pageIndex = pages.indexOf(pageContent);
            
            // Check if content exceeds max height (4 lines)
            if (pageContent.scrollHeight > pageContent.clientHeight) {
                // Get selection to restore it later
                const selection = window.getSelection();
                const range = selection.getRangeAt(0);
                const cursorOffset = range.startOffset;
                const cursorNode = range.startContainer;
                
                // Get overflow content
                const overflowText = getOverflowContent(pageContent);
                if (overflowText) {
                    // Remove overflow content from current page
                    truncateToFit(pageContent);
                    
                    // Check if next page exists
                    if (pageIndex + 1 < pages.length) {
                        // Add overflow to beginning of next page
                        const nextPage = pages[pageIndex + 1];
                        nextPage.innerHTML = overflowText + nextPage.innerHTML;
                    } else {
                        // Create new page with overflow
                        createPage(overflowText, pageIndex);
                    }
                    
                    // If cursor was in overflowed content, move it to next page
                    if (isInOverflow(cursorNode, cursorOffset, pageContent)) {
                        if (pageIndex + 1 < pages.length) {
                            const nextPage = pages[pageIndex + 1];
                            nextPage.focus();
                            // Position cursor at beginning of next page
                            placeCursorAtBeginning(nextPage);
                        }
                    }
                }
            }
            
            // Update page numbers
            updatePageNumbers();
        }
        
        // Handle keyboard events
        function handlePageKeydown(event) {
            const pageContent = event.target;
            const pageIndex = pages.indexOf(pageContent);
            
            // Enter key at the end of page
            if (event.key === 'Enter' && isCaretAtEnd(pageContent) && 
                pageContent.scrollHeight >= pageContent.clientHeight) {
                event.preventDefault();
                
                // Focus or create next page
                if (pageIndex + 1 < pages.length) {
                    pages[pageIndex + 1].focus();
                    placeCursorAtBeginning(pages[pageIndex + 1]);
                } else {
                    const newPage = createPage('', pageIndex);
                    newPage.focus();
                }
                return;
            }
            
            // Backspace at beginning of page
            if (event.key === 'Backspace' && isCaretAtBeginning(pageContent) && pageIndex > 0) {
                event.preventDefault();
                
                // Move cursor to end of previous page
                const prevPage = pages[pageIndex - 1];
                prevPage.focus();
                placeCursorAtEnd(prevPage);
                
                // If current page is empty, remove it
                if (pageContent.textContent.trim() === '') {
                    removePage(pageIndex);
                } else {
                    // Otherwise, move current content to previous page
                    const currentContent = pageContent.innerHTML;
                    prevPage.innerHTML += currentContent;
                    
                    // Handle overflow in the previous page
                    if (prevPage.scrollHeight > prevPage.clientHeight) {
                        const overflow = getOverflowContent(prevPage);
                        truncateToFit(prevPage);
                        pageContent.innerHTML = overflow;
                    } else {
                        // If no overflow, remove current page
                        removePage(pageIndex);
                    }
                }
                return;
            }
            
            // Arrow up at beginning of page
            if (event.key === 'ArrowUp' && isCaretAtBeginning(pageContent) && pageIndex > 0) {
                event.preventDefault();
                const prevPage = pages[pageIndex - 1];
                prevPage.focus();
                placeCursorAtEnd(prevPage);
                return;
            }
            
            // Arrow down at end of page
            if (event.key === 'ArrowDown' && isCaretAtEnd(pageContent) && pageIndex < pages.length - 1) {
                event.preventDefault();
                const nextPage = pages[pageIndex + 1];
                nextPage.focus();
                placeCursorAtBeginning(nextPage);
                return;
            }
        }
        
        // Check if caret is at the beginning of element
        function isCaretAtBeginning(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            if (range.startContainer === element && range.startOffset === 0) {
                return true;
            }
            
            // Handle text nodes
            if (range.startContainer.nodeType === Node.TEXT_NODE && 
                range.startContainer === element.firstChild && 
                range.startOffset === 0) {
                return true;
            }
            
            return false;
        }
        
        // Check if caret is at the end of element
        function isCaretAtEnd(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            
            // If element has no text, any position is end
            if (element.textContent.length === 0) return true;
            
            // Check if at end of the element
            if (range.startContainer === element) {
                return range.startOffset === element.childNodes.length;
            }
            
            // Handle text nodes
            if (range.startContainer.nodeType === Node.TEXT_NODE) {
                const textNode = range.startContainer;
                // If this is the last text node and we're at its end
                if (textNode === getLastTextNode(element) && 
                    range.startOffset === textNode.length) {
                    return true;
                }
            }
            
            return false;
        }
        
        // Get the last text node
        function getLastTextNode(element) {
            if (element.nodeType === Node.TEXT_NODE) return element;
            
            // Traverse child nodes in reverse
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
            
            // Find the first text node or use the element itself
            let targetNode = element;
            if (element.firstChild && element.firstChild.nodeType === Node.TEXT_NODE) {
                targetNode = element.firstChild;
            }
            
            range.setStart(targetNode, 0);
            range.collapse(true);
            
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        // Place cursor at end of element
        function placeCursorAtEnd(element) {
            const range = document.createRange();
            const selection = window.getSelection();
            
            // Find the last text node or use the element itself
            const lastTextNode = getLastTextNode(element);
            
            if (lastTextNode) {
                range.setStart(lastTextNode, lastTextNode.length);
            } else {
                // No text nodes, use the element
                range.selectNodeContents(element);
                range.collapse(false);
            }
            
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        // Extract overflow content that doesn't fit in a page
        function getOverflowContent(pageContent) {
            // Create a clone to work with
            const clone = pageContent.cloneNode(true);
            const tempDiv = document.createElement('div');
            tempDiv.style.position = 'absolute';
            tempDiv.style.left = '-9999px';
            tempDiv.style.width = pageContent.clientWidth + 'px';
            tempDiv.style.maxHeight = pageContent.clientHeight + 'px';
            tempDiv.style.overflow = 'hidden';
            tempDiv.appendChild(clone);
            document.body.appendChild(tempDiv);
            
            // If no overflow, return empty string
            if (clone.scrollHeight <= clone.clientHeight) {
                document.body.removeChild(tempDiv);
                return '';
            }
            
            // Simple approach: find a reasonable cut-off point
            // Start with crude percentage estimate
            let contentText = pageContent.textContent;
            let approxLines = Math.ceil(clone.scrollHeight / parseInt(window.getComputedStyle(clone).lineHeight));
            let targetLines = 4; // Max allowed lines
            let cutRatio = targetLines / approxLines;
            let cutIndex = Math.floor(contentText.length * cutRatio);
            
            // Find a better cut point near our estimate (prefer word boundaries)
            let wordBoundary = contentText.lastIndexOf(' ', cutIndex);
            if (wordBoundary === -1 || wordBoundary < contentText.length * 0.5) {
                // Fall back to character cut if word boundary is too far back
                wordBoundary = cutIndex;
            }
            
            // Clean up
            document.body.removeChild(tempDiv);
            
            // Return the overflow content
            return contentText.substring(wordBoundary).trim();
        }
        
        // Truncate content to fit within max height
        function truncateToFit(pageContent) {
            const overflowContent = getOverflowContent(pageContent);
            if (!overflowContent) return;
            
            const fullText = pageContent.textContent;
            const keepLength = fullText.length - overflowContent.length;
            
            // Find a reasonable cut point
            let cutPoint = fullText.lastIndexOf(' ', keepLength);
            if (cutPoint === -1 || cutPoint < fullText.length * 0.5) {
                cutPoint = keepLength;
            }
            
            // Update content
            pageContent.textContent = fullText.substring(0, cutPoint);
        }
        
        // Check if cursor position is in overflow area
        function isInOverflow(node, offset, pageContent) {
            // This is a simplification - we check if cursor is beyond 80% of max content
            const selection = document.createRange();
            selection.setStart(pageContent, 0);
            selection.setEnd(node, offset);
            
            const cursorPosition = selection.toString().length;
            const maxPosition = pageContent.textContent.length * 0.8;
            
            return cursorPosition > maxPosition;
        }
        
        // Remove a page by index
        function removePage(index) {
            if (index < 0 || index >= pages.length) return;
            
            // Remove from DOM
            const pageToRemove = pages[index];
            const pageElement = pageToRemove.parentNode;
            pageElement.remove();
            
            // Remove from array
            pages.splice(index, 1);
            
            // Update page numbers
            updatePageNumbers();
        }
        
        // Update page numbers
        function updatePageNumbers() {
            pages.forEach((page, index) => {
                const pageNumber = page.parentNode.querySelector('.page-number');
                if (pageNumber) {
                    pageNumber.textContent = `Page ${index + 1}`;
                }
            });
            
            // Notify about current page
            notifyPageChange(currentFocusedPageIndex + 1);
        }
        
        // Notify GTK app about page changes
        function notifyPageChange(pageNum) {
            try {
                window.webkit.messageHandlers.pageChanged.postMessage("Page:" + pageNum);
            } catch (e) {
                console.error("Failed to notify about page change:", e);
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
        # Update the page label
        try:
            # Extract page number using regex
            import re
            text = str(message)
            matches = re.findall(r'\d+', text)
            if matches:
                page_num = int(matches[0])
                self.page_label.set_text(f"Page: {page_num}")
            else:
                self.page_label.set_text("Page: 1")  # Default fallback
        except Exception as e:
            print(f"Error updating page label: {e}")
            self.page_label.set_text("Page: 1")  # Default fallback

if __name__ == "__main__":
    app = PageEditor()
    app.run(None)
