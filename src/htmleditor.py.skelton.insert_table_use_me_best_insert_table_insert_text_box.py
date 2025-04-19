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
        
        try:
            user_content_manager = win.webview.get_user_content_manager()
            user_content_manager.register_script_message_handler("contentChanged")
            user_content_manager.connect("script-message-received::contentChanged", 
                                        lambda mgr, res: self.on_content_changed(win, mgr, res))
            
        except:
            print("Warning: Could not set up JavaScript message handlers")
                    
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        
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
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return """ """

    def insert_text_box_js(self):
        return """
    // Function to insert a text box as a 1x1 table
    function insertTextBox() {
        // Create a styled 1x1 table to serve as a text box
        let textBox = '<table border="1" cellspacing="0" cellpadding="10" class="text-box-table" ' +
                     'style="border-collapse: collapse; min-height: 80px; width: 100%; max-width: 500px; ' +
                     'border: 1px solid #ccc; resize: both; overflow: auto; margin: 10px 0;">' +
                     '<tr><td style="padding: 10px;">Type text here...</td></tr>' +
                     '</table><p></p>';
                     
        document.execCommand('insertHTML', false, textBox);
        
        // Activate the newly inserted table/text box - this uses your existing table activation code
        setTimeout(() => {
            const tables = document.querySelectorAll('table.text-box-table');
            const newTable = tables[tables.length - 1];
            if (newTable) {
                activateTable(newTable);
                window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
            }
        }, 10);
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


    def get_editor_html(self, content=""):
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f"""
    <!DOCTYPE html>
    <html style="height: 100%;">
    <head>
        <title>HTML Editor</title>
        <style>
            html, body {{
                height: 100%;
                /*margin: 40px; */ /*Change this for page border*/
                padding: 0;
                font-family: Sans;
            }}
            #editor {{
                /*border: 1px solid #ccc;*/
                padding: 0px;
                outline: none;
                /*min-height: 200px; */ /* Reduced fallback minimum height */
                height: 100%; /* Allow it to expand fully */
                /*box-sizing: border-box; */ /* Include padding/border in height */
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
            @media (prefers-color-scheme: dark) {{
                html, body {{
                    background-color: #1e1e1e;
                    color: #c0c0c0;
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
    
    def execute_js(self, win, script):
        """Execute JavaScript in the WebView"""
        win.webview.evaluate_javascript(script, -1, None, None, None, None, None)
    

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
    def get_editor_html(self, content=""):
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f"""
        <!DOCTYPE html>
        <html style="height: 100%;">
        <head>
            <title>HTML Editor</title>
            <style>
                html, body {{
                    height: 100%;
                    /*margin: 40px; */ /*Change this for page border*/
                    padding: 0;
                    font-family: Sans;
                }}
                #editor {{
                    /*border: 1px solid #ccc;*/
                    padding: 0px;
                    outline: none;
                    /*min-height: 200px; */ /* Reduced fallback minimum height */
                    height: 100%; /* Allow it to expand fully */
                    /*box-sizing: border-box; */ /* Include padding/border in height */
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
################
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
                    window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
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
            activeTable = tableElement;
            tableElement.style.marginLeft = '';
            tableElement.style.marginTop = '';
            
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
                tableElement.appendChild(resizeHandle);
            }
            
            // Add drag handle if needed
            if (!tableElement.querySelector('.table-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'table-drag-handle';
                dragHandle.innerHTML = '↕';
                dragHandle.title = 'Drag to reposition table between paragraphs';
                tableElement.appendChild(dragHandle);
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
        
        // Add event handlers for table interactions
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Handle mouse down events
            editor.addEventListener('mousedown', function(e) {
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

    # Create the main modified HTMLEditorApp class with table functionality
    class HTMLEditorApp(Adw.Application):
        # ... existing code ...
        
        def create_window(self):
            """Create a new window with all initialization (former HTMLEditorWindow.__init__)"""
            win = super().create_window()
            
            # Create table toolbar with revealer (hidden by default)
            win.table_toolbar_revealer = Gtk.Revealer()
            win.table_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
            win.table_toolbar_revealer.set_transition_duration(250)
            win.table_toolbar_revealer.set_reveal_child(False)
            
            # Create table toolbar
            win.table_toolbar = self.create_table_toolbar(win)
            win.table_toolbar_revealer.set_child(win.table_toolbar)
            
            # Insert the table toolbar after the file toolbar
            win.headerbar_box.append(win.table_toolbar_revealer)
            
            # Setup table related message handlers
            user_content_manager = win.webview.get_user_content_manager()
            user_content_manager.register_script_message_handler("tableClicked")
            user_content_manager.register_script_message_handler("tableDeleted")
            user_content_manager.register_script_message_handler("tablesDeactivated")
            
            user_content_manager.connect("script-message-received::tableClicked", 
                                        lambda mgr, res: self.on_table_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::tableDeleted", 
                                        lambda mgr, res: self.on_table_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::tablesDeactivated", 
                                        lambda mgr, res: self.on_tables_deactivated(win, mgr, res))
            
            return win
        
        # Event handlers for table events
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
        
        def execute_js(self, win, script):
            """Execute JavaScript in the WebView"""
            win.webview.evaluate_javascript(script, -1, None, None, None, None, None)
        
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
########################
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

    # Table event handlers to add to the class
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

##################
    # Add these methods to your HTMLEditorApp class to fix the AttributeError issues

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

#########################################################
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
            activeTable = tableElement;
            tableElement.style.marginLeft = '';
            tableElement.style.marginTop = '';
            
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
                dragHandle.innerHTML = '↕';
                dragHandle.title = 'Drag to reposition table between paragraphs';
                
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
                    startTableDrag(e, tableElement);
                }, true);
                
                tableElement.appendChild(dragHandle);
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

    def get_editor_html(self, content=""):
        """Return HTML for the editor with table styles"""
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
