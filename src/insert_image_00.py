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
import show_html

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
        
        # Import methods from show_html module
        show_html_methods = [
            # File opening methods
            'on_show_html_clicked', 'show_html_dialog',
            'apply_html_changes', 'copy_html_to_clipboard',
            'handle_apply_html_result', 
        ]
        
        # Import methods from show_html
        for method_name in show_html_methods:
            if hasattr(show_html, method_name):
                setattr(self, method_name, getattr(show_html, method_name).__get__(self, HTMLEditorApp))
                 
        
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
        return

    def on_insert_text_box_clicked(self, win, btn):
        return
        
    def on_insert_image_clicked(self, win, btn):
        return

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
            
            // Capture tab key and shift+tab to prevent focus from shifting
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    // Prevent the default focus shift action for both tab and shift+tab
                    e.preventDefault();
                    e.stopPropagation();
                    
                    if (e.shiftKey) {
                        // Handle shift+tab (backwards tab)
                        // You can customize this behavior if needed
                        // For now, just insert a tab character like normal tab
                        document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                    } else {
                        // Normal tab behavior
                        document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                    }
                    
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
        return """  """    
        
    def create_window(self):
        """Create a new window with all initialization"""
        win = Adw.ApplicationWindow(application=self)
        
        # Set window properties
        win.modified = False
        win.auto_save_enabled = False
        win.auto_save_interval = 60
        win.current_file = None
        win.auto_save_source_id = None
        
        win.set_default_size(676, 480)
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
        
        # Create the main headerbar
        win.headerbar = Adw.HeaderBar()
        win.headerbar.add_css_class("flat-header")  # Add flat-header style
        self.setup_headerbar_content(win)
        
        # Create a vertical box to contain headerbar and unified toolbar
        win.headerbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.headerbar_box.append(win.headerbar)
        
        # Create toolbar revealer for smooth show/hide
        win.toolbar_revealer = Gtk.Revealer()
        win.toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.toolbar_revealer.set_transition_duration(250)
        win.toolbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create WrapBox for flexible toolbar layout
        win.toolbars_wrapbox = Adw.WrapBox()
        win.toolbars_wrapbox.set_margin_start(4)
        win.toolbars_wrapbox.set_margin_end(4)
        win.toolbars_wrapbox.set_margin_top(4)
        win.toolbars_wrapbox.set_margin_bottom(4)
        win.toolbars_wrapbox.set_child_spacing(4)
        win.toolbars_wrapbox.set_line_spacing(4)
        
        # --- Insert operations group (Table, Text Box, Image) ---
        insert_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        insert_group.add_css_class("linked")  # Apply linked styling
        insert_group.set_margin_start(0)

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
        win.toolbars_wrapbox.append(insert_group)

        # Add toolbar to revealer
        win.toolbar_revealer.set_child(win.toolbars_wrapbox)
        
        # Add headerbar and toolbar to headerbar_box
        win.headerbar_box.append(win.toolbar_revealer)
        
        # Add headerbar_box to headerbar_revealer
        win.headerbar_revealer.set_child(win.headerbar_box)
        
        # Add headerbar_revealer to main_box
        win.main_box.append(win.headerbar_revealer)
        
        # Create a content box for the editor and statusbar
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
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
            
            # Add handler for formatting changes
            user_content_manager.register_script_message_handler("formattingChanged")
            user_content_manager.connect("script-message-received::formattingChanged", 
                                        lambda mgr, res: self.on_formatting_changed(win, mgr, res))
            
            # ADD THESE TABLE-RELATED MESSAGE HANDLERS
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

        # Add content box to the main box
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


    #####################
    def execute_js(self, win, script):
        """Execute JavaScript in the WebView"""
        win.webview.evaluate_javascript(script, -1, None, None, None, None, None)
        
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
    # First, let's implement the JavaScript function for image insertion
    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return """
        // Insert image function
        function insertImage(src, alt, width, height) {
            // Create new image element
            let img = document.createElement('img');
            
            // Set attributes
            img.src = src;
            img.alt = alt || '';
            
            // Set size if provided
            if (width) img.width = width;
            if (height) img.height = height;
            
            // Insert the image at current selection
            document.execCommand('insertHTML', false, img.outerHTML);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage("changed");
            } catch(e) {
                console.log("Could not notify about changes:", e);
            }
        }
        
        // Handle the image element selection
        function handleImageSelection(event) {
            // Check if an image is selected
            const selection = window.getSelection();
            if (!selection.rangeCount) return;
            
            const range = selection.getRangeAt(0);
            const node = range.commonAncestorContainer;
            
            // Find the clicked image
            let img = null;
            if (node.nodeName === 'IMG') {
                img = node;
            } else if (node.parentNode && node.parentNode.nodeName === 'IMG') {
                img = node.parentNode;
            }
            
            // If an image is found, handle it
            if (img) {
                event.preventDefault();
                event.stopPropagation();
                
                // Notify image clicked - can be used to show image properties dialog
                try {
                    window.webkit.messageHandlers.imageClicked.postMessage({
                        src: img.src,
                        alt: img.alt || '',
                        width: img.width || '',
                        height: img.height || ''
                    });
                } catch(e) {
                    console.log("Could not notify about image click:", e);
                }
            }
        }
        
        // Add event listener for image selection when the document is loaded
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Listen for clicks to detect image selection
            editor.addEventListener('click', handleImageSelection);
        });
        """

    # Now, let's implement the Python function to handle the image insertion UI
    def on_insert_image_clicked(self, win, btn):
        """Show a dialog to insert an image"""
        # Create a file chooser dialog
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select Image")
        
        # Set up file filter for images
        filter = Gtk.FileFilter.new()
        filter.set_name("Image files")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/gif")
        filter.add_mime_type("image/svg+xml")
        
        # Create a list of filters
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter)
        dialog.set_filters(filters)
        
        # Show the dialog
        dialog.open(win, None, self._on_image_file_selected, win)

    def _on_image_file_selected(self, dialog, result, win):
        """Handle the selected image file"""
        try:
            file = dialog.open_finish(result)
            if file:
                # Get the file path
                file_path = file.get_path()
                
                # Show image properties dialog
                self._show_image_properties_dialog(win, file_path)
        except Exception as e:
            print(f"Error selecting image: {e}")
            # Show error message
            error_dialog = Adw.MessageDialog(
                transient_for=win,
                title="Error",
                body=f"Could not load the image: {e}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def _show_image_properties_dialog(self, win, file_path):
        """Show dialog to set image properties"""
        # Create dialog
        dialog = Adw.Window()
        dialog.set_title("Image Properties")
        dialog.set_transient_for(win)
        dialog.set_modal(True)
        dialog.set_default_size(400, 300)
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        
        # Create preview (optional - for small images)
        try:
            # Load image for preview
            texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(file_path))
            picture = Gtk.Picture.new_for_file(Gio.File.new_for_path(file_path))
            
            # Scale down if too large
            img_width = texture.get_width()
            img_height = texture.get_height()
            
            if img_width > 300 or img_height > 200:
                scale = min(300 / img_width, 200 / img_height)
                picture.set_size_request(int(img_width * scale), int(img_height * scale))
            
            picture.set_halign(Gtk.Align.CENTER)
            content_box.append(picture)
        except Exception as e:
            print(f"Error creating preview: {e}")
            # Add label instead of preview
            preview_label = Gtk.Label(label="Image Preview Not Available")
            preview_label.set_halign(Gtk.Align.CENTER)
            content_box.append(preview_label)
        
        # Create form fields
        alt_label = Gtk.Label(label="Alt Text:")
        alt_label.set_halign(Gtk.Align.START)
        content_box.append(alt_label)
        
        alt_entry = Gtk.Entry()
        alt_entry.set_placeholder_text("Description of the image")
        content_box.append(alt_entry)
        
        # Size options
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)
        size_box.append(width_label)
        
        width_entry = Gtk.Entry()
        width_entry.set_placeholder_text("Auto")
        width_entry.set_hexpand(True)
        size_box.append(width_entry)
        
        height_label = Gtk.Label(label="Height:")
        height_label.set_halign(Gtk.Align.START)
        size_box.append(height_label)
        
        height_entry = Gtk.Entry()
        height_entry.set_placeholder_text("Auto")
        height_entry.set_hexpand(True)
        size_box.append(height_entry)
        
        content_box.append(size_box)
        
        # Add buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.destroy())
        button_box.append(cancel_button)
        
        insert_button = Gtk.Button(label="Insert")
        insert_button.add_css_class("suggested-action")
        insert_button.connect("clicked", lambda btn: self._insert_image_to_editor(
            win, 
            file_path, 
            alt_entry.get_text(), 
            width_entry.get_text(), 
            height_entry.get_text(), 
            dialog
        ))
        button_box.append(insert_button)
        
        content_box.append(button_box)
        
        # Set content and show dialog
        dialog.set_content(content_box)
        dialog.present()

    def _insert_image_to_editor(self, win, file_path, alt_text, width, height, dialog):
        """Insert the image into the editor"""
        try:
            # Convert the file path to a data URL for embedding
            # For production, you might want to copy the file to a designated location
            # and use relative paths instead of data URLs
            import base64
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Get file extension for mime type
            _, ext = os.path.splitext(file_path)
            ext = ext.lower().strip('.')
            
            # Map extension to mime type
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'svg': 'image/svg+xml'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            # Create data URL
            data_url = f"data:{mime_type};base64,{encoded_string}"
            
            # Create JavaScript to insert the image
            js_code = f"""
            (function() {{
                insertImage("{data_url}", "{alt_text}", "{width}", "{height}");
                return true;
            }})();
            """
            
            # Execute the JavaScript
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            
            # Close the dialog
            dialog.destroy()
            
            # Update status
            win.statusbar.set_text("Image inserted")
            
        except Exception as e:
            print(f"Error inserting image: {e}")
            # Show error message
            error_dialog = Adw.MessageDialog(
                transient_for=win,
                title="Error",
                body=f"Could not insert the image: {e}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    # Add message handler for image clicks
    def on_image_clicked(self, win, manager, message):
        """Handle when an image is clicked in the editor"""
        try:
            # Extract image properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties (this is a simplified version)
            import json
            img_props = json.loads(properties)
            
            # Show image properties dialog for editing
            # This could reuse _show_image_properties_dialog with modifications
            print(f"Image clicked: {img_props}")
            
            # Update status
            win.statusbar.set_text("Image selected")
            
        except Exception as e:
            print(f"Error handling image click: {e}")


    # Add this method to the HTMLEditorApp class
    def image_event_handlers_js(self):
        """JavaScript for event handlers related to image interactions"""
        return """
        // Add event handlers for image interactions
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Add the custom style for image handles
            addImageHandleStyles();
            
            // Handle mouse down events for image interactions
            editor.addEventListener('mousedown', function(e) {
                // Prevent selection of image handles
                if (e.target.classList.contains('image-resize-handle') || 
                    e.target.classList.contains('image-drag-handle')) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                
                let imageElement = findParentImage(e.target);
                
                if (e.target.classList.contains('image-drag-handle')) {
                    if (e.button === 0) { // Left mouse button
                        startImageDrag(e, findParentImage(e.target));
                    }
                }
                
                if (e.target.classList.contains('image-resize-handle')) {
                    startImageResize(e, findParentImage(e.target));
                }
            });
            
            // Handle mouse move events
            document.addEventListener('mousemove', function(e) {
                if (isImageDragging && activeImage) {
                    moveImage(e);
                }
                if (isImageResizing && activeImage) {
                    resizeImage(e);
                }
            });
            
            // Handle mouse up events
            document.addEventListener('mouseup', function() {
                if (isImageDragging || isImageResizing) {
                    isImageDragging = false;
                    isImageResizing = false;
                    document.body.style.cursor = '';
                    
                    if (activeImage) {
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            });
            
            // Handle click events for image selection
            editor.addEventListener('click', function(e) {
                let imageElement = findParentImage(e.target);
                
                if (!imageElement) {
                    // We clicked outside any image
                    if (activeImage) {
                        // If there was a previously active image, deactivate it
                        deactivateAllImages();
                    } else {
                        // Even if there was no active image, still send the deactivation message
                        try {
                            window.webkit.messageHandlers.imagesDeactivated.postMessage('images-deactivated');
                        } catch(e) {
                            console.log("Could not notify about image deactivation:", e);
                        }
                    }
                } else if (imageElement !== activeImage) {
                    // We clicked on a different image than the currently active one
                    deactivateAllImages();
                    activateImage(imageElement);
                    
                    try {
                        window.webkit.messageHandlers.imageClicked.postMessage({
                            src: imageElement.querySelector('img')?.src || '',
                            alt: imageElement.querySelector('img')?.alt || '',
                            width: imageElement.querySelector('img')?.width || '',
                            height: imageElement.querySelector('img')?.height || ''
                        });
                    } catch(e) {
                        console.log("Could not notify about image click:", e);
                    }
                }
            });
            
            // Add a document-level click handler that will deactivate images when clicking outside the editor
            document.addEventListener('click', function(e) {
                // Check if the click is outside the editor
                if (!editor.contains(e.target) && activeImage) {
                    deactivateAllImages();
                }
            });
        });
        """

    # Update the create_window method to return the window object
    # Add this at the very end of the create_window method:
    # Find this line:
        # Add to windows list
        self.windows.append(win)
        
        return win  # Make sure to return the window object here
         
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
