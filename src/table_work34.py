#!/usr/bin/env python3
import sys
import gi
import re
import os

# Hardware Acclerated Rendering (0); Software Rendering (1)
os.environ['WEBKIT_DISABLE_COMPOSITING_MODE'] = '1'

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gdk, WebKit, GLib, Gio, Pango, PangoCairo, Gdk


class HTMLEditorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='io.github.fastrizwaan.htmleditor',
                        flags=Gio.ApplicationFlags.HANDLES_OPEN,
                        **kwargs)
        self.windows = []  # Track all open windows
        self.window_buttons = {}  # Track window menu buttons {window_id: button}
        self.connect('activate', self.on_activate)

        
        # Window properties (migrated from HTMLEditorWindow)
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None
        
 
        
    def do_startup(self):
        """Initialize application and set up CSS provider"""
        Adw.Application.do_startup(self)
        
        # Set up CSS provider
        self.setup_css_provider()
        
  

    def setup_css_provider(self):
        """Set up CSS provider for custom styling"""
        self.css_provider = Gtk.CssProvider()
        
        css_data = b"""
        .flat { background: none; }
        .flat:hover { background: rgba(127, 127, 127, 0.25); }
        .flat:checked { background: rgba(127, 127, 127, 0.25); }

        """
        
        # Load the CSS data
        try:
            self.css_provider.load_from_data(css_data)
        except Exception as e:
            print(f"Error loading CSS data: {e}")
            return
        
        # Apply the CSS provider using the appropriate method based on GTK version
        try:
            # GTK4 method (modern approach)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except (AttributeError, TypeError) as e:
            # Fallback for GTK3 if the application is using an older version
            try:
                screen = Gdk.Screen.get_default()
                Gtk.StyleContext.add_provider_for_screen(
                    screen,
                    self.css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e2:
                print(f"Error applying CSS provider: {e2}")
        
    def on_activate(self, app):
        """Handle application activation (new window)"""
        win = self.create_window()
        win.present()
        
        # Set focus after window is shown - this is crucial
        GLib.timeout_add(500, lambda: self.set_initial_focus(win))
        
                    
    def setup_headerbar_content(self, win):
        """Create simplified headerbar content (menu and window buttons)"""
        win.headerbar.set_margin_top(0)
        win.headerbar.set_margin_bottom(0)

        
        # Set up the window title widget (can be customized further)
        title_widget = Adw.WindowTitle()
        title_widget.set_title("Untitled  - HTML Editor")
        win.title_widget = title_widget  # Store for later updates
        
        # Save reference to update title 
        win.headerbar.set_title_widget(title_widget)
        

            
    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        # --- Insert operations group (Table, Text Box, Image) ---
        insert_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        insert_group.add_css_class("linked")  # Apply linked styling
        insert_group.set_margin_start(6)

        # Insert table button
        table_button = Gtk.Button(icon_name="table-symbolic")  # Use a standard table icon
        table_button.set_size_request(40, 36)
        table_button.set_tooltip_text("Insert Table")
        table_button.connect("clicked", lambda btn: self.on_insert_table_clicked(win, btn))

        # Insert text box button
        text_box_button = Gtk.Button(icon_name="insert-text-symbolic")
        text_box_button.set_size_request(40, 36)
        text_box_button.set_tooltip_text("Insert Text Box")
        text_box_button.connect("clicked", lambda btn: self.on_insert_text_box_clicked(win, btn))

        # Insert image button
        image_button = Gtk.Button(icon_name="insert-image-symbolic")
        image_button.set_size_request(40, 36)
        image_button.set_tooltip_text("Insert Image")
        image_button.connect("clicked", lambda btn: self.on_insert_image_clicked(win, btn))

        # Insert link button
        link_button = Gtk.Button(icon_name="insert-link-symbolic")
        link_button.set_size_request(40, 36)
        link_button.set_tooltip_text("Insert link")
        link_button.connect("clicked", lambda btn: self.on_insert_link_clicked(win, btn))

        # Add buttons to insert group
        insert_group.append(table_button)
        insert_group.append(text_box_button)
        insert_group.append(image_button)
        insert_group.append(link_button)
        # Add insert group to toolbar
        file_toolbar.append(insert_group)

        # --- Add the Show HTML button ---
        show_html_button = Gtk.Button(icon_name="text-x-generic-symbolic")
        show_html_button.set_tooltip_text("Show HTML")
        show_html_button.set_margin_start(10)
        show_html_button.connect("clicked", lambda btn: self.on_show_html_clicked(win, btn))
        file_toolbar.append(show_html_button)
        
        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar

## Insert related code

    def insert_text_box_js(self):
        return """ """

    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return """ """

    def insert_link_js(self):
        """JavaScript for insert link and related functionality"""
        return """ """


    def on_insert_text_box_clicked(self, win, btn):
        """Handle text box insertion button click, textbox is basically 1x1 table"""
        win.statusbar.set_text("Inserting text box...")
        
        # Execute JavaScript to insert a text box at the cursor position
        js_code = """
        (function() {
            insertTextBox();
            return true;
        })();
        """
        self.execute_js(win, js_code)
        
    def on_insert_image_clicked(self, win, btn):
        """Handle image insertion button click"""
        win.statusbar.set_text("Inserting image...")

        # Create a file chooser dialog using Gtk.FileChooserNative
        dialog = Gtk.FileChooserNative(
            title="Select an Image",
            transient_for=win,  # Set the transient parent correctly
            action=Gtk.FileChooserAction.OPEN,
            accept_label="_Open",
            cancel_label="_Cancel"
        )

        # Add image file filters
        filter_image = Gtk.FileFilter()
        filter_image.set_name("Image files")
        filter_image.add_mime_type("image/png")
        filter_image.add_mime_type("image/jpeg")
        filter_image.add_mime_type("image/gif")
        dialog.set_filter(filter_image)

        dialog.connect("response", lambda dlg, response: self.on_image_dialog_response(dlg, response, win))
        dialog.show()

    def on_image_dialog_response(self, dialog, response, win):
        """Handle the response from the image file chooser dialog"""
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file and (file_path := file.get_path()):
                # Convert file path to a data URL for JavaScript
                import base64
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    mime_type = "image/png" if file_path.endswith(".png") else "image/jpeg"
                    data_url = f"data:{mime_type};base64,{encoded_string}"

                # Execute JavaScript to insert the image
                js_code = f"""
                (function() {{
                    insertImage('{data_url}');
                    return true;
                }})();
                """
                self.execute_js(win, js_code)
            else:
                win.statusbar.set_text("Failed to select a valid image file.")
        dialog.destroy() 

    def on_insert_link_clicked(self, win, btn):
      """show a dialog with URL and Text """
      return
      
## /Insert related code



    def get_editor_js(self):
        """Return the combined JavaScript logic for the editor."""
        return f"""
        // Global scope for persistence
        window.undoStack = [];
        window.redoStack = [];
        window.isUndoRedo = false;
        window.lastContent = "";
        
        // Search variables
        var searchResults = [];
        var searchIndex = -1;
        var currentSearchText = "";

        {self.set_content_js()}
        {self.insert_table_js()}
        {self.table_border_style_js()}
        {self.table_color_js()}
        {self.insert_text_box_js()}
        {self.insert_image_js()}
        {self.insert_link_js()}
        {self.init_editor_js()}
        """

    

    def find_last_text_node_js(self):
        """JavaScript to find the last text node for cursor restoration."""
        return """
        function findLastTextNode(node) {
            if (node.nodeType === 3) return node;
            for (let i = node.childNodes.length - 1; i >= 0; i--) {
                const found = findLastTextNode(node.childNodes[i]);
                if (found) return found;
            }
            return null;
        }
        """

    def set_content_js(self):
        """JavaScript to set the editor content and reset stacks."""
        return """
        function setContent(html) {
            const editor = document.getElementById('editor');
            if (!html || html.trim() === '') {
                editor.innerHTML = '<div><br></div>';
            } else if (!html.trim().match(/^<(div|p|h[1-6]|ul|ol|table)/i)) {
                editor.innerHTML = '<div>' + html + '</div>';
            } else {
                editor.innerHTML = html;
            }
            window.lastContent = editor.innerHTML;
            window.undoStack = [window.lastContent];
            window.redoStack = [];
            editor.focus();
        }
        """


        
    def get_initial_html(self):
        return self.get_editor_html('<div><font face="Sans" style="font-size: 11pt;"><br></font></div>')
    
    # Show Caret in the window (for new and fresh start)
    def set_initial_focus(self, win):
        """Set focus to the WebView and its editor element after window is shown"""
        try:
            # First grab focus on the WebView widget itself
            win.webview.grab_focus()
            
            # Then focus the editor element inside the WebView
            js_code = """
            (function() {
                const editor = document.getElementById('editor');
                if (!editor) return false;
                
                editor.focus();
                
                // Set cursor position
                try {
                    const range = document.createRange();
                    const sel = window.getSelection();
                    
                    // Find or create a text node to place cursor
                    let textNode = null;
                    let firstDiv = editor.querySelector('div');
                    
                    if (!firstDiv) {
                        editor.innerHTML = '<div><br></div>';
                        firstDiv = editor.querySelector('div');
                    }
                    
                    if (firstDiv) {
                        range.setStart(firstDiv, 0);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                } catch (e) {
                    console.log("Error setting cursor position:", e);
                }
                
                return true;
            })();
            """
            
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            return False  # Don't call again
        except Exception as e:
            print(f"Error setting initial focus: {e}")
            return False  # Don't call again
            
##################
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return f"""
        {self.table_theme_helpers_js()}
        {self.table_handles_css_js()}
        {self.table_insert_functions_js()}
        {self.table_activation_js()}
        {self.table_drag_resize_js()}
        {self.table_row_column_js()}
        {self.table_alignment_js()}
        {self.table_floating_js()}
        {self.table_event_handlers_js()}
        """

    def table_theme_helpers_js(self):
        """JavaScript helper functions for theme detection and colors"""
        return """
        // Function to check if we're in dark mode
        function isDarkMode() {
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        
        // Function to get appropriate border color based on current theme
        function getBorderColor() {
            return isDarkMode() ? '#444' : '#ccc';
        }
        
        // Function to get appropriate header background color based on current theme
        function getHeaderBgColor() {
            return isDarkMode() ? '#2a2a2a' : '#f0f0f0';
        }
        """


    def table_insert_functions_js(self):
        """JavaScript for inserting tables with default margins"""
        return """
        // Function to insert a table at the current cursor position
        function insertTable(rows, cols, hasHeader, borderWidth, tableWidth, isFloating) {
            // Get theme-appropriate colors
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Create table HTML
            let tableHTML = '<table cellspacing="0" cellpadding="5" ';
            
            // Add class and style attributes (including default margins)
            tableHTML += 'class="editor-table no-wrap" style="border-collapse: collapse; width: ' + tableWidth + '; margin: 6px 6px 0 0;">';
            
            // Create header row if requested
            if (hasHeader) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<th style="border: ' + borderWidth + 'px solid ' + borderColor + '; padding: 5px; background-color: ' + headerBgColor + ';">Header ' + (j+1) + '</th>';
                }
                tableHTML += '</tr>';
                rows--; // Reduce regular rows by one since we added a header
            }
            
            // Create regular rows and cells
            for (let i = 0; i < rows; i++) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<td style="border: ' + borderWidth + 'px solid ' + borderColor + '; padding: 5px; min-width: 30px;">Cell</td>';
                }
                tableHTML += '</tr>';
            }
            
            tableHTML += '</table><p></p>';
            
            // Insert the table at the current cursor position
            document.execCommand('insertHTML', false, tableHTML);
            
            // Activate the newly inserted table
            setTimeout(() => {
                const tables = document.querySelectorAll('table.editor-table');
                const newTable = tables[tables.length - 1] || document.querySelector('table:last-of-type');
                if (newTable) {
                    // Ensure the editor-table class is present
                    if (!newTable.classList.contains('editor-table')) {
                        newTable.classList.add('editor-table');
                    }
                    
                    // Set default margins
                    newTable.style.marginTop = '6px';
                    newTable.style.marginRight = '6px';
                    newTable.style.marginBottom = '0px';
                    newTable.style.marginLeft = '0px';
                    
                    // Store margin values as attributes
                    newTable.setAttribute('data-margin-top', '6');
                    newTable.setAttribute('data-margin-right', '6');
                    newTable.setAttribute('data-margin-bottom', '0');
                    newTable.setAttribute('data-margin-left', '0');
                    
                    // Make table floating if requested
                    if (isFloating) {
                        newTable.classList.add('floating-table');
                        setTableFloating(newTable);
                    }
                    
                    activateTable(newTable);
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
                }
            }, 10);
        }
        """


        
    def table_drag_resize_js(self):
        """JavaScript for table dragging and resizing"""
        return """
        // Function to start table drag
        function startTableDrag(e, tableElement) {
            e.preventDefault();
            if (!tableElement) return;
            
            isDragging = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            
            // Set cursor based on whether the table is floating or not
            if (tableElement.classList.contains('floating-table')) {
                document.body.style.cursor = 'grabbing';
            } else {
                document.body.style.cursor = 'move';
            }
        }
        
        // Function to move table
        function moveTable(e) {
            if (!isDragging || !activeTable) return;
            
            // Check if the table is a floating table
            if (activeTable.classList.contains('floating-table')) {
                // For floating tables, just move it to the mouse position with offset
                const deltaX = e.clientX - dragStartX;
                const deltaY = e.clientY - dragStartY;
                
                // Get current position from style
                const currentTop = parseInt(activeTable.style.top) || 0;
                const currentLeft = parseInt(activeTable.style.left) || 0;
                
                // Update position
                activeTable.style.top = `${currentTop + deltaY}px`;
                activeTable.style.left = `${currentLeft + deltaX}px`;
                
                // Update starting points for next movement
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            } else {
                const currentY = e.clientY;
                const deltaY = currentY - dragStartY;
                
                if (Math.abs(deltaY) > 30) {
                    const editor = document.getElementById('editor');
                    const blocks = Array.from(editor.children).filter(node => {
                        const style = window.getComputedStyle(node);
                        return style.display.includes('block') || node.tagName === 'TABLE';
                    });
                    
                    const tableIndex = blocks.indexOf(activeTable);
                    
                    if (deltaY < 0 && tableIndex > 0) {
                        const targetElement = blocks[tableIndex - 1];
                        editor.insertBefore(activeTable, targetElement);
                        dragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    } 
                    else if (deltaY > 0 && tableIndex < blocks.length - 1) {
                        const targetElement = blocks[tableIndex + 1];
                        if (targetElement.nextSibling) {
                            editor.insertBefore(activeTable, targetElement.nextSibling);
                        } else {
                            editor.appendChild(activeTable);
                        }
                        dragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            }
        }
        
        // Function to start table resize
        function startTableResize(e, tableElement) {
            e.preventDefault();
            isResizing = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            const style = window.getComputedStyle(tableElement);
            tableStartX = parseInt(style.width) || tableElement.offsetWidth;
            tableStartY = parseInt(style.height) || tableElement.offsetHeight;
        }
        
        // Function to resize table
        function resizeTable(e) {
            if (!isResizing || !activeTable) return;
            
            const deltaX = e.clientX - dragStartX;
            
            // Only adjust width, not height - this prevents the horizontal line artifact
            activeTable.style.width = (tableStartX + deltaX) + 'px';
        }
        """



    def table_alignment_js(self):
        """JavaScript for table alignment"""
        return """
        // Function to set table alignment
        function setTableAlignment(alignClass) {
            if (!activeTable) return;
            
            // Remove all alignment classes
            activeTable.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap', 'floating-table');
            
            // Add the requested alignment class
            activeTable.classList.add(alignClass);
            
            // Reset positioning if it was previously floating
            if (activeTable.style.position === 'absolute') {
                activeTable.style.position = 'relative';
                activeTable.style.top = '';
                activeTable.style.left = '';
                activeTable.style.zIndex = '';
            }
            
            // Set width to auto except for full-width
            if (alignClass === 'no-wrap') {
                activeTable.style.width = '100%';
            } else {
                activeTable.style.width = 'auto';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """
        
    def table_floating_js(self):
        """JavaScript for floating table functionality"""
        return """
        // Function to make a table floating (freely positionable)
        function setTableFloating(tableElement) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            // First, remove any alignment classes
            tableElement.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            
            // Add floating class for special styling
            tableElement.classList.add('floating-table');
            
            // Set positioning to absolute
            tableElement.style.position = 'absolute';
            
            // Calculate initial position - center in the visible editor area
            const editorRect = document.getElementById('editor').getBoundingClientRect();
            const tableRect = tableElement.getBoundingClientRect();
            
            // Set initial position
            const editorScrollTop = document.getElementById('editor').scrollTop;
            
            // Position in the middle of the visible editor area
            const topPos = (editorRect.height / 2) - (tableRect.height / 2) + editorScrollTop;
            const leftPos = (editorRect.width / 2) - (tableRect.width / 2);
            
            tableElement.style.top = `${Math.max(topPos, editorScrollTop)}px`;
            tableElement.style.left = `${Math.max(leftPos, 0)}px`;
            
            // Enhance the drag handle for position control
            enhanceTableDragHandles(tableElement);
            
            // Ensure proper z-index to be above regular content
            tableElement.style.zIndex = "50";
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            // Activate the table to show handles
            if (tableElement !== activeTable) {
                activateTable(tableElement);
            }
        }
        
        // Add enhanced drag handling for floating tables
        function enhanceTableDragHandles(tableElement) {
            if (!tableElement) return;
            
            // Find or create the drag handle
            let dragHandle = tableElement.querySelector('.table-drag-handle');
            if (!dragHandle) {
                // If it doesn't exist, we might need to activate the table first
                activateTable(tableElement);
                dragHandle = tableElement.querySelector('.table-drag-handle');
            }
            
            if (dragHandle) {
                // Update tooltip to reflect new functionality
                dragHandle.title = "Drag to move table freely";
                
                // Make the drag handle more visible for floating tables
                dragHandle.style.width = "20px";
                dragHandle.style.height = "20px";
                dragHandle.style.backgroundColor = "#4e9eff";
                dragHandle.style.borderRadius = "3px";
                dragHandle.style.opacity = "0.9";
            }
        }
        """


        
    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option, is_floating):
        """Handle response from the table dialog"""
        dialog.close()
        
        # Prepare the width value
        width_value = "auto"
        if width_option != "Auto":
            width_value = width_option
        
        # Execute JavaScript to insert the table
        js_code = f"""
        (function() {{
            insertTable({rows}, {cols}, {str(has_header).lower()}, {border_width}, "{width_value}", {str(is_floating).lower()});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        
        # Update status message based on table type
        if is_floating:
            win.statusbar.set_text("Floating table inserted")
        else:
            win.statusbar.set_text("Table inserted")        
################
    def create_window(self):
        """Create a new window with all initialization (former HTMLEditorWindow.__init__)"""
        win = Adw.ApplicationWindow(application=self)
        
        # Set window properties
        win.modified = False
        win.auto_save_enabled = False
        win.auto_save_interval = 60
        win.current_file = None
        win.auto_save_source_id = None
        
        win.set_default_size(800, 600)
        win.set_title("Untitled - HTML Editor")
        
        # Create main box to contain all UI elements
        win.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.main_box.set_vexpand(True)
        win.main_box.set_hexpand(True)
        
        # Create master headerbar revealer
        win.headerbar_revealer = Gtk.Revealer()
        win.headerbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.headerbar_revealer.set_margin_start(0)
        win.headerbar_revealer.set_margin_end(0)
        win.headerbar_revealer.set_margin_top(0)
        win.headerbar_revealer.set_margin_bottom(0)
        win.headerbar_revealer.set_transition_duration(250)
        win.headerbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create a vertical box to contain headerbar and toolbars
        win.headerbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create the main headerbar
        win.headerbar = Adw.HeaderBar()
        win.headerbar.add_css_class("flat-header")  # Add flat-header style
        self.setup_headerbar_content(win)
        win.headerbar_box.append(win.headerbar)
        
        # Create file toolbar with revealer
        win.file_toolbar_revealer = Gtk.Revealer()
        win.file_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.file_toolbar_revealer.set_transition_duration(250)
        win.file_toolbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create and add file toolbar
        win.file_toolbar = self.create_file_toolbar(win)
        win.file_toolbar_revealer.set_child(win.file_toolbar)
        win.headerbar_box.append(win.file_toolbar_revealer)
        
        # Set the headerbar_box as the child of the headerbar_revealer
        win.headerbar_revealer.set_child(win.headerbar_box)
        win.main_box.append(win.headerbar_revealer)
        
        
        # Create content box (for webview and toolbars)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        # Create webview
        win.webview = WebKit.WebView()
        win.webview.set_vexpand(True)
        win.webview.set_hexpand(True) 
        win.webview.load_html(self.get_editor_html(), None)
        settings = win.webview.get_settings()
        try:
            settings.set_enable_developer_extras(True)
        except:
            pass
        
        # Set up WebView message handlers
        try:
            user_content_manager = win.webview.get_user_content_manager()
            
            # Register content change handler
            user_content_manager.register_script_message_handler("contentChanged")
            user_content_manager.connect("script-message-received::contentChanged", 
                                        lambda mgr, res: self.on_content_changed(win, mgr, res))
            
            # Register table-related message handlers
            user_content_manager.register_script_message_handler("tableClicked")
            user_content_manager.register_script_message_handler("tableDeleted")
            user_content_manager.register_script_message_handler("tablesDeactivated")
            
            user_content_manager.connect("script-message-received::tableClicked", 
                                        lambda mgr, res: self.on_table_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::tableDeleted", 
                                        lambda mgr, res: self.on_table_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::tablesDeactivated", 
                                        lambda mgr, res: self.on_tables_deactivated(win, mgr, res))
            
        except:
            print("Warning: Could not set up JavaScript message handlers")
                    
        # Add key event controller to capture Shift+Tab
        win.key_controller = Gtk.EventControllerKey()
        win.key_controller.connect("key-pressed", self.on_webview_key_pressed)
        win.webview.add_controller(win.key_controller)
        
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        # Create table toolbar with revealer (hidden by default)
        win.table_toolbar_revealer = Gtk.Revealer()
        win.table_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.table_toolbar_revealer.set_transition_duration(250)
        win.table_toolbar_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create and add table toolbar
        win.table_toolbar = self.create_table_toolbar(win)
        win.table_toolbar_revealer.set_child(win.table_toolbar)
        content_box.append(win.table_toolbar_revealer)
        
        # Create statusbar with revealer
        win.statusbar_revealer = Gtk.Revealer()
        win.statusbar_revealer.add_css_class("flat-header")
        win.statusbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.statusbar_revealer.set_transition_duration(250)
        win.statusbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create a box for the statusbar 
        statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        statusbar_box.set_margin_start(10)
        statusbar_box.set_margin_end(10)
        statusbar_box.set_margin_top(0)
        statusbar_box.set_margin_bottom(4)
        
        # Create the text label
        win.statusbar = Gtk.Label(label="Ready")
        win.statusbar.set_halign(Gtk.Align.START)
        win.statusbar.set_hexpand(True)
        statusbar_box.append(win.statusbar)
        
        # Set the statusbar box as the child of the revealer
        win.statusbar_revealer.set_child(statusbar_box)
        content_box.append(win.statusbar_revealer)

        win.main_box.append(content_box)
        win.set_content(win.main_box)

        # Add case change action to the window
        case_change_action = Gio.SimpleAction.new("change-case", GLib.VariantType.new("s"))
        case_change_action.connect("activate", lambda action, param: self.on_change_case(win, param.get_string()))
        win.add_action(case_change_action)
        
        # Add to windows list
        self.windows.append(win)

        return win

    def on_webview_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events on the webview"""
        # Check for Shift+Tab
        if keyval == Gdk.KEY_ISO_Left_Tab or (keyval == Gdk.KEY_Tab and (state & Gdk.ModifierType.SHIFT_MASK)):
            # Return True to indicate we've handled the event and prevent default behavior
            return True
        
        # For all other keys, let them pass through normally
        return False

    def _create_border_tab(self, win, popover):
        """Create the border properties tab"""
        border_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        border_box.set_margin_start(12)
        border_box.set_margin_end(12)
        border_box.set_margin_top(12)
        border_box.set_margin_bottom(12)
        
        # Border style and width in a single row
        style_width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Border style dropdown (more compact)
        style_label = Gtk.Label(label="Style:")
        style_label.set_halign(Gtk.Align.START)
        
        style_combo = Gtk.DropDown()
        style_options = Gtk.StringList()
        styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
        for style in styles:
            style_options.append(style)
        style_combo.set_model(style_options)
        style_combo.set_selected(0)  # Default to solid
        
        # Border width spinner (more compact)
        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)
        
        width_adjustment = Gtk.Adjustment(value=1, lower=0, upper=10, step_increment=1)
        width_spin = Gtk.SpinButton()
        width_spin.set_adjustment(width_adjustment)
        width_spin.set_width_chars(3)  # Make it more compact
        
        # Connect style change
        style_combo.connect("notify::selected", lambda cb, p: self.on_border_style_changed(
            win, styles[cb.get_selected()], width_spin.get_value_as_int()))
        
        # Connect width change
        width_spin.connect("value-changed", lambda spin: self.on_border_width_changed(
            win, styles[style_combo.get_selected()], spin.get_value_as_int()))
        
        # Add all to the row
        style_width_box.append(style_label)
        style_width_box.append(style_combo)
        style_width_box.append(width_label)
        style_width_box.append(width_spin)
        border_box.append(style_width_box)
        
        # Border shadow option
        shadow_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        shadow_label = Gtk.Label(label="Shadow:")
        shadow_label.set_halign(Gtk.Align.START)
        
        shadow_switch = Gtk.Switch()
        shadow_switch.set_active(False)
        shadow_switch.connect("notify::active", lambda sw, _: self.on_border_shadow_changed(win, sw.get_active()))
        
        shadow_box.append(shadow_label)
        shadow_box.append(shadow_switch)
        border_box.append(shadow_box)
        
        # Add a separator
        border_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Border display options title (more compact)
        display_label = Gtk.Label(label="Border Display:")
        display_label.set_halign(Gtk.Align.START)
        display_label.set_margin_top(4)
        border_box.append(display_label)
        
        # Create a horizontal box for all border options
        all_options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Create a linked box for primary border toggles
        primary_border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        primary_border_box.add_css_class("linked")
        
        # Create the primary border buttons
        border_options = [
            {"icon": "table-border-all-symbolic", "tooltip": "All Borders", "value": "all"},
            {"icon": "table-border-none-symbolic", "tooltip": "No Borders", "value": "none"},
            {"icon": "table-border-outer-symbolic", "tooltip": "Outer Borders", "value": "outer"},
            {"icon": "table-border-inner-symbolic", "tooltip": "Inner Borders", "value": "inner"}
        ]
        
        for option in border_options:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                win, None, width_spin, border_option))
            primary_border_box.append(button)
        
        all_options_box.append(primary_border_box)
        
        # Create a linked box for combo border options
        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box.add_css_class("linked")
        
        # Create horizontal/vertical buttons
        combo_options = [
            {"icon": "table-border-horizontal-symbolic", "tooltip": "Horizontal Borders", "value": "horizontal"},
            {"icon": "table-border-vertical-symbolic", "tooltip": "Vertical Borders", "value": "vertical"}
        ]
        
        for option in combo_options:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                win, None, width_spin, border_option))
            combo_box.append(button)
        
        all_options_box.append(combo_box)
        border_box.append(all_options_box)
        
        # Create a second row for combination border options
        combo_row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        combo_row2.set_margin_top(4)
        
        # First linked box for combined options
        combo_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box2.add_css_class("linked")
        
        combo_options2 = [
            {"icon": "table-border-outer-horizontal-symbolic", "tooltip": "Outer Horizontal", "value": ["outer", "horizontal"]},
            {"icon": "table-border-outer-vertical-symbolic", "tooltip": "Outer Vertical", "value": ["outer", "vertical"]},
            {"icon": "table-border-inner-horizontal-symbolic", "tooltip": "Inner Horizontal", "value": ["inner", "horizontal"]},
            {"icon": "table-border-inner-vertical-symbolic", "tooltip": "Inner Vertical", "value": ["inner", "vertical"]}
        ]
        
        for option in combo_options2:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            if isinstance(option["value"], list):
                button.connect("clicked", lambda btn, border_types=option["value"]: self._apply_combined_borders(
                    win, width_spin, border_types))
            else:
                button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                    win, None, width_spin, border_option))
            combo_box2.append(button)
        
        combo_row2.append(combo_box2)
        
        # Second linked box for all combined options
        combo_box3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box3.add_css_class("linked")
        
        combo_options3 = [
            {"icon": "table-border-outer-inner-horizontal-symbolic", "tooltip": "Outer + Inner Horizontal", "value": ["outer", "inner", "horizontal"]},
            {"icon": "table-border-outer-inner-vertical-symbolic", "tooltip": "Outer + Inner Vertical", "value": ["outer", "inner", "vertical"]}
        ]
        
        for option in combo_options3:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            button.connect("clicked", lambda btn, border_types=option["value"]: self._apply_combined_borders(
                win, width_spin, border_types))
            combo_box3.append(button)
        
        combo_row2.append(combo_box3)
        border_box.append(combo_row2)
        
        # Store references for later initialization
        border_box.style_combo = style_combo
        border_box.width_spin = width_spin
        border_box.shadow_switch = shadow_switch
        
        return border_box


    def on_border_shadow_changed(self, win, active):
        """Apply or remove border shadow"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            if ({str(active).lower()}) {{
                activeTable.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)';
            }} else {{
                activeTable.style.boxShadow = 'none';
            }}
            
            // Store shadow state
            activeTable.setAttribute('data-border-shadow', {str(active).lower()});
            
            // Notify that content changed
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about content change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Border shadow {'enabled' if active else 'disabled'}")
        
    def _create_margin_tab(self, win, popover):
        """Create the margin properties tab with default values"""
        margin_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        margin_box.set_margin_start(12)
        margin_box.set_margin_end(12)
        margin_box.set_margin_top(12)
        margin_box.set_margin_bottom(12)
        
        # Create grid for margin controls
        margin_grid = Gtk.Grid()
        margin_grid.set_row_spacing(8)
        margin_grid.set_column_spacing(12)
        margin_grid.set_halign(Gtk.Align.CENTER)
        
        margin_controls = {}
        
        # Define positions for a visual layout with default values
        positions = {
            'top': (0, 1, 6),      # (row, col, default_value)
            'left': (1, 0, 0),
            'right': (1, 2, 6),
            'bottom': (2, 1, 0)
        }
        
        for side, (row, col, default_value) in positions.items():
            # Create a box for label and spin button
            side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            
            # Add label
            label = Gtk.Label(label=side.capitalize())
            label.set_halign(Gtk.Align.CENTER)
            side_box.append(label)
            
            # Create spin button with appropriate default value
            adjustment = Gtk.Adjustment(value=default_value, lower=0, upper=100, step_increment=1)
            spin = Gtk.SpinButton()
            spin.set_adjustment(adjustment)
            spin.set_width_chars(5)
            
            # Connect change signal
            spin.connect("value-changed", lambda s, sd=side: self.on_margin_changed(win, sd, s.get_value_as_int()))
            
            side_box.append(spin)
            margin_grid.attach(side_box, col, row, 1, 1)
            margin_controls[side] = spin
        
        # Add a visual representation of the table in the center
        table_visual = Gtk.DrawingArea()
        table_visual.set_size_request(80, 60)
        table_visual.set_content_width(80)
        table_visual.set_content_height(60)
        
        def draw_table_visual(area, cr, width, height, data):
            # Draw a simple table representation
            cr.set_source_rgb(0.8, 0.8, 0.8)
            cr.rectangle(10, 10, width - 20, height - 20)
            cr.fill()
            
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.rectangle(10, 10, width - 20, height - 20)
            cr.stroke()
        
        table_visual.set_draw_func(draw_table_visual, None)
        margin_grid.attach(table_visual, 1, 1, 1, 1)
        
        margin_box.append(margin_grid)
        
        # Add separator before default button
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        margin_box.append(separator)
        
        # Add default button
        default_button = Gtk.Button(label="Reset to Default Margins")
        default_button.connect("clicked", lambda btn: self._reset_default_margins(win, margin_controls))
        margin_box.append(default_button)
        
        # Store margin controls for later reference
        margin_box.margin_controls = margin_controls
        
        return margin_box

    def _reset_default_margins(self, win, margin_controls):
        """Reset margins to default values"""
        default_margins = {
            'top': 6,
            'right': 6,
            'bottom': 0,
            'left': 0
        }
        
        # Update spin buttons
        for side, value in default_margins.items():
            if side in margin_controls:
                margin_controls[side].set_value(value)
        
        # Apply the margins in JavaScript
        js_code = f"""
        (function() {{
            setTableMargins({default_margins['top']}, {default_margins['right']}, 
                            {default_margins['bottom']}, {default_margins['left']});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text("Reset to default margins")


    def _get_color_from_button(self, color_button):
        """Get color from button in a safe way that handles deprecation"""
        try:
            # Try the standard method first
            rgba = color_button.get_rgba()
            hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            return hex_color
        except:
            try:
                # Try alternative methods
                color = color_button.get_color()
                red = (color.red >> 8) / 255.0
                green = (color.green >> 8) / 255.0
                blue = (color.blue >> 8) / 255.0
                hex_color = f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"
                return hex_color
            except:
                # Final fallback
                return "#000000"

    def _set_color_on_button(self, color_button, color_string):
        """Set color on button in a safe way that handles deprecation"""
        try:
            rgba = self._parse_color_string(color_string)
            if rgba:
                try:
                    color_button.set_rgba(rgba)
                except:
                    # Try alternative methods
                    color_button.set_color(self._rgba_to_color(rgba))
        except Exception as e:
            print(f"Error setting color on button: {e}")
            

        
    def create_table_toolbar(self, win):
        """Create a toolbar for table editing"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        
        # Table operations label
        table_label = Gtk.Label(label="Table:")
        table_label.set_margin_end(10)
        toolbar.append(table_label)
        
        # Create a group for row operations
        row_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        row_group.add_css_class("linked")
        
        # Add Row Above button
        add_row_above_button = Gtk.Button(icon_name="list-add-symbolic")
        add_row_above_button.set_tooltip_text("Add row above")
        add_row_above_button.connect("clicked", lambda btn: self.on_add_row_above_clicked(win))
        row_group.append(add_row_above_button)
        
        # Add Row Below button
        add_row_below_button = Gtk.Button(icon_name="list-add-symbolic")
        add_row_below_button.set_tooltip_text("Add row below")
        add_row_below_button.connect("clicked", lambda btn: self.on_add_row_below_clicked(win))
        row_group.append(add_row_below_button)
        
        # Add row group to toolbar
        toolbar.append(row_group)
        
        # Create a group for column operations
        col_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        col_group.add_css_class("linked")
        col_group.set_margin_start(5)
        
        # Add Column Before button
        add_col_before_button = Gtk.Button(icon_name="list-add-symbolic")
        add_col_before_button.set_tooltip_text("Add column before")
        add_col_before_button.connect("clicked", lambda btn: self.on_add_column_before_clicked(win))
        col_group.append(add_col_before_button)
        
        # Add Column After button
        add_col_after_button = Gtk.Button(icon_name="list-add-symbolic")
        add_col_after_button.set_tooltip_text("Add column after")
        add_col_after_button.connect("clicked", lambda btn: self.on_add_column_after_clicked(win))
        col_group.append(add_col_after_button)
        
        # Add column group to toolbar
        toolbar.append(col_group)
        
        # Small separator
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator1.set_margin_start(5)
        separator1.set_margin_end(5)
        toolbar.append(separator1)
        
        # Create a group for delete operations
        delete_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        delete_group.add_css_class("linked")
        
        # Delete Row button
        del_row_button = Gtk.Button(icon_name="list-remove-symbolic")
        del_row_button.set_tooltip_text("Delete row")
        del_row_button.connect("clicked", lambda btn: self.on_delete_row_clicked(win))
        delete_group.append(del_row_button)
        
        # Delete Column button
        del_col_button = Gtk.Button(icon_name="list-remove-symbolic")
        del_col_button.set_tooltip_text("Delete column")
        del_col_button.connect("clicked", lambda btn: self.on_delete_column_clicked(win))
        delete_group.append(del_col_button)
        
        # Delete Table button
        del_table_button = Gtk.Button(icon_name="edit-delete-symbolic")
        del_table_button.set_tooltip_text("Delete table")
        del_table_button.connect("clicked", lambda btn: self.on_delete_table_clicked(win))
        delete_group.append(del_table_button)
        
        # Add delete group to toolbar
        toolbar.append(delete_group)
        
        # Separator
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator2.set_margin_start(10)
        separator2.set_margin_end(10)
        toolbar.append(separator2)
        
        # Table properties button (combines border, margin, and color)
        table_props_button = Gtk.Button(icon_name="document-properties-symbolic")
        table_props_button.set_tooltip_text("Table Properties")
        table_props_button.connect("clicked", lambda btn: self.on_table_button_clicked(win, btn))
        toolbar.append(table_props_button)
        
        # Separator
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator3.set_margin_start(10)
        separator3.set_margin_end(10)
        toolbar.append(separator3)
        
        # Alignment options
        align_label = Gtk.Label(label="Align:")
        align_label.set_margin_end(5)
        toolbar.append(align_label)
        
        # Create a group for alignment buttons
        align_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        align_group.add_css_class("linked")
        
        # Left alignment
        align_left_button = Gtk.Button(icon_name="format-justify-left-symbolic")
        align_left_button.set_tooltip_text("Align Left (text wraps around right)")
        align_left_button.connect("clicked", lambda btn: self.on_table_align_left(win))
        align_group.append(align_left_button)
        
        # Center alignment
        align_center_button = Gtk.Button(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Center (no text wrap)")
        align_center_button.connect("clicked", lambda btn: self.on_table_align_center(win))
        align_group.append(align_center_button)
        
        # Right alignment
        align_right_button = Gtk.Button(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right (text wraps around left)")
        align_right_button.connect("clicked", lambda btn: self.on_table_align_right(win))
        align_group.append(align_right_button)
        
        # Full width (no wrap)
        full_width_button = Gtk.Button(icon_name="format-justify-fill-symbolic")
        full_width_button.set_tooltip_text("Full Width (no text wrap)")
        full_width_button.connect("clicked", lambda btn: self.on_table_full_width(win))
        align_group.append(full_width_button)
        
        # Add alignment group to toolbar
        toolbar.append(align_group)
        
        # Float button
        float_button = Gtk.Button(icon_name="move-tool-symbolic")
        float_button.set_tooltip_text("Make table float freely in editor")
        float_button.set_margin_start(5)
        float_button.connect("clicked", lambda btn: self.on_table_float_clicked(win))
        toolbar.append(float_button)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Close button
        close_button = Gtk.Button(icon_name="window-close-symbolic")
        close_button.set_tooltip_text("Close table toolbar")
        close_button.connect("clicked", lambda btn: self.on_close_table_toolbar_clicked(win))
        toolbar.append(close_button)
        
        return toolbar


    def on_table_button_clicked(self, win, button):
        """Show the table properties popup with tabs"""
        # Create a popover for table properties
        popover = Gtk.Popover()
        popover.set_parent(button)
        
        # Create the content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_size_request(350, 250)  # More compact size
        
        # Create header with title and close button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header_box.set_margin_bottom(8)
        
        # Add title label
        title_label = Gtk.Label(label="<b>Table Properties</b>")
        title_label.set_use_markup(True)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)
        
        # Add close button [x]
        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_button.set_tooltip_text("Close")
        close_button.add_css_class("flat")
        close_button.connect("clicked", lambda btn: popover.popdown())
        header_box.append(close_button)
        
        content_box.append(header_box)
        
        # Create tab view
        tab_view = Gtk.Notebook()
        tab_view.set_vexpand(True)
        
        # Create Border tab
        border_page = self._create_border_tab(win, popover)
        tab_view.append_page(border_page, Gtk.Label(label="Border"))
        
        # Create Margin tab
        margin_page = self._create_margin_tab(win, popover)
        tab_view.append_page(margin_page, Gtk.Label(label="Margin"))
        
        # Create Color tab
        color_page = self._create_color_tab(win, popover)
        tab_view.append_page(color_page, Gtk.Label(label="Color"))
        
        content_box.append(tab_view)
        
        # Set the content and show the popover
        popover.set_child(content_box)
        popover.popup()
        
        # Get current properties to initialize the dialogs
        self._initialize_table_properties(win, popover)
        
    # Add the handler for the float button click
    def on_table_float_clicked(self, win):
        """Make table float freely in the editor"""
        js_code = "setTableFloating();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table is now floating")
        
    def on_content_changed(self, win, manager, message):
        """Handle content changes from the editor"""
        win.modified = True
        self.update_window_title(win)
        # Add any other logic you want to perform when content changes
        win.statusbar.set_text("Content modified")

    def update_window_title(self, win):
        """Update window title to reflect modified state"""
        if win.current_file:
            filename = os.path.basename(win.current_file)
            title = f"{filename}{' *' if win.modified else ''} - HTML Editor"
        else:
            title = f"Untitled{' *' if win.modified else ''} - HTML Editor"
        win.set_title(title)

    def on_table_clicked(self, win, manager, message):
        """Handle table click event from editor"""
        win.table_toolbar_revealer.set_reveal_child(True)
        win.statusbar.set_text("Table selected")
        
        # Update margin controls with current table margins
        js_code = """
        (function() {
            const margins = getTableMargins();
            return JSON.stringify(margins);
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self._update_margin_controls(win, webview, result),
            None
        )
    def _update_margin_controls(self, win, webview, result):
        """Update margin spin buttons with current table margins"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            result_str = None
            
            if hasattr(js_result, 'get_js_value'):
                result_str = js_result.get_js_value().to_string()
            else:
                result_str = js_result.to_string()
            
            if result_str:
                import json
                margins = json.loads(result_str)
                
                if hasattr(win, 'margin_controls') and isinstance(margins, dict):
                    for side in ['top', 'right', 'bottom', 'left']:
                        if side in win.margin_controls and side in margins:
                            win.margin_controls[side].set_value(margins[side])
        except Exception as e:
            print(f"Error updating margin controls: {e}")

    def on_margin_changed(self, win, side, value):
        """Apply margin change to the active table"""
        js_code = f"""
        (function() {{
            // Pass all four sides with the updated value for the specified side
            const margins = getTableMargins() || {{ top: 0, right: 0, bottom: 0, left: 0 }};
            margins.{side} = {value};
            setTableMargins(margins.top, margins.right, margins.bottom, margins.left);
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied {side} margin: {value}px")   
                 
    def on_table_deleted(self, win, manager, message):
        """Handle table deleted event from editor"""
        win.table_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("Table deleted")

    def on_tables_deactivated(self, win, manager, message):
        """Handle event when all tables are deactivated"""
        win.table_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("No table selected")

    def execute_js(self, win, script):
        """Execute JavaScript in the WebView"""
        win.webview.evaluate_javascript(script, -1, None, None, None, None, None)

    # Table operation methods
    def on_add_row_above_clicked(self, win):
        """Add a row above the current row in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current row index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the start
                addTableRow(activeTable, 0);
                return;
            }
            
            // Find the TR parent
            let row = cell;
            while (row && row.tagName !== 'TR') {
                row = row.parentNode;
            }
            
            if (!row) return;
            
            // Find the row index
            let rowIndex = row.rowIndex;
            
            // Add a row above this one
            addTableRow(activeTable, rowIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_add_row_below_clicked(self, win):
        """Add a row below the current row in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current row index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the end
                addTableRow(activeTable);
                return;
            }
            
            // Find the TR parent
            let row = cell;
            while (row && row.tagName !== 'TR') {
                row = row.parentNode;
            }
            
            if (!row) return;
            
            // Find the row index
            let rowIndex = row.rowIndex;
            
            // Add a row below this one
            addTableRow(activeTable, rowIndex + 1);
        })();
        """
        self.execute_js(win, js_code)

    def on_add_column_before_clicked(self, win):
        """Add a column before the current column in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current cell index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the start
                addTableColumn(activeTable, 0);
                return;
            }
            
            // Find the cell index
            let cellIndex = cell.cellIndex;
            
            // Add a column before the current one
            addTableColumn(activeTable, cellIndex);
        })();
        """
        self.execute_js(win, js_code)     
        
        
    def on_add_column_after_clicked(self, win):
        """Add a column after the current column in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current cell index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
    // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the end
                addTableColumn(activeTable);
                return;
            }
            
            // Find the cell index
            let cellIndex = cell.cellIndex;
            
            // Add a column after the current one
            addTableColumn(activeTable, cellIndex + 1);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_row_clicked(self, win):
        """Delete the current row from the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current row index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just delete the last row
                deleteTableRow(activeTable);
                return;
            }
            
            // Find the TR parent
            let row = cell;
            while (row && row.tagName !== 'TR') {
                row = row.parentNode;
            }
            
            if (!row) return;
            
            // Find the row index
            let rowIndex = row.rowIndex;
            
            // Delete this row
            deleteTableRow(activeTable, rowIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_column_clicked(self, win):
        """Delete the current column from the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current cell index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just delete the last column
                deleteTableColumn(activeTable);
                return;
            }
            
            // Find the cell index
            let cellIndex = cell.cellIndex;
            
            // Delete this column
            deleteTableColumn(activeTable, cellIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_table_clicked(self, win):
        """Delete the entire table"""
        js_code = "deleteTable(activeTable);"
        self.execute_js(win, js_code)

    def on_table_align_left(self, win):
        """Align table to the left with text wrapping around right"""
        js_code = "setTableAlignment('left-align');"
        self.execute_js(win, js_code)

    def on_table_align_center(self, win):
        """Align table to the center with no text wrapping"""
        js_code = "setTableAlignment('center-align');"
        self.execute_js(win, js_code)

    def on_table_align_right(self, win):
        """Align table to the right with text wrapping around left"""
        js_code = "setTableAlignment('right-align');"
        self.execute_js(win, js_code)

    def on_table_full_width(self, win):
        """Make table full width with no text wrapping"""
        js_code = "setTableAlignment('no-wrap');"
        self.execute_js(win, js_code)

    def on_close_table_toolbar_clicked(self, win):
        """Hide the table toolbar and deactivate tables"""
        win.table_toolbar_revealer.set_reveal_child(False)
        js_code = "deactivateAllTables();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table toolbar closed")

    # Python handler for table insertion
    def on_insert_table_clicked(self, win, btn):
        """Handle table insertion button click"""
        win.statusbar.set_text("Inserting table...")
        
        # Create a dialog to configure the table
        dialog = Adw.Dialog()
        dialog.set_title("Insert Table")
        dialog.set_content_width(350)
        
        # Create layout for dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Rows input
        rows_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rows_label = Gtk.Label(label="Rows:")
        rows_label.set_halign(Gtk.Align.START)
        rows_label.set_hexpand(True)
        
        rows_adjustment = Gtk.Adjustment(value=3, lower=1, upper=20, step_increment=1)
        rows_spin = Gtk.SpinButton()
        rows_spin.set_adjustment(rows_adjustment)
        
        rows_box.append(rows_label)
        rows_box.append(rows_spin)
        content_box.append(rows_box)
        
        # Columns input
        cols_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cols_label = Gtk.Label(label="Columns:")
        cols_label.set_halign(Gtk.Align.START)
        cols_label.set_hexpand(True)
        
        cols_adjustment = Gtk.Adjustment(value=3, lower=1, upper=10, step_increment=1)
        cols_spin = Gtk.SpinButton()
        cols_spin.set_adjustment(cols_adjustment)
        
        cols_box.append(cols_label)
        cols_box.append(cols_spin)
        content_box.append(cols_box)
        
        # Header row checkbox
        header_check = Gtk.CheckButton(label="Include header row")
        header_check.set_active(True)
        content_box.append(header_check)
        
        # Border options
        border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        border_label = Gtk.Label(label="Border width:")
        border_label.set_halign(Gtk.Align.START)
        border_label.set_hexpand(True)
        
        border_adjustment = Gtk.Adjustment(value=1, lower=0, upper=5, step_increment=1)
        border_spin = Gtk.SpinButton()
        border_spin.set_adjustment(border_adjustment)
        
        border_box.append(border_label)
        border_box.append(border_spin)
        content_box.append(border_box)
        
        # Table width options
        width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        width_label = Gtk.Label(label="Table width:")
        width_label.set_halign(Gtk.Align.START)
        width_label.set_hexpand(True)
        
        width_combo = Gtk.DropDown()
        width_options = Gtk.StringList()
        width_options.append("Auto")
        width_options.append("100%")
        width_options.append("75%")
        width_options.append("50%")
        width_combo.set_model(width_options)
        width_combo.set_selected(1)  # Default to 100% (index 1)
        
        width_box.append(width_label)
        width_box.append(width_combo)
        content_box.append(width_box)
        
        # ADDED: Floating option checkbox
        float_check = Gtk.CheckButton(label="Free-floating (text wraps around)")
        float_check.set_active(True)  # Enabled by default
        content_box.append(float_check)
        
        # Set initial width based on floating setting (Auto for floating tables)
        width_combo.set_selected(0)  # Start with Auto since floating is active by default
        
        # Connect change handler for float check to update width combo
        def on_float_check_toggled(check_button):
            if check_button.get_active():  # If float is enabled
                width_combo.set_selected(0)  # Set to "Auto"
            else:  # If float is disabled
                width_combo.set_selected(1)  # Set to "100%"
        
        float_check.connect("toggled", on_float_check_toggled)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(16)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        
        insert_button = Gtk.Button(label="Insert")
        insert_button.add_css_class("suggested-action")
        insert_button.connect("clicked", lambda btn: self.on_table_dialog_response(
            win, dialog, 
            rows_spin.get_value_as_int(), 
            cols_spin.get_value_as_int(),
            header_check.get_active(),
            border_spin.get_value_as_int(),
            width_options.get_string(width_combo.get_selected()),
            float_check.get_active()  # Pass floating state
        ))
        
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        # Set dialog content and present
        dialog.set_child(content_box)
        dialog.present(win)

    #####################

    def get_editor_html(self, content=""):
        """Return HTML for the editor with improved table and text box styles"""
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f"""
        <!DOCTYPE html>
        <html style="height: 100%;">
        <head>
            <title>HTML Editor</title>
            <style>
                html, body {{
                    height: 100%;
                    padding: 0;
                    font-family: Sans;
                }}
                #editor {{
                    padding: 0px;
                    outline: none;
                    height: 100%;
                    font-family: Sans;
                    font-size: 11pt;
                    position: relative; /* Important for absolute positioning of floating tables */
                    min-height: 300px;  /* Ensure there's space to drag tables */
                }}
                #editor div {{
                    margin: 0;
                    padding: 0;
                }}
                #editor:empty:not(:focus):before {{
                    content: "Type here to start editing...";
                    color: #aaa;
                    font-style: italic;
                    position: absolute;
                    pointer-events: none;
                    top: 10px;
                    left: 10px;
                }}
                /* Table styles */
                table {{
                    border-collapse: collapse;
                    margin: 0 0 10px 0;  /* Changed from margin: 10px 0 */
                    position: relative;  /* Important for internal handles */
                    resize: both;
                    overflow: visible;   /* Changed from auto to visible to ensure handles are not clipped */
                    min-width: 30px;
                    min-height: 30px;
                }}
                table.left-align {{
                    float: left;
                    margin-right: 10px;
                    margin-top: 0;  /* Ensure no top margin for floated tables */
                    clear: none;
                }}
                table.right-align {{
                    float: right;
                    margin-left: 10px;
                    margin-top: 0;  /* Ensure no top margin for floated tables */
                    clear: none;
                }}
                table.center-align {{
                    display: table;  /* Ensure block behavior is correct */
                    margin-left: auto !important;
                    margin-right: auto !important;
                    margin-top: 0;
                    float: none !important;
                    clear: both;
                    position: relative;
                }}
                table.no-wrap {{
                    float: none;
                    clear: both;
                    width: 100%;
                    margin-top: 0;
                }}
                table td {{
                    padding: 5px;
                    min-width: 30px;
                    position: relative;
                }}
                table th {{
                    padding: 5px;
                    min-width: 30px;
                    background-color: #f0f0f0;
                }}
                
                /* Floating table styles - border removed from CSS and applied conditionally via JS */
                table.floating-table {{
                    position: absolute !important;
                    z-index: 50;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                    background-color: rgba(255, 255, 255, 0.95);
                    cursor: grab;
                }}
                
                table.floating-table:active {{
                    cursor: grabbing;
                }}
                
                table.floating-table .table-drag-handle {{
                    width: 20px !important;
                    height: 20px !important;
                    border-radius: 3px;
                    opacity: 0.9;
                }}
                
                /* Table handles are now defined in JavaScript for better control */
                
                /* Text box styles (enhanced table) */
                table.text-box-table {{
                    border: 1px solid #ccc !important;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    background-color: #fff;
                    width: 80px;  /* Initial width */
                    height: 80px; /* Initial height */
                    min-width: 80px;
                    min-height: 80px;
                    resize: both !important; /* Ensure resizability */
                }}
                
                table.text-box-table td {{
                    vertical-align: top;
                }}
                
                /* Ensure text boxes handle selection properly */
                #editor ::selection {{
                    background-color: #b5d7ff;
                    color: inherit;
                }}
                
                @media (prefers-color-scheme: dark) {{
                    html, body {{
                        background-color: #1e1e1e;
                        color: #c0c0c0;
                    }}
                    table th {{
                        background-color: #2a2a2a;
                    }}
                    table.text-box-table {{
                        border-color: #444 !important;
                        background-color: #2d2d2d;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    }}
                    table.floating-table {{
                        background-color: rgba(45, 45, 45, 0.95);
                        box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                    }}
                    #editor ::selection {{
                        background-color: #264f78;
                        color: inherit;
                    }}
                }}
                @media (prefers-color-scheme: light) {{
                    html, body {{
                        background-color: #ffffff;
                        color: #000000;
                    }}
                }}
            </style>
            <script>
                window.initialContent = "{content or '<div><font face=\"Sans\" style=\"font-size: 11pt;\"><br></font></div>'}";
                {self.get_editor_js()}
            </script>
        </head>
        <body>
            <div id="editor" contenteditable="true"></div>
        </body>
        </html>
        """ 
        
    # Add JavaScript functions for border style and color manipulation
    def table_border_style_js(self):
        """JavaScript for table border style manipulation with combined borders"""
        return """
        // Function to set table border style
        function setTableBorderStyle(style, width, color) {
            if (!activeTable) return false;
            
            // Get all cells in the table
            const cells = activeTable.querySelectorAll('th, td');
            
            // First try to get current values from table attributes
            let currentStyle = activeTable.getAttribute('data-border-style');
            let currentWidth = activeTable.getAttribute('data-border-width');
            let currentColor = activeTable.getAttribute('data-border-color');
            
            // If not stored, get from the first cell
            if (!currentStyle || !currentWidth || !currentColor) {
                if (cells.length > 0) {
                    const firstCell = cells[0];
                    currentStyle = currentStyle || firstCell.style.borderStyle || 'solid';
                    currentWidth = currentWidth || parseInt(firstCell.style.borderWidth) || 1;
                    currentColor = currentColor || firstCell.style.borderColor || getBorderColor();
                } else {
                    // Default values if no cells exist
                    currentStyle = currentStyle || 'solid';
                    currentWidth = currentWidth || 1;
                    currentColor = currentColor || getBorderColor();
                }
            }
            
            // Use provided values or fall back to current/default values
            const newStyle = style !== null && style !== undefined ? style : currentStyle;
            const newWidth = width !== null && width !== undefined ? width : currentWidth;
            const newColor = color !== null && color !== undefined ? color : currentColor;
            
            // Update border style for all cells
            cells.forEach(cell => {
                // Always set all three properties to ensure consistency
                cell.style.borderStyle = newStyle;
                cell.style.borderWidth = newWidth + 'px';
                cell.style.borderColor = newColor;
            });
            
            // Store the current border settings as attributes on the table for later reference
            activeTable.setAttribute('data-border-style', newStyle);
            activeTable.setAttribute('data-border-width', newWidth);
            activeTable.setAttribute('data-border-color', newColor);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set table border color
        function setTableBorderColor(color) {
            return setTableBorderStyle(null, null, color);
        }
        
        // Function to set table border width
        function setTableBorderWidth(width) {
            return setTableBorderStyle(null, width, null);
        }
        
        // Function to get current table border style
        function getTableBorderStyle() {
            if (!activeTable) return null;
            
            // First try to get from stored data attributes
            const storedStyle = activeTable.getAttribute('data-border-style');
            const storedWidth = activeTable.getAttribute('data-border-width');
            const storedColor = activeTable.getAttribute('data-border-color');
            
            if (storedStyle && storedWidth && storedColor) {
                return {
                    style: storedStyle,
                    width: parseInt(storedWidth),
                    color: storedColor
                };
            }
            
            // If not stored, get from the first cell
            const firstCell = activeTable.querySelector('td, th');
            if (!firstCell) return {
                style: 'solid',
                width: 1,
                color: getBorderColor()
            };
            
            // Get computed style to ensure we get actual values
            const computedStyle = window.getComputedStyle(firstCell);
            
            const result = {
                style: firstCell.style.borderStyle || computedStyle.borderStyle || 'solid',
                width: parseInt(firstCell.style.borderWidth) || parseInt(computedStyle.borderWidth) || 1,
                color: firstCell.style.borderColor || computedStyle.borderColor || getBorderColor()
            };
            
            // Store these values for future use
            activeTable.setAttribute('data-border-style', result.style);
            activeTable.setAttribute('data-border-width', result.width);
            activeTable.setAttribute('data-border-color', result.color);
            
            return result;
        }
        
        // Function to get current table border properties (including shadow)
        function getTableBorderProperties() {
            if (!activeTable) return null;
            
            const borderStyle = getTableBorderStyle();
            const hasShadow = activeTable.getAttribute('data-border-shadow') === 'true' || 
                             (window.getComputedStyle(activeTable).boxShadow !== 'none' && 
                              window.getComputedStyle(activeTable).boxShadow !== '');
            
            return {
                ...borderStyle,
                shadow: hasShadow
            };
        }
        
        // Function to set table margins
        function setTableMargins(top, right, bottom, left) {
            if (!activeTable) return false;
            
            // Set margins individually if provided
            if (top !== undefined && top !== null) {
                activeTable.style.marginTop = top + 'px';
            }
            if (right !== undefined && right !== null) {
                activeTable.style.marginRight = right + 'px';
            }
            if (bottom !== undefined && bottom !== null) {
                activeTable.style.marginBottom = bottom + 'px';
            }
            if (left !== undefined && left !== null) {
                activeTable.style.marginLeft = left + 'px';
            }
            
            // Store margin values as attributes for later reference
            activeTable.setAttribute('data-margin-top', parseInt(activeTable.style.marginTop) || 0);
            activeTable.setAttribute('data-margin-right', parseInt(activeTable.style.marginRight) || 0);
            activeTable.setAttribute('data-margin-bottom', parseInt(activeTable.style.marginBottom) || 0);
            activeTable.setAttribute('data-margin-left', parseInt(activeTable.style.marginLeft) || 0);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current table margins
        function getTableMargins() {
            if (!activeTable) return null;
            
            // Try to get from stored attributes first
            const storedTop = activeTable.getAttribute('data-margin-top');
            const storedRight = activeTable.getAttribute('data-margin-right');
            const storedBottom = activeTable.getAttribute('data-margin-bottom');
            const storedLeft = activeTable.getAttribute('data-margin-left');
            
            if (storedTop !== null || storedRight !== null || storedBottom !== null || storedLeft !== null) {
                return {
                    top: parseInt(storedTop) || 0,
                    right: parseInt(storedRight) || 0,
                    bottom: parseInt(storedBottom) || 0,
                    left: parseInt(storedLeft) || 0
                };
            }
            
            // Otherwise get from computed style
            const computedStyle = window.getComputedStyle(activeTable);
            
            return {
                top: parseInt(computedStyle.marginTop) || 0,
                right: parseInt(computedStyle.marginRight) || 0,
                bottom: parseInt(computedStyle.marginBottom) || 0,
                left: parseInt(computedStyle.marginLeft) || 0
            };
        }
        
        // Enhanced function to apply border to specific sides of the table
        // Now supports combined options like 'outer' + 'horizontal'
        function applyTableBorderSides(sides) {
            if (!activeTable) return false;
            
            const cells = activeTable.querySelectorAll('td, th');
            const currentStyle = getTableBorderStyle();
            
            if (!currentStyle) return false;
            
            // Create the border string with preserved style, width and color
            const borderValue = `${currentStyle.width}px ${currentStyle.style} ${currentStyle.color}`;
            
            // Check for special combined cases
            const hasOuter = sides.includes('outer');
            const hasInner = sides.includes('inner');
            const hasHorizontal = sides.includes('horizontal');
            const hasVertical = sides.includes('vertical');
            
            // Apply borders based on selected sides
            cells.forEach(cell => {
                // Get row and column position
                const row = cell.parentElement;
                const rowIndex = row.rowIndex;
                const cellIndex = cell.cellIndex;
                const isFirstRow = rowIndex === 0;
                const isLastRow = rowIndex === activeTable.rows.length - 1;
                const isFirstColumn = cellIndex === 0;
                const isLastColumn = cellIndex === row.cells.length - 1;
                
                // Reset all borders first
                cell.style.borderTop = 'none';
                cell.style.borderRight = 'none';
                cell.style.borderBottom = 'none';
                cell.style.borderLeft = 'none';
                
                // Apply borders based on sides parameter and cell position
                if (sides.includes('all')) {
                    cell.style.border = borderValue;
                } else if (sides.includes('none')) {
                    cell.style.border = 'none';
                } else {
                    // Outer + Inner Horizontal: Apply outer borders on all 4 sides PLUS inner horizontal borders
                    if (hasOuter && hasInner && hasHorizontal && !hasVertical) {
                        // Apply outer borders (all 4 sides)
                        if (isFirstRow) cell.style.borderTop = borderValue;
                        if (isLastRow) cell.style.borderBottom = borderValue;
                        if (isFirstColumn) cell.style.borderLeft = borderValue;
                        if (isLastColumn) cell.style.borderRight = borderValue;
                        
                        // Plus inner horizontal borders
                        if (!isLastRow) cell.style.borderBottom = borderValue;
                    }
                    // Outer + Inner Vertical: Apply outer borders on all 4 sides PLUS inner vertical borders
                    else if (hasOuter && hasInner && hasVertical && !hasHorizontal) {
                        // Apply outer borders (all 4 sides)
                        if (isFirstRow) cell.style.borderTop = borderValue;
                        if (isLastRow) cell.style.borderBottom = borderValue;
                        if (isFirstColumn) cell.style.borderLeft = borderValue;
                        if (isLastColumn) cell.style.borderRight = borderValue;
                        
                        // Plus inner vertical borders
                        if (!isLastColumn) cell.style.borderRight = borderValue;
                    }
                    // Handle outer borders
                    else if (hasOuter) {
                        if (isFirstRow) cell.style.borderTop = borderValue;
                        if (isLastRow) cell.style.borderBottom = borderValue;
                        if (isFirstColumn) cell.style.borderLeft = borderValue;
                        if (isLastColumn) cell.style.borderRight = borderValue;
                        
                        // If outer + horizontal, add only top and bottom outer borders
                        if (hasHorizontal && !hasVertical) {
                            if (isFirstRow) cell.style.borderTop = borderValue;
                            if (isLastRow) cell.style.borderBottom = borderValue;
                            cell.style.borderLeft = 'none';
                            cell.style.borderRight = 'none';
                        }
                        
                        // If outer + vertical, add only left and right outer borders
                        if (hasVertical && !hasHorizontal) {
                            cell.style.borderTop = 'none';
                            cell.style.borderBottom = 'none';
                            if (isFirstColumn) cell.style.borderLeft = borderValue;
                            if (isLastColumn) cell.style.borderRight = borderValue;
                        }
                    }
                    
                    // Handle inner borders
                    else if (hasInner) {
                        if (!isLastRow) cell.style.borderBottom = borderValue;
                        if (!isLastColumn) cell.style.borderRight = borderValue;
                        
                        // If inner + horizontal, add only horizontal inner borders
                        if (hasHorizontal && !hasVertical) {
                            if (!isLastRow) cell.style.borderBottom = borderValue;
                            cell.style.borderRight = 'none';
                        }
                        
                        // If inner + vertical, add only vertical inner borders
                        if (hasVertical && !hasHorizontal) {
                            cell.style.borderBottom = 'none';
                            if (!isLastColumn) cell.style.borderRight = borderValue;
                        }
                    }
                    
                    // Handle standalone horizontal/vertical if not combined with outer/inner
                    else {
                        if (hasHorizontal) {
                            cell.style.borderTop = borderValue;
                            cell.style.borderBottom = borderValue;
                        }
                        
                        if (hasVertical) {
                            cell.style.borderLeft = borderValue;
                            cell.style.borderRight = borderValue;
                        }
                    }
                }
            });
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        """
        
    def on_border_style_button_clicked(self, win, button):
        """Show the border style popup menu with improved UI"""
        # Create a popover for border styles
        popover = Gtk.Popover()
        popover.set_parent(button)
        
        # Create the content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        
        # Create header with title and close button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header_box.set_margin_bottom(8)
        
        # Add title label
        title_label = Gtk.Label(label="<b>Border Style</b>")
        title_label.set_use_markup(True)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)
        
        # Add close button [x]
        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_button.set_tooltip_text("Close")
        close_button.add_css_class("flat")  # Use flat style for better appearance
        close_button.connect("clicked", lambda btn: popover.popdown())
        header_box.append(close_button)
        
        content_box.append(header_box)
        
        # First get current border style info
        js_code = """
        (function() {
            const style = getTableBorderStyle();
            return JSON.stringify(style);
        })();
        """
        
        # Call JavaScript and initialize dialog after getting results
        win.webview.evaluate_javascript(
            js_code,
            -1,  # Length
            None,  # Source URI
            None,  # Cancellable
            None,  # Callback
            self._on_get_border_style,  # User data
            {"win": win, "button": button, "content_box": content_box, "popover": popover}  # Additional user data
        )
        
        # Set the content and show the popover
        popover.set_child(content_box)
        popover.popup()
        
    def _on_get_border_style(self, webview, result, user_data):
        """Handle getting current border style from JavaScript"""
        win = user_data["win"]
        content_box = user_data["content_box"]
        popover = user_data["popover"]
        
        # Default values
        current_style = "solid"
        current_width = 1
        
        try:
            # Get JavaScript result and handle both WebKit2 and WebKit1 APIs
            js_result = webview.evaluate_javascript_finish(result)
            result_str = None
            
            try:
                # For newer WebKit2
                if hasattr(js_result, 'get_js_value'):
                    result_str = js_result.get_js_value().to_string()
                else:
                    # For WebKit1
                    result_str = js_result.to_string()
            except:
                result_str = str(js_result)
            
            if result_str:
                # Clean up the string (remove quotes and extra characters if needed)
                result_str = result_str.strip().strip('"').strip("'")
                
                try:
                    import json
                    style_data = json.loads(result_str)
                    if isinstance(style_data, dict):
                        current_style = style_data.get("style", "solid")
                        current_width = style_data.get("width", 1)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract values from a string format
                    pass
        except Exception as e:
            print(f"Error getting border style: {e}")
        
        # Now create the content with the current values
        
        # Create a horizontal box for style and color with linked buttons
        style_color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Create border style dropdown in a MenuButton for compact UI
        style_button = Gtk.MenuButton()
        style_button.set_label(f"Style: {current_style}")
        style_button.set_tooltip_text("Select border style")
        style_button.set_hexpand(True)
        
        # Create the dropdown menu
        popover_menu = Gtk.Popover()
        popover_menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        popover_menu_box.set_margin_start(8)
        popover_menu_box.set_margin_end(8)
        popover_menu_box.set_margin_top(8)
        popover_menu_box.set_margin_bottom(8)
        
        # Add style options as buttons
        style_options = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
        
        for style in style_options:
            style_option = Gtk.Button(label=style)
            style_option.connect("clicked", lambda btn, s=style: [
                self.on_border_style_changed(win, s, width_spin.get_value_as_int()),
                style_button.set_label(f"Style: {s}"),
                popover_menu.popdown()
            ])
            popover_menu_box.append(style_option)
        
        popover_menu.set_child(popover_menu_box)
        style_button.set_popover(popover_menu)
        
        # Color button - a button with a color swatch icon
        color_button = Gtk.Button()
        color_button.set_tooltip_text("Border Color")
        color_button.set_icon_name("preferences-color-symbolic")
        
        # Connect click handler for color button
        color_button.connect("clicked", lambda btn: self._show_color_preset_popover(win, btn))
        
        style_color_box.append(style_button)
        style_color_box.append(color_button)
        content_box.append(style_color_box)
        
        # Border width spinner
        width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)
        width_label.set_hexpand(True)
        
        width_adjustment = Gtk.Adjustment(value=current_width, lower=0, upper=10, step_increment=1)
        width_spin = Gtk.SpinButton()
        width_spin.set_adjustment(width_adjustment)
        
        # Connect spinner to instantly apply width when changed
        width_spin.connect("value-changed", lambda spin: self.on_border_width_changed(
            win,
            current_style,  # Use the current style (we don't have direct access to dropdown value)
            spin.get_value_as_int()
        ))
        
        width_box.append(width_label)
        width_box.append(width_spin)
        content_box.append(width_box)
        
        # Add a separator
        content_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Border display options title
        display_label = Gtk.Label(label="<b>Border Display</b>")
        display_label.set_use_markup(True)
        display_label.set_halign(Gtk.Align.START)
        display_label.set_margin_top(8)
        content_box.append(display_label)
        
        # Create a linked box for primary border toggles
        primary_border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        primary_border_box.add_css_class("linked")
        primary_border_box.set_margin_top(8)
        
        # Create the primary border buttons - with just icons
        border_options = [
            {"icon": "table-border-all-symbolic", "tooltip": "All Borders", "value": "all"},
            {"icon": "table-border-none-symbolic", "tooltip": "No Borders", "value": "none"},
            {"icon": "table-border-outer-symbolic", "tooltip": "Outer Borders", "value": "outer"},
            {"icon": "table-border-inner-symbolic", "tooltip": "Inner Borders", "value": "inner"}
        ]
        
        # Store buttons to access them for combined operations
        border_buttons = {}
        
        for option in border_options:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            
            # Connect the click signal with explicit parameter in lambda
            button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                win, None, width_spin, border_option))
            
            primary_border_box.append(button)
            border_buttons[option["value"]] = button
        
        content_box.append(primary_border_box)
        
        # Create a second linked box for combination border buttons
        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box.add_css_class("linked")
        combo_box.set_margin_top(8)
        
        # Create horizontal/vertical buttons with additional combinations
        combo_options = [
            {"icon": "table-border-horizontal-symbolic", "tooltip": "Horizontal Borders", "value": "horizontal"},
            {"icon": "table-border-vertical-symbolic", "tooltip": "Vertical Borders", "value": "vertical"},
            {"icon": "table-border-outer-horizontal-symbolic", "tooltip": "Outer Horizontal Borders", "value": ["outer", "horizontal"]},
            {"icon": "table-border-outer-vertical-symbolic", "tooltip": "Outer Vertical Borders", "value": ["outer", "vertical"]},
            {"icon": "table-border-inner-horizontal-symbolic", "tooltip": "Inner Horizontal Borders", "value": ["inner", "horizontal"]},
            {"icon": "table-border-inner-vertical-symbolic", "tooltip": "Inner Vertical Borders", "value": ["inner", "vertical"]},
            {"icon": "table-border-outer-inner-horizontal-symbolic", "tooltip": "Outer + Inner Horizontal Borders", "value": ["outer", "inner", "horizontal"]},
            {"icon": "table-border-outer-inner-vertical-symbolic", "tooltip": "Outer + Inner Vertical Borders", "value": ["outer", "inner", "vertical"]}
        ]
        
        # Create a grid for the combo options since we have more buttons now
        combo_grid = Gtk.Grid()
        combo_grid.set_row_spacing(4)
        combo_grid.set_column_spacing(4)
        
        # Organize buttons into a grid (4 buttons per row)
        for i, option in enumerate(combo_options):
            row = i // 4
            col = i % 4
            
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            
            # Handle single values and combined values differently with explicit parameter names
            if isinstance(option["value"], list):
                # If it's a combined value (list), use _apply_combined_borders
                button.connect("clicked", lambda btn, border_types=option["value"]: self._apply_combined_borders(
                    win, width_spin, border_types))
            else:
                # If it's a single value, use the standard handler
                button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                    win, None, width_spin, border_option))
            
            # Add the button to the grid
            combo_grid.attach(button, col, row, 1, 1)
        
        content_box.append(combo_grid)

    def on_border_display_option_clicked(self, win, popover, width_spin, option):
        """Apply the selected border display option"""
        # First ensure there's a border style set - default to "solid" if none
        js_code = f"""
        (function() {{
            // Get current border style
            const currentStyle = getTableBorderStyle();
            let style = currentStyle ? currentStyle.style : null;
            
            // If no style is set or it's 'none', default to 'solid'
            if (!style || style === 'none') {{
                style = 'solid';
                setTableBorderStyle(style, null, null);
            }}
            
            // Now apply the border option
            applyTableBorderSides(['{option}']);
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {option} borders")
        
        # Close the popover if provided (but for instant apply we pass None)
        if popover:
            popover.popdown()

    def _apply_combined_borders(self, win, width_spin, border_types):
        """Apply a combination of border types (e.g., outer + horizontal)"""
        # Join the border types for the JavaScript array
        border_types_str = "', '".join(border_types)
        
        # Execute JavaScript to apply the combined border options
        js_code = f"""
        (function() {{
            // Get current border style
            const currentStyle = getTableBorderStyle();
            let style = currentStyle ? currentStyle.style : null;
            
            // If no style is set or it's 'none', default to 'solid'
            if (!style || style === 'none') {{
                style = 'solid';
                setTableBorderStyle(style, null, null);
            }}
            
            // Now apply the combined border options
            applyTableBorderSides(['{border_types_str}']);
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {' + '.join(border_types)} borders")
    def on_border_style_changed(self, win, style, width):
        """Apply border style change immediately"""
        # Execute JavaScript to apply the border style
        js_code = f"""
        (function() {{
            setTableBorderStyle('{style}', {width}, null);
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {style} border style")

    def on_border_width_changed(self, win, style, width):
        """Apply border width change immediately"""
        # Execute JavaScript to apply the border width
        js_code = f"""
        (function() {{
            setTableBorderWidth({width});
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {width}px border width")

    def _show_color_preset_popover(self, win, button):
        """Create a color picker popover with preset colors that apply instantly"""
        popover = Gtk.Popover()
        popover.set_parent(button)
        
        # Create grid layout for color swatches
        grid = Gtk.Grid()
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        grid.set_margin_start(10)
        grid.set_margin_end(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        
        # Define preset colors
        preset_colors = [
            "#000000", "#333333", "#666666", "#999999", "#CCCCCC",
            "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
            "#FF00FF", "#00FFFF", "#800000", "#008000", "#000080",
            "#808000", "#800080", "#008080", "#FFA500", "#A52A2A"
        ]
        
        # Create color buttons
        for i, color in enumerate(preset_colors):
            row = i // 5
            col = i % 5
            
            # Create a button with color style
            button = Gtk.Button()
            button.set_size_request(24, 24)
            
            # Apply color to button using CSS
            css_provider = Gtk.CssProvider()
            css_data = f"button {{ background-color: {color}; }}".encode('utf8')
            css_provider.load_from_data(css_data)
            
            ctx = button.get_style_context()
            ctx.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            # Connect click handler to apply the color
            button.connect("clicked", lambda btn, c=color: self._apply_preset_color(win, popover, c))
            
            # Add to grid
            grid.attach(button, col, row, 1, 1)
        
        popover.set_child(grid)
        popover.popup()

    def _apply_preset_color(self, win, popover, color):
        """Apply a preset color to the table border"""
        # Execute JavaScript to apply the color
        js_code = f"""
        (function() {{
            setTableBorderColor('{color}');
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied border color: {color}")
        
        # Close the popover
        popover.popdown()

    def on_border_color_button_clicked(self, win, button):
        """Show the border color picker dialog"""
        try:
            # Different GTK versions may use different color dialog widgets
            # Try different approaches based on the GTK version
            
            # Method 1: Modern Gtk.ColorDialog (GTK4)
            try:
                color_dialog = Gtk.ColorDialog()
                color_dialog.set_title("Choose Border Color")
                
                # Set initial color from the current border
                # First get the current border color from JavaScript
                win.webview.evaluate_javascript(
                    """(function() { 
                        const style = getTableBorderStyle(); 
                        return style ? style.color : '#000000';
                    })();""", 
                    -1,  # Length
                    None,  # Source URI
                    None,  # Cancellable
                    None,  # Callback
                    self._on_get_current_border_color,  # User data
                    win  # Additional user data
                )
                
                # Show the color dialog in a deferred way
                GLib.timeout_add(100, self._show_color_dialog, win, color_dialog, button)
                return
            except (AttributeError, TypeError):
                # ColorDialog not available, try alternative
                pass
                
            # Method 2: ColorChooserDialog (GTK3+)
            try:
                # Create a color chooser dialog
                color_dialog = Gtk.ColorChooserDialog(
                    title="Choose Border Color",
                    parent=win
                )
                
                # Set up dialog buttons
                color_dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
                color_dialog.add_button("_Select", Gtk.ResponseType.OK)
                color_dialog.set_default_response(Gtk.ResponseType.OK)
                
                # Set initial color (black as default)
                try:
                    # Using RGBA to set color
                    rgba = Gdk.RGBA()
                    rgba.parse("#000000")
                    color_dialog.set_rgba(rgba)
                except:
                    # Older method
                    try:
                        color = Gdk.Color.parse("#000000")
                        color_dialog.set_current_color(color)
                    except:
                        pass  # If both methods fail, accept default
                
                # Connect the response signal
                color_dialog.connect("response", self._on_color_dialog_response, win)
                
                # Show the dialog
                color_dialog.show()
                return
            except (AttributeError, TypeError):
                # ColorChooserDialog not available, try fallback
                pass
                
            # Method 3: Ultimate fallback - simple popover with preset colors
            self._show_color_preset_popover(win, button)
                
        except Exception as e:
            print(f"Error showing color dialog: {e}")
            win.statusbar.set_text("Could not open color picker")
            


    def _on_get_current_border_color(self, webview, result, win):
        """Handle getting the current border color from JavaScript"""
        try:
            # Different WebKit versions return different result types
            # Try the most common methods to extract the value
            js_result = webview.evaluate_javascript_finish(result)
            
            # Method 1: Direct string conversion (newer WebKit)
            try:
                color_value = str(js_result)
                if color_value.startswith('#') or color_value.startswith('rgb'):
                    win.current_border_color = color_value
                    return
            except:
                pass
                
            # Method 2: get_js_value (some WebKit versions)
            try:
                color_value = js_result.get_js_value().to_string()
                win.current_border_color = color_value
                return
            except:
                pass
                
            # Method 3: to_string (some WebKit versions)
            try:
                color_value = js_result.to_string()
                win.current_border_color = color_value
                return
            except:
                pass
                
            # Default if all methods fail
            win.current_border_color = "#000000"
                
        except Exception as e:
            print(f"Error getting current border color: {e}")
            win.current_border_color = "#000000"  # Default to black



    def table_color_js(self):
        """JavaScript for table color operations with theme preservation"""
        return """
        // Function to set table background color
        function setTableBackgroundColor(color) {
            if (!activeTable) return false;
            
            activeTable.style.backgroundColor = color;
            
            // Store the background color
            activeTable.setAttribute('data-bg-color', color);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set header background color
        function setHeaderBackgroundColor(color) {
            if (!activeTable) return false;
            
            const headers = activeTable.querySelectorAll('th');
            headers.forEach(header => {
                header.style.backgroundColor = color;
            });
            
            // Store the header color
            activeTable.setAttribute('data-header-color', color);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set cell background color (only for the active cell)
        function setCellBackgroundColor(color) {
            if (!activeTable) return false;
            
            // Get the current selection
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Find the active cell
            let activeCell = selection.anchorNode;
            
            // If the selection is in a text node, get the parent element
            if (activeCell.nodeType === Node.TEXT_NODE) {
                activeCell = activeCell.parentElement;
            }
            
            // Find the closest td or th element
            while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {
                activeCell = activeCell.parentElement;
            }
            
            // If we found a cell and it belongs to our active table
            if (activeCell && activeTable.contains(activeCell)) {
                activeCell.style.backgroundColor = color;
                
                // Store the color on the cell itself
                activeCell.setAttribute('data-cell-color', color);
                
                // Notify that content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
                
                return true;
            }
            
            return false;
        }
        
        // Function to get current table colors
        function getTableColors() {
            if (!activeTable) return null;
            
            // Get stored values
            const bgColor = activeTable.getAttribute('data-bg-color') || activeTable.style.backgroundColor || '';
            const headerColor = activeTable.getAttribute('data-header-color') || '';
            const borderColor = activeTable.getAttribute('data-border-color') || '';
            
            // Get active cell color if there's a selection
            let cellColor = '';
            const selection = window.getSelection();
            if (selection.rangeCount) {
                let activeCell = selection.anchorNode;
                if (activeCell.nodeType === Node.TEXT_NODE) {
                    activeCell = activeCell.parentElement;
                }
                while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {
                    activeCell = activeCell.parentElement;
                }
                if (activeCell && activeTable.contains(activeCell)) {
                    cellColor = activeCell.getAttribute('data-cell-color') || activeCell.style.backgroundColor || '';
                }
            }
            
            return {
                background: bgColor,
                header: headerColor,
                cell: cellColor,
                border: borderColor
            };
        }
        
        // Function to preserve table colors during theme changes
        function preserveTableColors() {
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                // Preserve background color
                const bgColor = table.getAttribute('data-bg-color');
                if (bgColor) {
                    table.style.backgroundColor = bgColor;
                }
                
                // Preserve header colors
                const headerColor = table.getAttribute('data-header-color');
                const headers = table.querySelectorAll('th');
                headers.forEach(header => {
                    if (headerColor) {
                        header.style.backgroundColor = headerColor;
                    } else if (!header.getAttribute('data-cell-color')) {
                        // Set default header color based on theme
                        header.style.backgroundColor = getHeaderBgColor();
                    }
                });
                
                // Preserve cell colors
                const cells = table.querySelectorAll('td, th');
                cells.forEach(cell => {
                    const cellColor = cell.getAttribute('data-cell-color');
                    if (cellColor) {
                        cell.style.backgroundColor = cellColor;
                    }
                });
                
                // Preserve border colors
                const borderColor = table.getAttribute('data-border-color');
                if (borderColor) {
                    cells.forEach(cell => {
                        cell.style.borderColor = borderColor;
                    });
                }
            });
        }
        """
        
    def _initialize_table_properties(self, win, popover):
        """Initialize the table properties popup with current values"""
        # Get current table properties
        js_code = """
        (function() {
            const borderProps = getTableBorderProperties();
            const margins = getTableMargins();
            const colors = getTableColors();
            
            return JSON.stringify({
                border: borderProps,
                margins: margins,
                colors: colors
            });
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self._on_get_table_properties(win, webview, result, popover),
            None
        )

    def _parse_color_string(self, color_str):
        """Parse a color string (hex, rgb, or rgba) into a Gdk.RGBA object"""
        try:
            rgba = Gdk.RGBA()
            
            if color_str.startswith('#'):
                # Hex color
                rgba.parse(color_str)
                return rgba
            elif color_str.startswith('rgb'):
                # RGB(A) color
                import re
                match = re.search(r'rgba?\(([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s]+([\d.]+))?\)', color_str)
                if match:
                    r, g, b = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    a = float(match.group(4)) if match.group(4) else 1.0
                    
                    # Convert 0-255 range to 0-1 range if necessary
                    if r > 1 or g > 1 or b > 1:
                        r, g, b = r/255, g/255, b/255
                    
                    rgba.red, rgba.green, rgba.blue, rgba.alpha = r, g, b, a
                    return rgba
            
            return None
        except Exception as e:
            print(f"Error parsing color string '{color_str}': {e}")
            return None

    # 7. Check if using dark theme
    def _is_dark_theme(self):
        """Check if the system is using dark theme"""
        try:
            style_manager = Adw.StyleManager.get_default()
            return style_manager.get_dark()
        except:
            # Fallback method
            settings = Gtk.Settings.get_default()
            return settings.get_property("gtk-application-prefer-dark-theme")

    def _rgba_to_color(self, rgba):
        """Convert Gdk.RGBA to Gdk.Color for compatibility"""
        color = Gdk.Color()
        color.red = int(rgba.red * 65535)
        color.green = int(rgba.green * 65535)
        color.blue = int(rgba.blue * 65535)
        return color



##########################  show html
    def on_show_html_clicked(self, win, btn):
        """Handle Show HTML button click"""
        win.statusbar.set_text("Getting HTML content...")
        
        # Execute JavaScript to get the full HTML content
        js_code = """
        (function() {
            // Get the complete HTML content of the editor
            const editorContent = document.getElementById('editor').innerHTML;
            return editorContent;
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self.show_html_dialog(win, webview, result),
            None
        )

    # 3. Function to display the HTML in a dialog

    def show_html_dialog(self, win, webview, result):
        """Show the HTML content in a dialog"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            html_content = ""
            
            if js_result:
                # Get the HTML content
                if hasattr(js_result, 'get_js_value'):
                    html_content = js_result.get_js_value().to_string()
                else:
                    html_content = js_result.to_string()
                
                # Create a dialog with resizable text view
                dialog = Adw.Dialog()
                dialog.set_title("HTML Source")
                dialog.set_content_width(600)
                dialog.set_content_height(400)
                
                # Create content box
                content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                content_box.set_margin_top(24)
                content_box.set_margin_bottom(24)
                content_box.set_margin_start(24)
                content_box.set_margin_end(24)
                
                # Add explanation label
                explanation = Gtk.Label()
                explanation.set_markup("<b>HTML Source Code:</b>")
                explanation.set_halign(Gtk.Align.START)
                content_box.append(explanation)
                
                # Create scrolled window for text view
                scrolled_window = Gtk.ScrolledWindow()
                scrolled_window.set_vexpand(True)
                scrolled_window.set_hexpand(True)
                
                # Create text view for HTML content
                text_view = Gtk.TextView()
                text_view.set_editable(True)  # Allow editing
                text_view.set_monospace(True)  # Use monospace font for code
                text_view.set_wrap_mode(Gtk.WrapMode.WORD)
                
                # Create text buffer and set content
                text_buffer = text_view.get_buffer()
                text_buffer.set_text(html_content)
                
                scrolled_window.set_child(text_view)
                content_box.append(scrolled_window)
                
                # Add buttons box
                buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                buttons_box.set_halign(Gtk.Align.END)
                buttons_box.set_margin_top(12)
                
                # Copy button - left aligned with spacer to separate from other buttons
                copy_button = Gtk.Button(label="Copy to Clipboard")
                copy_button.connect("clicked", lambda btn: self.copy_html_to_clipboard(win, text_buffer))
                copy_button.set_halign(Gtk.Align.START)
                
                # Button spacer to push close/apply buttons to the right
                button_spacer = Gtk.Box()
                button_spacer.set_hexpand(True)
                
                # Apply changes button
                apply_button = Gtk.Button(label="Apply Changes")
                apply_button.add_css_class("suggested-action")
                apply_button.connect("clicked", lambda btn: self.apply_html_changes(win, dialog, text_buffer))
                
                # Close button
                close_button = Gtk.Button(label="Close")
                close_button.connect("clicked", lambda btn: dialog.close())
                
                buttons_box.append(copy_button)
                buttons_box.append(button_spacer)
                buttons_box.append(close_button)
                buttons_box.append(apply_button)
                content_box.append(buttons_box)
                
                # Set dialog content and present
                dialog.set_child(content_box)
                dialog.present(win)
                
                # Update status
                win.statusbar.set_text("HTML content displayed")
            else:
                win.statusbar.set_text("Failed to get HTML content")
                
        except Exception as e:
            print(f"Error displaying HTML: {e}")
            win.statusbar.set_text(f"Error displaying HTML: {e}")

    # 4. Function to apply HTML changes

    def apply_html_changes(self, win, dialog, text_buffer):
        """Apply the edited HTML content back to the editor"""
        try:
            # Get the text from the buffer
            start_iter = text_buffer.get_start_iter()
            end_iter = text_buffer.get_end_iter()
            html_content = text_buffer.get_text(start_iter, end_iter, True)
            
            # Escape for JavaScript
            js_content = html_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            
            # Set the content in the editor
            js_code = f'setContent("{js_content}");'
            self.execute_js(win, js_code)
            
            # Close the dialog
            dialog.close()
            
            # Update status
            win.statusbar.set_text("HTML changes applied")
            
            # Mark document as modified
            win.modified = True
            self.update_window_title(win)
            
        except Exception as e:
            print(f"Error applying HTML changes: {e}")
            win.statusbar.set_text(f"Error applying HTML changes: {e}")

    def copy_html_to_clipboard(self, win, text_buffer):
        """Copy the HTML content to clipboard"""
        try:
            # Get the text from the buffer
            start_iter = text_buffer.get_start_iter()
            end_iter = text_buffer.get_end_iter()
            html_content = text_buffer.get_text(start_iter, end_iter, True)
            
            # Get the clipboard
            clipboard = Gdk.Display.get_default().get_clipboard()
            
            # Set the text to the clipboard
            clipboard.set(html_content)
            
            # Update status
            win.statusbar.set_text("HTML copied to clipboard")
            
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            win.statusbar.set_text(f"Error copying to clipboard: {e}")
##########################  /show html     
    def set_theme_colors_js(self):
        """JavaScript to update theme colors with enhanced debugging."""
        return """
        function setThemeColors(isDark) {
            console.log(`Setting theme colors. isDark: ${isDark}`);
            
            // Update styles based on theme
            const editorDiv = document.getElementById('editor');
            if (editorDiv) {
                const theme = isDark ? 'dark' : 'light';
                editorDiv.className = 'editor ' + theme;
                console.log(`Applied classes: ${editorDiv.className}`);
            }
            
            // Preserve table colors during theme change
            preserveTableColors();
            
            // Update all tables and elements with theme
            updateTableBorders();
            updateFixedBlockStyles();
            updateTextBoxStyles();
            
            console.log('Theme change completed');
        }
        """
 #############################
 # Fixed functions to address the deprecation warnings and AttributeError

    # 1. Fixed _reset_default_colors that works without table_props_popover
    def _reset_default_colors(self, win):
        """Reset table colors to default values"""
        js_code = """
        (function() {
            if (!activeTable) return false;
            
            // Get default colors based on theme
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Reset border color
            setTableBorderColor(borderColor);
            
            // Reset table background color
            activeTable.style.backgroundColor = '';
            activeTable.removeAttribute('data-bg-color');
            
            // Reset header color
            const headers = activeTable.querySelectorAll('th');
            headers.forEach(header => {
                header.style.backgroundColor = headerBgColor;
            });
            activeTable.setAttribute('data-header-color', headerBgColor);
            
            // Reset all cell colors
            const cells = activeTable.querySelectorAll('td');
            cells.forEach(cell => {
                cell.style.backgroundColor = '';
                cell.removeAttribute('data-cell-color');
            });
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return JSON.stringify({
                border: borderColor,
                header: headerBgColor
            });
        })();
        """
        
        # Execute the reset and update color buttons
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self._update_color_buttons_after_reset(webview, result, win),
            None
        )
        
        win.statusbar.set_text("Reset to default colors")

    # 2. Helper method to update color buttons after reset
    def _update_color_buttons_after_reset(self, webview, result, win):
        """Update color buttons after resetting to defaults"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                result_str = js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result)
                import json
                colors = json.loads(result_str)
                
                # Update color buttons if they exist in the current context
                for child in win.main_box:
                    if isinstance(child, Gtk.Popover):
                        content = child.get_child()
                        if content and isinstance(content, Gtk.Box):
                            for widget in content:
                                if isinstance(widget, Gtk.Notebook):
                                    color_page = widget.get_nth_page(2)  # Color tab
                                    if color_page:
                                        # Update border color button
                                        if hasattr(color_page, 'border_color_button'):
                                            rgba = self._parse_color_string(colors['border'])
                                            if rgba:
                                                color_page.border_color_button.set_rgba(rgba)
                                        
                                        # Clear other color buttons
                                        if hasattr(color_page, 'table_color_button'):
                                            rgba = Gdk.RGBA()
                                            rgba.parse('#ffffff')
                                            color_page.table_color_button.set_rgba(rgba)
                                        
                                        if hasattr(color_page, 'header_color_button'):
                                            rgba = self._parse_color_string(colors['header'])
                                            if rgba:
                                                color_page.header_color_button.set_rgba(rgba)
                                        
                                        if hasattr(color_page, 'cell_color_button'):
                                            rgba = Gdk.RGBA()
                                            rgba.parse('#ffffff')
                                            color_page.cell_color_button.set_rgba(rgba)
        except Exception as e:
            print(f"Error updating color buttons: {e}")




    # 1. Updated _create_color_tab with proper GTK4 color dialogs
    def _create_color_tab(self, win, popover):
        """Create the color properties tab with GTK4 compatible color handling"""
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        color_box.set_margin_start(12)
        color_box.set_margin_end(12)
        color_box.set_margin_top(12)
        color_box.set_margin_bottom(12)
        
        # Helper function to create color button with custom color picker
        def create_color_button_row(label_text, apply_function):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            
            # Create a button with color icon instead of ColorButton
            color_button = Gtk.Button()
            color_button.set_size_request(40, 24)
            
            # Create a DrawingArea for color display
            color_display = Gtk.DrawingArea()
            color_display.set_size_request(30, 18)
            color_button.set_child(color_display)
            
            # Default color
            color_button.current_color = "#000000"
            
            # Draw function for color display
            def draw_color(area, cr, width, height, data):
                rgba = self._parse_color_string(color_button.current_color)
                if rgba:
                    cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
                else:
                    cr.set_source_rgba(0, 0, 0, 1)  # Default to black
                cr.rectangle(2, 2, width - 4, height - 4)
                cr.fill()
                
                # Draw border
                cr.set_source_rgba(0.5, 0.5, 0.5, 1)
                cr.rectangle(2, 2, width - 4, height - 4)
                cr.set_line_width(1)
                cr.stroke()
            
            color_display.set_draw_func(draw_color, None)
            
            # Connect click handler to show color dialog
            color_button.connect("clicked", lambda btn: self._show_color_dialog(win, btn, apply_function))
            
            row_box.append(label)
            row_box.append(color_button)
            return row_box, color_button
        
        # Border color row
        border_color_box, border_color_button = create_color_button_row(
            "Border Color:", self._apply_border_color)
        color_box.append(border_color_box)
        
        # Table background color row
        table_color_box, table_color_button = create_color_button_row(
            "Table Color:", self._apply_table_color)
        color_box.append(table_color_box)
        
        # Header color row
        header_color_box, header_color_button = create_color_button_row(
            "Header Color:", self._apply_header_color)
        color_box.append(header_color_box)
        
        # Cell color row
        cell_color_box, cell_color_button = create_color_button_row(
            "Current Cell Color:", self._apply_cell_color)
        color_box.append(cell_color_box)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        color_box.append(separator)
        
        # Add default button
        default_button = Gtk.Button(label="Reset to Default Colors")
        default_button.connect("clicked", lambda btn: self._reset_default_colors(win))
        color_box.append(default_button)
        
        # Store color buttons for later initialization
        color_box.border_color_button = border_color_button
        color_box.table_color_button = table_color_button
        color_box.header_color_button = header_color_button
        color_box.cell_color_button = cell_color_button
        
        return color_box

    # 2. Custom color dialog function
    def _show_color_dialog(self, win, color_button, apply_function):
        """Show a color dialog compatible with GTK4"""
        try:
            # Try using GTK4 ColorDialog
            try:
                dialog = Gtk.ColorDialog()
                dialog.set_title("Choose Color")
                
                # Set initial color
                initial_rgba = self._parse_color_string(color_button.current_color)
                if not initial_rgba:
                    initial_rgba = Gdk.RGBA()
                    initial_rgba.parse("#000000")
                
                dialog.choose_rgba(
                    win,
                    initial_rgba,
                    None,
                    lambda dlg, result, data: self._on_color_chosen(dlg, result, color_button, apply_function, win),
                    None
                )
                return
            except AttributeError:
                # ColorDialog not available, use ColorChooserDialog
                dialog = Gtk.ColorChooserDialog(
                    title="Choose Color",
                    transient_for=win
                )
                
                # Set initial color
                initial_rgba = self._parse_color_string(color_button.current_color)
                if initial_rgba:
                    try:
                        dialog.set_rgba(initial_rgba)
                    except AttributeError:
                        pass
                
                # Connect response handler
                dialog.connect("response", lambda dlg, response: self._on_color_dialog_response(
                    dlg, response, color_button, apply_function, win))
                
                dialog.show()
        except Exception as e:
            print(f"Error showing color dialog: {e}")
            # Fallback to preset color popover
            self._show_color_preset_popover(win, color_button, apply_function)

    # 3. Handle color selection from dialog
    def _on_color_chosen(self, dialog, result, color_button, apply_function, win):
        """Handle color selection from GTK4 ColorDialog"""
        try:
            rgba = dialog.choose_rgba_finish(result)
            if rgba:
                # Convert to hex color
                hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
                color_button.current_color = hex_color
                
                # Update color display
                color_display = color_button.get_child()
                if color_display:
                    color_display.queue_draw()
                
                # Apply the color
                apply_function(win, hex_color)
        except Exception as e:
            print(f"Error choosing color: {e}")

    # 4. Handle response from ColorChooserDialog
    def _on_color_dialog_response(self, dialog, response, color_button, apply_function, win):
        """Handle response from ColorChooserDialog"""
        if response == Gtk.ResponseType.OK:
            try:
                rgba = dialog.get_rgba()
                hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
                color_button.current_color = hex_color
                
                # Update color display
                color_display = color_button.get_child()
                if color_display:
                    color_display.queue_draw()
                
                # Apply the color
                apply_function(win, hex_color)
            except Exception as e:
                print(f"Error getting color: {e}")
        
        dialog.destroy()

    # 5. Fixed _apply_border_color to accept hex color directly
    def _apply_border_color(self, win, hex_color):
        """Apply border color"""
        try:
            print(f"Applying border color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply the color to all cells' borders
                const cells = activeTable.querySelectorAll('td, th');
                cells.forEach(cell => {{
                    cell.style.borderColor = '{hex_color}';
                }});
                
                // Store the color for theme preservation
                activeTable.setAttribute('data-border-color', '{hex_color}');
                
                // Debug output
                console.log('Applied border color:', '{hex_color}');
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }} catch(e) {{
                    console.log("Could not notify about content change:", e);
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied border color: {hex_color}")
        except Exception as e:
            print(f"Error applying border color: {e}")
            win.statusbar.set_text("Error applying border color")

    # 6. Fixed _apply_table_color to accept hex color directly
    def _apply_table_color(self, win, hex_color):
        """Apply table background color"""
        try:
            print(f"Applying table color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply the color
                activeTable.style.backgroundColor = '{hex_color}';
                
                // Store the color for theme preservation
                activeTable.setAttribute('data-bg-color', '{hex_color}');
                
                // Debug output
                console.log('Applied table color:', '{hex_color}');
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }} catch(e) {{
                    console.log("Could not notify about content change:", e);
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied table color: {hex_color}")
        except Exception as e:
            print(f"Error applying table color: {e}")
            win.statusbar.set_text("Error applying table color")

    # 7. Fixed _apply_header_color to accept hex color directly
    def _apply_header_color(self, win, hex_color):
        """Apply header background color"""
        try:
            print(f"Applying header color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply the color to all header cells
                const headers = activeTable.querySelectorAll('th');
                headers.forEach(header => {{
                    header.style.backgroundColor = '{hex_color}';
                }});
                
                // Store the color for theme preservation
                activeTable.setAttribute('data-header-color', '{hex_color}');
                
                // Debug output
                console.log('Applied header color:', '{hex_color}');
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }} catch(e) {{
                    console.log("Could not notify about content change:", e);
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied header color: {hex_color}")
        except Exception as e:
            print(f"Error applying header color: {e}")
            win.statusbar.set_text("Error applying header color")

    # 8. Fixed _apply_cell_color to accept hex color directly
    def _apply_cell_color(self, win, hex_color):
        """Apply cell background color"""
        try:
            print(f"Applying cell color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Get the current selection
                const selection = window.getSelection();
                if (!selection.rangeCount) return false;
                
                // Find the active cell
                let activeCell = selection.anchorNode;
                
                // If the selection is in a text node, get the parent element
                if (activeCell.nodeType === Node.TEXT_NODE) {{
                    activeCell = activeCell.parentElement;
                }}
                
                // Find the closest td or th element
                while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {{
                    activeCell = activeCell.parentElement;
                }}
                
                // If we found a cell and it belongs to our active table
                if (activeCell && activeTable.contains(activeCell)) {{
                    activeCell.style.backgroundColor = '{hex_color}';
                    
                    // Store the color on the cell itself
                    activeCell.setAttribute('data-cell-color', '{hex_color}');
                    
                    // Debug output
                    console.log('Applied cell color:', '{hex_color}');
                    
                    // Notify that content changed
                    try {{
                        window.webkit.messageHandlers.contentChanged.postMessage('changed');
                    }} catch(e) {{
                        console.log("Could not notify about content change:", e);
                    }}
                    
                    return true;
                }}
                
                return false;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied cell color: {hex_color}")
        except Exception as e:
            print(f"Error applying cell color: {e}")
            win.statusbar.set_text("Error applying cell color")

    # 9. Updated _on_get_table_properties to properly initialize custom color buttons
    def _on_get_table_properties(self, win, webview, result, popover):
        """Handle getting current table properties"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            result_str = None
            
            if hasattr(js_result, 'get_js_value'):
                result_str = js_result.get_js_value().to_string()
            else:
                result_str = js_result.to_string()
            
            if result_str:
                import json
                properties = json.loads(result_str)
                
                # Get references to the tab pages
                content_box = popover.get_child()
                notebook = None
                
                # Find the notebook widget (skip header)
                for child in content_box:
                    if isinstance(child, Gtk.Notebook):
                        notebook = child
                        break
                
                if notebook:
                    border_page = notebook.get_nth_page(0)
                    margin_page = notebook.get_nth_page(1)
                    color_page = notebook.get_nth_page(2)
                    
                    # Initialize border controls
                    if properties.get('border'):
                        border_style = properties['border'].get('style', 'solid')
                        border_width = properties['border'].get('width', 1)
                        has_shadow = properties['border'].get('shadow', False)
                        
                        # Find index of style
                        styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
                        try:
                            style_index = styles.index(border_style)
                        except ValueError:
                            style_index = 0  # Default to solid
                        
                        border_page.style_combo.set_selected(style_index)
                        border_page.width_spin.set_value(border_width)
                        border_page.shadow_switch.set_active(has_shadow)
                    
                    # Initialize margin controls
                    if properties.get('margins'):
                        margins = properties['margins']
                        for side in ['top', 'right', 'bottom', 'left']:
                            if side in margin_page.margin_controls and side in margins:
                                margin_page.margin_controls[side].set_value(margins[side])
                    
                    # Initialize color controls
                    if properties.get('colors'):
                        colors = properties['colors']
                        
                        # Set border color
                        if colors.get('border'):
                            color_page.border_color_button.current_color = colors['border']
                            color_display = color_page.border_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
                        # Set table background color
                        if colors.get('background'):
                            color_page.table_color_button.current_color = colors['background']
                            color_display = color_page.table_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
                        # Set header color
                        if colors.get('header'):
                            color_page.header_color_button.current_color = colors['header']
                            color_display = color_page.header_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
                        # Set cell color (if selected)
                        if colors.get('cell'):
                            color_page.cell_color_button.current_color = colors['cell']
                            color_display = color_page.cell_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
        except Exception as e:
            print(f"Error initializing table properties: {e}")        

    def table_event_handlers_js(self):
        """JavaScript for table event handlers with handle hiding during editing and tab navigation"""
        return """
        // Function to save editor state
        function saveState() {
            const editor = document.getElementById('editor');
            if (!editor) return;
            
            window.undoStack.push(editor.innerHTML);
            if (window.undoStack.length > 100) {
                window.undoStack.shift();
            }
        }
        
        // Function to handle dark mode changes
        function handleColorSchemeChange(e) {
            const tables = document.querySelectorAll('table');
            tables.forEach(updateTableThemeColors);
        }
        
        // Function to hide table handles
        function hideTableHandles() {
            if (activeTable) {
                const dragHandle = activeTable.querySelector('.table-drag-handle');
                const resizeHandle = activeTable.querySelector('.table-handle');
                
                if (dragHandle) dragHandle.style.display = 'none';
                if (resizeHandle) resizeHandle.style.display = 'none';
            }
        }
        
        // Function to show table handles
        function showTableHandles() {
            if (activeTable) {
                const dragHandle = activeTable.querySelector('.table-drag-handle');
                const resizeHandle = activeTable.querySelector('.table-handle');
                
                if (dragHandle) dragHandle.style.display = 'flex';
                if (resizeHandle) resizeHandle.style.display = 'block';
            }
        }
        
        // Check if element is a table cell
        function isTableCell(element) {
            return element && (element.tagName === 'TD' || element.tagName === 'TH');
        }
        
        // Find parent cell element
        function findParentCell(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'TD' || element.tagName === 'TH') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Add event handlers for table interactions
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Add the custom style for table handles
            addTableHandleStyles();
            
            // Handle mouse down events
            editor.addEventListener('mousedown', function(e) {
                // Prevent selection of table handles
                if (e.target.classList.contains('table-handle') || 
                    e.target.classList.contains('table-drag-handle')) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                
                let tableElement = findParentTable(e.target);
                
                if (e.target.classList.contains('table-drag-handle')) {
                    if (e.button === 0) { // Left mouse button
                        startTableDrag(e, findParentTable(e.target));
                    }
                }
                
                if (e.target.classList.contains('table-handle')) {
                    startTableResize(e, findParentTable(e.target));
                }
            });
            
            // Handle focus events on cells to hide handles when editing
            editor.addEventListener('focusin', function(e) {
                const cell = findParentCell(e.target);
                if (cell && activeTable && activeTable.contains(cell)) {
                    hideTableHandles();
                }
            });
            
            // Handle when user starts typing in a cell
            editor.addEventListener('keydown', function(e) {
                const cell = findParentCell(e.target);
                if (cell && activeTable && activeTable.contains(cell)) {
                    // Hide handles when typing in cells (except for navigation keys and Tab)
                    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab', 'Escape', 'Shift'].includes(e.key)) {
                        hideTableHandles();
                    }
                }
            });
            
            // Handle mouse move events
            document.addEventListener('mousemove', function(e) {
                if (isDragging && activeTable) {
                    moveTable(e);
                }
                if (isResizing && activeTable) {
                    resizeTable(e);
                }
            });
            
            // Handle mouse up events
            document.addEventListener('mouseup', function() {
                if (isDragging || isResizing) {
                    isDragging = false;
                    isResizing = false;
                    document.body.style.cursor = '';
                    
                    if (activeTable) {
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            });
            
            // Handle click events for table selection
            editor.addEventListener('click', function(e) {
                let tableElement = findParentTable(e.target);
                
                if (!tableElement) {
                    // We clicked outside any table
                    if (activeTable) {
                        // If there was a previously active table, deactivate it
                        deactivateAllTables();
                    } else {
                        // Even if there was no active table, still send the deactivation message
                        try {
                            window.webkit.messageHandlers.tablesDeactivated.postMessage('tables-deactivated');
                        } catch(e) {
                            console.log("Could not notify about table deactivation:", e);
                        }
                    }
                } else if (tableElement !== activeTable) {
                    // We clicked on a different table than the currently active one
                    deactivateAllTables();
                    activateTable(tableElement);
                    
                    // Show handles unless we clicked inside a cell for editing
                    const cell = findParentCell(e.target);
                    if (!cell || !isTableCell(e.target)) {
                        showTableHandles();
                    }
                    
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
                } else {
                    // Clicking on the same table
                    const cell = findParentCell(e.target);
                    if (cell) {
                        // If clicking on a cell, hide handles for editing
                        hideTableHandles();
                    } else if (!e.target.classList.contains('table-handle') && 
                              !e.target.classList.contains('table-drag-handle')) {
                        // If clicking elsewhere on the table (not handles), show handles
                        showTableHandles();
                    }
                }
            });
            
            // Add a focusout handler to show handles again when leaving a cell
            editor.addEventListener('focusout', function(e) {
                if (activeTable) {
                    // Check if the focus is moving outside the table
                    setTimeout(() => {
                        const newFocusElement = document.activeElement;
                        if (!activeTable.contains(newFocusElement)) {
                            showTableHandles();
                        } else {
                            // If focus moved to another cell in the same table, keep handles hidden
                            const newCell = findParentCell(newFocusElement);
                            if (!newCell) {
                                showTableHandles();
                            }
                        }
                    }, 0);
                }
            });

            // Add a document-level click handler that will deactivate tables when clicking outside the editor
            document.addEventListener('click', function(e) {
                // Check if the click is outside the editor
                if (!editor.contains(e.target) && activeTable) {
                    deactivateAllTables();
                }
            });

            // Listen for color scheme changes
            if (window.matchMedia) {
                const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
                // Modern approach (newer browsers)
                if (colorSchemeQuery.addEventListener) {
                    colorSchemeQuery.addEventListener('change', handleColorSchemeChange);
                } 
                // Legacy approach (older browsers)
                else if (colorSchemeQuery.addListener) {
                    colorSchemeQuery.addListener(handleColorSchemeChange);
                }
            }
        });
        """            


    def init_editor_js(self):
        """JavaScript to initialize the editor and set up event listeners with improved table tab navigation"""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Give the editor a proper tabindex to ensure it can capture keyboard focus
            editor.setAttribute('tabindex', '0');
            
            // Function to find the next cell in the table
            function findNextCell(currentCell) {
                const row = currentCell.parentElement;
                const table = row.parentElement.parentElement; // tr -> tbody/thead -> table
                const cellIndex = Array.from(row.cells).indexOf(currentCell);
                const rowIndex = Array.from(table.rows).indexOf(row);
                
                // Try next cell in same row
                if (cellIndex < row.cells.length - 1) {
                    return row.cells[cellIndex + 1];
                }
                
                // Try first cell in next row
                if (rowIndex < table.rows.length - 1) {
                    return table.rows[rowIndex + 1].cells[0];
                }
                
                // If at the last cell of the table, create a new row
                const newRow = table.insertRow(-1);
                for (let i = 0; i < row.cells.length; i++) {
                    const newCell = newRow.insertCell(i);
                    newCell.innerHTML = '&nbsp;';
                    // Copy styles from the last row
                    const lastRowCell = table.rows[rowIndex].cells[i];
                    if (lastRowCell) {
                        newCell.style.border = lastRowCell.style.border;
                        newCell.style.padding = lastRowCell.style.padding;
                    }
                }
                
                // Notify that content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
                
                return newRow.cells[0];
            }
            
            // Function to find the previous cell in the table
            function findPreviousCell(currentCell) {
                const row = currentCell.parentElement;
                const table = row.parentElement.parentElement; // tr -> tbody/thead -> table
                const cellIndex = Array.from(row.cells).indexOf(currentCell);
                const rowIndex = Array.from(table.rows).indexOf(row);
                
                // Try previous cell in same row
                if (cellIndex > 0) {
                    return row.cells[cellIndex - 1];
                }
                
                // Try last cell in previous row
                if (rowIndex > 0) {
                    const prevRow = table.rows[rowIndex - 1];
                    return prevRow.cells[prevRow.cells.length - 1];
                }
                
                // If at the first cell, just return the current cell
                return currentCell;
            }
            
            // Function to focus cell without selecting text, just place caret at start
            function focusCell(cell) {
                const range = document.createRange();
                const sel = window.getSelection();
                
                // Find the first text node or create one if empty
                if (cell.childNodes.length > 0) {
                    let firstTextNode = null;
                    for (let i = 0; i < cell.childNodes.length; i++) {
                        if (cell.childNodes[i].nodeType === Node.TEXT_NODE) {
                            firstTextNode = cell.childNodes[i];
                            break;
                        }
                    }
                    
                    if (firstTextNode) {
                        // Place caret at the beginning of the text node
                        range.setStart(firstTextNode, 0);
                        range.setEnd(firstTextNode, 0);
                    } else {
                        // No text node found, place caret at the beginning of the cell
                        range.setStart(cell, 0);
                        range.setEnd(cell, 0);
                    }
                } else {
                    // Empty cell - set the range at the beginning
                    range.setStart(cell, 0);
                    range.setEnd(cell, 0);
                }
                
                sel.removeAllRanges();
                sel.addRange(range);
                
                // Ensure cell is scrolled into view
                cell.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            
            // Handle tab key navigation
            editor.addEventListener('keydown', function(e) {
                // Check if we're inside a table cell when Tab is pressed
                if (e.key === 'Tab') {
                    // Find if we're inside a table cell
                    let currentElement = document.getSelection().anchorNode;
                    if (currentElement.nodeType === Node.TEXT_NODE) {
                        currentElement = currentElement.parentElement;
                    }
                    
                    let cell = currentElement;
                    while (cell && cell !== editor) {
                        if (cell.tagName === 'TD' || cell.tagName === 'TH') {
                            break;
                        }
                        cell = cell.parentElement;
                    }
                    
                    // If we're in a table cell, handle tab navigation
                    if (cell && (cell.tagName === 'TD' || cell.tagName === 'TH')) {
                        e.preventDefault();
                        
                        if (e.shiftKey) {
                            // Navigate to previous cell
                            const prevCell = findPreviousCell(cell);
                            if (prevCell) {
                                focusCell(prevCell);
                            }
                        } else {
                            // Navigate to next cell
                            const nextCell = findNextCell(cell);
                            if (nextCell) {
                                focusCell(nextCell);
                            }
                        }
                        
                        // Hide handles when navigating between cells
                        if (activeTable) {
                            hideTableHandles();
                        }
                        
                        return;
                    }
                    
                    // If not in a table cell, use default behavior (insert tab)
                    if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                        e.preventDefault();
                        document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                        
                        // Trigger input event to register the change for undo/redo
                        const event = new Event('input', {
                            bubbles: true,
                            cancelable: true
                        });
                        editor.dispatchEvent(event);
                    }
                }
            });
            
            editor.addEventListener('focus', function onFirstFocus(e) {
                if (!editor.textContent.trim() && editor.innerHTML === '') {
                    editor.innerHTML = '<div><br></div>';
                    const range = document.createRange();
                    const sel = window.getSelection();
                    const firstDiv = editor.querySelector('div');
                    if (firstDiv) {
                        range.setStart(firstDiv, 0);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                    editor.removeEventListener('focus', onFirstFocus);
                }
            });

            window.lastContent = editor.innerHTML;
            saveState();
            editor.focus();

            editor.addEventListener('input', function(e) {
                if (document.getSelection().anchorNode === editor) {
                    document.execCommand('formatBlock', false, 'div');
                }
                if (!window.isUndoRedo) {
                    const currentContent = editor.innerHTML;
                    if (currentContent !== window.lastContent) {
                        saveState();
                        window.lastContent = currentContent;
                        window.redoStack = [];
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage("changed");
                        } catch(e) {
                            console.log("Could not notify about changes:", e);
                        }
                    }
                }
            });

            if (window.initialContent) {
                setContent(window.initialContent);
            }
        });
        """



    def table_row_column_js(self):
        """JavaScript for table row and column operations with resizing functionality"""
        return """
        // Function to add a row to the table
        function addTableRow(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const rows = tableElement.rows;
            if (rows.length > 0) {
                // If position is provided, use it, otherwise append at the end
                const rowIndex = (position !== undefined) ? position : rows.length;
                const newRow = tableElement.insertRow(rowIndex);
                
                for (let i = 0; i < rows[0].cells.length; i++) {
                    const cell = newRow.insertCell(i);
                    cell.innerHTML = '&nbsp;';
                    // Copy border style from other cells
                    if (rows[0].cells[i].style.border) {
                        cell.style.border = rows[0].cells[i].style.border;
                    } else {
                        cell.style.border = '1px solid ' + borderColor;
                    }
                    // Copy padding style from other cells
                    if (rows[0].cells[i].style.padding) {
                        cell.style.padding = rows[0].cells[i].style.padding;
                    } else {
                        cell.style.padding = '5px';
                    }
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to add a column to the table
        function addTableColumn(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            const rows = tableElement.rows;
            for (let i = 0; i < rows.length; i++) {
                // If position is provided, use it, otherwise append at the end
                const cellIndex = (position !== undefined) ? position : rows[i].cells.length;
                const cell = rows[i].insertCell(cellIndex);
                cell.innerHTML = '&nbsp;';
                
                // Default styles based on theme
                let cellStyle = {
                    border: '1px solid ' + borderColor,
                    padding: '5px'
                };
                
                // Copy styles from adjacent cells if available
                if (rows[i].cells.length > 1) {
                    const refCell = cellIndex > 0 ? 
                                    rows[i].cells[cellIndex - 1] : 
                                    rows[i].cells[cellIndex + 1];
                                    
                    if (refCell) {
                        if (refCell.style.border) {
                            cellStyle.border = refCell.style.border;
                        }
                        if (refCell.style.padding) {
                            cellStyle.padding = refCell.style.padding;
                        }
                        
                        // If it's a header cell, make new cell a header too
                        if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                            const headerCell = document.createElement('th');
                            headerCell.innerHTML = cell.innerHTML;
                            
                            // Apply all styles
                            Object.assign(headerCell.style, cellStyle);
                            headerCell.style.backgroundColor = headerBgColor;
                            
                            cell.parentNode.replaceChild(headerCell, cell);
                        } else {
                            // Apply styles to normal cell
                            Object.assign(cell.style, cellStyle);
                        }
                    }
                } else {
                    // Apply default styles if no reference cells
                    Object.assign(cell.style, cellStyle);
                    
                    // If this is the first row, it might be a header
                    if (i === 0 && rows[0].cells[0].tagName === 'TH') {
                        const headerCell = document.createElement('th');
                        headerCell.innerHTML = cell.innerHTML;
                        Object.assign(headerCell.style, cellStyle);
                        headerCell.style.backgroundColor = headerBgColor;
                        cell.parentNode.replaceChild(headerCell, cell);
                    }
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a row from the table
        function deleteTableRow(tableElement, rowIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 1) {
                // If rowIndex is provided, delete that row, otherwise delete the last row
                const indexToDelete = (rowIndex !== undefined) ? rowIndex : rows.length - 1;
                if (indexToDelete >= 0 && indexToDelete < rows.length) {
                    tableElement.deleteRow(indexToDelete);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a column from the table
        function deleteTableColumn(tableElement, colIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 0 && rows[0].cells.length > 1) {
                // If colIndex is provided, delete that column, otherwise delete the last column
                const indexToDelete = (colIndex !== undefined) ? colIndex : rows[0].cells.length - 1;
                
                for (let i = 0; i < rows.length; i++) {
                    if (indexToDelete >= 0 && indexToDelete < rows[i].cells.length) {
                        rows[i].deleteCell(indexToDelete);
                    }
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a table
        function deleteTable(tableElement) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            // Remove the table from the DOM
            tableElement.parentNode.removeChild(tableElement);
            
            // Reset activeTable reference
            activeTable = null;
            
            // Notify the app
            try {
                window.webkit.messageHandlers.tableDeleted.postMessage('table-deleted');
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about table deletion:", e);
            }
        }
        
        // Variables for row/column resizing
        var isResizingRow = false;
        var isResizingColumn = false;
        var currentRowBorder = null;
        var currentColumnBorder = null;
        var resizeStartX = 0;
        var resizeStartY = 0;
        var resizeStartHeight = 0;
        var resizeStartWidth = 0;
        var resizingRowIndex = -1;
        var resizingColumnIndex = -1;
        
        // Function to initialize row/column resizing
        function initializeTableResizers(tableElement) {
            if (!tableElement || tableElement.dataset.resizersInitialized) return;
            
            tableElement.dataset.resizersInitialized = 'true';
            
            // Add column resizers
            const headerRow = tableElement.rows[0];
            if (headerRow) {
                for (let i = 0; i < headerRow.cells.length; i++) {
                    const cell = headerRow.cells[i];
                    const resizer = document.createElement('div');
                    resizer.className = 'column-resizer';
                    resizer.dataset.columnIndex = i;
                    cell.appendChild(resizer);
                }
            }
            
            // Add row resizers
            for (let i = 0; i < tableElement.rows.length; i++) {
                const row = tableElement.rows[i];
                const cell = row.cells[0];
                if (cell) {
                    const resizer = document.createElement('div');
                    resizer.className = 'row-resizer';
                    resizer.dataset.rowIndex = i;
                    cell.appendChild(resizer);
                }
            }
        }
        
        // Function to update column width
        function updateColumnWidth(tableElement, columnIndex, newWidth) {
            if (!tableElement) return;
            
            // Ensure minimum width
            const minWidth = 30;
            newWidth = Math.max(minWidth, newWidth);
            
            // Update the width of all cells in the column
            for (let i = 0; i < tableElement.rows.length; i++) {
                const cell = tableElement.rows[i].cells[columnIndex];
                if (cell) {
                    cell.style.width = newWidth + 'px';
                    cell.style.minWidth = minWidth + 'px';
                }
            }
            
            // Update table layout
            tableElement.style.tableLayout = 'fixed';
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to update row height
        function updateRowHeight(tableElement, rowIndex, newHeight) {
            if (!tableElement || !tableElement.rows[rowIndex]) return;
            
            // Ensure minimum height
            const minHeight = 20;
            newHeight = Math.max(minHeight, newHeight);
            
            // Update the height of all cells in the row
            const row = tableElement.rows[rowIndex];
            for (let i = 0; i < row.cells.length; i++) {
                const cell = row.cells[i];
                cell.style.height = newHeight + 'px';
                cell.style.minHeight = minHeight + 'px';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Event handlers for row/column resizing
        document.addEventListener('mousedown', function(e) {
            if (e.target.classList.contains('column-resizer')) {
                isResizingColumn = true;
                const cell = e.target.parentElement;
                const columnIndex = parseInt(e.target.dataset.columnIndex);
                const table = findParentTable(e.target);
                
                if (table) {
                    currentColumnBorder = e.target;
                    resizingColumnIndex = columnIndex;
                    resizeStartX = e.clientX;
                    resizeStartWidth = cell.offsetWidth;
                    activeTable = table;
                    
                    e.preventDefault();
                    e.stopPropagation();
                }
            } else if (e.target.classList.contains('row-resizer')) {
                isResizingRow = true;
                const cell = e.target.parentElement;
                const rowIndex = parseInt(e.target.dataset.rowIndex);
                const table = findParentTable(e.target);
                
                if (table) {
                    currentRowBorder = e.target;
                    resizingRowIndex = rowIndex;
                    resizeStartY = e.clientY;
                    resizeStartHeight = cell.offsetHeight;
                    activeTable = table;
                    
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isResizingColumn && activeTable) {
                const deltaX = e.clientX - resizeStartX;
                const newWidth = resizeStartWidth + deltaX;
                updateColumnWidth(activeTable, resizingColumnIndex, newWidth);
            } else if (isResizingRow && activeTable) {
                const deltaY = e.clientY - resizeStartY;
                const newHeight = resizeStartHeight + deltaY;
                updateRowHeight(activeTable, resizingRowIndex, newHeight);
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isResizingColumn || isResizingRow) {
                isResizingColumn = false;
                isResizingRow = false;
                currentColumnBorder = null;
                currentRowBorder = null;
                resizingColumnIndex = -1;
                resizingRowIndex = -1;
            }
        });
        """

    def table_handles_css_js(self):
        """JavaScript that defines CSS for table handles and resizers"""
        return """
            // CSS for table handles and resizers
            const tableHandlesCSS = `
            /* Table drag handle - positioned inside the table */
            .table-drag-handle {
                position: absolute;
                top: 0;
                left: 0;
                width: 16px;
                height: 16px;
                background-color: #4e9eff;
                cursor: move;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }

            /* Table resize handle - triangular shape in bottom right */
            .table-handle {
                position: absolute;
                bottom: 0;
                right: 0;
                width: 0;
                height: 0;
                border-style: solid;
                border-width: 0 0 16px 16px;
                border-color: transparent transparent #4e9eff transparent;
                cursor: nwse-resize;
                z-index: 1000;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                display: block;
            }
            
            /* Column resizer */
            .column-resizer {
                position: absolute;
                right: -3px;
                top: 0;
                width: 7px;
                height: 100%;
                cursor: col-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .column-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Row resizer */
            .row-resizer {
                position: absolute;
                bottom: -3px;
                left: 0;
                height: 7px;
                width: 100%;
                cursor: row-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .row-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Table cells with resizers need relative positioning */
            table td, table th {
                position: relative;
            }
            
            /* Floating table styles */
            .floating-table {
                position: absolute !important;
                z-index: 50;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                background-color: rgba(255, 255, 255, 0.95);
                cursor: grab;
            }
            
            .floating-table:active {
                cursor: grabbing;
            }
            
            .floating-table .table-drag-handle {
                width: 20px !important;
                height: 20px !important;
                border-radius: 3px;
                opacity: 0.9;
            }

            @media (prefers-color-scheme: dark) {
                .table-drag-handle {
                    background-color: #0078d7;
                }
                .table-handle {
                    border-color: transparent transparent #0078d7 transparent;
                }
                .floating-table {
                    background-color: rgba(45, 45, 45, 0.95);
                    box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                }
                .floating-table .table-drag-handle {
                    background-color: #0078d7;
                }
                .column-resizer:hover, .row-resizer:hover {
                    background: rgba(0, 120, 215, 0.5);
                }
            }`;
            
            // Function to add the table handle styles to the document
            function addTableHandleStyles() {
                // Check if our style element already exists
                let styleElement = document.getElementById('table-handle-styles');
                
                // If not, create and append it
                if (!styleElement) {
                    styleElement = document.createElement('style');
                    styleElement.id = 'table-handle-styles';
                    styleElement.textContent = tableHandlesCSS;
                    document.head.appendChild(styleElement);
                } else {
                    // If it exists, update the content
                    styleElement.textContent = tableHandlesCSS;
                }
            }
        """

    def table_activation_js(self):
        """JavaScript for table activation and deactivation with resizers"""
        return """
        // Variables for table handling
        var activeTable = null;
        var isDragging = false;
        var isResizing = false;
        var dragStartX = 0;
        var dragStartY = 0;
        var tableStartX = 0;
        var tableStartY = 0;
        
        // Function to find parent table element
        function findParentTable(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'TABLE') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Function to activate a table (add handles and resizers)
        function activateTable(tableElement) {
            if (activeTable === tableElement) return; // Already active
            
            // Deactivate any previously active tables
            if (activeTable && activeTable !== tableElement) {
                deactivateTable(activeTable);
            }
            
            activeTable = tableElement;
            
            // Store original styles and apply selection styling
            storeAndApplyTableStyles(tableElement);
            
            // Initialize row/column resizers
            initializeTableResizers(tableElement);
            
            // Determine current table alignment class
            const currentClasses = tableElement.className;
            const alignmentClasses = ['left-align', 'right-align', 'center-align', 'no-wrap'];
            let currentAlignment = 'no-wrap';
            
            alignmentClasses.forEach(cls => {
                if (currentClasses.includes(cls)) {
                    currentAlignment = cls;
                }
            });
            
            // Reset and apply the appropriate alignment class
            alignmentClasses.forEach(cls => tableElement.classList.remove(cls));
            tableElement.classList.add(currentAlignment);
            
            // Add resize handle if needed
            if (!tableElement.querySelector('.table-handle')) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'table-handle';
                
                // Make handle non-selectable and prevent focus
                resizeHandle.setAttribute('contenteditable', 'false');
                resizeHandle.setAttribute('unselectable', 'on');
                resizeHandle.setAttribute('tabindex', '-1');
                
                // Add event listener to prevent propagation of mousedown events
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTableResize(e, tableElement);
                }, true);
                
                tableElement.appendChild(resizeHandle);
            }
            
            // Add drag handle if needed
            if (!tableElement.querySelector('.table-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'table-drag-handle';
                dragHandle.innerHTML = '↕';
                
                // Set title based on whether it's a floating table or not
                if (tableElement.classList.contains('floating-table')) {
                    dragHandle.title = 'Drag to move table freely';
                } else {
                    dragHandle.title = 'Drag to reposition table between paragraphs';
                }
                
                // Make handle non-selectable and prevent focus
                dragHandle.setAttribute('contenteditable', 'false');
                dragHandle.setAttribute('unselectable', 'on');
                dragHandle.setAttribute('tabindex', '-1');
                
                // Add event listener to prevent propagation of mousedown events
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTableDrag(e, tableElement);
                }, true);
                
                tableElement.appendChild(dragHandle);
            }
            
            // Special styling for floating tables
            if (tableElement.classList.contains('floating-table')) {
                enhanceTableDragHandles(tableElement);
            }
        }
        
        // Store original table styles and apply selection styling
        function storeAndApplyTableStyles(tableElement) {
            // Add selected class for CSS styling
            tableElement.classList.add('table-selected');
            
            // Ensure table has editor-table class
            if (!tableElement.classList.contains('editor-table')) {
                tableElement.classList.add('editor-table');
            }
            
            // Ensure the table has position: relative for proper handle positioning
            // Only set relative position if not already a floating table
            if (!tableElement.classList.contains('floating-table')) {
                tableElement.style.position = 'relative';
            }
        }
        
        // Function to deactivate a specific table
        function deactivateTable(tableElement) {
            if (!tableElement) return;
            
            // Remove selected class
            tableElement.classList.remove('table-selected');
            
            // Remove handles
            const resizeHandle = tableElement.querySelector('.table-handle');
            if (resizeHandle) resizeHandle.remove();
            
            const dragHandle = tableElement.querySelector('.table-drag-handle');
            if (dragHandle) dragHandle.remove();
            
            // Remove row/column resizers
            const columnResizers = tableElement.querySelectorAll('.column-resizer');
            columnResizers.forEach(resizer => resizer.remove());
            
            const rowResizers = tableElement.querySelectorAll('.row-resizer');
            rowResizers.forEach(resizer => resizer.remove());
            
            // Clear the resizers initialized flag
            delete tableElement.dataset.resizersInitialized;
            
            if (tableElement === activeTable) {
                activeTable = null;
            }
        }
        
        // Function to deactivate all tables
        function deactivateAllTables() {
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {
                deactivateTable(table);
            });
            
            // Always notify that tables are deactivated, regardless of whether activeTable was set
            activeTable = null;
            try {
                window.webkit.messageHandlers.tablesDeactivated.postMessage('tables-deactivated');
            } catch(e) {
                console.log("Could not notify about table deactivation:", e);
            }
        }
        
        // Function to update table colors based on current theme
        function updateTableThemeColors(tableElement) {
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Update all headers
            const headers = tableElement.querySelectorAll('th');
            headers.forEach(header => {
                header.style.backgroundColor = headerBgColor;
                header.style.borderColor = borderColor;
            });
            
            // Update all cells
            const cells = tableElement.querySelectorAll('td');
            cells.forEach(cell => {
                cell.style.borderColor = borderColor;
            });
        }
        """            
        
        
    ########
    def table_row_column_js(self):
            """JavaScript for table row and column operations with resizing functionality"""
            return """
            // Function to add a row to the table
            function addTableRow(tableElement, position) {
                if (!tableElement && activeTable) {
                    tableElement = activeTable;
                }
                
                if (!tableElement) return;
                
                const borderColor = getBorderColor();
                const rows = tableElement.rows;
                if (rows.length > 0) {
                    // If position is provided, use it, otherwise append at the end
                    const rowIndex = (position !== undefined) ? position : rows.length;
                    const newRow = tableElement.insertRow(rowIndex);
                    
                    for (let i = 0; i < rows[0].cells.length; i++) {
                        const cell = newRow.insertCell(i);
                        cell.innerHTML = '&nbsp;';
                        // Copy border style from other cells
                        if (rows[0].cells[i].style.border) {
                            cell.style.border = rows[0].cells[i].style.border;
                        } else {
                            cell.style.border = '1px solid ' + borderColor;
                        }
                        // Copy padding style from other cells
                        if (rows[0].cells[i].style.padding) {
                            cell.style.padding = rows[0].cells[i].style.padding;
                        } else {
                            cell.style.padding = '5px';
                        }
                    }
                }
                
                // Add resizers for the new row
                initializeTableResizers(tableElement);
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            }
            
            // Function to add a column to the table
            function addTableColumn(tableElement, position) {
                if (!tableElement && activeTable) {
                    tableElement = activeTable;
                }
                
                if (!tableElement) return;
                
                const borderColor = getBorderColor();
                const headerBgColor = getHeaderBgColor();
                const rows = tableElement.rows;
                for (let i = 0; i < rows.length; i++) {
                    // If position is provided, use it, otherwise append at the end
                    const cellIndex = (position !== undefined) ? position : rows[i].cells.length;
                    const cell = rows[i].insertCell(cellIndex);
                    cell.innerHTML = '&nbsp;';
                    
                    // Default styles based on theme
                    let cellStyle = {
                        border: '1px solid ' + borderColor,
                        padding: '5px'
                    };
                    
                    // Copy styles from adjacent cells if available
                    if (rows[i].cells.length > 1) {
                        const refCell = cellIndex > 0 ? 
                                        rows[i].cells[cellIndex - 1] : 
                                        rows[i].cells[cellIndex + 1];
                                        
                        if (refCell) {
                            if (refCell.style.border) {
                                cellStyle.border = refCell.style.border;
                            }
                            if (refCell.style.padding) {
                                cellStyle.padding = refCell.style.padding;
                            }
                            
                            // If it's a header cell, make new cell a header too
                            if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                                const headerCell = document.createElement('th');
                                headerCell.innerHTML = cell.innerHTML;
                                
                                // Apply all styles
                                Object.assign(headerCell.style, cellStyle);
                                headerCell.style.backgroundColor = headerBgColor;
                                
                                cell.parentNode.replaceChild(headerCell, cell);
                            } else {
                                // Apply styles to normal cell
                                Object.assign(cell.style, cellStyle);
                            }
                        }
                    } else {
                        // Apply default styles if no reference cells
                        Object.assign(cell.style, cellStyle);
                        
                        // If this is the first row, it might be a header
                        if (i === 0 && rows[0].cells[0].tagName === 'TH') {
                            const headerCell = document.createElement('th');
                            headerCell.innerHTML = cell.innerHTML;
                            Object.assign(headerCell.style, cellStyle);
                            headerCell.style.backgroundColor = headerBgColor;
                            cell.parentNode.replaceChild(headerCell, cell);
                        }
                    }
                }
                
                // Add resizers for the new column
                initializeTableResizers(tableElement);
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            }        
"""
##############################
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return f"""
        {self.table_theme_helpers_js()}
        {self.table_handles_css_js_fixed()}  # Use the fixed version
        {self.table_insert_functions_js()}
        {self.table_activation_js()}
        {self.table_drag_resize_js()}
        {self.table_row_column_js_fixed()}  # Use the fixed version
        {self.table_alignment_js()}
        {self.table_floating_js()}
        {self.table_event_handlers_js()}
        """
    def get_editor_js(self):
        """Return the combined JavaScript logic for the editor."""
        return f"""
        // Global scope for persistence
        window.undoStack = [];
        window.redoStack = [];
        window.isUndoRedo = false;
        window.lastContent = "";
        
        // Search variables
        var searchResults = [];
        var searchIndex = -1;
        var currentSearchText = "";

        {self.set_content_js()}
        {self.insert_table_js()}
        {self.table_border_style_js()}
        {self.table_color_js()}
        {self.insert_text_box_js()}
        {self.insert_image_js()}
        {self.insert_link_js()}
        {self.init_editor_js()}
        """

    def table_row_column_js_fixed(self):
        """Fixed JavaScript for table row and column operations with resizing functionality"""
        return """
        // Function to add a row to the table
        function addTableRow(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const rows = tableElement.rows;
            if (rows.length > 0) {
                // If position is provided, use it, otherwise append at the end
                const rowIndex = (position !== undefined) ? position : rows.length;
                const newRow = tableElement.insertRow(rowIndex);
                
                for (let i = 0; i < rows[0].cells.length; i++) {
                    const cell = newRow.insertCell(i);
                    cell.innerHTML = '&nbsp;';
                    // Copy border style from other cells
                    if (rows[0].cells[i].style.border) {
                        cell.style.border = rows[0].cells[i].style.border;
                    } else {
                        cell.style.border = '1px solid ' + borderColor;
                    }
                    // Copy padding style from other cells
                    if (rows[0].cells[i].style.padding) {
                        cell.style.padding = rows[0].cells[i].style.padding;
                    } else {
                        cell.style.padding = '5px';
                    }
                }
                
                // Re-initialize resizers for the table
                if (tableElement === activeTable) {
                    initializeTableResizers(tableElement);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to add a column to the table
        function addTableColumn(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            const rows = tableElement.rows;
            for (let i = 0; i < rows.length; i++) {
                // If position is provided, use it, otherwise append at the end
                const cellIndex = (position !== undefined) ? position : rows[i].cells.length;
                const cell = rows[i].insertCell(cellIndex);
                cell.innerHTML = '&nbsp;';
                
                // Default styles based on theme
                let cellStyle = {
                    border: '1px solid ' + borderColor,
                    padding: '5px'
                };
                
                // Copy styles from adjacent cells if available
                if (rows[i].cells.length > 1) {
                    const refCell = cellIndex > 0 ? 
                                    rows[i].cells[cellIndex - 1] : 
                                    rows[i].cells[cellIndex + 1];
                                    
                    if (refCell) {
                        if (refCell.style.border) {
                            cellStyle.border = refCell.style.border;
                        }
                        if (refCell.style.padding) {
                            cellStyle.padding = refCell.style.padding;
                        }
                        
                        // If it's a header cell, make new cell a header too
                        if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                            const headerCell = document.createElement('th');
                            headerCell.innerHTML = cell.innerHTML;
                            
                            // Apply all styles
                            Object.assign(headerCell.style, cellStyle);
                            headerCell.style.backgroundColor = headerBgColor;
                            
                            cell.parentNode.replaceChild(headerCell, cell);
                        } else {
                            // Apply styles to normal cell
                            Object.assign(cell.style, cellStyle);
                        }
                    }
                } else {
                    // Apply default styles if no reference cells
                    Object.assign(cell.style, cellStyle);
                    
                    // If this is the first row, it might be a header
                    if (i === 0 && rows[0].cells[0].tagName === 'TH') {
                        const headerCell = document.createElement('th');
                        headerCell.innerHTML = cell.innerHTML;
                        Object.assign(headerCell.style, cellStyle);
                        headerCell.style.backgroundColor = headerBgColor;
                        cell.parentNode.replaceChild(headerCell, cell);
                    }
                }
            }
            
            // Re-initialize resizers for the table
            if (tableElement === activeTable) {
                initializeTableResizers(tableElement);
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a row from the table
        function deleteTableRow(tableElement, rowIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 1) {
                // If rowIndex is provided, delete that row, otherwise delete the last row
                const indexToDelete = (rowIndex !== undefined) ? rowIndex : rows.length - 1;
                if (indexToDelete >= 0 && indexToDelete < rows.length) {
                    tableElement.deleteRow(indexToDelete);
                }
                
                // Re-initialize resizers for the table
                if (tableElement === activeTable) {
                    initializeTableResizers(tableElement);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a column from the table
        function deleteTableColumn(tableElement, colIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 0 && rows[0].cells.length > 1) {
                // If colIndex is provided, delete that column, otherwise delete the last column
                const indexToDelete = (colIndex !== undefined) ? colIndex : rows[0].cells.length - 1;
                
                for (let i = 0; i < rows.length; i++) {
                    if (indexToDelete >= 0 && indexToDelete < rows[i].cells.length) {
                        rows[i].deleteCell(indexToDelete);
                    }
                }
                
                // Re-initialize resizers for the table
                if (tableElement === activeTable) {
                    initializeTableResizers(tableElement);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a table
        function deleteTable(tableElement) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            // Remove the table from the DOM
            tableElement.parentNode.removeChild(tableElement);
            
            // Reset activeTable reference
            activeTable = null;
            
            // Notify the app
            try {
                window.webkit.messageHandlers.tableDeleted.postMessage('table-deleted');
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about table deletion:", e);
            }
        }
        
        // Variables for row/column resizing
        var isResizingRow = false;
        var isResizingColumn = false;
        var currentRowBorder = null;
        var currentColumnBorder = null;
        var resizeStartX = 0;
        var resizeStartY = 0;
        var resizeStartHeight = 0;
        var resizeStartWidth = 0;
        var resizingRowIndex = -1;
        var resizingColumnIndex = -1;
        
        // Function to initialize row/column resizing
        function initializeTableResizers(tableElement) {
            if (!tableElement) return;
            
            // Clear existing resizers first
            const existingResizers = tableElement.querySelectorAll('.column-resizer, .row-resizer');
            existingResizers.forEach(resizer => resizer.remove());
            
            // Add column resizers to all cells (except the last column)
            for (let i = 0; i < tableElement.rows.length; i++) {
                const row = tableElement.rows[i];
                for (let j = 0; j < row.cells.length - 1; j++) {
                    const cell = row.cells[j];
                    const resizer = document.createElement('div');
                    resizer.className = 'column-resizer';
                    resizer.dataset.columnIndex = j;
                    cell.appendChild(resizer);
                }
            }
            
            // Add row resizers to all cells (except the last row)
            for (let i = 0; i < tableElement.rows.length - 1; i++) {
                const row = tableElement.rows[i];
                for (let j = 0; j < row.cells.length; j++) {
                    const cell = row.cells[j];
                    const resizer = document.createElement('div');
                    resizer.className = 'row-resizer';
                    resizer.dataset.rowIndex = i;
                    cell.appendChild(resizer);
                }
            }
            
            tableElement.dataset.resizersInitialized = 'true';
        }
        
        // Function to update column width
        function updateColumnWidth(tableElement, columnIndex, newWidth) {
            if (!tableElement) return;
            
            // Ensure minimum width
            const minWidth = 30;
            newWidth = Math.max(minWidth, newWidth);
            
            // Update the width of all cells in the column
            for (let i = 0; i < tableElement.rows.length; i++) {
                const cell = tableElement.rows[i].cells[columnIndex];
                if (cell) {
                    cell.style.width = newWidth + 'px';
                    cell.style.minWidth = minWidth + 'px';
                }
            }
            
            // Update table layout
            tableElement.style.tableLayout = 'fixed';
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to update row height
        function updateRowHeight(tableElement, rowIndex, newHeight) {
            if (!tableElement || !tableElement.rows[rowIndex]) return;
            
            // Ensure minimum height
            const minHeight = 20;
            newHeight = Math.max(minHeight, newHeight);
            
            // Update the height of all cells in the row
            const row = tableElement.rows[rowIndex];
            for (let i = 0; i < row.cells.length; i++) {
                const cell = row.cells[i];
                cell.style.height = newHeight + 'px';
                cell.style.minHeight = minHeight + 'px';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Event handlers for row/column resizing
        document.addEventListener('mousedown', function(e) {
            if (e.target.classList.contains('column-resizer')) {
                isResizingColumn = true;
                const cell = e.target.parentElement;
                const columnIndex = parseInt(e.target.dataset.columnIndex);
                const table = findParentTable(e.target);
                
                if (table) {
                    currentColumnBorder = e.target;
                    resizingColumnIndex = columnIndex;
                    resizeStartX = e.clientX;
                    resizeStartWidth = cell.offsetWidth;
                    activeTable = table;
                    
                    e.preventDefault();
                    e.stopPropagation();
                }
            } else if (e.target.classList.contains('row-resizer')) {
                isResizingRow = true;
                const cell = e.target.parentElement;
                const rowIndex = parseInt(e.target.dataset.rowIndex);
                const table = findParentTable(e.target);
                
                if (table) {
                    currentRowBorder = e.target;
                    resizingRowIndex = rowIndex;
                    resizeStartY = e.clientY;
                    resizeStartHeight = cell.offsetHeight;
                    activeTable = table;
                    
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isResizingColumn && activeTable) {
                const deltaX = e.clientX - resizeStartX;
                const newWidth = resizeStartWidth + deltaX;
                updateColumnWidth(activeTable, resizingColumnIndex, newWidth);
            } else if (isResizingRow && activeTable) {
                const deltaY = e.clientY - resizeStartY;
                const newHeight = resizeStartHeight + deltaY;
                updateRowHeight(activeTable, resizingRowIndex, newHeight);
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isResizingColumn || isResizingRow) {
                isResizingColumn = false;
                isResizingRow = false;
                currentColumnBorder = null;
                currentRowBorder = null;
                resizingColumnIndex = -1;
                resizingRowIndex = -1;
            }
        });
        """

    def table_handles_css_js_fixed(self):
        """Fixed JavaScript that defines CSS for table handles and resizers"""
        return """
            // CSS for table handles and resizers
            const tableHandlesCSS = `
            /* Table drag handle - positioned inside the table */
            .table-drag-handle {
                position: absolute;
                top: 0;
                left: 0;
                width: 16px;
                height: 16px;
                background-color: #4e9eff;
                cursor: move;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }

            /* Table resize handle - triangular shape in bottom right */
            .table-handle {
                position: absolute;
                bottom: 0;
                right: 0;
                width: 0;
                height: 0;
                border-style: solid;
                border-width: 0 0 16px 16px;
                border-color: transparent transparent #4e9eff transparent;
                cursor: nwse-resize;
                z-index: 1000;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                display: block;
            }
            
            /* Column resizer */
            .column-resizer {
                position: absolute;
                right: -3px;
                top: 0;
                width: 7px;
                height: calc(100% - 7px); /* Leave space for row resizer */
                cursor: col-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .column-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Row resizer */
            .row-resizer {
                position: absolute;
                bottom: -3px;
                left: 0;
                height: 7px;
                width: calc(100% - 7px); /* Leave space for column resizer */
                cursor: row-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .row-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Table cells with resizers need relative positioning */
            table td, table th {
                position: relative;
            }
            
            /* Floating table styles */
            .floating-table {
                position: absolute !important;
                z-index: 50;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                background-color: rgba(255, 255, 255, 0.95);
                cursor: grab;
            }
            
            .floating-table:active {
                cursor: grabbing;
            }
            
            .floating-table .table-drag-handle {
                width: 20px !important;
                height: 20px !important;
                border-radius: 3px;
                opacity: 0.9;
            }

            @media (prefers-color-scheme: dark) {
                .table-drag-handle {
                    background-color: #0078d7;
                }
                .table-handle {
                    border-color: transparent transparent #0078d7 transparent;
                }
                .floating-table {
                    background-color: rgba(45, 45, 45, 0.95);
                    box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                }
                .floating-table .table-drag-handle {
                    background-color: #0078d7;
                }
                .column-resizer:hover, .row-resizer:hover {
                    background: rgba(0, 120, 215, 0.5);
                }
            }`;
            
            // Function to add the table handle styles to the document
            function addTableHandleStyles() {
                // Check if our style element already exists
                let styleElement = document.getElementById('table-handle-styles');
                
                // If not, create and append it
                if (!styleElement) {
                    styleElement = document.createElement('style');
                    styleElement.id = 'table-handle-styles';
                    styleElement.textContent = tableHandlesCSS;
                    document.head.appendChild(styleElement);
                } else {
                    // If it exists, update the content
                    styleElement.textContent = tableHandlesCSS;
                }
            }
        """
    def table_insert_functions_js(self):
        """JavaScript for inserting tables with default margins"""
        return """
        // Function to insert a table at the current cursor position
        function insertTable(rows, cols, hasHeader, borderWidth, tableWidth, isFloating) {
            // Get theme-appropriate colors
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Create table HTML
            let tableHTML = '<table cellspacing="0" cellpadding="5" ';
            
            // Add class and style attributes
            tableHTML += 'class="editor-table' + (isFloating ? ' floating-table' : '') + '" ';
            tableHTML += 'style="border-collapse: collapse; width: ' + tableWidth + '; margin: 6px 6px 0 0;">';
            
            // Create header row if requested
            if (hasHeader) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<th style="border: ' + borderWidth + 'px solid ' + borderColor + '; padding: 5px; background-color: ' + headerBgColor + ';">Header ' + (j+1) + '</th>';
                }
                tableHTML += '</tr>';
                rows--; // Reduce regular rows by one since we added a header
            }
            
            // Create regular rows and cells
            for (let i = 0; i < rows; i++) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<td style="border: ' + borderWidth + 'px solid ' + borderColor + '; padding: 5px; min-width: 30px;">Cell</td>';
                }
                tableHTML += '</tr>';
            }
            
            tableHTML += '</table><p></p>';
            
            // Insert the table at the current cursor position
            document.execCommand('insertHTML', false, tableHTML);
            
            // Activate the newly inserted table
            setTimeout(() => {
                const tables = document.querySelectorAll('table.editor-table');
                const newTable = tables[tables.length - 1] || document.querySelector('table:last-of-type');
                if (newTable) {
                    // Ensure the editor-table class is present
                    if (!newTable.classList.contains('editor-table')) {
                        newTable.classList.add('editor-table');
                    }
                    
                    // Set default margins
                    newTable.style.marginTop = '6px';
                    newTable.style.marginRight = '6px';
                    newTable.style.marginBottom = '0px';
                    newTable.style.marginLeft = '0px';
                    
                    // Store margin values as attributes
                    newTable.setAttribute('data-margin-top', '6');
                    newTable.setAttribute('data-margin-right', '6');
                    newTable.setAttribute('data-margin-bottom', '0');
                    newTable.setAttribute('data-margin-left', '0');
                    
                    // Make table floating if requested
                    if (isFloating) {
                        newTable.classList.add('floating-table');
                        setTableFloating(newTable);
                    }
                    
                    activateTable(newTable);
                    
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
                }
            }, 10);
        }
        """

    def table_theme_helpers_js(self):
        """JavaScript helper functions for theme detection and colors"""
        return """
        // Function to check if we're in dark mode
        function isDarkMode() {
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        
        // Function to get appropriate border color based on current theme
        function getBorderColor() {
            return isDarkMode() ? '#444' : '#ccc';
        }
        
        // Function to get appropriate header background color based on current theme
        function getHeaderBgColor() {
            return isDarkMode() ? '#2a2a2a' : '#f0f0f0';
        }
        """

    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return f"""
        {self.table_theme_helpers_js()}
        {self.table_handles_css_js_fixed()}
        {self.table_insert_functions_js()}
        {self.table_activation_js()}
        {self.table_drag_resize_js()}
        {self.table_row_column_js_fixed()}
        {self.table_alignment_js()}
        {self.table_floating_js()}
        {self.table_event_handlers_js()}
        """
    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option, is_floating):
        """Handle response from the table dialog"""
        dialog.close()
        
        # Prepare the width value
        width_value = "auto"
        if width_option != "Auto":
            width_value = width_option
        
        # Execute JavaScript to insert the table
        js_code = f"""
        (function() {{
            insertTable({rows}, {cols}, {str(has_header).lower()}, {border_width}, "{width_value}", {str(is_floating).lower()});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        
        # Update status message based on table type
        if is_floating:
            win.statusbar.set_text("Floating table inserted")
        else:
            win.statusbar.set_text("Table inserted")

    def table_handles_css_js_fixed(self):
        """Fixed JavaScript that defines CSS for table handles and resizers"""
        return """
            // CSS for table handles and resizers
            const tableHandlesCSS = `
            /* Table drag handle - positioned inside the table */
            .table-drag-handle {
                position: absolute;
                top: 0;
                left: 0;
                width: 16px;
                height: 16px;
                background-color: #4e9eff;
                cursor: move;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }

            /* Table resize handle - triangular shape in bottom right */
            .table-handle {
                position: absolute;
                bottom: 0;
                right: 0;
                width: 0;
                height: 0;
                border-style: solid;
                border-width: 0 0 16px 16px;
                border-color: transparent transparent #4e9eff transparent;
                cursor: nwse-resize;
                z-index: 1000;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                display: block;
            }
            
            /* Column resizer */
            .column-resizer {
                position: absolute;
                right: -3px;
                top: 0;
                width: 7px;
                height: 100%;
                cursor: col-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .column-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Row resizer */
            .row-resizer {
                position: absolute;
                bottom: -3px;
                left: 0;
                height: 7px;
                width: 100%;
                cursor: row-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .row-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Special styling for outer resizers */
            .column-resizer[data-is-last-column="true"] {
                right: -3px;
                width: 7px;
            }
            
            .row-resizer[data-is-last-row="true"] {
                bottom: -3px;
                height: 7px;
            }
            
            /* Table cells with resizers need relative positioning */
            table td, table th {
                position: relative;
            }
            
            /* Floating table styles */
            .floating-table {
                position: absolute !important;
                z-index: 50;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                background-color: rgba(255, 255, 255, 0.95);
                cursor: grab;
            }
            
            .floating-table:active {
                cursor: grabbing;
            }
            
            .floating-table .table-drag-handle {
                width: 20px !important;
                height: 20px !important;
                border-radius: 3px;
                opacity: 0.9;
            }

            @media (prefers-color-scheme: dark) {
                .table-drag-handle {
                    background-color: #0078d7;
                }
                .table-handle {
                    border-color: transparent transparent #0078d7 transparent;
                }
                .floating-table {
                    background-color: rgba(45, 45, 45, 0.95);
                    box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                }
                .floating-table .table-drag-handle {
                    background-color: #0078d7;
                }
                .column-resizer:hover, .row-resizer:hover {
                    background: rgba(0, 120, 215, 0.5);
                }
            }`;
            
            // Function to add the table handle styles to the document
            function addTableHandleStyles() {
                // Check if our style element already exists
                let styleElement = document.getElementById('table-handle-styles');
                
                // If not, create and append it
                if (!styleElement) {
                    styleElement = document.createElement('style');
                    styleElement.id = 'table-handle-styles';
                    styleElement.textContent = tableHandlesCSS;
                    document.head.appendChild(styleElement);
                } else {
                    // If it exists, update the content
                    styleElement.textContent = tableHandlesCSS;
                }
            }
        """
#
    def table_handles_css_js_fixed(self):
        """Fixed JavaScript that defines CSS for table handles and resizers"""
        return """
            // CSS for table handles and resizers
            const tableHandlesCSS = `
            /* Table drag handle - positioned inside the table */
            .table-drag-handle {
                position: absolute;
                top: 0;
                left: 0;
                width: 16px;
                height: 16px;
                background-color: #4e9eff;
                cursor: move;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }

            /* Table resize handle - triangular shape in bottom right */
            .table-handle {
                position: absolute;
                bottom: 0;
                right: 0;
                width: 0;
                height: 0;
                border-style: solid;
                border-width: 0 0 16px 16px;
                border-color: transparent transparent #4e9eff transparent;
                cursor: nwse-resize;
                z-index: 1000;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                display: block;
            }
            
            /* Column resizer */
            .column-resizer {
                position: absolute;
                right: -3px;
                top: 0;
                width: 7px;
                height: calc(100% - 7px);
                cursor: col-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .column-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Row resizer */
            .row-resizer {
                position: absolute;
                bottom: -3px;
                left: 0;
                height: 7px;
                width: calc(100% - 7px);
                cursor: row-resize;
                background: transparent;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .row-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            /* Table edge resizers */
            .table-edge-resizer {
                position: absolute;
                background: transparent;
                z-index: 15;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .table-edge-resizer:hover {
                background: rgba(78, 158, 255, 0.5);
            }
            
            .table-edge-resizer.right-edge {
                right: -3px;
                top: 0;
                width: 7px;
                height: 100%;
                cursor: col-resize;
            }
            
            .table-edge-resizer.bottom-edge {
                bottom: -3px;
                left: 0;
                height: 7px;
                width: 100%;
                cursor: row-resize;
            }
            
            .table-edge-resizer.left-edge {
                left: -3px;
                top: 0;
                width: 7px;
                height: 100%;
                cursor: col-resize;
            }
            
            .table-edge-resizer.top-edge {
                top: -3px;
                left: 0;
                height: 7px;
                width: 100%;
                cursor: row-resize;
            }
            
            /* Table cells with resizers need relative positioning */
            table td, table th {
                position: relative;
            }
            
            /* Floating table styles */
            .floating-table {
                position: absolute !important;
                z-index: 50;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                background-color: rgba(255, 255, 255, 0.95);
                cursor: grab;
            }
            
            .floating-table:active {
                cursor: grabbing;
            }
            
            .floating-table .table-drag-handle {
                width: 20px !important;
                height: 20px !important;
                border-radius: 3px;
                opacity: 0.9;
            }

            @media (prefers-color-scheme: dark) {
                .table-drag-handle {
                    background-color: #0078d7;
                }
                .table-handle {
                    border-color: transparent transparent #0078d7 transparent;
                }
                .floating-table {
                    background-color: rgba(45, 45, 45, 0.95);
                    box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                }
                .floating-table .table-drag-handle {
                    background-color: #0078d7;
                }
                .column-resizer:hover, .row-resizer:hover, .table-edge-resizer:hover {
                    background: rgba(0, 120, 215, 0.5);
                }
            }`;
            
            // Function to add the table handle styles to the document
            function addTableHandleStyles() {
                // Check if our style element already exists
                let styleElement = document.getElementById('table-handle-styles');
                
                // If not, create and append it
                if (!styleElement) {
                    styleElement = document.createElement('style');
                    styleElement.id = 'table-handle-styles';
                    styleElement.textContent = tableHandlesCSS;
                    document.head.appendChild(styleElement);
                } else {
                    // If it exists, update the content
                    styleElement.textContent = tableHandlesCSS;
                }
            }
        """
    def table_row_column_js_fixed(self):
        """Fixed JavaScript for table row and column operations with resizing functionality"""
        return """
        // Function to add a row to the table
        function addTableRow(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const rows = tableElement.rows;
            if (rows.length > 0) {
                // If position is provided, use it, otherwise append at the end
                const rowIndex = (position !== undefined) ? position : rows.length;
                const newRow = tableElement.insertRow(rowIndex);
                
                for (let i = 0; i < rows[0].cells.length; i++) {
                    const cell = newRow.insertCell(i);
                    cell.innerHTML = '&nbsp;';
                    // Copy border style from other cells
                    if (rows[0].cells[i].style.border) {
                        cell.style.border = rows[0].cells[i].style.border;
                    } else {
                        cell.style.border = '1px solid ' + borderColor;
                    }
                    // Copy padding style from other cells
                    if (rows[0].cells[i].style.padding) {
                        cell.style.padding = rows[0].cells[i].style.padding;
                    } else {
                        cell.style.padding = '5px';
                    }
                }
                
                // Re-initialize resizers for the table
                if (tableElement === activeTable) {
                    initializeTableResizers(tableElement);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to add a column to the table
        function addTableColumn(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            const rows = tableElement.rows;
            for (let i = 0; i < rows.length; i++) {
                // If position is provided, use it, otherwise append at the end
                const cellIndex = (position !== undefined) ? position : rows[i].cells.length;
                const cell = rows[i].insertCell(cellIndex);
                cell.innerHTML = '&nbsp;';
                
                // Default styles based on theme
                let cellStyle = {
                    border: '1px solid ' + borderColor,
                    padding: '5px'
                };
                
                // Copy styles from adjacent cells if available
                if (rows[i].cells.length > 1) {
                    const refCell = cellIndex > 0 ? 
                                    rows[i].cells[cellIndex - 1] : 
                                    rows[i].cells[cellIndex + 1];
                                    
                    if (refCell) {
                        if (refCell.style.border) {
                            cellStyle.border = refCell.style.border;
                        }
                        if (refCell.style.padding) {
                            cellStyle.padding = refCell.style.padding;
                        }
                        
                        // If it's a header cell, make new cell a header too
                        if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                            const headerCell = document.createElement('th');
                            headerCell.innerHTML = cell.innerHTML;
                            
                            // Apply all styles
                            Object.assign(headerCell.style, cellStyle);
                            headerCell.style.backgroundColor = headerBgColor;
                            
                            cell.parentNode.replaceChild(headerCell, cell);
                        } else {
                            // Apply styles to normal cell
                            Object.assign(cell.style, cellStyle);
                        }
                    }
                } else {
                    // Apply default styles if no reference cells
                    Object.assign(cell.style, cellStyle);
                    
                    // If this is the first row, it might be a header
                    if (i === 0 && rows[0].cells[0].tagName === 'TH') {
                        const headerCell = document.createElement('th');
                        headerCell.innerHTML = cell.innerHTML;
                        Object.assign(headerCell.style, cellStyle);
                        headerCell.style.backgroundColor = headerBgColor;
                        cell.parentNode.replaceChild(headerCell, cell);
                    }
                }
            }
            
            // Re-initialize resizers for the table
            if (tableElement === activeTable) {
                initializeTableResizers(tableElement);
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a row from the table
        function deleteTableRow(tableElement, rowIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 1) {
                // If rowIndex is provided, delete that row, otherwise delete the last row
                const indexToDelete = (rowIndex !== undefined) ? rowIndex : rows.length - 1;
                if (indexToDelete >= 0 && indexToDelete < rows.length) {
                    tableElement.deleteRow(indexToDelete);
                }
                
                // Re-initialize resizers for the table
                if (tableElement === activeTable) {
                    initializeTableResizers(tableElement);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a column from the table
        function deleteTableColumn(tableElement, colIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 0 && rows[0].cells.length > 1) {
                // If colIndex is provided, delete that column, otherwise delete the last column
                const indexToDelete = (colIndex !== undefined) ? colIndex : rows[0].cells.length - 1;
                
                for (let i = 0; i < rows.length; i++) {
                    if (indexToDelete >= 0 && indexToDelete < rows[i].cells.length) {
                        rows[i].deleteCell(indexToDelete);
                    }
                }
                
                // Re-initialize resizers for the table
                if (tableElement === activeTable) {
                    initializeTableResizers(tableElement);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a table
        function deleteTable(tableElement) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            // Remove the table from the DOM
            tableElement.parentNode.removeChild(tableElement);
            
            // Reset activeTable reference
            activeTable = null;
            
            // Notify the app
            try {
                window.webkit.messageHandlers.tableDeleted.postMessage('table-deleted');
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about table deletion:", e);
            }
        }
        
        // Variables for row/column resizing
        var isResizingRow = false;
        var isResizingColumn = false;
        var currentRowBorder = null;
        var currentColumnBorder = null;
        var resizeStartX = 0;
        var resizeStartY = 0;
        var resizeStartHeight = 0;
        var resizeStartWidth = 0;
        var resizingRowIndex = -1;
        var resizingColumnIndex = -1;
        
        // Function to initialize row/column resizing
        function initializeTableResizers(tableElement) {
            if (!tableElement) return;
            
            // Clear existing resizers first
            const existingResizers = tableElement.querySelectorAll('.column-resizer, .row-resizer, .table-edge-resizer');
            existingResizers.forEach(resizer => resizer.remove());
            
            // Add column resizers to all cells EXCEPT the last column
            for (let i = 0; i < tableElement.rows.length; i++) {
                const row = tableElement.rows[i];
                for (let j = 0; j < row.cells.length - 1; j++) {
                    const cell = row.cells[j];
                    const resizer = document.createElement('div');
                    resizer.className = 'column-resizer';
                    resizer.dataset.columnIndex = j;
                    cell.appendChild(resizer);
                }
            }
            
            // Add row resizers to all cells EXCEPT the last row
            for (let i = 0; i < tableElement.rows.length - 1; i++) {
                const row = tableElement.rows[i];
                for (let j = 0; j < row.cells.length; j++) {
                    const cell = row.cells[j];
                    const resizer = document.createElement('div');
                    resizer.className = 'row-resizer';
                    resizer.dataset.rowIndex = i;
                    cell.appendChild(resizer);
                }
            }
            
            // Add edge resizers for the table itself
            // Right edge resizer (for table width)
            const rightEdgeResizer = document.createElement('div');
            rightEdgeResizer.className = 'table-edge-resizer right-edge';
            tableElement.appendChild(rightEdgeResizer);
            
            // Bottom edge resizer (for table height)
            const bottomEdgeResizer = document.createElement('div');
            bottomEdgeResizer.className = 'table-edge-resizer bottom-edge';
            tableElement.appendChild(bottomEdgeResizer);
            
            // Left edge resizer (for table width from left side)
            const leftEdgeResizer = document.createElement('div');
            leftEdgeResizer.className = 'table-edge-resizer left-edge';
            tableElement.appendChild(leftEdgeResizer);
            
            // Top edge resizer (for table height from top)
            const topEdgeResizer = document.createElement('div');
            topEdgeResizer.className = 'table-edge-resizer top-edge';
            tableElement.appendChild(topEdgeResizer);
            
            tableElement.dataset.resizersInitialized = 'true';
        }
        
        // Function to update column width
        function updateColumnWidth(tableElement, columnIndex, newWidth) {
            if (!tableElement) return;
            
            // Ensure minimum width
            const minWidth = 30;
            newWidth = Math.max(minWidth, newWidth);
            
            // Update the width of all cells in the column
            for (let i = 0; i < tableElement.rows.length; i++) {
                const cell = tableElement.rows[i].cells[columnIndex];
                if (cell) {
                    cell.style.width = newWidth + 'px';
                    cell.style.minWidth = minWidth + 'px';
                }
            }
            
            // Update table layout
            tableElement.style.tableLayout = 'fixed';
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to update row height
        function updateRowHeight(tableElement, rowIndex, newHeight) {
            if (!tableElement || !tableElement.rows[rowIndex]) return;
            
            // Ensure minimum height
            const minHeight = 20;
            newHeight = Math.max(minHeight, newHeight);
            
            // Update the height of all cells in the row
            const row = tableElement.rows[rowIndex];
            for (let i = 0; i < row.cells.length; i++) {
                const cell = row.cells[i];
                cell.style.height = newHeight + 'px';
                cell.style.minHeight = minHeight + 'px';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to resize table from edges
        function resizeTableFromEdge(tableElement, edge, deltaX, deltaY) {
            if (!tableElement) return;
            
            const minWidth = 50;
            const minHeight = 50;
            
            switch(edge) {
                case 'right':
                    const newWidth = resizeStartWidth + deltaX;
                    tableElement.style.width = Math.max(minWidth, newWidth) + 'px';
                    break;
                case 'bottom':
                    const newHeight = resizeStartHeight + deltaY;
                    tableElement.style.height = Math.max(minHeight, newHeight) + 'px';
                    break;
                case 'left':
                    const newWidthLeft = resizeStartWidth - deltaX;
                    if (newWidthLeft >= minWidth) {
                        tableElement.style.width = newWidthLeft + 'px';
                        // If floating, adjust position
                        if (tableElement.classList.contains('floating-table')) {
                            const currentLeft = parseInt(tableElement.style.left) || 0;
                            tableElement.style.left = (currentLeft + deltaX) + 'px';
                        }
                    }
                    break;
                case 'top':
                    const newHeightTop = resizeStartHeight - deltaY;
                    if (newHeightTop >= minHeight) {
                        tableElement.style.height = newHeightTop + 'px';
                        // If floating, adjust position
                        if (tableElement.classList.contains('floating-table')) {
                            const currentTop = parseInt(tableElement.style.top) || 0;
                            tableElement.style.top = (currentTop + deltaY) + 'px';
                        }
                    }
                    break;
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Event handlers for row/column resizing
        document.addEventListener('mousedown', function(e) {
            if (e.target.classList.contains('column-resizer')) {
                isResizingColumn = true;
                const cell = e.target.parentElement;
                const columnIndex = parseInt(e.target.dataset.columnIndex);
                const table = findParentTable(e.target);
                
                if (table) {
                    currentColumnBorder = e.target;
                    resizingColumnIndex = columnIndex;
                    resizeStartX = e.clientX;
                    resizeStartWidth = cell.offsetWidth;
                    activeTable = table;
                    
                    e.preventDefault();
                    e.stopPropagation();
                }
            } else if (e.target.classList.contains('row-resizer')) {
                isResizingRow = true;
                const cell = e.target.parentElement;
                const rowIndex = parseInt(e.target.dataset.rowIndex);
                const table = findParentTable(e.target);
                
                if (table) {
                    currentRowBorder = e.target;
                    resizingRowIndex = rowIndex;
                    resizeStartY = e.clientY;
                    resizeStartHeight = cell.offsetHeight;
                    activeTable = table;
                    
                    e.preventDefault();
                    e.stopPropagation();
                }
            } else if (e.target.classList.contains('table-edge-resizer')) {
                const table = e.target.parentElement;
                activeTable = table;
                resizeStartX = e.clientX;
                resizeStartY = e.clientY;
                resizeStartWidth = table.offsetWidth;
                resizeStartHeight = table.offsetHeight;
                
                if (e.target.classList.contains('right-edge')) {
                    currentResizeEdge = 'right';
                } else if (e.target.classList.contains('bottom-edge')) {
                    currentResizeEdge = 'bottom';
                } else if (e.target.classList.contains('left-edge')) {
                    currentResizeEdge = 'left';
                } else if (e.target.classList.contains('top-edge')) {
                    currentResizeEdge = 'top';
                }
                
                isResizingEdge = true;
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isResizingColumn && activeTable) {
                const deltaX = e.clientX - resizeStartX;
                const newWidth = resizeStartWidth + deltaX;
                updateColumnWidth(activeTable, resizingColumnIndex, newWidth);
            } else if (isResizingRow && activeTable) {
                const deltaY = e.clientY - resizeStartY;
                const newHeight = resizeStartHeight + deltaY;
                updateRowHeight(activeTable, resizingRowIndex, newHeight);
            } else if (isResizingEdge && activeTable) {
                const deltaX = e.clientX - resizeStartX;
                const deltaY = e.clientY - resizeStartY;
                resizeTableFromEdge(activeTable, currentResizeEdge, deltaX, deltaY);
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isResizingColumn || isResizingRow || isResizingEdge) {
                isResizingColumn = false;
                isResizingRow = false;
                isResizingEdge = false;
                currentColumnBorder = null;
                currentRowBorder = null;
                currentResizeEdge = null;
                resizingColumnIndex = -1;
                resizingRowIndex = -1;
            }
        });
        
        // Additional variables for edge resizing
        var isResizingEdge = false;
        var currentResizeEdge = null;
        """


        
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())
