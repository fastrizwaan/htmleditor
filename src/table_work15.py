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
        {self.table_style_js()}  # table styling functions
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
    def table_style_js(self):
        return r"""
        // JavaScript for table styling (border, background, etc.)

function table_style_js() {
    return `
    // Global variable to track if color changes should only affect selected cells
    var colorSelectionOnly = false;
    
    // Function to set table border style (solid, dashed, dotted, etc.)
    function setTableBorderStyle(style, target) {
        if (!activeTable) return;
        
        if (target === 'table') {
            // Apply only to table outline
            activeTable.style.borderStyle = style;
            
            // If 'none', also set border width to 0 for proper hiding
            if (style === 'none') {
                activeTable.style.borderWidth = '0px';
            } else if (!activeTable.style.borderWidth || activeTable.style.borderWidth === '0px') {
                // If we're showing a border that was previously hidden, give it a width
                activeTable.style.borderWidth = '1px';
            }
        } else {
            // Apply to all cells
            const cells = activeTable.querySelectorAll('th, td');
            cells.forEach(cell => {
                cell.style.borderStyle = style;
                
                // If 'none', also set border width to 0 for proper hiding
                if (style === 'none') {
                    cell.style.borderWidth = '0px';
                } else if (!cell.style.borderWidth || cell.style.borderWidth === '0px') {
                    // If we're showing a border that was previously hidden, give it a width
                    cell.style.borderWidth = '1px';
                }
            });
        }
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set table border width
    function setTableBorderWidth(width, target) {
        if (!activeTable) return;
        
        const widthValue = width + 'px';
        
        if (target === 'table') {
            // Apply only to table outline
            activeTable.style.borderWidth = widthValue;
            
            // If setting non-zero width, ensure there's a border style
            if (width > 0 && (!activeTable.style.borderStyle || activeTable.style.borderStyle === 'none')) {
                activeTable.style.borderStyle = 'solid';
            }
        } else {
            // Apply to all cells
            const cells = activeTable.querySelectorAll('th, td');
            cells.forEach(cell => {
                cell.style.borderWidth = widthValue;
                
                // If setting non-zero width, ensure there's a border style
                if (width > 0 && (!cell.style.borderStyle || cell.style.borderStyle === 'none')) {
                    cell.style.borderStyle = 'solid';
                }
            });
        }
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set border color
    function setTableBorderColor(color, target) {
        if (!activeTable) return;
        
        if (target === 'table') {
            // Apply only to table outline
            activeTable.style.borderColor = color;
        } else {
            // Apply to all cells
            const cells = activeTable.querySelectorAll('th, td');
            cells.forEach(cell => {
                cell.style.borderColor = color;
            });
        }
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set transparent border
    function setTransparentBorder(transparent, target) {
        const color = transparent ? 'transparent' : getBorderColor();
        setTableBorderColor(color, target);
    }
    
    // Function to set table shadow
    function setTableShadow(addShadow) {
        if (!activeTable) return;
        
        if (addShadow) {
            // Add shadow with medium intensity by default
            activeTable.style.boxShadow = '0 3px 5px rgba(0,0,0,0.3)';
        } else {
            // Remove shadow
            activeTable.style.boxShadow = 'none';
        }
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set shadow intensity
    function setShadowIntensity(intensity) {
        if (!activeTable) return;
        
        // Scale intensity from 1-10 to appropriate shadow values
        const blur = Math.round(intensity * 1.5);
        const spread = Math.round(intensity * 0.3);
        const opacity = 0.1 + (intensity * 0.05); // 0.15 to 0.6
        
        activeTable.style.boxShadow = \`0 \${Math.ceil(intensity/3)}px \${blur}px \${spread}px rgba(0,0,0,\${opacity})\`;
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set table background color
    function setTableBackground(color) {
        if (!activeTable) return;
        
        activeTable.style.backgroundColor = color;
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set header background color
    function setHeaderBackground(color) {
        if (!activeTable) return;
        
        const headers = activeTable.querySelectorAll('th');
        
        if (colorSelectionOnly) {
            // Get current selection
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                // Check if any header cells are in the selection
                for (let i = 0; i < headers.length; i++) {
                    const header = headers[i];
                    if (isElementInSelection(header, selection)) {
                        header.style.backgroundColor = color;
                    }
                }
            }
        } else {
            // Apply to all header cells
            headers.forEach(header => {
                header.style.backgroundColor = color;
            });
        }
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Function to set data cell background color
    function setCellBackground(color) {
        if (!activeTable) return;
        
        const cells = activeTable.querySelectorAll('td');
        
        if (colorSelectionOnly) {
            // Get current selection
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                // Check if any data cells are in the selection
                for (let i = 0; i < cells.length; i++) {
                    const cell = cells[i];
                    if (isElementInSelection(cell, selection)) {
                        cell.style.backgroundColor = color;
                    }
                }
            }
        } else {
            // Apply to all data cells
            cells.forEach(cell => {
                cell.style.backgroundColor = color;
            });
        }
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Check if an element is within the current selection
    function isElementInSelection(element, selection) {
        for (let i = 0; i < selection.rangeCount; i++) {
            const range = selection.getRangeAt(i);
            if (range.intersectsNode(element)) {
                return true;
            }
        }
        return false;
    }
    
    // Function to apply a predefined theme to the table
    function applyTableTheme(tableColor, headerColor, cellColor) {
        if (!activeTable) return;
        
        // Apply table background
        activeTable.style.backgroundColor = tableColor;
        
        // Apply header background
        const headers = activeTable.querySelectorAll('th');
        headers.forEach(header => {
            header.style.backgroundColor = headerColor;
            
            // Adjust text color for dark backgrounds
            if (isColorDark(headerColor)) {
                header.style.color = 'white';
            } else {
                header.style.color = 'black';
            }
        });
        
        // Apply cell background
        const cells = activeTable.querySelectorAll('td');
        cells.forEach(cell => {
            cell.style.backgroundColor = cellColor;
            
            // Adjust text color for dark backgrounds
            if (isColorDark(cellColor)) {
                cell.style.color = 'white';
            } else {
                cell.style.color = 'black';
            }
        });
        
        try {
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        } catch(e) {
            console.log("Could not notify about content change:", e);
        }
    }
    
    // Helper function to determine if a color is dark
    function isColorDark(color) {
        // For hex colors
        if (color.startsWith('#')) {
            // Convert hex to RGB
            const r = parseInt(color.slice(1, 3), 16);
            const g = parseInt(color.slice(3, 5), 16);
            const b = parseInt(color.slice(5, 7), 16);
            
            // Calculate relative luminance
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            
            // Return true if color is dark
            return luminance < 0.5;
        } 
        // For named colors and rgb values
        else {
            // Create a temporary element to get computed color
            const tempElement = document.createElement('div');
            tempElement.style.color = color;
            tempElement.style.display = 'none';
            document.body.appendChild(tempElement);
            
            const computedColor = window.getComputedStyle(tempElement).color;
            document.body.removeChild(tempElement);
            
            // Parse RGB values from computed color
            const rgbMatch = computedColor.match(/^rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);
            if (rgbMatch) {
                const r = parseInt(rgbMatch[1], 10);
                const g = parseInt(rgbMatch[2], 10);
                const b = parseInt(rgbMatch[3], 10);
                
                // Calculate relative luminance
                const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
                
                // Return true if color is dark
                return luminance < 0.5;
            }
            
            // Default to false if can't determine
            return false;
        }
    }
    
    // Function to set whether colors apply to selected cells only
    function setColorSelectionOnly(selectionOnly) {
        colorSelectionOnly = selectionOnly;
    }
    
    // Function to convert a text-box-table to a freely positioned element
    function convertTextBoxToFloating(tableElement) {
        if (!tableElement) return;
        
        // Add floating class
        tableElement.classList.add('floating-table');
        
        // Make it absolutely positioned
        tableElement.style.position = 'absolute';
        
        // Calculate position
        const editorRect = document.getElementById('editor').getBoundingClientRect();
        const tableRect = tableElement.getBoundingClientRect();
        
        // Position in the center of the visible editor area
        const editorScrollTop = document.getElementById('editor').scrollTop;
        
        const topPos = (editorRect.height / 2) - (tableRect.height / 2) + editorScrollTop;
        const leftPos = (editorRect.width / 2) - (tableRect.width / 2);
        
        tableElement.style.top = \`\${Math.max(topPos, editorScrollTop)}px\`;
        tableElement.style.left = \`\${Math.max(leftPos, 0)}px\`;
        
        // Add resize handle
        enhanceTableDragHandles(tableElement);
        
        // Set z-index
        tableElement.style.zIndex = "50";
    }
    
    // Function to insert a text box (basically a 1x1 table with special styling)
    function insertTextBox() {
        // First, create and insert a 1x1 table
        const tableHTML = '<table class="editor-table text-box-table" cellspacing="0" cellpadding="5" ' +
                         'style="border: 1px solid ' + getBorderColor() + '; padding: 5px; ' +
                         'width: 200px; height: 100px;"><tr><td>Text box content</td></tr></table><p></p>';
        
        // Insert the text box at the current cursor position
        document.execCommand('insertHTML', false, tableHTML);
        
        // Find and activate the newly inserted text box
        setTimeout(() => {
            const tables = document.querySelectorAll('table.text-box-table');
            const newTextBox = tables[tables.length - 1];
            
            if (newTextBox) {
                // Add floating behavior if desired
                convertTextBoxToFloating(newTextBox);
                
                // Activate it
                activateTable(newTextBox);
                
                try {
                    window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                } catch(e) {
                    console.log("Could not notify about table click:", e);
                }
            }
        }, 10);
    }
    
    // Function to insert an image
    function insertImage(dataUrl) {
        // Create an image element with the data URL
        const imgHTML = '<img src="' + dataUrl + '" style="max-width: 100%;" />';
        
        // Insert at cursor position
        document.execCommand('insertHTML', false, imgHTML);
    }
    
    // Function to insert a link
    function insertLink(url, text) {
        // Create a link element
        const linkHTML = '<a href="' + url + '" target="_blank">' + text + '</a>';
        
        // Insert at cursor position
        document.execCommand('insertHTML', false, linkHTML);
    }
    `;
}
        """
    def table_handles_css_js(self):
        """JavaScript that defines CSS for table handles"""
        return """
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
            
            /* Floating table styles */
            .floating-table {
                position: absolute !important;
                z-index: 50;
                /* Border has been moved to inline style for conditional application */
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
                    /* Border has been moved to inline style for conditional application */
                    background-color: rgba(45, 45, 45, 0.95);
                    box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                }
                .floating-table .table-drag-handle {
                    background-color: #0078d7;
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
        """JavaScript for inserting tables"""
        return """
        // Function to insert a table at the current cursor position
        function insertTable(rows, cols, hasHeader, borderWidth, tableWidth, isFloating) {
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

    def table_activation_js(self):
        """JavaScript for table activation and deactivation"""
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

    def table_row_column_js(self):
        """JavaScript for table row and column operations"""
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

    def table_event_handlers_js(self):
        """JavaScript for table event handlers"""
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
        });"""
        
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
        
###############
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
        
        # Add separator before style options
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator3.set_margin_start(10)
        separator3.set_margin_end(10)
        toolbar.append(separator3)
        
        # NEW: Border style button with popup menu
        border_style_button = Gtk.MenuButton()
        border_style_button.set_icon_name("format-border-style-symbolic")  # Use an appropriate icon
        border_style_button.set_tooltip_text("Border Style")
        border_style_button.set_margin_start(5)
        
        # Create the border style popover
        border_style_popover = self.create_border_style_popover(win)
        border_style_button.set_popover(border_style_popover)
        toolbar.append(border_style_button)
        
        # NEW: Table/Cell Color button with popup menu
        table_color_button = Gtk.MenuButton()
        table_color_button.set_icon_name("color-select-symbolic")  # Use an appropriate icon
        table_color_button.set_tooltip_text("Table/Cell Colors")
        table_color_button.set_margin_start(5)
        
        # Create the table/cell color popover
        table_color_popover = self.create_table_color_popover(win)
        table_color_button.set_popover(table_color_popover)
        toolbar.append(table_color_button)
        
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

    # Now, let's add the methods to create the border style popover
    def create_border_style_popover(self, win):
        """Create a popover for border style options"""
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Title
        title_label = Gtk.Label(label="<b>Border Style</b>")
        title_label.set_use_markup(True)
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)
        
        # Border target selection
        target_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        target_label = Gtk.Label(label="Apply to:")
        target_label.set_halign(Gtk.Align.START)
        target_box.append(target_label)
        
        # Radio buttons for border target
        target_group = None
        table_border_radio = Gtk.CheckButton(label="Table outline only")
        table_border_radio.set_active(True)
        target_group = table_border_radio
        
        cell_border_radio = Gtk.CheckButton(label="All cells")
        cell_border_radio.set_group(target_group)
        
        target_box.append(table_border_radio)
        target_box.append(cell_border_radio)
        box.append(target_box)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        box.append(separator)
        
        # Border style options
        style_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        style_label = Gtk.Label(label="Border Style:")
        style_label.set_halign(Gtk.Align.START)
        style_box.append(style_label)
        
        # Style buttons in a grid
        style_grid = Gtk.Grid()
        style_grid.set_column_homogeneous(True)
        style_grid.set_row_spacing(8)
        style_grid.set_column_spacing(8)
        
        # Border style buttons with preview
        styles = [
            ("Solid", "solid"), 
            ("Dashed", "dashed"), 
            ("Dotted", "dotted"), 
            ("Double", "double"),
            ("None", "none")
        ]
        
        for i, (style_name, style_value) in enumerate(styles):
            style_button = Gtk.Button(label=style_name)
            style_button.set_size_request(80, 30)
            style_button.connect("clicked", lambda btn, s=style_value: self.apply_border_style(win, s, 
                                                                      table_border_radio.get_active()))
            row = i // 2
            col = i % 2
            style_grid.attach(style_button, col, row, 1, 1)
        
        style_box.append(style_grid)
        box.append(style_box)
        
        # Border width slider
        width_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        width_label = Gtk.Label(label="Border Width:")
        width_label.set_halign(Gtk.Align.START)
        width_box.append(width_label)
        
        width_slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        width_adjustment = Gtk.Adjustment(value=1, lower=0, upper=9, step_increment=1)
        width_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=width_adjustment)
        width_scale.set_digits(0)
        width_scale.set_draw_value(True)
        width_scale.set_has_origin(True)
        width_scale.set_hexpand(True)
        
        # Connect value-changed signal to apply the border width
        width_scale.connect("value-changed", lambda scale: self.apply_border_width(
            win, scale.get_value(), table_border_radio.get_active()))
        
        width_slider_box.append(width_scale)
        width_box.append(width_slider_box)
        box.append(width_box)
        
        # Border color
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        color_label = Gtk.Label(label="Border Color:")
        color_label.set_halign(Gtk.Align.START)
        color_box.append(color_label)
        
        # Color button with a color chooser dialog
        color_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse("#808080")  # Default gray color
        color_button.set_rgba(rgba)
        
        # Connect color-set signal to apply the border color
        color_button.connect("color-set", lambda btn: self.apply_border_color(
            win, btn.get_rgba(), table_border_radio.get_active()))
        
        color_box.append(color_button)
        box.append(color_box)
        
        # Transparent border checkbox
        transparent_check = Gtk.CheckButton(label="Transparent border")
        transparent_check.connect("toggled", lambda btn: self.apply_transparent_border(
            win, btn.get_active(), table_border_radio.get_active()))
        box.append(transparent_check)
        
        # Box shadow checkbox and options
        shadow_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        shadow_check = Gtk.CheckButton(label="Add shadow")
        shadow_check.connect("toggled", lambda btn: self.apply_table_shadow(win, btn.get_active()))
        shadow_box.append(shadow_check)
        
        # Shadow intensity (only shown when shadow is enabled)
        shadow_intensity_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        shadow_intensity_box.set_margin_start(24)  # Indent
        shadow_intensity_label = Gtk.Label(label="Intensity:")
        shadow_intensity_box.append(shadow_intensity_label)
        
        shadow_adjustment = Gtk.Adjustment(value=3, lower=1, upper=10, step_increment=1)
        shadow_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=shadow_adjustment)
        shadow_scale.set_digits(0)
        shadow_scale.set_draw_value(True)
        shadow_scale.set_size_request(100, -1)
        shadow_scale.set_hexpand(True)
        
        # Connect value-changed signal to apply the shadow intensity
        shadow_scale.connect("value-changed", lambda scale: self.apply_shadow_intensity(
            win, scale.get_value()))
        
        shadow_intensity_box.append(shadow_scale)
        shadow_box.append(shadow_intensity_box)
        
        # Only show shadow intensity when shadow is enabled
        shadow_check.connect("toggled", lambda btn: shadow_intensity_box.set_visible(btn.get_active()))
        shadow_intensity_box.set_visible(False)  # Initially hidden
        
        box.append(shadow_box)
        
        # Connect the radio buttons to update the border style
        table_border_radio.connect("toggled", lambda btn: self.update_border_target(win, "table") if btn.get_active() else None)
        cell_border_radio.connect("toggled", lambda btn: self.update_border_target(win, "cells") if btn.get_active() else None)
        
        popover.set_child(box)
        return popover

    # Now, let's add the methods to create the table/cell color popover
    def create_table_color_popover(self, win):
        """Create a popover for table and cell color options"""
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Title
        title_label = Gtk.Label(label="<b>Table Colors</b>")
        title_label.set_use_markup(True)
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)
        
        # Table background color
        table_bg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        table_bg_label = Gtk.Label(label="Table Background:")
        table_bg_label.set_halign(Gtk.Align.START)
        table_bg_box.append(table_bg_label)
        
        # Table background color button
        table_bg_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse("#ffffff")  # Default white color
        table_bg_button.set_rgba(rgba)
        
        # Connect color-set signal to apply the table background color
        table_bg_button.connect("color-set", lambda btn: self.apply_table_background(win, btn.get_rgba()))
        
        table_bg_box.append(table_bg_button)
        box.append(table_bg_box)
        
        # Header cell background color
        header_bg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header_bg_label = Gtk.Label(label="Header Cell Background:")
        header_bg_label.set_halign(Gtk.Align.START)
        header_bg_box.append(header_bg_label)
        
        # Header background color button
        header_bg_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse("#f0f0f0")  # Default light gray color for headers
        header_bg_button.set_rgba(rgba)
        
        # Connect color-set signal to apply the header background color
        header_bg_button.connect("color-set", lambda btn: self.apply_header_background(win, btn.get_rgba()))
        
        header_bg_box.append(header_bg_button)
        box.append(header_bg_box)
        
        # Data cell background color
        cell_bg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cell_bg_label = Gtk.Label(label="Data Cell Background:")
        cell_bg_label.set_halign(Gtk.Align.START)
        cell_bg_box.append(cell_bg_label)
        
        # Cell background color button
        cell_bg_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse("#ffffff")  # Default white color for cells
        cell_bg_button.set_rgba(rgba)
        
        # Connect color-set signal to apply the cell background color
        cell_bg_button.connect("color-set", lambda btn: self.apply_cell_background(win, btn.get_rgba()))
        
        cell_bg_box.append(cell_bg_button)
        box.append(cell_bg_box)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        box.append(separator)
        
        # Predefined themes section
        themes_label = Gtk.Label(label="<b>Quick Themes</b>")
        themes_label.set_use_markup(True)
        themes_label.set_halign(Gtk.Align.START)
        box.append(themes_label)
        
        # Grid for theme buttons
        themes_grid = Gtk.Grid()
        themes_grid.set_column_homogeneous(True)
        themes_grid.set_row_spacing(8)
        themes_grid.set_column_spacing(8)
        
        # Define themes: (name, table_bg, header_bg, cell_bg)
        themes = [
            ("Classic", "#ffffff", "#f0f0f0", "#ffffff"),
            ("Blue", "#eef5ff", "#d4e6ff", "#ffffff"),
            ("Green", "#f0fff0", "#e0ffe0", "#ffffff"),
            ("Gray", "#f5f5f5", "#e0e0e0", "#f8f8f8"),
            ("Dark", "#333333", "#444444", "#3a3a3a"),
            ("Contrast", "#ffffff", "#000000", "#ffffff"),
        ]
        
        for i, (theme_name, table_bg, header_bg, cell_bg) in enumerate(themes):
            theme_button = Gtk.Button(label=theme_name)
            theme_button.set_size_request(90, 30)
            
            # Set button background color to give a hint of the theme
            theme_css = f"""
            button {{
                background-color: {header_bg};
                color: {'white' if header_bg.startswith('#3') or header_bg.startswith('#4') or header_bg == '#000000' else 'black'};
            }}
            """
            theme_css_provider = Gtk.CssProvider()
            theme_css_provider.load_from_data(theme_css.encode())
            
            # Apply CSS to the button
            theme_button_context = theme_button.get_style_context()
            theme_button_context.add_provider(theme_css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            # Connect clicked signal to apply the theme
            theme_button.connect("clicked", lambda btn, tb=table_bg, hb=header_bg, cb=cell_bg: 
                                 self.apply_table_theme(win, tb, hb, cb))
            
            row = i // 2
            col = i % 2
            themes_grid.attach(theme_button, col, row, 1, 1)
        
        box.append(themes_grid)
        
        # Apply to selection only checkbox
        selection_check = Gtk.CheckButton(label="Apply to selected cells only")
        selection_check.connect("toggled", lambda btn: self.set_color_selection_only(win, btn.get_active()))
        box.append(selection_check)
        
        popover.set_child(box)
        return popover

    # Now, let's add the handlers for border style operations
    def apply_border_style(self, win, style, table_outline_only):
        """Apply the selected border style to the table or cells"""
        target = "table" if table_outline_only else "cells"
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setTableBorderStyle('{style}', '{target}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied {style} border style to {target}")

    def apply_border_width(self, win, width, table_outline_only):
        """Apply border width to the table or cells"""
        target = "table" if table_outline_only else "cells"
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setTableBorderWidth({int(width)}, '{target}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied border width {int(width)} to {target}")

    def apply_border_color(self, win, rgba, table_outline_only):
        """Apply border color to the table or cells"""
        # Convert Gdk.RGBA to CSS hex color
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        target = "table" if table_outline_only else "cells"
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setTableBorderColor('{hex_color}', '{target}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied border color {hex_color} to {target}")

    def apply_transparent_border(self, win, is_transparent, table_outline_only):
        """Make the border transparent or restore its color"""
        target = "table" if table_outline_only else "cells"
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setTransparentBorder({str(is_transparent).lower()}, '{target}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        status_text = f"Applied {'transparent' if is_transparent else 'colored'} border to {target}"
        win.statusbar.set_text(status_text)

    def apply_table_shadow(self, win, add_shadow):
        """Add or remove shadow from the table"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setTableShadow({str(add_shadow).lower()});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        status_text = f"{'Added' if add_shadow else 'Removed'} table shadow"
        win.statusbar.set_text(status_text)

    def apply_shadow_intensity(self, win, intensity):
        """Set the shadow intensity"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setShadowIntensity({intensity});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Set shadow intensity to {int(intensity)}")

    def update_border_target(self, win, target):
        """Update the border target (table or cells)"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            // Just a notification, actual changes will happen when applying styles
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Border styles will apply to {target}")

    # Handlers for table/cell color operations
    def apply_table_background(self, win, rgba):
        """Apply background color to the entire table"""
        # Convert Gdk.RGBA to CSS hex color
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setTableBackground('{hex_color}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied table background color {hex_color}")

    def apply_header_background(self, win, rgba):
        """Apply background color to header cells"""
        # Convert Gdk.RGBA to CSS hex color
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setHeaderBackground('{hex_color}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied header background color {hex_color}")

    def apply_cell_background(self, win, rgba):
        """Apply background color to data cells"""
        # Convert Gdk.RGBA to CSS hex color
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            setCellBackground('{hex_color}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied cell background color {hex_color}")

    def apply_table_theme(self, win, table_bg, header_bg, cell_bg):
        """Apply a predefined theme to the table"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            applyTableTheme('{table_bg}', '{header_bg}', '{cell_bg}');
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied table theme")

    def set_color_selection_only(self, win, selection_only):
        """Set whether colors apply to selected cells only"""
        js_code = f"""
        (function() {{
            setColorSelectionOnly({str(selection_only).lower()});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        status_text = "Colors will apply to " + ("selected cells only" if selection_only else "all cells")
        win.statusbar.set_text(status_text)
        
        
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
