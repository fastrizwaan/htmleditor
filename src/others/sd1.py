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
            overflow: hidden;
            height: 100vh;
        }
        #editor-container {
            width: 100%;
            height: 100%;
            position: relative;
            overflow: auto;
        }
        .page {
            border: 1px solid #ccc;
            padding: 10px;
            margin: 10px auto;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            width: calc(100% - 40px);
            height: calc(4em + 10px); /* Height for 4 lines + padding */
            line-height: 1em;
            position: relative;
            box-sizing: border-box;
        }
        .page-content {
            width: 100%;
            height: 100%;
            outline: none;
            white-space: pre-wrap;
            overflow: hidden;
            line-height: 1em;
        }
        /* Page number indicator */
        .page-number {
            position: absolute;
            bottom: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            color: #888;
            background: white;
            padding: 2px 8px;
            border-radius: 10px;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div id="editor-container"></div>

    <script>
        // Store references
        const editorContainer = document.getElementById('editor-container');
        
        // Initialize content storage
        let pages = [];
        let currentFocusedPage = null;
        
        // Create initial page
        createNewPage();
        
        // Function to create a new page
        function createNewPage(position = -1) {
            const page = document.createElement('div');
            page.className = 'page';
            
            const pageContent = document.createElement('div');
            pageContent.className = 'page-content';
            pageContent.contentEditable = true;
            pageContent.dataset.pageIndex = position >= 0 ? position : pages.length;
            
            const pageNumber = document.createElement('div');
            pageNumber.className = 'page-number';
            pageNumber.textContent = `Page ${(position >= 0 ? position : pages.length) + 1}`;
            
            page.appendChild(pageContent);
            page.appendChild(pageNumber);
            
            // Add before a specific position or at the end
            if (position >= 0 && position < editorContainer.children.length) {
                editorContainer.insertBefore(page, editorContainer.children[position]);
                
                // Update all subsequent page numbers
                updatePageNumbers();
            } else {
                editorContainer.appendChild(page);
                position = editorContainer.children.length - 1;
            }
            
            // Add event listeners
            pageContent.addEventListener('input', handlePageInput);
            pageContent.addEventListener('keydown', handlePageKeydown);
            pageContent.addEventListener('focus', () => {
                currentFocusedPage = pageContent;
                notifyPageChange(parseInt(pageContent.dataset.pageIndex) + 1);
            });
            
            // Store in our pages array
            if (position >= 0) {
                pages.splice(position, 0, pageContent);
            } else {
                pages.push(pageContent);
            }
            
            // Focus the new page if it's the first one
            if (pages.length === 1) {
                pageContent.focus();
            }
            
            return pageContent;
        }
        
        // Handle input on a page
        function handlePageInput(event) {
            const pageContent = event.target;
            
            // Check if content exceeds page height
            if (pageContent.scrollHeight > pageContent.clientHeight) {
                // Content overflow detected
                requestAnimationFrame(() => {
                    redistributeContent();
                });
            }
            
            // Check if page is empty (except for the last page)
            const pageIndex = parseInt(pageContent.dataset.pageIndex);
            if (pageContent.textContent.trim() === '' && pageIndex < pages.length - 1 && pages.length > 1) {
                // Check again in a moment to avoid race conditions
                setTimeout(() => {
                    if (pageContent.textContent.trim() === '') {
                        removePage(pageIndex);
                    }
                }, 0);
            }
        }
        
        // Handle keydown events
        function handlePageKeydown(event) {
            const pageContent = event.target;
            const pageIndex = parseInt(pageContent.dataset.pageIndex);
            
            // Enter key at the end of a full page should create new page and move cursor there
            if (event.key === 'Enter' && pageContent.scrollHeight > pageContent.clientHeight) {
                event.preventDefault();
                
                // Create new page after current one and focus it
                const newPage = createNewPage(pageIndex + 1);
                newPage.focus();
                return;
            }
            
            // Backspace at beginning of page should move content to previous page
            if (event.key === 'Backspace' && getCursorPosition(pageContent) === 0 && pageIndex > 0) {
                event.preventDefault();
                
                const prevPage = pages[pageIndex - 1];
                const prevContent = prevPage.innerHTML;
                const currentContent = pageContent.innerHTML;
                
                // Set content of previous page to combined content
                prevPage.innerHTML = prevContent + currentContent;
                
                // Remove current page
                removePage(pageIndex);
                
                // Focus the previous page at the end
                setCaretAtEnd(prevPage);
                
                // Redistribute content if needed
                redistributeContent();
                return;
            }
            
            // Arrow up at the beginning should move to previous page
            if (event.key === 'ArrowUp' && getCursorPosition(pageContent) === 0 && pageIndex > 0) {
                event.preventDefault();
                const prevPage = pages[pageIndex - 1];
                setCaretAtEnd(prevPage);
                return;
            }
            
            // Arrow down at the end should move to next page
            if (event.key === 'ArrowDown' && 
                isCaretAtEnd(pageContent) && 
                pageIndex < pages.length - 1) {
                event.preventDefault();
                const nextPage = pages[pageIndex + 1];
                nextPage.focus();
                document.getSelection().collapse(nextPage, 0);
                return;
            }
        }
        
        // Redistribute content across pages
        function redistributeContent() {
            // If no pages exist, return early
            if (pages.length === 0) return;
            
            // Remember which page had focus and the cursor position
            const activePage = currentFocusedPage;
            let activePageContent = '';
            let activePageIndex = 0;
            let selectionStart = 0;
            
            if (activePage) {
                activePageContent = activePage.innerHTML;
                activePageIndex = parseInt(activePage.dataset.pageIndex);
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    selectionStart = getCursorPosition(activePage);
                }
            }
            
            // Collect all content
            let allContent = '';
            pages.forEach(page => {
                allContent += page.innerHTML;
            });
            
            // If there's no content at all, just keep the first page empty
            if (allContent.trim() === '') {
                // Keep only the first page
                while (pages.length > 1) {
                    removePage(pages.length - 1);
                }
                pages[0].innerHTML = '';
                pages[0].focus();
                return;
            }
            
            // Get the maximum height per page
            const testPage = pages[0];
            const testPageStyle = window.getComputedStyle(testPage);
            const lineHeight = parseFloat(testPageStyle.lineHeight);
            const maxLines = 4;
            
            // Create a temporary element to measure text
            const tempElement = document.createElement('div');
            tempElement.style.visibility = 'hidden';
            tempElement.style.position = 'absolute';
            tempElement.style.width = testPage.clientWidth + 'px';
            tempElement.style.lineHeight = lineHeight + 'px';
            document.body.appendChild(tempElement);
            tempElement.innerHTML = allContent;
            
            // Get current nodes
            const nodes = Array.from(tempElement.childNodes);
            
            // Clear existing pages except the first one
            const firstPage = pages[0];
            firstPage.innerHTML = '';
            
            // Remove all pages except the first one
            while (pages.length > 1) {
                removePage(pages.length - 1);
            }
            
            // Start adding content to pages
            let currentPage = firstPage;
            let currentPageIndex = 0;
            
            // Helper function to add node and check if new page needed
            function addNodeToPage(node) {
                // Clone to avoid moving the original from the temp element
                const nodeClone = node.cloneNode(true);
                currentPage.appendChild(nodeClone);
                
                // Check if it overflows
                if (currentPage.scrollHeight > currentPage.clientHeight) {
                    // Remove the node that caused overflow
                    currentPage.removeChild(currentPage.lastChild);
                    
                    // Create a new page
                    currentPageIndex++;
                    const newPage = createNewPage();
                    currentPage = newPage;
                    
                    // Add node to new page
                    currentPage.appendChild(nodeClone.cloneNode(true));
                    
                    // If it still overflows on its own page, we need to split text
                    if (currentPage.scrollHeight > currentPage.clientHeight) {
                        splitTextNode(nodeClone, currentPage);
                    }
                }
            }
            
            // Add each node to pages
            for (const node of nodes) {
                addNodeToPage(node);
            }
            
            // Clean up
            document.body.removeChild(tempElement);
            
            // Update page numbers
            updatePageNumbers();
            
            // Try to restore focus to the same logical position if possible
            if (activePageIndex < pages.length) {
                pages[activePageIndex].focus();
                try {
                    // Attempt to place cursor at a similar position
                    const selection = window.getSelection();
                    const range = document.createRange();
                    
                    // Find a position close to the original
                    const content = pages[activePageIndex].textContent;
                    const targetPos = Math.min(selectionStart, content.length);
                    
                    // Set cursor position
                    setCursorPosition(pages[activePageIndex], targetPos);
                } catch (e) {
                    console.error("Failed to restore cursor position:", e);
                    // Fallback to setting cursor at the end
                    setCaretAtEnd(pages[activePageIndex]);
                }
            } else if (pages.length > 0) {
                // Focus last page if the original page no longer exists
                setCaretAtEnd(pages[pages.length - 1]);
            }
        }
        
        // Set cursor at specific position
        function setCursorPosition(element, position) {
            const selection = window.getSelection();
            const range = document.createRange();
            let currentNode = element;
            let currentPos = 0;
            
            // Helper function to find the right text node and position
            function findPosition(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    if (currentPos + node.length >= position) {
                        range.setStart(node, position - currentPos);
                        return true;
                    }
                    currentPos += node.length;
                } else {
                    for (let i = 0; i < node.childNodes.length; i++) {
                        if (findPosition(node.childNodes[i])) {
                            return true;
                        }
                    }
                }
                return false;
            }
            
            // Find the position
            if (findPosition(element)) {
                range.collapse(true);
                selection.removeAllRanges();
                selection.addRange(range);
            } else {
                // Fallback - set to end
                setCaretAtEnd(element);
            }
        }
        
        // Intelligently distribute nodes across pages
        function distributeNodes(nodeList, maxHeight) {
            // No-op - replaced by the redesigned content redistribution logic
        }
        
        // Split a text node across pages
        function splitTextNode(node, page) {
            if (!node || node.nodeType !== Node.TEXT_NODE) {
                // If not a text node, just return
                if (node && node.textContent) {
                    // If it has text content but isn't a text node, create a text node from it
                    const textNode = document.createTextNode(node.textContent);
                    page.innerHTML = ''; // Clear existing content
                    page.appendChild(textNode);
                }
                return;
            }
            
            // Start with full text
            const fullText = node.textContent;
            if (!fullText || fullText.length === 0) return;
            
            // Binary search to find maximum text that fits
            let start = 0;
            let end = fullText.length;
            let mid;
            let lastGoodMid = 0;
            
            // Create a test element to measure text
            const testElement = document.createElement('div');
            testElement.style.position = 'absolute';
            testElement.style.visibility = 'hidden';
            testElement.style.width = page.clientWidth + 'px';
            testElement.style.lineHeight = window.getComputedStyle(page).lineHeight;
            document.body.appendChild(testElement);
            
            // Binary search to find the split point
            while (start < end) {
                mid = Math.floor((start + end) / 2);
                
                // Try with text up to mid point
                testElement.textContent = fullText.substring(0, mid);
                
                if (testElement.scrollHeight <= page.clientHeight) {
                    // This fits, try with more text
                    lastGoodMid = mid;
                    start = mid + 1;
                } else {
                    // Too much text, try with less
                    end = mid;
                }
            }
            
            // Clean up test element
            document.body.removeChild(testElement);
            
            // Find a good break point near the calculated position
            const breakPos = findBreakPoint(fullText, lastGoodMid);
            
            // Update the current page with content that fits
            page.textContent = fullText.substring(0, breakPos);
            
            // If there's remaining text, create a new page for it
            if (breakPos < fullText.length) {
                const remainingText = fullText.substring(breakPos);
                if (remainingText.trim().length > 0) {
                    const newPage = createNewPage();
                    newPage.textContent = remainingText;
                }
            }
        }
        
        // Find a good point to break text (word boundary)
        function findBreakPoint(text, position) {
            // If already at start/end, return position
            if (position <= 0) return 0;
            if (position >= text.length) return text.length;
            
            // Try to break at a word boundary
            const nextSpace = text.indexOf(' ', position);
            const prevSpace = text.lastIndexOf(' ', position);
            
            // If no spaces, just use the position
            if (nextSpace === -1 && prevSpace === -1) return position;
            
            // Choose the closest space
            if (nextSpace === -1) return prevSpace + 1;
            if (prevSpace === -1) return nextSpace;
            
            // Return the closest space
            return (position - prevSpace <= nextSpace - position) ? prevSpace + 1 : nextSpace;
        }
        
        // Remove a page
        function removePage(index) {
            if (index < 0 || index >= pages.length) return;
            
            // Remove from DOM
            const page = pages[index];
            page.parentElement.parentElement.remove();
            
            // Remove from array
            pages.splice(index, 1);
            
            // Update page indices and numbers
            updatePageNumbers();
        }
        
        // Update all page numbers and indices
        function updatePageNumbers() {
            for (let i = 0; i < pages.length; i++) {
                pages[i].dataset.pageIndex = i;
                const pageElement = pages[i].parentElement;
                const pageNumberElement = pageElement.querySelector('.page-number');
                if (pageNumberElement) {
                    pageNumberElement.textContent = `Page ${i + 1}`;
                }
            }
            
            // Notify current page
            if (currentFocusedPage) {
                const currentIndex = parseInt(currentFocusedPage.dataset.pageIndex);
                notifyPageChange(currentIndex + 1);
            } else if (pages.length > 0) {
                notifyPageChange(1);
            }
        }
        
        // Helper function to get cursor position
        function getCursorPosition(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return 0;
            
            const range = selection.getRangeAt(0);
            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(element);
            preCaretRange.setEnd(range.endContainer, range.endOffset);
            return preCaretRange.toString().length;
        }
        
        // Check if caret is at the end of content
        function isCaretAtEnd(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(element);
            preCaretRange.setEnd(range.endContainer, range.endOffset);
            
            return preCaretRange.toString().length === element.textContent.length;
        }
        
        // Helper to set caret at the end of an element
        function setCaretAtEnd(element) {
            element.focus();
            const range = document.createRange();
            const selection = window.getSelection();
            
            range.selectNodeContents(element);
            range.collapse(false); // Collapse to end
            
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        // Notify GTK app about page changes
        function notifyPageChange(pageNumber) {
            try {
                // Convert to string to ensure consistent format for extraction
                const message = "Page:" + pageNumber;
                window.webkit.messageHandlers.pageChanged.postMessage(message);
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
            # WebKit6 doesn't have a unified API across all versions
            # Try to extract the page number from the string representation
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
