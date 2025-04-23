#!/usr/bin/env python3
import sys
import gi
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit, GLib, Gio

class SimplePageEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.pageeditor", 
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        # Create the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(900, 800)
        self.win.set_title("Page Layout Editor")

        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Create toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        
        # Add page size selector
        page_size_label = Gtk.Label(label="Page Size:")
        toolbar.append(page_size_label)
        
        self.page_size_combo = Gtk.DropDown()
        page_sizes = Gtk.StringList()
        page_sizes.append("US Letter")
        page_sizes.append("A4")
        self.page_size_combo.set_model(page_sizes)
        self.page_size_combo.connect("notify::selected", self.on_page_size_changed)
        toolbar.append(self.page_size_combo)
        
        # Add debug button
        debug_button = Gtk.ToggleButton(label="Debug Mode")
        debug_button.connect("toggled", self.on_debug_toggled)
        toolbar.append(debug_button)
        
        main_box.append(toolbar)
        
        # Create scrolled window for WebKit
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)

        # Create WebKit view
        settings = WebKit.Settings()
        settings.set_enable_javascript(True)
        settings.set_javascript_can_access_clipboard(True)
        
        self.web_view = WebKit.WebView()
        self.web_view.set_settings(settings)
        self.web_view.connect("load-changed", self.on_load_changed)
        
        scrolled_window.set_child(self.web_view)
        main_box.append(scrolled_window)
        
        # Add status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_bar.set_margin_start(6)
        status_bar.set_margin_end(6)
        status_bar.set_margin_top(6)
        status_bar.set_margin_bottom(6)
        
        self.page_count_label = Gtk.Label(label="Pages: 1")
        status_bar.append(self.page_count_label)
        
        main_box.append(status_bar)
        
        # Set window content
        self.win.set_content(main_box)
        
        # Load editor HTML
        self.load_editor()
        
        # Show window
        self.win.present()

    def load_editor(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Page Layout Editor</title>
            <style>
                :root {
                    --page-width: 8.5in;
                    --page-height: 11in;
                    --margin: 1in;
                    --content-width: calc(var(--page-width) - 2 * var(--margin));
                    --content-height: calc(var(--page-height) - 2 * var(--margin));
                }
                
                body {
                    margin: 0;
                    padding: 20px;
                    background-color: #f0f0f0;
                    font-family: 'Liberation Sans', Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.5;
                }
                
                #editor-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 30px;
                }
                
                .page {
                    width: var(--page-width);
                    height: var(--page-height);
                    position: relative;
                    background-color: white;
                    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
                }
                
                .page-content {
                    position: absolute;
                    top: var(--margin);
                    left: var(--margin);
                    width: var(--content-width);
                    height: var(--content-height);
                    overflow: hidden;
                    outline: none;
                }
                
                .page-number {
                    position: absolute;
                    bottom: 0.5in;
                    right: 0.5in;
                    font-size: 10pt;
                    color: #888;
                }
                
                /* A4 page size */
                .a4 {
                    --page-width: 210mm;
                    --page-height: 297mm;
                    --margin: 25.4mm;
                }
                
                /* Highlight current page */
                .current-page {
                    box-shadow: 0 0 15px rgba(0, 100, 255, 0.5);
                }
                
                /* Debug style */
                .debug .page-content {
                    border: 1px dashed rgba(255, 0, 0, 0.3);
                }
            </style>
        </head>
        <body>
            <div id="editor-container">
                <!-- Pages will be added here dynamically -->
            </div>
            
            <script>
                // Initialize global variables
                let pageSize = 'us-letter';
                let pageCount = 1;
                let currentPage = 1;
                let compositionInProgress = false;
                
                // Initialize the editor when the DOM is loaded
                document.addEventListener('DOMContentLoaded', initEditor);
                
                function initEditor() {
                    // Create the first page
                    addPage();
                    
                    // Set focus to the first page
                    focusPage(1);
                    
                    // Handle input method composition events
                    document.addEventListener('compositionstart', () => { compositionInProgress = true; });
                    document.addEventListener('compositionend', () => {
                        compositionInProgress = false;
                        // Check all pages for overflow after composition ends
                        checkAllPagesForOverflow();
                    });
                }
                
                function addPage() {
                    const container = document.getElementById('editor-container');
                    const pageNumber = container.children.length + 1;
                    
                    // Create page element
                    const page = document.createElement('div');
                    page.className = `page ${pageSize}`;
                    page.dataset.pageNumber = pageNumber;
                    
                    // Create editable content area
                    const content = document.createElement('div');
                    content.className = 'page-content';
                    content.contentEditable = true;
                    content.dataset.pageNumber = pageNumber;
                    content.addEventListener('input', handleInput);
                    content.addEventListener('keydown', handleKeydown);
                    content.addEventListener('paste', handlePaste);
                    content.addEventListener('focus', () => updateCurrentPage(pageNumber));
                    
                    // Create page number indicator
                    const pageNumberElement = document.createElement('div');
                    pageNumberElement.className = 'page-number';
                    pageNumberElement.textContent = pageNumber;
                    
                    // Add elements to page
                    page.appendChild(content);
                    page.appendChild(pageNumberElement);
                    
                    // Add page to container
                    container.appendChild(page);
                    
                    // Update page count
                    pageCount = container.children.length;
                    updatePageCount();
                    
                    return page;
                }
                
                function handleInput(event) {
                    // Skip processing during IME composition
                    if (compositionInProgress) return;
                    
                    const content = event.target;
                    const pageNumber = parseInt(content.dataset.pageNumber);
                    
                    // Check if content overflows
                    if (isOverflowing(content)) {
                        handleOverflow(content, pageNumber);
                    }
                    
                    // Check if we need to merge with next page
                    checkForMerge(pageNumber);
                }
                
                function handlePaste(event) {
                    // Use setTimeout to allow the paste operation to complete
                    setTimeout(() => {
                        const content = event.target;
                        const pageNumber = parseInt(content.dataset.pageNumber);
                        
                        if (isOverflowing(content)) {
                            handleOverflow(content, pageNumber);
                        }
                    }, 0);
                }
                
                function handleKeydown(event) {
                    const content = event.target;
                    const pageNumber = parseInt(content.dataset.pageNumber);
                    
                    // Handle backspace at beginning of page (except first page)
                    if (event.key === 'Backspace' && pageNumber > 1) {
                        const selection = window.getSelection();
                        if (selection.rangeCount && isCursorAtStart(content)) {
                            event.preventDefault();
                            moveToPreviousPage(pageNumber);
                            return;
                        }
                    }
                    
                    // Handle deletion at end of page content (except last page)
                    if (event.key === 'Delete' && pageNumber < pageCount) {
                        const selection = window.getSelection();
                        if (selection.rangeCount && isCursorAtEnd(content)) {
                            event.preventDefault();
                            moveToNextPage(pageNumber, true); // true = merge content
                            return;
                        }
                    }
                    
                    // Handle down arrow at bottom of page
                    if (event.key === 'ArrowDown') {
                        const selection = window.getSelection();
                        if (selection.rangeCount && isCursorAtBottom(content) && pageNumber < pageCount) {
                            event.preventDefault();
                            moveToNextPage(pageNumber, false);
                            return;
                        }
                    }
                    
                    // Handle up arrow at top of page
                    if (event.key === 'ArrowUp') {
                        const selection = window.getSelection();
                        if (selection.rangeCount && isCursorAtTop(content) && pageNumber > 1) {
                            event.preventDefault();
                            moveToPreviousPage(pageNumber, true); // true = move to bottom
                            return;
                        }
                    }
                }
                
                function isOverflowing(element) {
                    return element.scrollHeight > element.clientHeight;
                }
                
                function handleOverflow(content, pageNumber) {
                    // Get or create next page
                    let nextPage;
                    let nextContent;
                    
                    if (pageNumber < pageCount) {
                        // Get existing next page
                        nextPage = document.querySelector(`.page[data-page-number="${pageNumber + 1}"]`);
                        nextContent = nextPage.querySelector('.page-content');
                    } else {
                        // Create new page
                        nextPage = addPage();
                        nextContent = nextPage.querySelector('.page-content');
                    }
                    
                    // Find where to split the content
                    const splitInfo = findSplitPosition(content);
                    if (!splitInfo) return;
                    
                    // Extract overflow content
                    const overflowText = extractOverflow(content, splitInfo);
                    
                    // Add text to beginning of next page
                    if (overflowText) {
                        const existingNextContent = nextContent.innerHTML;
                        nextContent.innerHTML = overflowText + existingNextContent;
                    }
                    
                    // Check if the next page now overflows
                    if (isOverflowing(nextContent)) {
                        handleOverflow(nextContent, pageNumber + 1);
                    }
                }
                
                function findSplitPosition(element) {
                    // Create a temporary clone for binary search
                    const tempElement = element.cloneNode(true);
                    tempElement.style.visibility = 'hidden';
                    tempElement.style.position = 'absolute';
                    tempElement.style.height = element.clientHeight + 'px';
                    document.body.appendChild(tempElement);
                    
                    // Get content as HTML to preserve formatting
                    const content = element.innerHTML;
                    
                    // Binary search to find split point
                    let low = 0;
                    let high = content.length;
                    let best = 0;
                    
                    while (low <= high) {
                        const mid = Math.floor((low + high) / 2);
                        tempElement.innerHTML = content.substring(0, mid);
                        
                        if (tempElement.scrollHeight <= element.clientHeight) {
                            // This amount of content fits
                            best = mid;
                            low = mid + 1;
                        } else {
                            // Too much content
                            high = mid - 1;
                        }
                    }
                    
                    // Clean up
                    document.body.removeChild(tempElement);
                    
                    // Find a good split position (ideally at a word boundary)
                    // First check if we're in the middle of a tag
                    let adjustedPosition = best;
                    const tagClose = content.indexOf('>', best);
                    const tagOpen = content.lastIndexOf('<', best);
                    
                    if (tagOpen > -1 && (tagClose === -1 || tagClose < tagOpen)) {
                        // We're in the middle of a tag, move to before the tag
                        adjustedPosition = tagOpen;
                    } else {
                        // Look for word boundaries
                        const nextSpace = content.indexOf(' ', best);
                        const prevSpace = content.lastIndexOf(' ', best);
                        
                        if (nextSpace !== -1 && nextSpace - best < 20) {
                            // If next space is close, break there
                            adjustedPosition = nextSpace + 1;
                        } else if (prevSpace !== -1 && best - prevSpace < 20) {
                            // If previous space is close, break there
                            adjustedPosition = prevSpace + 1;
                        }
                    }
                    
                    return {
                        position: adjustedPosition,
                        content: content
                    };
                }
                
                function extractOverflow(element, splitInfo) {
                    const content = splitInfo.content;
                    const splitPos = splitInfo.position;
                    
                    if (splitPos >= content.length) return '';
                    
                    // Split the content
                    const beforeSplit = content.substring(0, splitPos);
                    const afterSplit = content.substring(splitPos);
                    
                    // Update the current element with content that fits
                    element.innerHTML = beforeSplit;
                    
                    // Return overflow content
                    return afterSplit;
                }
                
                function checkForMerge(pageNumber) {
                    // Skip if this is the last page
                    if (pageNumber >= pageCount) return;
                    
                    const currentPage = document.querySelector(`.page[data-page-number="${pageNumber}"]`);
                    const currentContent = currentPage.querySelector('.page-content');
                    
                    const nextPage = document.querySelector(`.page[data-page-number="${pageNumber + 1}"]`);
                    const nextContent = nextPage.querySelector('.page-content');
                    
                    // Check if current page content is empty or nearly empty
                    if (currentContent.innerHTML.trim() === '' || currentContent.innerText.trim() === '') {
                        // Get content from next page
                        const nextPageContent = nextContent.innerHTML;
                        
                        // Try to merge the pages
                        currentContent.innerHTML = nextPageContent;
                        
                        // Remove the next page
                        removePage(pageNumber + 1);
                        
                        // If merged content overflows, split it again
                        if (isOverflowing(currentContent)) {
                            handleOverflow(currentContent, pageNumber);
                        }
                    }
                }
                
                function removePage(pageNumber) {
                    const page = document.querySelector(`.page[data-page-number="${pageNumber}"]`);
                    if (!page) return;
                    
                    // Remove the page
                    page.remove();
                    
                    // Renumber remaining pages
                    const pages = document.querySelectorAll('.page');
                    pages.forEach((page, index) => {
                        const newPageNumber = index + 1;
                        page.dataset.pageNumber = newPageNumber;
                        
                        const content = page.querySelector('.page-content');
                        content.dataset.pageNumber = newPageNumber;
                        
                        const pageNumberElement = page.querySelector('.page-number');
                        pageNumberElement.textContent = newPageNumber;
                    });
                    
                    // Update page count
                    pageCount = pages.length;
                    updatePageCount();
                }
                
                function isCursorAtStart(element) {
                    const selection = window.getSelection();
                    if (!selection.rangeCount) return false;
                    
                    const range = selection.getRangeAt(0);
                    
                    // Check if at start of element
                    return (range.startContainer === element && range.startOffset === 0) ||
                           (range.startContainer.nodeType === Node.TEXT_NODE && 
                            range.startOffset === 0 && 
                            range.startContainer === element.firstChild);
                }
                
                function isCursorAtEnd(element) {
                    const selection = window.getSelection();
                    if (!selection.rangeCount) return false;
                    
                    const range = selection.getRangeAt(0);
                    
                    // Check if at end of element
                    return (range.endContainer === element && range.endOffset === element.childNodes.length) ||
                           (range.endContainer.nodeType === Node.TEXT_NODE && 
                            range.endOffset === range.endContainer.length && 
                            isLastTextNode(range.endContainer, element));
                }
                
                function isLastTextNode(node, container) {
                    let lastTextNode = null;
                    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
                    while (walker.nextNode()) {
                        lastTextNode = walker.currentNode;
                    }
                    return node === lastTextNode;
                }
                
                function isCursorAtTop(element) {
                    const selection = window.getSelection();
                    if (!selection.rangeCount) return false;
                    
                    // Get caret position
                    const range = selection.getRangeAt(0);
                    const rect = range.getBoundingClientRect();
                    
                    // Get element position
                    const elementRect = element.getBoundingClientRect();
                    
                    // Check if caret is at the top of the element (with small tolerance)
                    return (rect.top - elementRect.top) < 20;
                }
                
                function isCursorAtBottom(element) {
                    const selection = window.getSelection();
                    if (!selection.rangeCount) return false;
                    
                    // Get caret position
                    const range = selection.getRangeAt(0);
                    const rect = range.getBoundingClientRect();
                    
                    // Get element position
                    const elementRect = element.getBoundingClientRect();
                    
                    // Check if caret is at the bottom of the element (with small tolerance)
                    return (elementRect.bottom - rect.bottom) < 20;
                }
                
                function moveToPreviousPage(pageNumber, moveToBottom = false) {
                    // Get current page content
                    const currentPage = document.querySelector(`.page[data-page-number="${pageNumber}"]`);
                    const currentContent = currentPage.querySelector('.page-content');
                    
                    // Get previous page content
                    const prevPage = document.querySelector(`.page[data-page-number="${pageNumber - 1}"]`);
                    const prevContent = prevPage.querySelector('.page-content');
                    
                    // Focus previous page
                    prevContent.focus();
                    
                    // Place cursor at end of previous page content
                    if (moveToBottom) {
                        placeCursorAtEnd(prevContent);
                    } else {
                        // Otherwise, just place cursor at end
                        placeCursorAtEnd(prevContent);
                    }
                    
                    // If the current content is empty, we can try to pull content from next page
                    if (!currentContent.innerHTML.trim()) {
                        // Remove the empty page
                        removePage(pageNumber);
                    }
                }
                
                function moveToNextPage(pageNumber, mergeContent = false) {
                    // Get current page content
                    const currentPage = document.querySelector(`.page[data-page-number="${pageNumber}"]`);
                    const currentContent = currentPage.querySelector('.page-content');
                    
                    // Get next page content
                    let nextPage = document.querySelector(`.page[data-page-number="${pageNumber + 1}"]`);
                    let nextContent;
                    
                    // Create next page if it doesn't exist
                    if (!nextPage) {
                        nextPage = addPage();
                    }
                    
                    nextContent = nextPage.querySelector('.page-content');
                    
                    // If merging content, add content from next page to current page
                    if (mergeContent && nextContent.innerHTML.trim()) {
                        const selection = window.getSelection();
                        const range = selection.getRangeAt(0);
                        
                        // Insert next page content at cursor
                        const nextPageContent = nextContent.innerHTML;
                        
                        // Create a fragment to insert at cursor
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = nextPageContent;
                        
                        // Insert fragment
                        range.deleteContents();
                        range.insertNode(document.createTextNode(' ')); // Add a space
                        
                        // Apply the changes
                        currentContent.normalize();
                        
                        // Check for overflow
                        if (isOverflowing(currentContent)) {
                            handleOverflow(currentContent, pageNumber);
                        }
                        
                        return;
                    }
                    
                    // Focus next page
                    nextContent.focus();
                    
                    // Place cursor at beginning of next page content
                    placeCursorAtStart(nextContent);
                }
                
                function placeCursorAtStart(element) {
                    const range = document.createRange();
                    const selection = window.getSelection();
                    
                    // Set range to the beginning of the element
                    if (element.firstChild) {
                        range.setStart(element.firstChild, 0);
                        range.setEnd(element.firstChild, 0);
                    } else {
                        range.setStart(element, 0);
                        range.setEnd(element, 0);
                    }
                    
                    // Apply the range selection
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
                
                function placeCursorAtEnd(element) {
                    const range = document.createRange();
                    const selection = window.getSelection();
                    
                    // Find the last text node if it exists
                    let lastChild = element.lastChild;
                    let lastNode = lastChild;
                    let offset = lastChild ? (lastChild.nodeType === Node.TEXT_NODE ? lastChild.length : 0) : 0;
                    
                    // If the last child is not a text node, try to find the last text node
                    if (lastChild && lastChild.nodeType !== Node.TEXT_NODE) {
                        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
                        while (walker.nextNode()) {
                            lastNode = walker.currentNode;
                            offset = lastNode.length;
                        }
                    }
                    
                    // Set range to the end of the element
                    if (lastNode) {
                        range.setStart(lastNode, offset);
                        range.setEnd(lastNode, offset);
                    } else {
                        range.setStart(element, element.childNodes.length);
                        range.setEnd(element, element.childNodes.length);
                    }
                    
                    // Apply the range selection
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
                
                function focusPage(pageNumber) {
                    const page = document.querySelector(`.page[data-page-number="${pageNumber}"]`);
                    if (!page) return;
                    
                    const content = page.querySelector('.page-content');
                    content.focus();
                    
                    // Update current page highlighting
                    updateCurrentPage(pageNumber);
                }
                
                function updateCurrentPage(pageNumber) {
                    currentPage = pageNumber;
                    
                    // Remove current-page class from all pages
                    const pages = document.querySelectorAll('.page');
                    pages.forEach(page => page.classList.remove('current-page'));
                    
                    // Add current-page class to the active page
                    const activePage = document.querySelector(`.page[data-page-number="${pageNumber}"]`);
                    if (activePage) {
                        activePage.classList.add('current-page');
                        
                        // Scroll page into view
                        activePage.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    
                    // Update page count display
                    updatePageCount();
                }
                
                function updatePageCount() {
                    // Send message to GTK app
                    try {
                        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.pageCount) {
                            window.webkit.messageHandlers.pageCount.postMessage(JSON.stringify({
                                currentPage: currentPage,
                                totalPages: pageCount
                            }));
                        }
                    } catch(e) {
                        console.error("Error updating page count:", e);
                    }
                }
                
                function checkAllPagesForOverflow() {
                    // Check all pages for overflow, starting from the first
                    for (let i = 1; i <= pageCount; i++) {
                        const page = document.querySelector(`.page[data-page-number="${i}"]`);
                        if (!page) continue;
                        
                        const content = page.querySelector('.page-content');
                        if (isOverflowing(content)) {
                            handleOverflow(content, i);
                        }
                    }
                }
                
                function setPageSize(size) {
                    pageSize = (size === 'a4') ? 'a4' : 'us-letter';
                    
                    // Update all page elements
                    const pages = document.querySelectorAll('.page');
                    pages.forEach(page => {
                        // Remove existing size classes
                        page.classList.remove('us-letter', 'a4');
                        // Add new size class
                        page.classList.add(pageSize);
                    });
                    
                    // Check all pages for overflow with new size
                    setTimeout(checkAllPagesForOverflow, 100);
                }
                
                function setDebugMode(enabled) {
                    if (enabled) {
                        document.body.classList.add('debug');
                    } else {
                        document.body.classList.remove('debug');
                    }
                }
                
                // Export functions for GTK
                window.setPageSize = setPageSize;
                window.setDebugMode = setDebugMode;
            </script>
        </body>
        </html>
        """
        
        self.web_view.load_html(html, "file:///")

    def on_load_changed(self, web_view, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            self.setup_message_handlers()

    def setup_message_handlers(self):
        try:
            content_manager = self.web_view.get_user_content_manager()
            if not content_manager:
                content_manager = WebKit.UserContentManager()
                self.web_view.set_user_content_manager(content_manager)
            
            # Register message handler with appropriate WebKit version
            if hasattr(content_manager, 'register_script_message_handler_with_world'):
                content_manager.register_script_message_handler_with_world('pageCount', 'main')
            else:
                content_manager.register_script_message_handler('pageCount')
            
            content_manager.connect('script-message-received::pageCount', self.on_page_count_message)
        except Exception as e:
            print(f"Error setting up message handlers: {e}")

    def on_page_count_message(self, content_manager, message):
        try:
            # Extract message data based on WebKit version
            if hasattr(message, 'get_js_value'):
                data_json = message.get_js_value().to_string()
            else:
                data_json = message.to_string()
            
            data = json.loads(data_json)
            
            current_page = data.get('currentPage', 1)
            total_pages = data.get('totalPages', 1)
            
            self.page_count_label.set_text(f"Page: {current_page} of {total_pages}")
        except Exception as e:
            print(f"Error handling page count message: {e}")

    def on_page_size_changed(self, combo, gparam):
        selected_index = combo.get_selected()
        page_size = "us-letter" if selected_index == 0 else "a4"
        
        # Run JavaScript to change page size
        self.run_js(f"setPageSize('{page_size}')")
    
    def on_debug_toggled(self, button):
        is_active = button.get_active()
        self.run_js(f"setDebugMode({str(is_active).lower()})")

    def run_js(self, js_code, callback=None):
        try:
            if hasattr(self.web_view, 'evaluate_javascript'):
                # WebKit 6 approach
                self.web_view.evaluate_javascript(js_code, -1, None, None, None, callback)
            else:
                # Newer WebKit approach
                self.web_view.run_javascript(js_code, None, callback)
        except Exception as e:
            print(f"Error running JavaScript: {e}")


if __name__ == "__main__":
    app = SimplePageEditor()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
