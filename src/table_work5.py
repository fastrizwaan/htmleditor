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
        """JavaScript for insert text box and related functionality"""
        return """
        // Function to insert a text box at the current cursor position
        function insertTextBox() {
            // Create a text box as a specialized table
            let textBoxHTML = '<table class="text-box-table" style="width: 200px; height: 100px;">';
            textBoxHTML += '<tr><td style="border: none; padding: 8px;">Text box content</td></tr>';
            textBoxHTML += '</table><p></p>';
            
            // Insert the text box at the current cursor position
            document.execCommand('insertHTML', false, textBoxHTML);
            
            // Activate the newly inserted text box
            setTimeout(() => {
                const tables = document.querySelectorAll('table.text-box-table');
                const newTextBox = tables[tables.length - 1];
                if (newTextBox) {
                    activateTextBox(newTextBox);
                }
            }, 10);
        }
        
        // Function to activate a text box for editing (similar to table activation)
        function activateTextBox(textBoxElement) {
            // We can reuse the activateTable function since text boxes are specialized tables
            activateTable(textBoxElement);
        }
        """

    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return """ """

    def insert_link_js(self):
        """JavaScript for insert link and related functionality"""
        return """ """

    # Python handler for table insertion
    def on_insert_table_clicked(self, win, btn):
        """Handle table insertion button click with enhanced styling options"""
        win.statusbar.set_text("Inserting table...")
        
        # Create a dialog to configure the table
        dialog = Adw.Dialog()
        dialog.set_title("Insert Table")
        dialog.set_content_width(400)
        
        # Create scrollable content area for all the options
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)
        scrolled_window.set_max_content_height(600)
        
        # Create layout for dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Create sections with header labels
        dimensions_header = Gtk.Label()
        dimensions_header.set_markup("<b>Table Dimensions</b>")
        dimensions_header.set_halign(Gtk.Align.START)
        content_box.append(dimensions_header)
        
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
        
        # Size section
        size_header = Gtk.Label()
        size_header.set_markup("<b>Table Size</b>")
        size_header.set_halign(Gtk.Align.START)
        size_header.set_margin_top(16)
        content_box.append(size_header)
        
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
        
        # Border section
        border_header = Gtk.Label()
        border_header.set_markup("<b>Border Options</b>")
        border_header.set_halign(Gtk.Align.START)
        border_header.set_margin_top(16)
        content_box.append(border_header)
        
        # Border width
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
        
        # Border style
        style_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        style_label = Gtk.Label(label="Border style:")
        style_label.set_halign(Gtk.Align.START)
        style_label.set_hexpand(True)
        
        style_combo = Gtk.DropDown()
        style_options = Gtk.StringList()
        style_options.append("Solid")
        style_options.append("Dotted")
        style_options.append("Dashed")
        style_options.append("Double")
        style_combo.set_model(style_options)
        style_combo.set_selected(0)  # Default to solid
        
        style_box.append(style_label)
        style_box.append(style_combo)
        content_box.append(style_box)
        
        # Border color
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_label = Gtk.Label(label="Border color:")
        color_label.set_halign(Gtk.Align.START)
        color_label.set_hexpand(True)
        
        # Create a color button
        color_button = Gtk.ColorButton()
        # Set default color to light gray
        color_button.set_rgba(Gdk.RGBA(0.8, 0.8, 0.8, 1.0))
        
        color_box.append(color_label)
        color_box.append(color_button)
        content_box.append(color_box)
        
        # Add shadow effect checkbox
        shadow_check = Gtk.CheckButton(label="Add drop shadow effect")
        shadow_check.set_active(False)
        content_box.append(shadow_check)
        
        # Position section
        position_header = Gtk.Label()
        position_header.set_markup("<b>Table Position</b>")
        position_header.set_halign(Gtk.Align.START)
        position_header.set_margin_top(16)
        content_box.append(position_header)
        
        # Position options
        position_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        position_label = Gtk.Label(label="Initial position:")
        position_label.set_halign(Gtk.Align.START)
        position_label.set_hexpand(True)
        
        position_combo = Gtk.DropDown()
        position_options = Gtk.StringList()
        position_options.append("Default")
        position_options.append("Left")
        position_options.append("Center")
        position_options.append("Right")
        position_options.append("Floating")
        position_combo.set_model(position_options)
        position_combo.set_selected(0)  # Default
        
        position_box.append(position_label)
        position_box.append(position_combo)
        content_box.append(position_box)
        
        # Z-index for floating tables
        z_index_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        z_index_label = Gtk.Label(label="Z-index (layer):")
        z_index_label.set_halign(Gtk.Align.START)
        z_index_label.set_hexpand(True)
        
        z_index_adjustment = Gtk.Adjustment(value=1, lower=0, upper=10, step_increment=1)
        z_index_spin = Gtk.SpinButton()
        z_index_spin.set_adjustment(z_index_adjustment)
        z_index_spin.set_sensitive(False)  # Only enable when floating is selected
        
        # Connect position dropdown to enable/disable z-index
        position_combo.connect("notify::selected", lambda w, p: z_index_spin.set_sensitive(w.get_selected() == 4))
        
        z_index_box.append(z_index_label)
        z_index_box.append(z_index_spin)
        content_box.append(z_index_box)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
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
            style_options.get_string(style_combo.get_selected()),
            color_button.get_rgba(),
            shadow_check.get_active(),
            position_options.get_string(position_combo.get_selected()),
            z_index_spin.get_value_as_int()
        ))
        
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        # Add content to scrolled window
        scrolled_window.set_child(content_box)
        
        # Set dialog content and present
        dialog.set_child(scrolled_window)
        dialog.present(win)

    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option, 
                                  border_style, border_color, add_shadow, position, z_index):
        """Handle response from the enhanced table dialog"""
        dialog.close()
        
        # Prepare the width value
        width_value = "auto"
        if width_option != "Auto":
            width_value = width_option
        
        # Convert border style to CSS
        border_style_value = border_style.lower()
        
        # Convert color to hex format
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(border_color.red * 255),
            int(border_color.green * 255),
            int(border_color.blue * 255)
        )
        
        # Prepare shadow CSS if needed
        shadow_css = ""
        if add_shadow:
            shadow_css = "box-shadow: 2px 2px 4px rgba(0,0,0,0.2);"
        
        # Prepare position class
        position_class = "no-wrap"  # Default positioning
        if position == "Left":
            position_class = "left-align"
        elif position == "Center":
            position_class = "center-align"
        elif position == "Right":
            position_class = "right-align"
        elif position == "Floating":
            position_class = "float-mode"
        
        # Z-index for floating tables
        z_index_css = ""
        if position == "Floating":
            z_index_css = f"z-index: {z_index};"
        
        # Execute JavaScript to insert the table with enhanced styling
        js_code = f"""
        (function() {{
            // Create a table with the specified styling
            let tableHTML = '<table class="{position_class}" style="border-collapse: collapse; width: {width_value}; {shadow_css} {z_index_css}">';
            
            // Create header row if requested
            if ({str(has_header).lower()}) {{
                tableHTML += '<tr>';
                for (let j = 0; j < {cols}; j++) {{
                    tableHTML += '<th style="border: {border_width}px {border_style_value} {color_hex}; padding: 5px; background-color: #f0f0f0;">Header ' + (j+1) + '</th>';
                }}
                tableHTML += '</tr>';
            }}
            
            // Create regular rows and cells
            for (let i = 0; i < {rows - (1 if has_header else 0)}; i++) {{
                tableHTML += '<tr>';
                for (let j = 0; j < {cols}; j++) {{
                    tableHTML += '<td style="border: {border_width}px {border_style_value} {color_hex}; padding: 5px; min-width: 30px;">Cell</td>';
                }}
                tableHTML += '</tr>';
            }}
            
            tableHTML += '</table><p></p>';
            
            // Insert the table at the current cursor position
            document.execCommand('insertHTML', false, tableHTML);
            
            // Activate the newly inserted table
            setTimeout(() => {{
                const tables = document.querySelectorAll('table');
                const newTable = tables[tables.length - 1];
                if (newTable) {{
                    activateTable(newTable);
                    try {{
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    }} catch(e) {{
                        console.log("Could not notify about table click:", e);
                    }}
                }}
            }}, 10);
            
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

        # Floating option (NEW)
        float_button = Gtk.Button(icon_name="object-float-symbolic")
        float_button.set_tooltip_text("Float (freely movable)")
        float_button.connect("clicked", lambda btn: self.on_table_float(win))
        align_group.append(float_button)
            
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
        
    def on_table_float(self, win):
        """Make table floating and freely movable"""
        js_code = "setTableAlignment('float-mode');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table set to floating mode")
        
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
        
        # Using triple quotes to ensure CSS is properly handled as a string
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
                    position: relative;
                    resize: both;
                    overflow: auto;
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
                /* Floating table style */
                table.float-mode {{
                    position: absolute;
                    z-index: 100;
                    border: 1px solid #ccc;
                    margin: 0;
                    float: none;
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
                .table-drag-handle {{
                    position: absolute;
                    top: -16px;
                    left: -1px;
                    width: 16px;
                    height: 16px;
                    background-color: #4e9eff;
                    border-radius: 2px;
                    cursor: ns-resize;
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
                }}
                .table-handle {{
                    position: absolute;
                    bottom: -10px;
                    right: -10px;
                    width: 16px;
                    height: 16px;
                    background-color: #4e9eff;
                    border-radius: 8px;
                    cursor: nwse-resize;
                    z-index: 1000;
                    pointer-events: all;
                    user-select: none;
                    -webkit-user-select: none;
                    -moz-user-select: none;
                    -ms-user-select: none;
                }}
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
                    .table-drag-handle, .table-handle {{
                        background-color: #0078d7;
                    }}
                    table.text-box-table {{
                        border-color: #444 !important;
                        background-color: #2d2d2d;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    }}
                    table.float-mode {{
                        border-color: #444;
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
#
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return """
            // Function to insert a table at the current cursor position
            function insertTable(rows, cols, hasHeader, borderWidth, tableWidth) {
                // Create table HTML
                let tableHTML = '<table border="' + borderWidth + '" cellspacing="0" cellpadding="5" ';
                
                // Add class and style attributes
                tableHTML += 'class="no-wrap" style="border-collapse: collapse; width: ' + tableWidth + ';">';
                
                // Create header row if requested
                if (hasHeader) {
                    tableHTML += '<tr>';
                    for (let j = 0; j < cols; j++) {
                        tableHTML += '<th style="border: ' + borderWidth + 'px solid #ccc; padding: 5px; background-color: #f0f0f0;">Header ' + (j+1) + '</th>';
                    }
                    tableHTML += '</tr>';
                    rows--; // Reduce regular rows by one since we added a header
                }
                
                // Create regular rows and cells
                for (let i = 0; i < rows; i++) {
                    tableHTML += '<tr>';
                    for (let j = 0; j < cols; j++) {
                        tableHTML += '<td style="border: ' + borderWidth + 'px solid #ccc; padding: 5px; min-width: 30px;">Cell</td>';
                    }
                    tableHTML += '</tr>';
                }
                
                tableHTML += '</table><p></p>';
                
                // Insert the table at the current cursor position
                document.execCommand('insertHTML', false, tableHTML);
                
                // Activate the newly inserted table
                setTimeout(() => {
                    const tables = document.querySelectorAll('table');
                    const newTable = tables[tables.length - 1];
                    if (newTable) {
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
            var isFloatingDrag = false;
            var dragStartX = 0;
            var dragStartY = 0;
            var tableStartX = 0;
            var tableStartY = 0;
            var floatDragStartX = 0;
            var floatDragStartY = 0;
            var tablePosX = 0;
            var tablePosY = 0;
            
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
                activeTable = tableElement;
                
                // Only clear margins if not in float mode
                if (!tableElement.classList.contains('float-mode')) {
                    tableElement.style.marginLeft = '';
                    tableElement.style.marginTop = '';
                }
                
                // Determine current table alignment class
                const currentClasses = tableElement.className;
                const alignmentClasses = ['left-align', 'right-align', 'center-align', 'no-wrap', 'float-mode'];
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
                    resizeHandle.style.userSelect = 'none';
                    resizeHandle.style.webkitUserSelect = 'none';
                    resizeHandle.style.MozUserSelect = 'none';
                    resizeHandle.style.msUserSelect = 'none';
                    
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
                    
                    if (currentAlignment === 'float-mode') {
                        dragHandle.innerHTML = '✥';
                        dragHandle.title = 'Drag to freely position table';
                    } else {
                        dragHandle.innerHTML = '↕';
                        dragHandle.title = 'Drag to reposition table between paragraphs';
                    }
                    
                    // Make handle non-selectable and prevent focus
                    dragHandle.setAttribute('contenteditable', 'false');
                    dragHandle.setAttribute('unselectable', 'on');
                    dragHandle.setAttribute('tabindex', '-1');
                    dragHandle.style.userSelect = 'none';
                    dragHandle.style.webkitUserSelect = 'none';
                    dragHandle.style.MozUserSelect = 'none';
                    dragHandle.style.msUserSelect = 'none';
                    
                    // Add event listener to prevent propagation of mousedown events
                    dragHandle.addEventListener('mousedown', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        if (tableElement.classList.contains('float-mode')) {
                            startFloatDrag(e, tableElement);
                        } else {
                            startTableDrag(e, tableElement);
                        }
                    }, true);
                    
                    tableElement.appendChild(dragHandle);
                } else {
                    // Update existing handle based on mode
                    const dragHandle = tableElement.querySelector('.table-drag-handle');
                    
                    if (currentAlignment === 'float-mode') {
                        dragHandle.innerHTML = '✥';
                        dragHandle.title = 'Drag to freely position table';
                        
                        // Clear existing listeners by cloning and replacing
                        const newDragHandle = dragHandle.cloneNode(true);
                        dragHandle.parentNode.replaceChild(newDragHandle, dragHandle);
                        
                        // Add event listener for float drag
                        newDragHandle.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            startFloatDrag(e, tableElement);
                        }, true);
                    } else {
                        dragHandle.innerHTML = '↕';
                        dragHandle.title = 'Drag to reposition table between paragraphs';
                        
                        // Clear existing listeners by cloning and replacing
                        const newDragHandle = dragHandle.cloneNode(true);
                        dragHandle.parentNode.replaceChild(newDragHandle, dragHandle);
                        
                        // Add event listener for regular drag
                        newDragHandle.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            startTableDrag(e, tableElement);
                        }, true);
                    }
                }
            }
            
            // Function to deactivate all tables
            function deactivateAllTables() {
                const tables = document.querySelectorAll('table');
                
                tables.forEach(table => {
                    const resizeHandle = table.querySelector('.table-handle');
                    if (resizeHandle) resizeHandle.remove();
                    
                    const dragHandle = table.querySelector('.table-drag-handle');
                    if (dragHandle) dragHandle.remove();
                });
                
                if (activeTable) {
                    activeTable = null;
                    try {
                        window.webkit.messageHandlers.tablesDeactivated.postMessage('tables-deactivated');
                    } catch(e) {
                        console.log("Could not notify about table deactivation:", e);
                    }
                }
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
            
            // Function to start floating drag
            function startFloatDrag(e, tableElement) {
                e.preventDefault();
                if (!tableElement) return;
                
                isFloatingDrag = true;
                activeTable = tableElement;
                
                floatDragStartX = e.clientX;
                floatDragStartY = e.clientY;
                
                // Get current table position
                tablePosX = parseInt(tableElement.style.left) || 0;
                tablePosY = parseInt(tableElement.style.top) || 0;
                
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
            
            // Function to move floating table
            function moveFloatingTable(e) {
                if (!isFloatingDrag || !activeTable) return;
                
                const deltaX = e.clientX - floatDragStartX;
                const deltaY = e.clientY - floatDragStartY;
                
                // Update table position
                activeTable.style.left = (tablePosX + deltaX) + 'px';
                activeTable.style.top = (tablePosY + deltaY) + 'px';
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
                const deltaY = e.clientY - dragStartY;
                
                activeTable.style.width = (tableStartX + deltaX) + 'px';
                activeTable.style.height = (tableStartY + deltaY) + 'px';
            }
            
            // Function to add a row to the table
            function addTableRow(tableElement, position) {
                if (!tableElement && activeTable) {
                    tableElement = activeTable;
                }
                
                if (!tableElement) return;
                
                const rows = tableElement.rows;
                if (rows.length > 0) {
                    // If position is provided, use it, otherwise append at the end
                    const rowIndex = (position !== undefined) ? position : rows.length;
                    const newRow = tableElement.insertRow(rowIndex);
                    
                    for (let i = 0; i < rows[0].cells.length; i++) {
                        const cell = newRow.insertCell(i);
                        cell.innerHTML = ' ';
                        // Copy border style from other cells
                        if (rows[0].cells[i].style.border) {
                            cell.style.border = rows[0].cells[i].style.border;
                        }
                        // Copy padding style from other cells
                        if (rows[0].cells[i].style.padding) {
                            cell.style.padding = rows[0].cells[i].style.padding;
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
                
                const rows = tableElement.rows;
                for (let i = 0; i < rows.length; i++) {
                    // If position is provided, use it, otherwise append at the end
                    const cellIndex = (position !== undefined) ? position : rows[i].cells.length;
                    const cell = rows[i].insertCell(cellIndex);
                    cell.innerHTML = ' ';
                    
                    // Copy styles from adjacent cells if available
                    if (rows[i].cells.length > 1) {
                        const refCell = cellIndex > 0 ? 
                                        rows[i].cells[cellIndex - 1] : 
                                        rows[i].cells[cellIndex + 1];
                                        
                        if (refCell) {
                            if (refCell.style.border) {
                                cell.style.border = refCell.style.border;
                            }
                            if (refCell.style.padding) {
                                cell.style.padding = refCell.style.padding;
                            }
                            // If it's a header cell, make new cell a header too
                            if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                                const headerCell = document.createElement('th');
                                headerCell.innerHTML = cell.innerHTML;
                                headerCell.style.cssText = cell.style.cssText;
                                if (refCell.style.backgroundColor) {
                                    headerCell.style.backgroundColor = refCell.style.backgroundColor;
                                }
                                cell.parentNode.replaceChild(headerCell, cell);
                            }
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
                activeTable.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap', 'float-mode');
                
                // Add the requested alignment class
                activeTable.classList.add(alignClass);
                
                // Set width based on alignment mode
                if (alignClass === 'no-wrap') {
                    activeTable.style.width = '100%';
                } else {
                    activeTable.style.width = 'auto';
                }
                
                // For floating tables, enable positioning
                if (alignClass === 'float-mode') {
                    // Set positioning styles
                    activeTable.style.position = 'absolute';
                    
                    // If the table doesn't have a position yet, set a default position
                    if (!activeTable.style.top && !activeTable.style.left) {
                        const editorRect = document.getElementById('editor').getBoundingClientRect();
                        activeTable.style.top = '100px';
                        activeTable.style.left = '100px';
                    }
                    
                    // Update the drag handle for floating mode
                    const dragHandle = activeTable.querySelector('.table-drag-handle');
                    if (dragHandle) {
                        dragHandle.innerHTML = '✥';
                        dragHandle.title = 'Drag to freely position table';
                        
                        // Clear existing listeners by cloning and replacing
                        const newDragHandle = dragHandle.cloneNode(true);
                        dragHandle.parentNode.replaceChild(newDragHandle, dragHandle);
                        
                        // Add event listener for float drag
                        newDragHandle.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            startFloatDrag(e, activeTable);
                        }, true);
                    }
                } else {
                    // Remove positioning for non-floating tables
                    activeTable.style.position = '';
                    activeTable.style.top = '';
                    activeTable.style.left = '';
                    
                    // Update the drag handle for normal mode
                    const dragHandle = activeTable.querySelector('.table-drag-handle');
                    if (dragHandle) {
                        dragHandle.innerHTML = '↕';
                        dragHandle.title = 'Drag to reposition table between paragraphs';
                        
                        // Clear existing listeners by cloning and replacing
                        const newDragHandle = dragHandle.cloneNode(true);
                        dragHandle.parentNode.replaceChild(newDragHandle, dragHandle);
                        
                        // Add event listener for regular drag
                        newDragHandle.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            startTableDrag(e, activeTable);
                        }, true);
                    }
                }
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            }
            
            // Add event handlers for table interactions
            document.addEventListener('DOMContentLoaded', function() {
                const editor = document.getElementById('editor');
                
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
                            const parentTable = findParentTable(e.target);
                            if (parentTable && parentTable.classList.contains('float-mode')) {
                                startFloatDrag(e, parentTable);
                            } else {
                                startTableDrag(e, findParentTable(e.target));
                            }
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
                    if (isFloatingDrag && activeTable) {
                        moveFloatingTable(e);
                    }
                });
                
                // Handle mouse up events
                document.addEventListener('mouseup', function() {
                    if (isDragging || isResizing || isFloatingDrag) {
                        isDragging = false;
                        isResizing = false;
                        isFloatingDrag = false;
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
                    
                    if (!tableElement && activeTable) {
                        deactivateAllTables();
                    } else if (tableElement && tableElement !== activeTable) {
                        deactivateAllTables();
                        activateTable(tableElement);
                        try {
                            window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                        } catch(e) {
                            console.log("Could not notify about table click:", e);
                        }
                    }
                });
            });
            """
#####################
    def create_table_toolbar(self, win):
        """Create a toolbar for table editing with border styling options"""
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
        
        # Create a border styling button with popover menu
        border_button = Gtk.MenuButton()
        border_button.set_icon_name("format-border-set-symbolic")
        border_button.set_tooltip_text("Border styles")
        
        # Create popover for border options
        border_popover = Gtk.Popover()
        border_popover.set_autohide(True)
        
        # Create box for border popover content
        border_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        border_box.set_margin_start(12)
        border_box.set_margin_end(12)
        border_box.set_margin_top(12)
        border_box.set_margin_bottom(12)
        
        # Border style section
        style_label = Gtk.Label(label="Border Style")
        style_label.set_halign(Gtk.Align.START)
        style_label.add_css_class("heading")
        border_box.append(style_label)
        
        # Border style buttons
        style_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        style_group.add_css_class("linked")
        
        # Solid border
        solid_btn = Gtk.Button(label="Solid")
        solid_btn.connect("clicked", lambda btn: self.set_table_border_style(win, "solid"))
        style_group.append(solid_btn)
        
        # Dashed border
        dashed_btn = Gtk.Button(label="Dashed")
        dashed_btn.connect("clicked", lambda btn: self.set_table_border_style(win, "dashed"))
        style_group.append(dashed_btn)
        
        # Dotted border
        dotted_btn = Gtk.Button(label="Dotted")
        dotted_btn.connect("clicked", lambda btn: self.set_table_border_style(win, "dotted"))
        style_group.append(dotted_btn)
        
        # Double border
        double_btn = Gtk.Button(label="Double")
        double_btn.connect("clicked", lambda btn: self.set_table_border_style(win, "double"))
        style_group.append(double_btn)
        
        border_box.append(style_group)
        
        # Border width section
        width_label = Gtk.Label(label="Border Width")
        width_label.set_halign(Gtk.Align.START)
        width_label.add_css_class("heading")
        width_label.set_margin_top(8)
        border_box.append(width_label)
        
        # Border width slider
        width_adjustment = Gtk.Adjustment(value=1, lower=0, upper=5, step_increment=1)
        width_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=width_adjustment)
        width_scale.set_digits(0)
        width_scale.set_draw_value(True)
        width_scale.set_value_pos(Gtk.PositionType.RIGHT)
        width_scale.connect("value-changed", lambda scale: self.set_table_border_width(win, scale.get_value()))
        border_box.append(width_scale)
        
        # Border color section
        color_label = Gtk.Label(label="Border Color")
        color_label.set_halign(Gtk.Align.START)
        color_label.add_css_class("heading")
        color_label.set_margin_top(8)
        border_box.append(color_label)
        
        # Color picker button
        color_button = Gtk.ColorButton()
        color_button.set_rgba(Gdk.RGBA(0.8, 0.8, 0.8, 1.0))  # Default to light gray
        color_button.set_halign(Gtk.Align.START)
        color_button.connect("color-set", lambda btn: self.set_table_border_color(win, btn.get_rgba()))
        border_box.append(color_button)
        
        # Shadow effect
        shadow_check = Gtk.CheckButton(label="Add drop shadow")
        shadow_check.set_margin_top(8)
        shadow_check.connect("toggled", lambda btn: self.toggle_table_shadow(win, btn.get_active()))
        border_box.append(shadow_check)
        
        # Attach the box to the popover
        border_popover.set_child(border_box)
        
        # Connect the popover to the button
        border_button.set_popover(border_popover)
        
        # Add border button to toolbar
        toolbar.append(border_button)

        # Create a cell fill color button with popover menu
        fill_button = Gtk.MenuButton()
        fill_button.set_icon_name("color-select-symbolic")  # Use color selection icon
        fill_button.set_tooltip_text("Cell fill colors")

        # Create popover for fill color options
        fill_popover = Gtk.Popover()
        fill_popover.set_autohide(True)

        # Create box for fill color popover content
        fill_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        fill_box.set_margin_start(12)
        fill_box.set_margin_end(12)
        fill_box.set_margin_top(12)
        fill_box.set_margin_bottom(12)

        # Header background section
        header_label = Gtk.Label(label="Header Background")
        header_label.set_halign(Gtk.Align.START)
        header_label.add_css_class("heading")
        fill_box.append(header_label)

        # Header color button
        header_color_button = Gtk.ColorButton()
        # Set default header background color (light gray)
        header_color_button.set_rgba(Gdk.RGBA(0.94, 0.94, 0.94, 1.0))  # #f0f0f0
        header_color_button.set_halign(Gtk.Align.START)
        header_color_button.connect("color-set", lambda btn: self.set_header_background_color(win, btn.get_rgba()))
        fill_box.append(header_color_button)

        # Cell background section
        cell_label = Gtk.Label(label="Cell Background")
        cell_label.set_halign(Gtk.Align.START)
        cell_label.add_css_class("heading")
        cell_label.set_margin_top(8)
        fill_box.append(cell_label)

        # Cell color button
        cell_color_button = Gtk.ColorButton()
        # Set default cell background color (white)
        cell_color_button.set_rgba(Gdk.RGBA(1.0, 1.0, 1.0, 1.0))  # white
        cell_color_button.set_halign(Gtk.Align.START)
        cell_color_button.connect("color-set", lambda btn: self.set_cell_background_color(win, btn.get_rgba()))
        fill_box.append(cell_color_button)

        # Alternating rows checkbox
        alternating_check = Gtk.CheckButton(label="Alternating row colors")
        alternating_check.set_margin_top(8)
        alternating_check.connect("toggled", lambda btn: self.toggle_alternating_rows(win, btn.get_active()))
        fill_box.append(alternating_check)

        # Preset color schemes section
        presets_label = Gtk.Label(label="Preset Color Schemes")
        presets_label.set_halign(Gtk.Align.START)
        presets_label.add_css_class("heading")
        presets_label.set_margin_top(12)
        fill_box.append(presets_label)

        # Create a grid for preset color schemes
        presets_grid = Gtk.Grid()
        presets_grid.set_column_spacing(4)
        presets_grid.set_row_spacing(4)

        # Default preset
        default_btn = Gtk.Button(label="Default")
        default_btn.connect("clicked", lambda btn: self.apply_color_preset(win, "default"))
        presets_grid.attach(default_btn, 0, 0, 1, 1)

        # Blue preset
        blue_btn = Gtk.Button(label="Blue")
        blue_btn.connect("clicked", lambda btn: self.apply_color_preset(win, "blue"))
        presets_grid.attach(blue_btn, 1, 0, 1, 1)

        # Green preset
        green_btn = Gtk.Button(label="Green")
        green_btn.connect("clicked", lambda btn: self.apply_color_preset(win, "green"))
        presets_grid.attach(green_btn, 0, 1, 1, 1)

        # Warm preset
        warm_btn = Gtk.Button(label="Warm")
        warm_btn.connect("clicked", lambda btn: self.apply_color_preset(win, "warm"))
        presets_grid.attach(warm_btn, 1, 1, 1, 1)

        fill_box.append(presets_grid)

        # Apply to selected cells only
        selection_check = Gtk.CheckButton(label="Apply to selected cells only")
        selection_check.set_margin_top(12)
        # Store checkbox in window properties to access its state in coloring methods
        win.color_selection_only = selection_check
        selection_check.connect("toggled", lambda btn: win.statusbar.set_text(f"{'Selected cells' if btn.get_active() else 'All cells'} will be colored"))
        fill_box.append(selection_check)

        # Attach the box to the popover
        fill_popover.set_child(fill_box)

        # Connect the popover to the button
        fill_button.set_popover(fill_popover)

        # Add fill button to toolbar
        toolbar.append(fill_button)
        
        # Alignment options
        align_label = Gtk.Label(label="Align:")
        align_label.set_margin_start(10)
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

        # Floating option
        float_button = Gtk.Button(icon_name="object-float-symbolic")
        float_button.set_tooltip_text("Float (freely movable)")
        float_button.connect("clicked", lambda btn: self.on_table_float(win))
        align_group.append(float_button)
            
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

    # New methods for border styling
# Add these methods to your HTMLEditorApp class

    def set_header_background_color(self, win, rgba):
        """Set the background color for table headers"""
        # Convert RGBA to hex
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        # Check if we're only applying to selected cells
        selection_only = hasattr(win, 'color_selection_only') and win.color_selection_only.get_active()
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            let selection = window.getSelection();
            let selectedHeaders = [];
            
            // If selection-only mode is active, try to find selected header cells
            if ({str(selection_only).lower()} && selection.rangeCount > 0) {{
                // Get all selected nodes
                const range = selection.getRangeAt(0);
                
                // Handle the case where a single cell is selected
                let startCell = range.startContainer;
                while (startCell && startCell.tagName !== 'TH' && startCell !== activeTable) {{
                    startCell = startCell.parentNode;
                }}
                
                if (startCell && startCell.tagName === 'TH') {{
                    selectedHeaders.push(startCell);
                }} else {{
                    // Try to get all TH elements within the selection
                    const headerElements = activeTable.querySelectorAll('th');
                    for (let header of headerElements) {{
                        if (range.intersectsNode(header)) {{
                            selectedHeaders.push(header);
                        }}
                    }}
                }}
            }}
            
            // If we're in selection-only mode and have selected headers, apply only to those
            if ({str(selection_only).lower()} && selectedHeaders.length > 0) {{
                for (let header of selectedHeaders) {{
                    header.style.backgroundColor = '{color_hex}';
                }}
            }} else {{
                // Otherwise apply to all headers
                const headers = activeTable.querySelectorAll('th');
                for (let header of headers) {{
                    header.style.backgroundColor = '{color_hex}';
                }}
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about header color change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Header background color set to {color_hex}")

    def set_cell_background_color(self, win, rgba):
        """Set the background color for regular table cells"""
        # Convert RGBA to hex
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        # Check if we're only applying to selected cells
        selection_only = hasattr(win, 'color_selection_only') and win.color_selection_only.get_active()
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            let selection = window.getSelection();
            let selectedCells = [];
            
            // If selection-only mode is active, try to find selected cells
            if ({str(selection_only).lower()} && selection.rangeCount > 0) {{
                // Get all selected nodes
                const range = selection.getRangeAt(0);
                
                // Handle the case where a single cell is selected
                let startCell = range.startContainer;
                while (startCell && startCell.tagName !== 'TD' && startCell !== activeTable) {{
                    startCell = startCell.parentNode;
                }}
                
                if (startCell && startCell.tagName === 'TD') {{
                    selectedCells.push(startCell);
                }} else {{
                    // Try to get all TD elements within the selection
                    const cellElements = activeTable.querySelectorAll('td');
                    for (let cell of cellElements) {{
                        if (range.intersectsNode(cell)) {{
                            selectedCells.push(cell);
                        }}
                    }}
                }}
            }}
            
            // If we're in selection-only mode and have selected cells, apply only to those
            if ({str(selection_only).lower()} && selectedCells.length > 0) {{
                for (let cell of selectedCells) {{
                    cell.style.backgroundColor = '{color_hex}';
                }}
            }} else {{
                // Otherwise apply to all cells
                const cells = activeTable.querySelectorAll('td');
                for (let cell of cells) {{
                    cell.style.backgroundColor = '{color_hex}';
                    // Remove any existing zebra-stripe class
                    cell.classList.remove('zebra-stripe');
                }}
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about cell color change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Cell background color set to {color_hex}")

    def toggle_alternating_rows(self, win, enable):
        """Toggle alternating row colors (zebra striping)"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            // First remove any existing zebra striping
            const allCells = activeTable.querySelectorAll('td');
            for (let cell of allCells) {{
                cell.classList.remove('zebra-stripe');
            }}
            
            if ({str(enable).lower()}) {{
                // Apply zebra striping
                const rows = activeTable.rows;
                for (let i = 0; i < rows.length; i++) {{
                    if (i % 2 === 1) {{  // Apply to odd rows (0-indexed)
                        const cells = rows[i].cells;
                        for (let j = 0; j < cells.length; j++) {{
                            if (cells[j].tagName === 'TD') {{
                                // Get computed background color and darken it slightly
                                const bgColor = window.getComputedStyle(cells[j]).backgroundColor;
                                
                                // Handle the case where backgroundColor might be 'transparent'
                                if (bgColor === 'transparent' || bgColor === 'rgba(0, 0, 0, 0)') {{
                                    cells[j].style.backgroundColor = '#f2f2f2'; // Light gray default
                                }} else {{
                                    cells[j].style.backgroundColor = getDarkerColor(bgColor, 0.9);
                                }}
                                
                                cells[j].classList.add('zebra-stripe');
                            }}
                        }}
                    }}
                }}
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about zebra striping change:", e);
            }}
            
            return true;
            
            // Helper function to darken a color
            function getDarkerColor(colorStr, factor) {{
                // Parse RGB or RGBA string
                const rgbMatch = colorStr.match(/rgba?\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*(?:,\\s*([\\d.]+)\\s*)?\\)/i);
                if (!rgbMatch) return colorStr;
                
                const r = Math.floor(parseInt(rgbMatch[1], 10) * factor);
                const g = Math.floor(parseInt(rgbMatch[2], 10) * factor);
                const b = Math.floor(parseInt(rgbMatch[3], 10) * factor);
                
                return rgbMatch[4] ? `rgba(${{r}},${{g}},${{b}},${{rgbMatch[4]}})` : `rgb(${{r}},${{g}},${{b}})`;
            }}
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Alternating row colors {'enabled' if enable else 'disabled'}")

    def apply_color_preset(self, win, preset):
        """Apply a predefined color scheme to the table"""
        # Define the preset color schemes
        presets = {
            "default": {
                "header": "#f0f0f0",  # Light gray
                "cell": "#ffffff"     # White
            },
            "blue": {
                "header": "#d4e6f1",  # Light blue
                "cell": "#eaf2f8"     # Very light blue
            },
            "green": {
                "header": "#d4efdf",  # Light green 
                "cell": "#eafaf1"     # Very light green
            },
            "warm": {
                "header": "#f9e79f",  # Light yellow
                "cell": "#fcf3cf"     # Very light yellow
            }
        }
        
        if preset not in presets:
            preset = "default"
        
        # Get the preset colors
        header_color = presets[preset]["header"]
        cell_color = presets[preset]["cell"]
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            // Apply header background color
            const headers = activeTable.querySelectorAll('th');
            for (let header of headers) {{
                header.style.backgroundColor = '{header_color}';
            }}
            
            // Apply cell background color
            const cells = activeTable.querySelectorAll('td');
            for (let cell of cells) {{
                cell.style.backgroundColor = '{cell_color}';
                // Remove any zebra striping
                cell.classList.remove('zebra-stripe');
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about color preset change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied '{preset}' color scheme to table")
    def set_table_border_style(self, win, style):
        """Set the border style for the active table"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            const cells = activeTable.querySelectorAll('td, th');
            for (let cell of cells) {{
                // Keep the current border width and color, just change the style
                const currentStyle = window.getComputedStyle(cell);
                const borderWidth = currentStyle.borderWidth || '1px';
                const borderColor = currentStyle.borderColor || '#cccccc';
                
                cell.style.borderStyle = '{style}';
                cell.style.borderWidth = borderWidth;
                cell.style.borderColor = borderColor;
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about border style change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Table border style set to {style}")

    def set_table_border_width(self, win, width):
        """Set the border width for the active table"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            const cells = activeTable.querySelectorAll('td, th');
            for (let cell of cells) {{
                // Keep the current border style and color, just change the width
                const currentStyle = window.getComputedStyle(cell);
                const borderStyle = currentStyle.borderStyle || 'solid';
                const borderColor = currentStyle.borderColor || '#cccccc';
                
                cell.style.borderStyle = borderStyle;
                cell.style.borderWidth = '{int(width)}px';
                cell.style.borderColor = borderColor;
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about border width change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Table border width set to {int(width)}px")

    def set_table_border_color(self, win, rgba):
        """Set the border color for the active table"""
        # Convert RGBA to hex
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            const cells = activeTable.querySelectorAll('td, th');
            for (let cell of cells) {{
                // Keep the current border style and width, just change the color
                const currentStyle = window.getComputedStyle(cell);
                const borderStyle = currentStyle.borderStyle || 'solid';
                const borderWidth = currentStyle.borderWidth || '1px';
                
                cell.style.borderStyle = borderStyle;
                cell.style.borderWidth = borderWidth;
                cell.style.borderColor = '{color_hex}';
            }}
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about border color change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Table border color set to {color_hex}")

    def toggle_table_shadow(self, win, enable):
        """Toggle drop shadow effect for the active table"""
        shadow_value = "2px 2px 4px rgba(0,0,0,0.2)" if enable else "none"
        
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            activeTable.style.boxShadow = '{shadow_value}';
            
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about shadow change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Table shadow {('enabled' if enable else 'disabled')}")
            
    def get_editor_html(self, content=""):
        """Return HTML for the editor with improved table and text box styles"""
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        # Using triple quotes to ensure CSS is properly handled as a string
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
                
                /* Table styles with normalized appearance */
                table {{
                    border-collapse: collapse;
                    margin: 10px 0;
                    position: relative;
                    resize: both;
                    overflow: visible;
                    min-width: 30px;
                    min-height: 30px;
                    border-spacing: 0;
                    /* Remove any transform that might cause rendering issues */
                    transform: none;
                }}
                
                /* Make all cells have identical styling - no special cases */
                table td, table th {{
                    border: 1px solid #ccc;
                    border-style: solid;
                    padding: 5px;
                    min-width: 30px;
                    position: relative;
                    box-sizing: border-box;
                    /* Remove any outlines that might appear on selection */
                    outline: none;
                }}
                
                /* Header cells */
                table th {{
                    background-color: #f0f0f0;
                }}
                
                /* Fix for selection outlines */
                table.selected, table.selected td, table.selected th,
                table td.selected, table th.selected {{
                    outline: none !important;
                    border-style: solid !important;
                }}
                
                /* Remove any focus or selection indicators that cause dashed borders */
                table:focus, table:focus-within,
                table td:focus, table td:focus-within,
                table th:focus, table th:focus-within {{
                    outline: none !important;
                    border-style: solid !important;
                }}
                
                /* Zebra stripe styling */
                table td.zebra-stripe {{
                    background-color: #f2f2f2;
                }}
                
                /* Table alignment classes */
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
                
                /* Floating table style */
                table.float-mode {{
                    position: absolute;
                    z-index: 100;
                    border: 1px solid #ccc;
                    margin: 0;
                    float: none;
                }}
                
                /* Table handles */
                .table-drag-handle {{
                    position: absolute;
                    top: -16px;
                    left: -1px;
                    width: 16px;
                    height: 16px;
                    background-color: #4e9eff;
                    border-radius: 2px;
                    cursor: ns-resize;
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
                }}
                
                .table-handle {{
                    position: absolute;
                    bottom: -10px;
                    right: -10px;
                    width: 16px;
                    height: 16px;
                    background-color: #4e9eff;
                    border-radius: 8px;
                    cursor: nwse-resize;
                    z-index: 1000;
                    pointer-events: all;
                    user-select: none;
                    -webkit-user-select: none;
                    -moz-user-select: none;
                    -ms-user-select: none;
                }}
                
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
                
                /* Dark mode support */
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
                    
                    .table-drag-handle, .table-handle {{
                        background-color: #0078d7;
                    }}
                    
                    table.text-box-table {{
                        border-color: #444 !important;
                        background-color: #2d2d2d;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    }}
                    
                    table.float-mode {{
                        border-color: #444;
                    }}
                    
                    #editor ::selection {{
                        background-color: #264f78;
                        color: inherit;
                    }}
                    
                    table td.zebra-stripe {{
                        background-color: #262626;
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
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
