#!/usr/bin/env python3
import sys
import gi
import re
import os
# Add these imports at the top of your file
import tempfile
import os
import subprocess
import json

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
        width_combo.set_selected(1)  # Default to 100%
        
        width_box.append(width_label)
        width_box.append(width_combo)
        content_box.append(width_box)
        
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
            width_options.get_string(width_combo.get_selected())
        ))
        
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        # Set dialog content and present
        dialog.set_child(content_box)
        dialog.present(win)
        
    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option):
        """Handle response from the table dialog"""
        dialog.close()
        
        # Prepare the width value
        width_value = "auto"
        if width_option != "Auto":
            width_value = width_option
        
        # Execute JavaScript to insert the table
        js_code = f"""
        (function() {{
            insertTable({rows}, {cols}, {str(has_header).lower()}, {border_width}, "{width_value}");
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table inserted")

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

    def init_editor_js(self):
        """JavaScript to initialize the editor and set up event listeners."""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Give the editor a proper tabindex to ensure it can capture keyboard focus
            editor.setAttribute('tabindex', '0');
            
            // Capture tab key to prevent focus from shifting
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    // Prevent the default focus shift action
                    e.preventDefault();
                    
                    // Insert tab character as a styled span
                    document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                    
                    // Trigger input event to register the change for undo/redo
                    const event = new Event('input', {
                        bubbles: true,
                        cancelable: true
                    });
                    editor.dispatchEvent(event);
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

################
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
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
        
        // CSS for table handles
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
        }

        @media (prefers-color-scheme: dark) {
            .table-drag-handle {
                background-color: #0078d7;
            }
            .table-handle {
                border-color: transparent transparent #0078d7 transparent;
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
        
        // Function to insert a table at the current cursor position
        function insertTable(rows, cols, hasHeader, borderWidth, tableWidth) {
            // Get theme-appropriate colors
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Create table HTML
            let tableHTML = '<table cellspacing="0" cellpadding="5" ';
            
            // Add class and style attributes
            tableHTML += 'class="editor-table no-wrap" style="border-collapse: collapse; width: ' + tableWidth + ';">';
            
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
                    activateTable(newTable);
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
                }
            }, 10);
        }
        
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
        
        // Function to activate a table (add handles)
        function activateTable(tableElement) {
            if (activeTable === tableElement) return; // Already active
            
            // Deactivate any previously active tables
            if (activeTable && activeTable !== tableElement) {
                deactivateTable(activeTable);
            }
            
            activeTable = tableElement;
            
            // Store original styles and apply selection styling
            storeAndApplyTableStyles(tableElement);
            
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
                dragHandle.title = 'Drag to reposition table between paragraphs';
                
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
            tableElement.style.position = 'relative';
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
        
        // Function to start table drag
        function startTableDrag(e, tableElement) {
            e.preventDefault();
            if (!tableElement) return;
            
            isDragging = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            document.body.style.cursor = 'move';
        }
        
        // Function to move table
        function moveTable(e) {
            if (!isDragging || !activeTable) return;
            
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
        
        // Function to set table alignment
        function setTableAlignment(alignClass) {
            if (!activeTable) return;
            
            // Remove all alignment classes
            activeTable.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            
            // Add the requested alignment class
            activeTable.classList.add(alignClass);
            
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
                        // This ensures the toolbar is hidden even if the activeTable reference was lost
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
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
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

        // Add function to add table handle styles
        function addTableHandleStyles() {
            const styleElement = document.createElement('style');
            styleElement.id = 'table-handle-styles';
            styleElement.textContent = tableHandlesCSS;
            document.head.appendChild(styleElement);
        }
        """    
        
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
                    margin: 10px 0;
                    position: relative;  /* Important for internal handles */
                    resize: both;
                    overflow: visible;   /* Changed from auto to visible to ensure handles are not clipped */
                    min-width: 30px;
                    min-height: 30px;
                }}
                table.left-align {{
                    float: left;
                    margin-right: 10px;
                    clear: none;
                }}
                table.right-align {{
                    float: right;
                    margin-left: 10px;
                    clear: none;
                }}
                table.center-align {{
                    margin-left: auto;
                    margin-right: auto;
                    float: none;
                    clear: both;
                }}
                table.no-wrap {{
                    float: none;
                    clear: both;
                    width: 100%;
                }}
                table td {{
                    border: 1px solid #ccc;
                    padding: 5px;
                    min-width: 30px;
                    position: relative;
                }}
                table th {{
                    border: 1px solid #ccc;
                    padding: 5px;
                    min-width: 30px;
                    background-color: #f0f0f0;
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
                    table td, table th {{
                        border-color: #444;
                    }}
                    table.text-box-table {{
                        border-color: #444 !important;
                        background-color: #2d2d2d;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
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
        """##################
    # 1. Add a "Show HTML" button to the file toolbar

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
        table_button = Gtk.Button(icon_name="table-symbolic")
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

        # Insert checkbox list button
        checkbox_button = Gtk.Button(icon_name="checkbox-symbolic")  # Use appropriate icon
        checkbox_button.set_size_request(40, 36)
        checkbox_button.set_tooltip_text("Insert Checkbox List")
        checkbox_button.connect("clicked", lambda btn: self.on_insert_checkbox_clicked(win, btn))

        # Add buttons to insert group
        insert_group.append(table_button)
        insert_group.append(text_box_button)
        insert_group.append(image_button)
        insert_group.append(link_button)
        insert_group.append(checkbox_button)
        
        # Add insert group to toolbar
        file_toolbar.append(insert_group)

        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator.set_margin_start(8)
        separator.set_margin_end(8)
        file_toolbar.append(separator)
        
        # Show HTML Code button
        show_html_button = Gtk.Button(label="Show HTML")
        show_html_button.set_tooltip_text("Show HTML Code")
        show_html_button.connect("clicked", lambda btn: self.on_show_html_clicked(win))
        file_toolbar.append(show_html_button)

        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar


    # 2. Add the handler for the "Show HTML" button click

    def on_show_html_clicked(self, win):
        """Handle Show HTML button click"""
        win.statusbar.set_text("Getting HTML code...")
        
        # Execute JavaScript to get the HTML content
        js_code = """
        (function() {
            // Get the editor's content
            const editor = document.getElementById('editor');
            return editor.innerHTML;
        })();
        """
        
        # Use a callback function to handle the result
        win.webview.evaluate_javascript(js_code, -1, None, None, None,
                                       self.show_html_dialog_callback, win)


    def show_html_dialog_callback(self, webview, result, win):
        """Callback to display the HTML code in a dialog"""
        try:
            html_content = webview.evaluate_javascript_finish(result)
            if not html_content:
                win.statusbar.set_text("Failed to get HTML content.")
                return
                
            # Create a dialog to show the HTML
            self.show_html_dialog(win, html_content)
        except Exception as e:
            print(f"Error getting HTML content: {e}")
            win.statusbar.set_text(f"Error: {str(e)}")


    def show_html_dialog(self, win, html_content):
        """Create and show a dialog with the HTML code"""
        # Create the dialog
        dialog = Adw.Dialog()
        dialog.set_title("HTML Code")
        dialog.set_content_width(800)
        dialog.set_content_height(600)
        
        # Create a vertical box for dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Create a HeaderBar to add to the top of the dialog
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_margin_bottom(12)
        
        # Create a title for the dialog
        title_label = Gtk.Label()
        title_label.set_markup("<b>Document HTML Code</b>")
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)
        
        # Add a copy button
        copy_button = Gtk.Button(label="Copy Code")
        copy_button.set_halign(Gtk.Align.END)
        copy_button.set_hexpand(True)
        copy_button.add_css_class("suggested-action")
        header_box.append(copy_button)
        
        content_box.append(header_box)
        
        # Create a scrollable text view for the HTML code
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)
        
        text_view = Gtk.TextView()
        text_view.set_editable(True)  # Make it editable so users can copy/edit
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.set_left_margin(12)
        text_view.set_right_margin(12)
        text_view.set_top_margin(12)
        text_view.set_bottom_margin(12)
        
        # Set monospace font for code
        text_view.get_style_context().add_class("monospace")
        
        # Set the HTML content
        buffer = text_view.get_buffer()
        buffer.set_text(html_content)
        
        scrolled_window.set_child(text_view)
        content_box.append(scrolled_window)
        
        # Add description text
        desc_label = Gtk.Label()
        desc_label.set_markup("<small>You can copy this HTML or select portions of it. This is read-only and changes here won't affect the document.</small>")
        desc_label.set_wrap(True)
        desc_label.set_margin_top(8)
        desc_label.set_halign(Gtk.Align.START)
        content_box.append(desc_label)
        
        # Add button box at the bottom
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(16)
        
        # Add an apply button to update document with edited HTML
        apply_button = Gtk.Button(label="Apply Changes")
        apply_button.add_css_class("suggested-action")
        
        close_button = Gtk.Button(label="Close")
        
        button_box.append(apply_button)
        button_box.append(close_button)
        content_box.append(button_box)
        
        # Set dialog content
        dialog.set_child(content_box)
        
        # Set up button handlers
        close_button.connect("clicked", lambda btn: dialog.close())
        
        # Handler for copy button
        copy_button.connect("clicked", lambda btn: self.copy_text_to_clipboard(buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(), True)))
        
        # Handler for apply button
        apply_button.connect("clicked", lambda btn: self.apply_html_changes(
            win, buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True), dialog))
        
        # Show the dialog
        dialog.present(win)
        win.statusbar.set_text("HTML code displayed")


    def copy_text_to_clipboard(self, text):
        """Copy text to clipboard"""
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(text)


    def apply_html_changes(self, win, html_content, dialog):
        """Apply edited HTML content to the document"""
        # JavaScript to set the editor content
        js_code = f"""
        (function() {{
            const editor = document.getElementById('editor');
            editor.innerHTML = `{html_content.replace('`', '\\`')}`;
            return true;
        }})();
        """
        
        self.execute_js(win, js_code)
        win.statusbar.set_text("HTML code updated")
        dialog.close()


###############

    def on_show_html_clicked(self, win):
        """Handle Show HTML button click using a temporary file approach"""
        win.statusbar.set_text("Getting HTML code...")
        
        # Register a custom message handler just for HTML content
        user_content_manager = win.webview.get_user_content_manager()
        
        # First check if the handler is already registered to avoid errors
        try:
            user_content_manager.register_script_message_handler("sendHtmlToFile")
        except:
            # Handler might already be registered
            pass
        
        # Connect the handler to our function
        user_content_manager.connect(
            "script-message-received::sendHtmlToFile", 
            lambda manager, message: self.receive_html_and_show(win, message)
        )
        
        # JavaScript to get the HTML and send it to our handler
        js_code = """
        (function() {
            const editor = document.getElementById('editor');
            
            // Get the HTML content
            const htmlContent = editor.innerHTML;
            
            // Send the content to Python
            window.webkit.messageHandlers.sendHtmlToFile.postMessage(htmlContent);
        })();
        """
        
        # Execute the JavaScript
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)


    def receive_html_and_show(self, win, message):
        """Receive HTML from JavaScript and show it in a dialog or external editor"""
        try:
            # Try to get the HTML content in the most basic way
            html_content = str(message)
            
            # If the content still looks like a JavaScript object reference,
            # we'll need to use a more direct approach with a temporary file
            if html_content.startswith("<JavaScriptCore.Value") or not html_content.strip():
                self.show_html_in_external_editor(win)
            else:
                # If we got actual HTML, show it in our dialog
                self.show_simple_html_dialog(win, html_content)
                
        except Exception as e:
            print(f"Error processing HTML message: {e}")
            # Fall back to the external editor approach
            self.show_html_in_external_editor(win)


    def show_html_in_external_editor(self, win):
        """Show HTML in an external editor using a temporary file"""
        try:
            # Create a file to communicate between JS and Python
            temp_path = None
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
                temp_path = temp.name
                # Just create an empty file first
                temp.write(b'<!-- HTML content will be written here -->')
            
            # Path where JavaScript can write the content
            print(f"Created temporary file: {temp_path}")
            win.statusbar.set_text(f"Extracting HTML to {temp_path}")
            
            # JavaScript to write the content directly to the file
            js_path = json.dumps(temp_path)  # Properly escape path for JS
            js_code = f"""
            (function() {{
                const editor = document.getElementById('editor');
                const htmlContent = editor.innerHTML;
                
                // Use a simple approach to tell Python the content is ready
                const path = {js_path};
                console.log("Writing HTML to path: " + path);
                
                // Create a download link
                const a = document.createElement('a');
                const blob = new Blob([htmlContent], {{type: 'text/html'}});
                a.href = URL.createObjectURL(blob);
                a.download = path.split('/').pop();
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                
                // Notify that we're done
                window.webkit.messageHandlers.sendHtmlToFile.postMessage("HTML export initiated to: " + path);
            }})();
            """
            
            # Execute the JavaScript to initiate the download
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            
            # Inform the user how to get the HTML
            dialog = Gtk.MessageDialog(
                transient_for=win,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="HTML Code Exported"
            )
            dialog.format_secondary_text(
                f"The HTML has been exported to '{temp_path}'.\n\n"
                f"You can open this file in any text editor to view or edit the HTML.\n\n"
                f"Would you like to open it now?"
            )
            
            # Add Open button
            dialog.add_button("Open File", Gtk.ResponseType.APPLY)
            
            # Show the dialog and handle response
            response = dialog.run()
            
            if response == Gtk.ResponseType.APPLY:
                # Open the HTML file in the default editor
                subprocess.run(['xdg-open', temp_path])
            
            dialog.destroy()
            
        except Exception as e:
            print(f"Error in HTML export: {e}")
            win.statusbar.set_text(f"Error exporting HTML: {str(e)}")
            
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=win,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="HTML Export Failed"
            )
            error_dialog.format_secondary_text(f"Failed to export HTML: {str(e)}")
            error_dialog.run()
            error_dialog.destroy()


    # Alternative direct export button
    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        # [... existing toolbar code ...]
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator.set_margin_start(8)
        separator.set_margin_end(8)
        file_toolbar.append(separator)
        
        # Export HTML button (simpler alternative)
        export_html_button = Gtk.Button(label="Export HTML")
        export_html_button.set_tooltip_text("Export HTML to a file")
        export_html_button.connect("clicked", lambda btn: self.export_html_to_file(win))
        file_toolbar.append(export_html_button)

        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar


    def export_html_to_file(self, win):
        """Export HTML directly to a file"""
        # Create a file chooser dialog
        dialog = Gtk.FileChooserNative(
            title="Save HTML As",
            transient_for=win,
            action=Gtk.FileChooserAction.SAVE,
            accept_label="_Save",
            cancel_label="_Cancel"
        )
        
        # Set default filename
        dialog.set_current_name("document.html")
        
        # Set up filters
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        filter_html.add_pattern("*.html")
        filter_html.add_pattern("*.htm")
        dialog.add_filter(filter_html)
        
        # Show the dialog
        response = dialog.show()
        
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            
            # Register a message handler to receive the HTML
            user_content_manager = win.webview.get_user_content_manager()
            try:
                user_content_manager.register_script_message_handler("saveHtmlToFile")
            except:
                pass  # May already be registered
                
            user_content_manager.connect(
                "script-message-received::saveHtmlToFile",
                lambda manager, message: self.write_html_to_file(str(message), file_path, win)
            )
            
            # Get the HTML content and send it to our handler
            js_code = """
            (function() {
                const editor = document.getElementById('editor');
                const htmlContent = editor.innerHTML;
                window.webkit.messageHandlers.saveHtmlToFile.postMessage(htmlContent);
            })();
            """
            
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        dialog.destroy()


    def write_html_to_file(self, html_content, file_path, win):
        """Write HTML content to the specified file"""
        try:
            # If html_content is a JavaScript object reference, use a different approach
            if html_content.startswith("<JavaScriptCore.Value"):
                # Fall back to saving an entire HTML document with a download approach
                js_path = json.dumps(file_path)
                js_code = f"""
                (function() {{
                    const editor = document.getElementById('editor');
                    const htmlContent = editor.innerHTML;
                    
                    // Use full HTML structure
                    const doctype = '<!DOCTYPE html>\\n';
                    const htmlStart = '<html>\\n<head>\\n<meta charset="utf-8">\\n<title>Exported Document</title>\\n</head>\\n<body>\\n';
                    const htmlEnd = '\\n</body>\\n</html>';
                    const fullHtml = doctype + htmlStart + htmlContent + htmlEnd;
                    
                    // Create a download link
                    const a = document.createElement('a');
                    const blob = new Blob([fullHtml], {{type: 'text/html'}});
                    a.href = URL.createObjectURL(blob);
                    a.download = {js_path}.split('/').pop();
                    a.style.display = 'none';
                    document.body.appendChild(a);
                    a.click();
                    
                    // Clean up
                    setTimeout(() => {{
                        URL.revokeObjectURL(a.href);
                        document.body.removeChild(a);
                    }}, 100);
                }})();
                """
                win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
                win.statusbar.set_text(f"HTML exported to {file_path} (download)")
            else:
                # Standard file writing
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Create a proper HTML document
                    f.write('<!DOCTYPE html>\n')
                    f.write('<html>\n<head>\n<meta charset="utf-8">\n<title>Exported Document</title>\n</head>\n<body>\n')
                    f.write(html_content)
                    f.write('\n</body>\n</html>')
                
                win.statusbar.set_text(f"HTML exported to {file_path}")
        except Exception as e:
            print(f"Error writing HTML to file: {e}")
            win.statusbar.set_text(f"Error saving HTML: {str(e)}")
#########
    def on_show_html_clicked(self, win):
        """Show HTML code in a dialog"""
        # Use a simple approach with webview directly
        try:
            # Execute JavaScript to get HTML
            js_code = """
            (function() {
                const editor = document.getElementById('editor');
                return editor.innerHTML;
            })();
            """
            
            # Set up a handler to receive the result
            win.webview.evaluate_javascript(
                js_code, 
                -1, 
                None, 
                None, 
                None,
                lambda source, result, data: self.process_html_result(source, result, win),
                None
            )
            
            win.statusbar.set_text("Getting HTML...")
        except Exception as e:
            print(f"Error in on_show_html_clicked: {e}")
            win.statusbar.set_text(f"Error: {str(e)}")


    def process_html_result(self, source, result, win):
        """Process the HTML result from JavaScript"""
        try:
            # Get whatever result we can
            js_result = source.evaluate_javascript_finish(result)
            html_text = str(js_result)
            
            # Show in a simple dialog
            self.show_html_in_dialog(win, html_text)
        except Exception as e:
            print(f"Error processing HTML result: {e}")
            win.statusbar.set_text(f"Error: {str(e)}")


    def show_html_in_dialog(self, win, html_text):
        """Show HTML in a simple dialog"""
        # Create a dialog
        dialog = Adw.Window()
        dialog.set_title("HTML Code")
        dialog.set_default_size(800, 600)
        dialog.set_transient_for(win)  # This fixes the "mapped without transient parent" warning
        
        # Create a vertical box for content
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        dialog.set_content(vbox)
        
        # Create a scrollable text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.append(scrolled)
        
        # Create the text view for the HTML
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.set_editable(True)
        text_view.add_css_class("monospace")
        text_view.set_left_margin(12)
        text_view.set_right_margin(12)
        text_view.set_top_margin(12)
        text_view.set_bottom_margin(12)
        scrolled.set_child(text_view)
        
        # Set the HTML content
        buffer = text_view.get_buffer()
        buffer.set_text(html_text)
        
        # Add button box at the bottom
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        vbox.append(button_box)
        
        # Add copy button
        copy_button = Gtk.Button(label="Copy Code")
        copy_button.connect("clicked", lambda btn: self.copy_buffer_to_clipboard(buffer))
        button_box.append(copy_button)
        
        # Add apply button
        apply_button = Gtk.Button(label="Apply Changes")
        apply_button.connect("clicked", lambda btn: self.apply_html_from_buffer(
            win, buffer, dialog))
        button_box.append(apply_button)
        
        # Add close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda btn: dialog.destroy())
        button_box.append(close_button)
        
        # Show the dialog
        dialog.present()
        win.statusbar.set_text("HTML code displayed")


    def copy_buffer_to_clipboard(self, buffer):
        """Copy text buffer to clipboard"""
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)


    def apply_html_from_buffer(self, win, buffer, dialog):
        """Apply HTML from text buffer to the document"""
        html_content = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        
        # JavaScript to set the editor content
        js_code = """
        (function() {
            const editor = document.getElementById('editor');
            editor.innerHTML = arguments[0];
            return true;
        })(arguments[0]);
        """
        
        # Set the HTML content
        win.webview.evaluate_javascript_with_params(
            js_code, 
            GLib.Variant("(s)", (html_content,)), 
            None, None, None, None, None, None
        )
        
        win.statusbar.set_text("HTML code updated")
        dialog.destroy()


    # Alternative export function
    def export_html_to_file(self, win):
        """Export HTML to file using modern GTK4 approaches"""
        # Create file chooser
        file_chooser = Gtk.FileDialog()
        file_chooser.set_title("Save HTML As")
        
        # Set up initial name and filters
        initial_name = GLib.Variant.new_string("document.html")
        save_options = Gtk.FileChooserNative.new_save()
        save_options.set_current_name(initial_name)
        
        # Create filter for HTML files
        file_filter = Gtk.FileFilter()
        file_filter.set_name("HTML files")
        file_filter.add_mime_type("text/html")
        file_filter.add_pattern("*.html")
        file_filter.add_pattern("*.htm")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        file_chooser.set_filters(filters)
        
        # Show the dialog
        file_chooser.save(
            win,                            # Parent window
            None,                           # Cancellable
            lambda dialog, result, data: self.on_save_dialog_response(dialog, result, win),
            None                            # User data
        )


    def on_save_dialog_response(self, dialog, result, win):
        """Handle save dialog response"""
        try:
            file = dialog.save_finish(result)
            if file:
                # Get the file path
                file_path = file.get_path()
                
                # Get HTML content from editor
                js_code = """
                (function() {
                    const editor = document.getElementById('editor');
                    return editor.innerHTML;
                })();
                """
                
                # Set up callback to get HTML and save to file
                win.webview.evaluate_javascript(
                    js_code,
                    -1, 
                    None, 
                    None, 
                    None,
                    lambda source, js_result, data: self.save_html_to_file(
                        source, js_result, file_path, win),
                    None
                )
        except Exception as e:
            print(f"Error in file dialog response: {e}")
            win.statusbar.set_text(f"Error: {str(e)}")


    def save_html_to_file(self, source, result, file_path, win):
        """Save HTML content to file"""
        try:
            # Get the JavaScript result
            js_result = source.evaluate_javascript_finish(result)
            html_content = str(js_result)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write a proper HTML document
                f.write('<!DOCTYPE html>\n')
                f.write('<html>\n<head>\n<meta charset="utf-8">\n<title>Exported Document</title>\n</head>\n<body>\n')
                f.write(html_content)
                f.write('\n</body>\n</html>')
            
            win.statusbar.set_text(f"HTML exported to {file_path}")
        except Exception as e:
            print(f"Error saving HTML to file: {e}")
            win.statusbar.set_text(f"Error saving HTML: {str(e)}")


    # Modern GTK4 way to add the button to toolbar
    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        # [... existing toolbar code ...]
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator.set_margin_start(8)
        separator.set_margin_end(8)
        file_toolbar.append(separator)
        
        # Show HTML Button
        show_html_button = Gtk.Button(label="Show HTML")
        show_html_button.set_tooltip_text("Show HTML Code")
        show_html_button.connect("clicked", lambda btn: self.on_show_html_clicked(win))
        file_toolbar.append(show_html_button)
        
        # Export HTML button
        export_html_button = Gtk.Button(label="Export HTML")
        export_html_button.set_tooltip_text("Export HTML to a file")
        export_html_button.connect("clicked", lambda btn: self.export_html_to_file(win))
        file_toolbar.append(export_html_button)

        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar         
        
###################
    def on_view_html_clicked(self, win):
        """Handle View HTML button click"""
        win.statusbar.set_text("Getting HTML code...")
        
        # Register the message handler with the user content manager
        user_content_manager = win.webview.get_user_content_manager()
        
        # First try to unregister if it exists (to avoid errors if called multiple times)
        try:
            user_content_manager.unregister_script_message_handler("sendHTML")
        except:
            pass
        
        # Now register the handler
        user_content_manager.register_script_message_handler("sendHTML")
        
        # Connect to the correct signal - this is how WebKit actually implements it
        # The signal name is just "script-message-received"
        user_content_manager.connect(
            "script-message-received::sendHTML", 
            lambda mgr, message: self.on_html_message_received(mgr, message, win)
        )
        
        # Use a simpler approach with message posting
        js_message_code = """
        (function() {
            var editor = document.getElementById('editor');
            if (!editor) {
                window.webkit.messageHandlers.sendHTML.postMessage('No editor element found');
                return;
            }
            window.webkit.messageHandlers.sendHTML.postMessage(editor.innerHTML);
        })();
        """
        
        # Execute the JavaScript to send us the HTML content
        win.webview.evaluate_javascript(js_message_code, -1, None, None, None, None, None)


    def on_html_message_received(self, user_content_manager, message, win):
        """Handle HTML content sent via message handler"""
        try:
            # Get the message value - this should always work without complex extraction
            html_content = message.get_js_value().to_string()
            
            if html_content:
                # Create a simple dialog to view the HTML
                self.show_html_in_dialog(win, html_content)
            else:
                win.statusbar.set_text("No HTML content found")
                
        except Exception as e:
            print(f"Error receiving HTML content: {e}")
            win.statusbar.set_text(f"Error: {str(e)}")
            
            # Fallback method if message handling fails
            self.fallback_get_html(win)


    def fallback_get_html(self, win):
        """Fallback method to get HTML when message handling fails"""
        # Try executing JavaScript directly with a simple approach
        js_code = """
        (function() {
            var editor = document.getElementById('editor');
            if (!editor) return "Editor element not found";
            return editor.innerHTML;
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code, 
            -1, 
            None, 
            None, 
            None,
            lambda webview, result, data: self.on_fallback_js_result(webview, result, win), 
            None
        )


    def on_fallback_js_result(self, webview, result, win):
        """Handle result from fallback JavaScript execution"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if not js_result:
                win.statusbar.set_text("Could not get HTML content")
                return
                
            # Try the most direct approach first - just use str()
            html_content = str(js_result)
            
            if html_content.startswith("<JavaScriptCore.Value") or not html_content or html_content == "None":
                # If we got a reference rather than content, use a simpler approach
                self.export_html_to_temp_file(win)
            else:
                # Show the HTML in a dialog
                self.show_html_in_dialog(win, html_content)
                
        except Exception as e:
            print(f"Error in fallback JS result: {e}")
            win.statusbar.set_text(f"Error: {str(e)}")
            
            # Ultimate fallback - export to a file
            self.export_html_to_temp_file(win)


    def show_html_in_dialog(self, win, html_content):
        """Show HTML in a basic dialog with text view"""
        dialog = Gtk.Dialog(
            title="HTML Code",
            transient_for=win,
            modal=True,
            destroy_with_parent=True
        )
        
        dialog.set_default_size(800, 600)
        content_area = dialog.get_content_area()
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        content_area.set_margin_start(12)
        content_area.set_margin_end(12)
        content_area.set_spacing(6)
        
        # Create scrolled window
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        
        # Create text view
        text_view = Gtk.TextView()
        text_view.set_editable(True)
        text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        text_view.set_left_margin(10)
        text_view.set_right_margin(10)
        text_view.set_top_margin(10)
        text_view.set_bottom_margin(10)
        text_view.add_css_class("monospace")  # Modern GTK4 way to add CSS class
        
        # Set the text content
        buffer = text_view.get_buffer()
        buffer.set_text(html_content)
        
        # Add text view to scrolled window
        scrolled_window.set_child(text_view)
        
        # Add scrolled window to dialog
        content_area.append(scrolled_window)
        
        # Add buttons for copy and apply
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        # Copy button
        copy_button = Gtk.Button(label="Copy Code")
        copy_button.connect("clicked", lambda btn: self.copy_to_clipboard(
            buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)))
        button_box.append(copy_button)
        
        # Apply button
        apply_button = Gtk.Button(label="Apply Changes")
        apply_button.connect("clicked", lambda btn: self.apply_html_changes(
            win, buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True), dialog))
        button_box.append(apply_button)
        
        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda btn: dialog.destroy())
        button_box.append(close_button)
        
        content_area.append(button_box)
        
        # Show the dialog
        dialog.present()
        win.statusbar.set_text("HTML code displayed")


    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)


    def apply_html_changes(self, win, html_content, dialog):
        """Apply edited HTML content to the document"""
        # Extremely simplified version that's more reliable - no javascript parameter escaping
        js_code = """
        (function() {
            var htmlContent = arguments[0];
            var editor = document.getElementById('editor');
            if (!editor) return false;
            editor.innerHTML = htmlContent;
            return true;
        })(arguments[0]);
        """
        
        # Use the evaluate_javascript_with_params to avoid string escaping issues
        win.webview.evaluate_javascript_with_params(
            js_code,
            GLib.Variant("(s)", (html_content,)),
            None, None, None, None, None, None
        )
        
        win.statusbar.set_text("HTML code updated")
        dialog.destroy()


    def export_html_to_temp_file(self, win):
        """Export HTML to a temporary file and open it"""
        # Use a very direct approach with a message handler
        user_content_manager = win.webview.get_user_content_manager()
        
        # First try to unregister if it exists (to avoid errors if called multiple times)
        try:
            user_content_manager.unregister_script_message_handler("exportHTML")
        except:
            pass
        
        # Now register the handler
        user_content_manager.register_script_message_handler("exportHTML")
        
        # Connect to the received signal
        user_content_manager.connect(
            "script-message-received::exportHTML", 
            lambda mgr, message: self.on_export_html_message_received(mgr, message, win)
        )
        
        # Send the HTML content through the message handler
        js_export_code = """
        (function() {
            var editor = document.getElementById('editor');
            if (!editor) {
                window.webkit.messageHandlers.exportHTML.postMessage("");
                return;
            }
            window.webkit.messageHandlers.exportHTML.postMessage(editor.innerHTML);
        })();
        """
        
        win.webview.evaluate_javascript(js_export_code, -1, None, None, None, None, None)


    def on_export_html_message_received(self, user_content_manager, message, win):
        """Handle HTML content for export"""
        try:
            html_content = message.get_js_value().to_string()
            
            if not html_content:
                win.statusbar.set_text("No HTML content to export")
                return
                
            # Create a temporary file
            import tempfile
            import subprocess
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
                temp_path = temp.name
                # Create a complete HTML document
                full_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>HTML Code</title>
        <style>
            body {{ background-color: #f9f9f9; font-family: sans-serif; padding: 20px; }}
            pre {{ 
                white-space: pre-wrap; 
                background-color: white; 
                border: 1px solid #ddd; 
                padding: 15px; 
                border-radius: 4px;
                font-family: monospace;
                font-size: 14px;
                line-height: 1.4;
            }}
            h1 {{ font-size: 24px; color: #333; }}
        </style>
    </head>
    <body>
    <h1>HTML Code</h1>
    <pre>{html_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</pre>
    </body>
    </html>"""
                temp.write(full_html.encode('utf-8'))
            
            # Show a dialog asking if they want to open the file
            dialog = Gtk.MessageDialog(
                transient_for=win,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.NONE,
                text="HTML Code Exported"
            )
            
            dialog.format_secondary_text(
                f"HTML code has been exported to:\n{temp_path}"
            )
            
            # Add custom buttons
            dialog.add_button("Open File", Gtk.ResponseType.OK)
            dialog.add_button("Close", Gtk.ResponseType.CANCEL)
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                # Open the file in the default application
                try:
                    subprocess.run(['xdg-open', temp_path])
                    win.statusbar.set_text(f"Opened HTML file: {temp_path}")
                except Exception as e:
                    print(f"Error opening file: {e}")
                    win.statusbar.set_text(f"Error opening file: {str(e)}")
            else:
                win.statusbar.set_text(f"HTML exported to: {temp_path}")
                
        except Exception as e:
            print(f"Error exporting HTML: {e}")
            win.statusbar.set_text(f"Error exporting HTML: {str(e)}")        
        
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
