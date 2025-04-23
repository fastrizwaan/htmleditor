#!/usr/bin/env python3
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit, GLib, Gio, GObject

class DocumentEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.documenteditor",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        # Create the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(800, 900)
        self.win.set_title("Document Editor")

        # Create the main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Create a toolbar for basic editing functions
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        
        # Buttons for the toolbar
        new_button = Gtk.Button(label="New")
        new_button.connect("clicked", self.on_new_clicked)
        toolbar.append(new_button)
        
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        toolbar.append(save_button)
        
        # Page size selector
        page_size_label = Gtk.Label(label="Page Size:")
        toolbar.append(page_size_label)
        
        self.page_size_combo = Gtk.DropDown()
        page_sizes = Gtk.StringList()
        page_sizes.append("US Letter (8.5\" × 11\")")
        page_sizes.append("A4 (210mm × 297mm)")
        self.page_size_combo.set_model(page_sizes)
        self.page_size_combo.connect("notify::selected", self.on_page_size_changed)
        toolbar.append(self.page_size_combo)
        
        main_box.append(toolbar)

        # Create the scrolled window to contain the WebKit view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)

        # Create the WebKit view
        self.web_view = WebKit.WebView()
        self.web_view.set_settings(WebKit.Settings())
        self.web_view.get_settings().set_enable_javascript(True)
        self.web_view.get_settings().set_javascript_can_access_clipboard(True)
        
        # Connect to the load-changed signal to inject our JavaScript
        self.web_view.connect("load-changed", self.on_load_changed)
        
        # Add the WebView to the scrolled window
        scrolled_window.set_child(self.web_view)
        
        # Add the scrolled window to the main box
        main_box.append(scrolled_window)
        
        # Add status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_bar.set_margin_start(6)
        status_bar.set_margin_end(6)
        status_bar.set_margin_top(6)
        status_bar.set_margin_bottom(6)
        
        self.page_count_label = Gtk.Label(label="Page: 1 of 1")
        status_bar.append(self.page_count_label)
        
        main_box.append(status_bar)
        
        # Set the main box as the content of the window
        self.win.set_content(main_box)
        
        # Load the initial HTML content
        self.load_editor()
        
        # Show the window
        self.win.present()

    def load_editor(self):
        # HTML template for the editor with CSS for pagination
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Document Editor</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Liberation Sans', Arial, sans-serif;
                    background-color: #f0f0f0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px;
                }
                
                #editor-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    width: 100%;
                    gap: 30px;
                }
                
                .page {
                    background-color: white;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                    padding: 1in;
                    margin-bottom: 20px;
                    width: 8.5in;
                    height: 11in;
                    box-sizing: border-box;
                    position: relative;
                    overflow: hidden;
                }
                
                .page-content {
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    outline: none;
                    line-height: 1.5;
                }
                
                /* US Letter dimensions: 8.5in x 11in */
                .us-letter {
                    width: 8.5in;
                    height: 11in;
                }
                
                /* A4 dimensions: 210mm x 297mm */
                .a4 {
                    width: 210mm;
                    height: 297mm;
                }
                
                .page-number {
                    position: absolute;
                    bottom: 0.25in;
                    right: 0.25in;
                    font-size: 10pt;
                    color: #888;
                }
            </style>
        </head>
        <body>
            <div id="editor-container">
                <!-- Pages will be added dynamically -->
            </div>
            
            <script>
                // Initialize the editor
                document.addEventListener('DOMContentLoaded', initEditor);
                
                let pageSize = 'us-letter';
                let pageCount = 1;
                let currentPage = 1;
                
                function initEditor() {
                    // Create the first page
                    createPage();
                    
                    // Set focus to the first page
                    document.querySelector('.page-content').focus();
                    
                    // Update page count
                    updatePageCount();
                }
                
                function createPage() {
                    const container = document.getElementById('editor-container');
                    const pageNumber = container.children.length + 1;
                    
                    // Create a new page element
                    const page = document.createElement('div');
                    page.className = `page ${pageSize}`;
                    page.dataset.pageNumber = pageNumber;
                    
                    // Create the editable content area
                    const content = document.createElement('div');
                    content.className = 'page-content';
                    content.contentEditable = true;
                    content.dataset.pageNumber = pageNumber;
                    content.addEventListener('input', handleInput);
                    content.addEventListener('keydown', handleKeyDown);
                    
                    // Create page number indicator
                    const pageNumberIndicator = document.createElement('div');
                    pageNumberIndicator.className = 'page-number';
                    pageNumberIndicator.textContent = pageNumber;
                    
                    // Add elements to the page
                    page.appendChild(content);
                    page.appendChild(pageNumberIndicator);
                    
                    // Add the page to the container
                    container.appendChild(page);
                    
                    pageCount = container.children.length;
                    return content;
                }
                
                function handleInput(event) {
                    const currentPageContent = event.target;
                    const currentPageElement = currentPageContent.parentElement;
                    
                    // Check if text overflows the current page
                    if (isContentOverflowing(currentPageContent)) {
                        const overflowText = moveOverflowToNextPage(currentPageContent);
                        updatePageCount();
                    }
                }
                
                function handleKeyDown(event) {
                    const currentPageContent = event.target;
                    const currentPageElement = currentPageContent.parentElement;
                    const pageNumber = parseInt(currentPageElement.dataset.pageNumber);
                    
                    // Handle backspace at the beginning of a page (except the first page)
                    if (event.key === 'Backspace' && pageNumber > 1) {
                        const selection = window.getSelection();
                        if (selection.rangeCount > 0) {
                            const range = selection.getRangeAt(0);
                            if (range.startOffset === 0 && range.startContainer === currentPageContent || 
                                (range.startContainer.nodeType === Node.TEXT_NODE && 
                                 range.startOffset === 0 && 
                                 range.startContainer.parentNode === currentPageContent && 
                                 range.startContainer === currentPageContent.firstChild)) {
                                
                                event.preventDefault();
                                
                                // Get the previous page
                                const prevPageContent = document.querySelector(`.page-content[data-page-number="${pageNumber - 1}"]`);
                                
                                // Move caret to the end of the previous page
                                prevPageContent.focus();
                                
                                // Create a range at the end of the previous page
                                const prevRange = document.createRange();
                                prevRange.selectNodeContents(prevPageContent);
                                prevRange.collapse(false); // collapse to end
                                
                                // Set the selection
                                selection.removeAllRanges();
                                selection.addRange(prevRange);
                                
                                // Merge the content of the current page into the previous page
                                prevPageContent.innerHTML += currentPageContent.innerHTML;
                                
                                // Remove the current page if it's empty or after merging
                                currentPageElement.remove();
                                
                                // Rebalance pages
                                rebalancePages();
                                
                                // Update page count
                                updatePageCount();
                            }
                        }
                    }
                }
                
                function isContentOverflowing(element) {
                    return element.scrollHeight > element.clientHeight;
                }
                
                function moveOverflowToNextPage(currentPageContent) {
                    // Find or create the next page
                    const currentPageNumber = parseInt(currentPageContent.dataset.pageNumber);
                    let nextPageContent = document.querySelector(`.page-content[data-page-number="${currentPageNumber + 1}"]`);
                    
                    if (!nextPageContent) {
                        nextPageContent = createPage();
                    }
                    
                    // First, we need to find the point where we should split the content
                    const range = document.createRange();
                    range.selectNodeContents(currentPageContent);
                    
                    let start = 0;
                    let end = currentPageContent.textContent.length;
                    let mid;
                    let tempRange = document.createRange();
                    
                    // Binary search to find the overflow point
                    while (start < end) {
                        mid = Math.floor((start + end) / 2);
                        
                        // Try to set range to contain text from start to mid
                        try {
                            // This is simplified - in a real app, you'd need a more robust algorithm
                            // that accounts for nested nodes, not just text
                            tempRange.setStart(currentPageContent.firstChild || currentPageContent, 0);
                            tempRange.setEnd(currentPageContent.firstChild || currentPageContent, mid);
                            
                            if (tempRange.getBoundingClientRect().height > currentPageContent.clientHeight) {
                                end = mid;
                            } else {
                                start = mid + 1;
                            }
                        } catch (e) {
                            // Handle error (e.g., out of bounds)
                            break;
                        }
                    }
                    
                    // Once we've found the split point, we move the content
                    const splitPoint = start - 1;
                    
                    // This is a simplified approach - a real implementation would need
                    // to handle HTML structure more carefully
                    if (currentPageContent.firstChild && currentPageContent.firstChild.nodeType === Node.TEXT_NODE) {
                        const text = currentPageContent.firstChild.textContent;
                        const firstHalf = text.substring(0, splitPoint);
                        const secondHalf = text.substring(splitPoint);
                        
                        currentPageContent.firstChild.textContent = firstHalf;
                        
                        // Prepend the overflow to the next page
                        if (nextPageContent.firstChild && nextPageContent.firstChild.nodeType === Node.TEXT_NODE) {
                            nextPageContent.firstChild.textContent = secondHalf + nextPageContent.firstChild.textContent;
                        } else {
                            nextPageContent.textContent = secondHalf + (nextPageContent.textContent || "");
                        }
                    }
                    
                    // Check if the next page now overflows
                    if (isContentOverflowing(nextPageContent)) {
                        moveOverflowToNextPage(nextPageContent);
                    }
                }
                
                function rebalancePages() {
                    const pages = document.querySelectorAll('.page-content');
                    
                    // Update page numbers
                    pages.forEach((page, index) => {
                        page.dataset.pageNumber = index + 1;
                        page.parentElement.dataset.pageNumber = index + 1;
                        page.parentElement.querySelector('.page-number').textContent = index + 1;
                    });
                    
                    // Check each page for overflow and fix it
                    pages.forEach(page => {
                        if (isContentOverflowing(page)) {
                            moveOverflowToNextPage(page);
                        }
                    });
                    
                    // Remove empty pages (except the first one)
                    pages.forEach((page, index) => {
                        if (index > 0 && page.textContent.trim() === '') {
                            page.parentElement.remove();
                        }
                    });
                    
                    // Final update of page numbers
                    const updatedPages = document.querySelectorAll('.page-content');
                    updatedPages.forEach((page, index) => {
                        page.dataset.pageNumber = index + 1;
                        page.parentElement.dataset.pageNumber = index + 1;
                        page.parentElement.querySelector('.page-number').textContent = index + 1;
                    });
                    
                    pageCount = updatedPages.length;
                }
                
                function updatePageCount() {
                    // Count the pages
                    const pageCount = document.querySelectorAll('.page').length;
                    const currentPageContent = document.activeElement;
                    let currentPage = 1;
                    
                    if (currentPageContent && currentPageContent.classList.contains('page-content')) {
                        currentPage = parseInt(currentPageContent.dataset.pageNumber);
                    }
                    
                    // Send a message to the GTK app
                    // Use try-catch to handle different WebKit versions
                    try {
                        // Try modern WebKit API
                        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.pageCount) {
                            window.webkit.messageHandlers.pageCount.postMessage(JSON.stringify({
                                currentPage: currentPage,
                                totalPages: pageCount
                            }));
                        } else {
                            console.log(`Page count update: ${currentPage} of ${pageCount}`);
                        }
                    } catch(e) {
                        console.log(`Error updating page count: ${e.message}`);
                    }
                }
                
                function setPageSize(size) {
                    pageSize = size;
                    const pages = document.querySelectorAll('.page');
                    
                    pages.forEach(page => {
                        // Remove all page size classes
                        page.classList.remove('us-letter', 'a4');
                        // Add the selected page size class
                        page.classList.add(size);
                    });
                    
                    // Rebalance pages to handle content overflow with new size
                    rebalancePages();
                }
                
                // Function to get the document content
                function getDocumentContent() {
                    const content = [];
                    const pages = document.querySelectorAll('.page-content');
                    
                    pages.forEach(page => {
                        content.push(page.innerHTML);
                    });
                    
                    return JSON.stringify(content);
                }
                
                // Function to set the document content
                function setDocumentContent(content) {
                    try {
                        const pages = JSON.parse(content);
                        const container = document.getElementById('editor-container');
                        
                        // Clear existing pages
                        container.innerHTML = '';
                        
                        // Create new pages with the loaded content
                        pages.forEach((pageContent, index) => {
                            const page = createPage();
                            page.innerHTML = pageContent;
                        });
                        
                        // Focus the first page
                        document.querySelector('.page-content').focus();
                        
                        // Update page count
                        updatePageCount();
                        
                        return true;
                    } catch (e) {
                        console.error('Error setting document content:', e);
                        return false;
                    }
                }
                
                // Make functions available to WebKit message handlers
                window.getDocumentContent = getDocumentContent;
                window.setDocumentContent = setDocumentContent;
                window.setPageSize = setPageSize;
            </script>
        </body>
        </html>
        """
        
        # Load the HTML content
        self.web_view.load_html(html, "file:///")

    def on_load_changed(self, web_view, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Set up message handlers for communication between JS and GTK
            self.setup_message_handlers()

    def setup_message_handlers(self):
        # Get the user content manager
        content_manager = self.web_view.get_user_content_manager()
        if not content_manager:
            content_manager = WebKit.UserContentManager()
            self.web_view.set_user_content_manager(content_manager)
        
        # Register script message handler - the API changed in WebKit 6
        try:
            # Try the WebKit 6 approach
            if hasattr(content_manager, 'register_script_message_handler_with_world'):
                # WebKit 6 API
                content_manager.register_script_message_handler_with_world('pageCount', 'main')
                content_manager.connect('script-message-received::pageCount', self.on_page_count_message)
            else:
                # Older WebKit API
                content_manager.register_script_message_handler('pageCount')
                content_manager.connect('script-message-received::pageCount', self.on_page_count_message)
        except Exception as e:
            print(f"Error setting up message handlers: {e}")

    def on_page_count_message(self, content_manager, message):
        # Parse the JSON message from the WebView
        # The message parameter is the JS value directly in WebKit 6
        try:
            # Get the message data as JSON
            if hasattr(message, 'get_js_value'):
                # Older WebKit versions
                js_result = message.get_js_value()
                if js_result.is_object():
                    current_page = js_result.object_get_property("currentPage").to_int32()
                    total_pages = js_result.object_get_property("totalPages").to_int32()
            else:
                # WebKit 6 approach
                data_json = message.to_string()
                import json
                data = json.loads(data_json)
                current_page = data.get('currentPage', 1)
                total_pages = data.get('totalPages', 1)
            
            # Update the status bar
            self.page_count_label.set_text(f"Page: {current_page} of {total_pages}")
        except Exception as e:
            print(f"Error parsing page count message: {e}")
            self.page_count_label.set_text("Page: 1 of 1")

    def on_new_clicked(self, button):
        # Confirm with user
        dialog = Adw.MessageDialog.new(self.win, 
                                     "Create New Document",
                                     "Are you sure you want to create a new document? Any unsaved changes will be lost.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("ok", "New Document")
        dialog.set_default_response("cancel")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_new_dialog_response)
        dialog.present()

    def on_new_dialog_response(self, dialog, response):
        if response == "ok":
            # Reload the editor
            self.load_editor()

    def on_save_clicked(self, button):
        # Run JavaScript to get the document content
        # Handle both old and new WebKit API
        try:
            if hasattr(self.web_view, 'evaluate_javascript'):
                # WebKit 6 approach
                self.web_view.evaluate_javascript(
                    "getDocumentContent()",
                    -1, None, None, None,
                    self.on_get_document_js_finish
                )
            else:
                # Newer approach with promises
                self.web_view.run_javascript(
                    "getDocumentContent()",
                    None,
                    self.on_get_document_js_finish_new
                )
        except Exception as e:
            print(f"Error running JavaScript: {e}")
            # Show error dialog
            error_dialog = Adw.MessageDialog.new(
                self.win, 
                "JavaScript Error",
                f"Failed to get document content: {str(e)}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def on_get_document_js_finish(self, web_view, result, user_data):
        try:
            js_result = web_view.evaluate_javascript_finish(result)
            if js_result and js_result.is_string():
                content = js_result.to_string()
                self.show_save_dialog(content)
        except Exception as e:
            print(f"Error getting document content: {e}")
            
    def on_get_document_js_finish_new(self, web_view, result):
        try:
            js_result = web_view.run_javascript_finish(result)
            if js_result:
                js_value = js_result.get_js_value()
                if js_value and js_value.is_string():
                    content = js_value.to_string()
                    self.show_save_dialog(content)
        except Exception as e:
            print(f"Error getting document content (new API): {e}")
            
    def show_save_dialog(self, content):
        # Create file save dialog
        dialog = Gtk.FileDialog()
        dialog.set_title("Save Document")
        
        # Set up file filter for document files
        filter = Gtk.FileFilter()
        filter.set_name("Document Files")
        filter.add_pattern("*.doc")
        filter.add_pattern("*.txt")
        
        dialog.save(self.win, None, self.on_save_dialog_response, content)

    def on_save_dialog_response(self, dialog, result, content):
        try:
            file = dialog.save_finish(result)
            if file:
                file_path = file.get_path()
                
                # Save the content to the file
                with open(file_path, 'w') as f:
                    f.write(content)
                
                # Show a success message
                toast = Adw.Toast.new("Document saved successfully")
                toast.set_timeout(3)
                toast_overlay = self.win.get_content().get_parent()
                if isinstance(toast_overlay, Adw.ToastOverlay):
                    toast_overlay.add_toast(toast)
        except Exception as e:
            print(f"Error saving file: {e}")
            # Show an error message
            error_dialog = Adw.MessageDialog.new(self.win, 
                                               "Save Error",
                                               f"Failed to save the document: {str(e)}")
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def on_page_size_changed(self, combo, gparam):
        selected_index = combo.get_selected()
        page_size = "us-letter" if selected_index == 0 else "a4"
        
        # Run JavaScript to change the page size
        # Handle both old and new WebKit API
        try:
            if hasattr(self.web_view, 'evaluate_javascript'):
                # WebKit 6 approach
                self.web_view.evaluate_javascript(
                    f"setPageSize('{page_size}')", 
                    -1, None, None, None, None
                )
            else:
                # Newer approach with promises
                self.web_view.run_javascript(
                    f"setPageSize('{page_size}')",
                    None,
                    None  # No callback needed for this operation
                )
        except Exception as e:
            print(f"Error changing page size: {e}")


if __name__ == "__main__":
    app = DocumentEditor()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
