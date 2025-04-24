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
        # Initialize libadwaita
        Adw.init()
        
        # Create the application window
        self.win = Adw.ApplicationWindow(application=app, default_width=800, default_height=800)
        self.win.set_title("Paginated Editor")
        
        # Create a toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.win.set_content(self.toast_overlay)
        
        # Main box layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.toast_overlay.set_child(main_box)
        
        # Create the header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        
        # Add page size adjustment controls in header bar
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        size_box.set_margin_start(10)
        
        # Width adjustment
        width_label = Gtk.Label(label="Width:")
        size_box.append(width_label)
        
        self.width_adjustment = Gtk.Adjustment(
            value=20,  # Default width (in characters)
            lower=10,
            upper=100,
            step_increment=5,
            page_increment=10
        )
        width_spin = Gtk.SpinButton()
        width_spin.set_adjustment(self.width_adjustment)
        width_spin.connect("value-changed", self.on_page_size_changed)
        size_box.append(width_spin)
        
        # Height adjustment
        height_label = Gtk.Label(label="Height:")
        size_box.append(height_label)
        
        self.height_adjustment = Gtk.Adjustment(
            value=15,  # Default height (in lines)
            lower=2,
            upper=50,
            step_increment=1,
            page_increment=5
        )
        height_spin = Gtk.SpinButton()
        height_spin.set_adjustment(self.height_adjustment)
        height_spin.connect("value-changed", self.on_page_size_changed)
        size_box.append(height_spin)
        
        header.pack_start(size_box)
        
        # Create WebView
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Enable developer tools for debugging (can be removed in production)
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(True)
        
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
        :root {
            --page-width: 40ch;
            --page-height: 15em;
            --page-padding: 12px;
            --page-margin: 20px;
            --page-border: 1px solid #ccc;
            --page-shadow: 0 2px 8px rgba(0,0,0,0.1);
            --page-background: white;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background-color: #f5f5f5;
            min-height: 100vh;
        }
        
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px;
            box-sizing: border-box;
            min-height: 100vh;
        }
        
        .page {
            width: var(--page-width);
            min-height: var(--page-height);
            border: var(--page-border);
            padding: var(--page-padding);
            margin-bottom: var(--page-margin);
            box-shadow: var(--page-shadow);
            background-color: var(--page-background);
            position: relative;
            overflow: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
            font-size: 16px;
            border-radius: 4px;
        }
        
        .page:focus {
            outline: 2px solid #4a86e8;
            box-shadow: 0 0 0 4px rgba(74, 134, 232, 0.2);
        }
        
        .page-number {
            position: absolute;
            bottom: 5px;
            right: 8px;
            font-size: 12px;
            color: #999;
            user-select: none;
            pointer-events: none;
        }
        
        .page-content {
            min-height: calc(var(--page-height) - 20px);
            outline: none;
        }
        
        /* Ensure paragraphs within page content have consistent spacing */
        .page-content p {
            margin: 0 0 0.5em 0;
        }
        
        /* Style for the last paragraph to prevent extra space at bottom */
        .page-content p:last-child {
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div id="editor-container"></div>

    <script>
        // Editor state
        let text = '';
        let pageWidth = 40; // characters
        let pageHeight = 15; // lines
        let charsPerPage;
        const container = document.getElementById('editor-container');
        
        // Calculate chars per page (this is an approximation)
        function calculateCharsPerPage() {
            // Using the width and average chars per line * number of lines
            // This is an approximation that works well enough for monospace
            // For proportional fonts, we'd need a more complex algorithm
            return pageWidth * pageHeight;
        }
        
        // Initialize chars per page
        charsPerPage = calculateCharsPerPage();
        
        // Function to update editor settings
        function updateEditorSettings(width, height) {
            // Update the CSS variables
            document.documentElement.style.setProperty('--page-width', width + 'ch');
            document.documentElement.style.setProperty('--page-height', height + 'em');
            
            // Update the JavaScript variables
            pageWidth = width;
            pageHeight = height;
            
            // Recalculate chars per page
            charsPerPage = calculateCharsPerPage();
            
            // Re-paginate the content
            updatePages();
        }
        
        // Function to update pages based on text content
        function updatePages() {
            // Save cursor position
            const selection = window.getSelection();
            const range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
            let selectionPageIndex = -1;
            let selectionOffset = 0;
            
            if (range && range.startContainer) {
                // Find which page and what offset we're at
                const node = range.startContainer;
                let contentElement;
                
                if (node.nodeType === 3) { // Text node
                    contentElement = node.parentElement;
                } else {
                    contentElement = node;
                }
                
                // Find the parent page-content div
                const pageContentDiv = contentElement.closest('.page-content');
                if (pageContentDiv) {
                    const pageDiv = pageContentDiv.closest('.page');
                    if (pageDiv) {
                        selectionPageIndex = parseInt(pageDiv.dataset.pageIndex);
                        
                        // Calculate the global position
                        for (let i = 0; i < selectionPageIndex; i++) {
                            const prevPage = document.querySelector(`.page[data-page-index="${i}"] .page-content`);
                            if (prevPage) {
                                selectionOffset += prevPage.textContent.length;
                            }
                        }
                        
                        // Add the offset within the current page
                        selectionOffset += range.startOffset;
                        
                        // If the node is a text node inside a page-content div, we need to calculate
                        // the offset differently to account for all text nodes in the div
                        if (node.nodeType === 3 && pageContentDiv) {
                            // We need to find the offset of this text node within its parent page-content
                            let curNode = pageContentDiv.firstChild;
                            let textBeforeCursor = 0;
                            
                            while (curNode && curNode !== node) {
                                if (curNode.nodeType === 3) { // Text node
                                    textBeforeCursor += curNode.textContent.length;
                                }
                                curNode = curNode.nextSibling;
                            }
                            
                            // Adjust the offset to include text from previous text nodes
                            selectionOffset = selectionOffset - range.startOffset + textBeforeCursor + range.startOffset;
                        }
                    }
                }
            }
            
            // Clear the container
            container.innerHTML = '';
            
            // Calculate how many pages we need
            const totalChars = text.length;
            const numPages = Math.max(1, Math.ceil(totalChars / charsPerPage));
            
            // Create pages
            for (let i = 0; i < numPages; i++) {
                const startChar = i * charsPerPage;
                const endChar = Math.min(startChar + charsPerPage, totalChars);
                const pageText = text.substring(startChar, endChar);
                
                // Create the page div
                const page = document.createElement('div');
                page.className = 'page';
                page.dataset.pageIndex = i;
                
                // Create the content div (where editing happens)
                const pageContent = document.createElement('div');
                pageContent.className = 'page-content';
                pageContent.setAttribute('contenteditable', 'true');
                
                // Set content as HTML with proper paragraph formatting
                if (pageText.includes('\n')) {
                    // Split by newlines and create paragraphs
                    const paragraphs = pageText.split('\n');
                    paragraphs.forEach((para, index) => {
                        const p = document.createElement('p');
                        p.textContent = para;
                        pageContent.appendChild(p);
                    });
                } else {
                    // Just set as a single paragraph if no newlines
                    const p = document.createElement('p');
                    p.textContent = pageText;
                    pageContent.appendChild(p);
                }
                
                // Create the page number indicator
                const pageNumber = document.createElement('div');
                pageNumber.className = 'page-number';
                pageNumber.textContent = (i + 1).toString();
                
                // Add the elements to the page
                page.appendChild(pageContent);
                page.appendChild(pageNumber);
                
                // Add event listeners
                pageContent.addEventListener('input', handleInput);
                pageContent.addEventListener('keydown', handleKeyDown);
                
                // Add the page to the container
                container.appendChild(page);
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
                        const pageContent = allPages[newPageIndex].querySelector('.page-content');
                        const pageLength = pageContent ? pageContent.textContent.length : 0;
                        
                        if (remainingOffset <= pageLength) {
                            break;
                        }
                        
                        remainingOffset -= pageLength;
                        newPageIndex++;
                    }
                    
                    // Make sure we don't exceed available pages
                    if (newPageIndex < allPages.length) {
                        const pageContent = allPages[newPageIndex].querySelector('.page-content');
                        if (pageContent) {
                            // Focus the page content
                            pageContent.focus();
                            
                            // Try to find the correct node and position
                            const walker = document.createTreeWalker(
                                pageContent,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );
                            
                            let currentTextNode = walker.nextNode();
                            let charactersWalked = 0;
                            
                            // Walk through text nodes until we reach our target offset
                            while (currentTextNode) {
                                const nodeLength = currentTextNode.textContent.length;
                                if (charactersWalked + nodeLength >= remainingOffset) {
                                    // Found the right node, now set the selection
                                    const offset = remainingOffset - charactersWalked;
                                    const newRange = document.createRange();
                                    newRange.setStart(currentTextNode, offset);
                                    newRange.collapse(true);
                                    
                                    selection.removeAllRanges();
                                    selection.addRange(newRange);
                                    break;
                                }
                                
                                charactersWalked += nodeLength;
                                currentTextNode = walker.nextNode();
                            }
                            
                            // If we couldn't find the exact position, just put cursor at start
                            if (!currentTextNode) {
                                // Try to place cursor at beginning of first paragraph
                                if (pageContent.firstChild) {
                                    if (pageContent.firstChild.nodeType === 1) { // Element node (like <p>)
                                        if (pageContent.firstChild.firstChild && pageContent.firstChild.firstChild.nodeType === 3) {
                                            // First child is text node
                                            const newRange = document.createRange();
                                            newRange.setStart(pageContent.firstChild.firstChild, 0);
                                            newRange.collapse(true);
                                            
                                            selection.removeAllRanges();
                                            selection.addRange(newRange);
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.error('Error restoring selection:', e);
                }
            } else {
                // Focus the first page if no selection to restore
                const firstPageContent = document.querySelector('.page-content');
                if (firstPageContent) {
                    firstPageContent.focus();
                }
            }
        }
        
        // Extract text from content, preserving paragraph structure
        function extractTextFromContent() {
            let extractedText = '';
            document.querySelectorAll('.page-content').forEach(content => {
                // Go through each child node
                content.childNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node (like <p>, <div>)
                        extractedText += node.textContent + '\n';
                    } else if (node.nodeType === 3) { // Text node
                        extractedText += node.textContent;
                    }
                });
            });
            return extractedText;
        }
        
        // Handle input events (typing, pasting, etc.)
        function handleInput(e) {
            // Extract text preserving paragraph structure
            text = extractTextFromContent();
            
            // Debounce the update to avoid interrupting typing
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => {
                updatePages();
                notifyContentChanged();
            }, 300);
        }
        
        // Handle keydown events for special keys
        function handleKeyDown(e) {
            // Current active element
            const activeElement = document.activeElement;
            if (!activeElement || !activeElement.classList.contains('page-content')) {
                return;
            }
            
            const pageDiv = activeElement.closest('.page');
            const currentPageIndex = parseInt(pageDiv.dataset.pageIndex);
            
            // Special handling for Enter key
            if (e.key === 'Enter') {
                // We'll let the browser handle the default behavior
                // But ensure we always create <p> elements for consistency
                
                // Prevent default behavior if necessary for certain browsers
                if (!e.shiftKey && document.queryCommandSupported('defaultParagraphSeparator')) {
                    document.execCommand('defaultParagraphSeparator', false, 'p');
                }
                
                // Update text model and pagination after the browser creates the new paragraph
                setTimeout(() => {
                    text = extractTextFromContent();
                    updatePages();
                    notifyContentChanged();
                }, 0);
            }
            
            // Handle navigation between pages
            if (e.key === 'ArrowDown' || e.key === 'PageDown') {
                const isAtEnd = isAtEndOfContent(activeElement);
                
                if (isAtEnd) {
                    const nextPage = document.querySelector(`.page[data-page-index="${currentPageIndex + 1}"] .page-content`);
                    if (nextPage) {
                        e.preventDefault();
                        nextPage.focus();
                        
                        // Place cursor at the beginning of the next page
                        const selection = window.getSelection();
                        
                        // Find the first text node in the next page
                        const walker = document.createTreeWalker(
                            nextPage,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        
                        const firstTextNode = walker.nextNode();
                        if (firstTextNode) {
                            const range = document.createRange();
                            range.setStart(firstTextNode, 0);
                            range.collapse(true);
                            selection.removeAllRanges();
                            selection.addRange(range);
                        } else {
                            // If no text nodes, just focus the element
                            if (nextPage.firstChild && nextPage.firstChild.nodeType === 1) {
                                nextPage.firstChild.focus();
                            } else {
                                nextPage.focus();
                            }
                        }
                    }
                }
            } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
                const isAtStart = isAtStartOfContent(activeElement);
                
                if (isAtStart) {
                    const prevPage = document.querySelector(`.page[data-page-index="${currentPageIndex - 1}"] .page-content`);
                    if (prevPage) {
                        e.preventDefault();
                        prevPage.focus();
                        
                        // Place cursor at the end of the previous page
                        const selection = window.getSelection();
                        
                        // Find the last text node in the prev page
                        const lastTextNode = findLastTextNode(prevPage);
                        if (lastTextNode) {
                            const range = document.createRange();
                            range.setStart(lastTextNode, lastTextNode.textContent.length);
                            range.collapse(true);
                            selection.removeAllRanges();
                            selection.addRange(range);
                        } else {
                            // If no text nodes, just focus the element
                            prevPage.focus();
                        }
                    }
                }
            } else if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                saveDocument();
            }
        }
        
        // Find the last text node in an element
        function findLastTextNode(element) {
            if (!element) return null;
            
            // Create a tree walker and find the last text node
            const walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let lastNode = null;
            let currentNode = walker.nextNode();
            
            while (currentNode) {
                lastNode = currentNode;
                currentNode = walker.nextNode();
            }
            
            return lastNode;
        }
        
        // Check if cursor is at the start of the content
        function isAtStartOfContent(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            
            // We're at the start if we're at offset 0 of the first text node
            const firstTextNode = findFirstTextNode(element);
            if (firstTextNode) {
                return range.startContainer === firstTextNode && range.startOffset === 0;
            }
            
            return false;
        }
        
        // Find first text node in an element
        function findFirstTextNode(element) {
            if (!element) return null;
            
            // Create a tree walker and find the first text node
            const walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            return walker.nextNode();
        }
        
        // Check if cursor is at the end of the content
        function isAtEndOfContent(element) {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return false;
            
            const range = selection.getRangeAt(0);
            
            // We're at the end if we're at the end of the last text node
            const lastTextNode = findLastTextNode(element);
            if (lastTextNode) {
                return range.startContainer === lastTextNode && 
                       range.startOffset === lastTextNode.textContent.length;
            }
            
            return false;
        }
        
        // For debouncing updates
        let updateTimer = null;
        
        // Initialize with one empty page
        updatePages();
        
        // Function to notify content changes to the Python app
        function notifyContentChanged() {
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.contentChanged) {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }
        }
        
        // Function to save the document
        function saveDocument() {
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.saveRequested) {
                window.webkit.messageHandlers.saveRequested.postMessage('save');
            }
        }
        
        // Function to get all content as HTML
        function getContentAsHtml() {
            // Create a new HTML document
            let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Paginated Document</title>';
            html += '<style>';
            html += 'body { font-family: system-ui, -apple-system, sans-serif; margin: 40px; line-height: 1.5; }';
            html += '.page { width: ' + pageWidth + 'ch; min-height: ' + pageHeight + 'em; border: 1px solid #ccc; ';
            html += 'padding: 12px; margin-bottom: 30px; page-break-after: always; background: white; }';
            html += '.page-number { text-align: right; font-size: 12px; color: #999; margin-top: 10px; }';
            html += 'p { margin: 0 0 0.5em 0; }';
            html += '</style></head><body>';
            
            // Add the pages
            document.querySelectorAll('.page').forEach((page, index) => {
                const pageContent = page.querySelector('.page-content').innerHTML;
                html += '<div class="page">';
                html += pageContent;
                html += '<div class="page-number">' + (index + 1) + '</div>';
                html += '</div>';
            });
            
            html += '</body></html>';
            return html;
        }
        
        // Function to get all content as text
        function getContentAsText() {
            return text;
        }
        
        // Expose functions to be called from Python
        window.updateEditorSettings = updateEditorSettings;
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
    
    def on_page_size_changed(self, spin_button):
        # Get current width and height values
        width = self.width_adjustment.get_value()
        height = self.height_adjustment.get_value()
        
        # Update the editor settings
        js_script = f"updateEditorSettings({width}, {height});"
        self.webview.evaluate_javascript(js_script, -1, None, None, None, None, None, None)
    
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Register message handlers for communication between JS and Python
            user_content_manager = self.webview.get_user_content_manager()
            
            # Handler for content changes
            content_changed_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "contentChanged")
            if content_changed_handler:
                user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            

    def on_content_changed(self, manager, message):
        self.content_changed = True
    

    
    def show_notification(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
    
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
