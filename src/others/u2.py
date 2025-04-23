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
        # Create the application window
        self.win = Adw.ApplicationWindow(application=app, default_width=800, default_height=900)
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
        
        # Add format options
        format_button = Gtk.MenuButton()
        format_button.set_label("Format")
        format_button.set_tooltip_text("Text formatting options")
        format_menu = Gtk.PopoverMenu()
        format_button.set_popover(format_menu)

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
            padding: 0;
            font-family: 'Noto Sans', Arial, sans-serif;
            overflow-x: hidden;
            background-color: #f0f0f0;
        }
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 30px;
            padding: 40px 20px;
            min-height: 100vh;
        }
        .page {
            width: 500px;
            height: 700px;
            border: 1px solid #ccc;
            padding: 50px;
            box-sizing: border-box;
            line-height: 1.5;
            overflow: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            position: relative;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background-color: white;
            user-select: text;
            cursor: text;
            font-size: 14px;
        }
        .page:focus {
            outline: 2px solid #4285f4;
        }
        .page-number {
            position: absolute;
            bottom: 20px;
            right: 20px;
            font-size: 12px;
            color: #888;
            user-select: none;
        }
        .toolbar {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            padding: 5px 10px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }
        .toolbar button {
            background: none;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
        }
        .toolbar button:hover {
            background: #f0f0f0;
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <button id="btnBold" title="Bold (Ctrl+B)">B</button>
        <button id="btnItalic" title="Italic (Ctrl+I)">I</button>
        <button id="btnUnderline" title="Underline (Ctrl+U)">U</button>
    </div>
    <div id="editor-container"></div>

    <script>
        // Editor state
        let textArray = []; // Array of words that form the document
        let pages = []; // Array of page objects to track content and state
        const pageWidth = 500; // pixels
        const pageHeight = 700; // pixels
        const padding = 50; // pixels
        const container = document.getElementById('editor-container');
        let cursorPositionInfo = { pageIndex: 0, wordIndex: 0, charIndex: 0 };
        let isEditingInProgress = false;
        
        // Initialize toolbar
        const toolbar = document.querySelector('.toolbar');
        const btnBold = document.getElementById('btnBold');
        const btnItalic = document.getElementById('btnItalic');
        const btnUnderline = document.getElementById('btnUnderline');
        
        btnBold.addEventListener('click', () => {
            document.execCommand('bold', false, null);
        });
        
        btnItalic.addEventListener('click', () => {
            document.execCommand('italic', false, null);
        });
        
        btnUnderline.addEventListener('click', () => {
            document.execCommand('underline', false, null);
        });
        
        // Function to initialize the editor with empty content or load content
        function initEditor(initialContent = '') {
            if (initialContent) {
                // Split content into words for pagination
                textArray = initialContent.split(/\\s+/);
            } else {
                textArray = [''];  // Start with an empty word
            }
            
            createPage(); // Create the first page
            paginateText(); // Distribute text across pages
        }
        
        // Function to create a new page
        function createPage() {
            const page = document.createElement('div');
            page.className = 'page';
            page.contentEditable = 'true';
            page.spellcheck = false;
            
            const pageNumber = document.createElement('div');
            pageNumber.className = 'page-number';
            pageNumber.textContent = (document.querySelectorAll('.page').length + 1).toString();
            page.appendChild(pageNumber);
            
            // Store metadata about this page
            const pageIndex = pages.length;
            pages.push({
                element: page,
                startWordIndex: pageIndex === 0 ? 0 : null, // Will be set during pagination
                endWordIndex: null,                         // Will be set during pagination
                content: ''                                 // Will be updated during pagination
            });
            
            // Handle page editing events
            page.dataset.pageIndex = pageIndex;
            page.addEventListener('input', handlePageInput);
            page.addEventListener('keydown', handleKeyDown);
            page.addEventListener('mouseup', updateSelection);
            page.addEventListener('keyup', updateSelection);
            page.addEventListener('focus', () => {
                toolbar.classList.remove('hidden');
            });
            page.addEventListener('blur', () => {
                setTimeout(() => {
                    if (!document.activeElement.classList.contains('page')) {
                        toolbar.classList.add('hidden');
                    }
                }, 100);
            });
            
            container.appendChild(page);
            return page;
        }
        
        // Function to distribute text across pages
        function paginateText() {
            if (isEditingInProgress) return;
            isEditingInProgress = true;
            
            // Save cursor position if possible
            saveCursorPosition();
            
            // Clear all pages except the first one
            const existingPages = document.querySelectorAll('.page');
            for (let i = 1; i < existingPages.length; i++) {
                container.removeChild(existingPages[i]);
            }
            pages.splice(1); // Keep only the first page in our pages array
            
            // Reset the first page
            const firstPage = existingPages[0];
            firstPage.innerHTML = '';
            const pageNumber = document.createElement('div');
            pageNumber.className = 'page-number';
            pageNumber.textContent = '1';
            firstPage.appendChild(pageNumber);
            
            pages[0].startWordIndex = 0;
            pages[0].endWordIndex = null;
            pages[0].content = '';
            
            let currentPage = firstPage;
            let currentPageIndex = 0;
            let wordIndex = 0;
            
            // Function to check if adding a word would overflow the page
            function wouldOverflow(page, word) {
                const originalContent = page.innerHTML;
                
                // Add the word to check overflow
                const textNode = document.createTextNode(word + ' ');
                page.appendChild(textNode);
                
                // Check if it overflows
                const overflows = page.scrollHeight > page.clientHeight;
                
                // Restore original content
                page.innerHTML = originalContent;
                
                return overflows;
            }
            
            // Add words to pages until all words are distributed
            while (wordIndex < textArray.length) {
                const word = textArray[wordIndex];
                
                // Check if adding this word would cause overflow
                if (wouldOverflow(currentPage, pages[currentPageIndex].content + word)) {
                    // Finish current page
                    pages[currentPageIndex].endWordIndex = wordIndex - 1;
                    
                    // Create a new page
                    currentPage = createPage();
                    currentPageIndex = pages.length - 1;
                    pages[currentPageIndex].startWordIndex = wordIndex;
                    pages[currentPageIndex].content = '';
                }
                
                // Add word to current page
                pages[currentPageIndex].content += (pages[currentPageIndex].content ? ' ' : '') + word;
                currentPage.insertBefore(document.createTextNode(word + ' '), currentPage.querySelector('.page-number'));
                
                wordIndex++;
            }
            
            // Set endWordIndex for the last page
            pages[currentPageIndex].endWordIndex = textArray.length - 1;
            
            // Restore cursor position if possible
            restoreCursorPosition();
            
            // Notify that content has changed
            notifyContentChanged();
            
            isEditingInProgress = false;
        }
        
        // Function to handle input in a page
        function handlePageInput(e) {
            // Prevent recursive calls during pagination
            if (isEditingInProgress) return;
            isEditingInProgress = true;
            
            // Get the updated text from all pages
            updateTextArrayFromPages();
            
            // Repaginate with a small delay to allow for continuous typing
            clearTimeout(window.paginationTimer);
            window.paginationTimer = setTimeout(() => {
                paginateText();
                isEditingInProgress = false;
            }, 300);
        }
        
        // Function to update text array from all pages
        function updateTextArrayFromPages() {
            let combinedText = '';
            
            // Collect text content from all pages, excluding page numbers
            document.querySelectorAll('.page').forEach(page => {
                // Create a clone without page number
                const clone = page.cloneNode(true);
                const pageNumber = clone.querySelector('.page-number');
                if (pageNumber) {
                    clone.removeChild(pageNumber);
                }
                combinedText += clone.textContent + ' ';
            });
            
            // Split by whitespace to get words
            textArray = combinedText.trim().split(/\\s+/);
            
            // Handle empty document case
            if (textArray.length === 1 && textArray[0] === '') {
                textArray = [''];
            }
        }
        
        // Save cursor position information
        function saveCursorPosition() {
            const selection = window.getSelection();
            if (!selection.rangeCount) return;
            
            const range = selection.getRangeAt(0);
            const startContainer = range.startContainer;
            
            // Find which page contains the selection
            let currentPage = startContainer.nodeType === 3 ? 
                startContainer.parentNode.closest('.page') : 
                startContainer.closest('.page');
                
            if (!currentPage) return;
            
            const pageIndex = parseInt(currentPage.dataset.pageIndex);
            if (isNaN(pageIndex)) return;
            
            // Find which word the cursor is in
            const pageStartWordIndex = pages[pageIndex].startWordIndex;
            
            // This is a simple approximation - in a real editor you'd need more sophisticated tracking
            const textBeforeCursor = getTextBeforeCursor(range, currentPage);
            const wordsBeforeCursor = textBeforeCursor.split(/\\s+/).length - 1;
            
            cursorPositionInfo = {
                pageIndex: pageIndex,
                wordIndex: pageStartWordIndex + wordsBeforeCursor,
                charOffset: range.startOffset
            };
        }
        
        // Helper to get text before cursor in a page
        function getTextBeforeCursor(range, page) {
            const tempRange = range.cloneRange();
            tempRange.selectNodeContents(page);
            tempRange.setEnd(range.startContainer, range.startOffset);
            return tempRange.toString();
        }
        
        // Restore cursor position after pagination
        function restoreCursorPosition() {
            if (!cursorPositionInfo) return;
            
            // Find which page contains the target word
            let targetPage = null;
            let targetPageIndex = -1;
            
            for (let i = 0; i < pages.length; i++) {
                if (pages[i].startWordIndex <= cursorPositionInfo.wordIndex && 
                    pages[i].endWordIndex >= cursorPositionInfo.wordIndex) {
                    targetPage = pages[i].element;
                    targetPageIndex = i;
                    break;
                }
            }
            
            if (!targetPage) {
                // If we can't find the right page, focus the last page
                const lastPage = document.querySelector('.page:last-child');
                if (lastPage) {
                    lastPage.focus();
                    
                    // Move cursor to end of content
                    const selection = window.getSelection();
                    const range = document.createRange();
                    const pageNumber = lastPage.querySelector('.page-number');
                    
                    if (pageNumber && pageNumber.previousSibling) {
                        range.setStartAfter(pageNumber.previousSibling);
                    } else {
                        range.setStart(lastPage, 0);
                    }
                    
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
                return;
            }
            
            // Focus the target page
            targetPage.focus();
            
            // Approximate cursor position - this is simplified
            // In a real implementation, you would need more precise cursor positioning
            try {
                const relativeWordIndex = cursorPositionInfo.wordIndex - pages[targetPageIndex].startWordIndex;
                
                // Simple approach: move to the nth text node
                // This is an approximation and would need refinement in a real editor
                const textNodes = [];
                const walker = document.createTreeWalker(targetPage, NodeFilter.SHOW_TEXT);
                let node;
                while (node = walker.nextNode()) {
                    if (node.parentNode !== targetPage.querySelector('.page-number')) {
                        textNodes.push(node);
                    }
                }
                
                const selection = window.getSelection();
                const range = document.createRange();
                
                if (textNodes.length > 0) {
                    // Simple approximation - select position in a specific text node
                    const nodeIndex = Math.min(relativeWordIndex, textNodes.length - 1);
                    const targetNode = textNodes[nodeIndex];
                    const offset = Math.min(cursorPositionInfo.charOffset, targetNode.length);
                    
                    range.setStart(targetNode, offset);
                } else {
                    // If no text nodes, set cursor at beginning of page
                    range.setStart(targetPage, 0);
                }
                
                selection.removeAllRanges();
                selection.addRange(range);
            } catch (e) {
                console.error('Error restoring cursor:', e);
                // Fallback: just focus the page
                targetPage.focus();
            }
        }
        
        // Handle selection updates
        function updateSelection() {
            saveCursorPosition();
        }
        
        // Handle special key presses
        function handleKeyDown(e) {
            // Navigate between pages with arrow keys
            if (e.key === 'ArrowDown' && e.ctrlKey) {
                e.preventDefault();
                navigateToNextPage();
            } else if (e.key === 'ArrowUp' && e.ctrlKey) {
                e.preventDefault();
                navigateToPreviousPage();
            } else if (e.key === 'b' && e.ctrlKey) {
                e.preventDefault();
                document.execCommand('bold', false, null);
            } else if (e.key === 'i' && e.ctrlKey) {
                e.preventDefault();
                document.execCommand('italic', false, null);
            } else if (e.key === 'u' && e.ctrlKey) {
                e.preventDefault();
                document.execCommand('underline', false, null);
            } else if (e.key === 's' && e.ctrlKey) {
                e.preventDefault();
                window.webkit.messageHandlers.saveRequested.postMessage('save');
            }
        }
        
        // Navigation functions
        function navigateToNextPage() {
            const currentPage = document.activeElement;
            if (!currentPage || !currentPage.classList.contains('page')) return;
            
            const currentIndex = parseInt(currentPage.dataset.pageIndex);
            const nextPage = document.querySelector(`.page[data-page-index="${currentIndex + 1}"]`);
            
            if (nextPage) {
                nextPage.focus();
                // Set cursor to beginning of page
                const selection = window.getSelection();
                const range = document.createRange();
                const firstChild = getFirstTextNode(nextPage);
                
                if (firstChild) {
                    range.setStart(firstChild, 0);
                } else {
                    range.setStart(nextPage, 0);
                }
                
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }
        
        function navigateToPreviousPage() {
            const currentPage = document.activeElement;
            if (!currentPage || !currentPage.classList.contains('page')) return;
            
            const currentIndex = parseInt(currentPage.dataset.pageIndex);
            const prevPage = document.querySelector(`.page[data-page-index="${currentIndex - 1}"]`);
            
            if (prevPage) {
                prevPage.focus();
                // Set cursor to end of page content
                const selection = window.getSelection();
                const range = document.createRange();
                const lastTextNode = getLastTextNode(prevPage);
                
                if (lastTextNode) {
                    range.setStart(lastTextNode, lastTextNode.length);
                } else {
                    range.setStart(prevPage, 0);
                }
                
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }
        
        // Helper functions to get first/last text nodes
        function getFirstTextNode(element) {
            const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
            return walker.nextNode();
        }
        
        function getLastTextNode(element) {
            const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
            let lastNode = null;
            let node;
            
            while (node = walker.nextNode()) {
                if (node.parentNode !== element.querySelector('.page-number')) {
                    lastNode = node;
                }
            }
            
            return lastNode;
        }
        
        // Notify content changes to the Python app
        function notifyContentChanged() {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        
        // Function to get all content as HTML with pagination preserved
        function getContentAsHtml() {
            const pagesElems = document.querySelectorAll('.page');
            let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Saved Document</title>';
            html += '<style>body{margin:20px;font-family:sans-serif;}';
            html += '.page{width:500px;height:700px;border:1px solid #ccc;padding:50px;box-sizing:border-box;';
            html += 'line-height:1.5;overflow:hidden;white-space:pre-wrap;word-wrap:break-word;';
            html += 'margin:20px auto;page-break-after:always;position:relative;box-shadow:0 2px 10px rgba(0,0,0,0.1);}';
            html += '.page-number{position:absolute;bottom:20px;right:20px;font-size:12px;color:#888;}</style></head><body>';
            
            html += '<div class="container">';
            pagesElems.forEach((page, index) => {
                html += '<div class="page">';
                
                // Clone the page without the page number
                const clone = page.cloneNode(true);
                const pageNumber = clone.querySelector('.page-number');
                if (pageNumber) {
                    clone.removeChild(pageNumber);
                }
                
                html += clone.innerHTML;
                html += `<div class="page-number">${index + 1}</div>`;
                html += '</div>';
            });
            html += '</div></body></html>';
            
            return html;
        }
        
        // Function to get all content as plain text
        function getContentAsText() {
            let text = '';
            document.querySelectorAll('.page').forEach(page => {
                // Clone the page without the page number
                const clone = page.cloneNode(true);
                const pageNumber = clone.querySelector('.page-number');
                if (pageNumber) {
                    clone.removeChild(pageNumber);
                }
                text += clone.textContent + '\\n\\n';
            });
            return text.trim();
        }
        
        // Initialize with empty content
        initEditor();
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Register message handlers for communication between JS and Python
            user_content_manager = self.webview.get_user_content_manager()
            
            # Handler for content changes
            content_changed_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "contentChanged")
            if content_changed_handler:
                user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            
            # Handler for save requests
            save_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "saveRequested")
            if save_handler:
                user_content_manager.connect("script-message-received::saveRequested", self.on_save_requested)
    
    def on_content_changed(self, manager, message):
        self.content_changed = True
    
    def on_save_requested(self, manager, message):
        self.on_save_clicked(None)
    
    def on_save_clicked(self, button):
        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self.win,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.ACCEPT
        )
        dialog.set_current_name("document.html")
        
        # Set up filters
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        dialog.add_filter(filter_html)
        
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)
        
        dialog.connect("response", self.on_save_dialog_response)
        dialog.present()
    
    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            file_filter = dialog.get_filter()
            
            if file_filter.get_name() == "HTML files":
                # Get HTML content from WebView
                self.webview.evaluate_javascript("getContentAsHtml();", -1, None, None, None, None, self.save_html_callback, file_path)
            else:
                # Get plain text content from WebView
                self.webview.evaluate_javascript("getContentAsText();", -1, None, None, None, None, self.save_text_callback, file_path)
        
        dialog.destroy()
    
    def save_html_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                html_content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    f.write(html_content)
                
                self.show_notification("Document saved as HTML")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")
    
    def save_text_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                text_content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    f.write(text_content)
                
                self.show_notification("Document saved as text")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")
    
    def show_notification(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        # In GTK4/libadwaita, we would add a ToastOverlay to show toasts properly
        # For simplicity in this example, we'll just print the message
        print(message)
    
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
