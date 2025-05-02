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
                                        
            # Add image-related message handlers
            user_content_manager.register_script_message_handler("imageClicked")
            user_content_manager.connect("script-message-received::imageClicked", 
                                        lambda mgr, res: self.on_image_clicked(win, mgr, res))
            
            # Add handler for image properties changes
            user_content_manager.register_script_message_handler("imagePropertiesChanged")
            user_content_manager.connect("script-message-received::imagePropertiesChanged", 
                                        lambda mgr, res: self.on_image_properties_changed(win, mgr, res))                                        
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

    ################
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
                
                // Initialize image handling when editor gets focus
                setTimeout(setupImageHandles, 100);
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
            
            // Set up a mutation observer to detect DOM changes
            const observer = new MutationObserver(function(mutations) {
                // Check if any mutations involved images
                const imageChanges = mutations.some(mutation => {
                    return Array.from(mutation.addedNodes).some(node => 
                        node.nodeName === 'IMG' || 
                        (node.nodeType === 1 && node.querySelector('img'))
                    );
                });
                
                if (imageChanges) {
                    // Call setupImageHandles after a short delay to let DOM settle
                    setTimeout(setupImageHandles, 100);
                }
            });
            
            // Start observing the editor for changes
            observer.observe(editor, { 
                childList: true, 
                subtree: true,
                attributes: true,
                attributeFilter: ['src', 'width', 'height']
            });

            // Initialize image handling
            setupImageHandles();

            if (window.initialContent) {
                setContent(window.initialContent);
                
                // Setup image handles again after content is loaded
                setTimeout(setupImageHandles, 100);
            }
        });
        
        // Helper function to save the current state for undo/redo
        function saveState() {
            window.undoStack.push(window.lastContent);
            // Limit stack size to prevent memory issues
            if (window.undoStack.length > 50) {
                window.undoStack.shift();
            }
        }
        
        // Helper function to undo the last action
        function undo() {
            if (window.undoStack.length > 1) { // Keep at least one state in the stack
                // Move current state to redoStack
                window.redoStack.push(window.undoStack.pop());
                
                // Set the previous state as current
                window.isUndoRedo = true;
                const previousState = window.undoStack[window.undoStack.length - 1];
                document.getElementById('editor').innerHTML = previousState;
                window.lastContent = previousState;
                window.isUndoRedo = false;
                
                // Limit redoStack size
                if (window.redoStack.length > 50) {
                    window.redoStack.shift();
                }
                
                // Notify about changes
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about undo:", e);
                }
                
                return true;
            }
            return false;
        }
        
        // Helper function to redo the last undone action
        function redo() {
            if (window.redoStack.length > 0) {
                // Get the last redoState
                const redoState = window.redoStack.pop();
                
                // Save current state to undoStack
                window.undoStack.push(redoState);
                
                // Set the redo state as current
                window.isUndoRedo = true;
                document.getElementById('editor').innerHTML = redoState;
                window.lastContent = redoState;
                window.isUndoRedo = false;
                
                // Notify about changes
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about redo:", e);
                }
                
                return true;
            }
            return false;
        }
        
        // Get all the formatting status for toolbar updates
        function getFormatStatus() {
            const commands = [
                'bold', 'italic', 'underline', 'strikeThrough',
                'justifyLeft', 'justifyCenter', 'justifyRight', 'justifyFull',
                'insertOrderedList', 'insertUnorderedList', 'indent', 'outdent'
            ];
            
            let status = {};
            commands.forEach(command => {
                status[command] = document.queryCommandState(command);
            });
            
            // Get additional states that are not covered by queryCommandState
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                
                // Check for block formatting
                let blockNode = range.commonAncestorContainer;
                if (blockNode.nodeType === 3) { // Text node
                    blockNode = blockNode.parentNode;
                }
                
                // Get block format
                status.block = getBlockFormat(blockNode);
                
                // Get font family
                status.fontFamily = document.queryCommandValue('fontName');
                
                // Get font size
                status.fontSize = document.queryCommandValue('fontSize');
            }
            
            // Try to send status back to the app
            try {
                window.webkit.messageHandlers.formattingChanged.postMessage(JSON.stringify(status));
            } catch(e) {
                console.log("Could not send formatting status:", e);
            }
            
            return status;
        }
        
        // Helper to get the block format
        function getBlockFormat(node) {
            const blockTags = {
                'P': 'paragraph',
                'H1': 'heading1',
                'H2': 'heading2',
                'H3': 'heading3',
                'H4': 'heading4',
                'H5': 'heading5',
                'H6': 'heading6',
                'PRE': 'preformatted',
                'BLOCKQUOTE': 'blockquote'
            };
            
            // Check if the node itself is a block element
            if (node.nodeType === 1 && blockTags[node.tagName]) {
                return blockTags[node.tagName];
            }
            
            // Check parent nodes
            let currentNode = node;
            while (currentNode && currentNode.tagName !== 'DIV' && currentNode.tagName !== 'BODY') {
                if (blockTags[currentNode.tagName]) {
                    return blockTags[currentNode.tagName];
                }
                currentNode = currentNode.parentNode;
            }
            
            // Default is paragraph
            return 'paragraph';
        }
        
        // Watch for selection changes to update formatting status
        document.addEventListener('selectionchange', function() {
            // Get format status after a short delay
            setTimeout(getFormatStatus, 10);
        });
        
        // Add a click handler to also check format status
        document.getElementById('editor').addEventListener('click', function() {
            setTimeout(getFormatStatus, 10);
        });
        
        // Initialize format status on load
        setTimeout(getFormatStatus, 100);
        """



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
                
                /* Image wrapper and handle styles */
                .img-wrapper {{
                    position: relative;
                    display: inline-block;
                    margin: 2px;
                    box-sizing: border-box;
                }}
                
                .img-wrapper-active {{
                    outline: 2px solid #1e90ff;
                    outline-offset: 2px;
                }}
                
                .img-wrapper img {{
                    display: block;
                    max-width: 100%;
                }}
                
                .img-drag-handle {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 10px;
                    height: 10px;
                    background-color: #1e90ff;
                    border: 1px solid white;
                    cursor: move;
                    z-index: 1000;
                }}
                
                .img-resize-handle {{
                    position: absolute;
                    bottom: 0;
                    right: 0;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    border-width: 0 0 10px 10px;
                    border-color: transparent transparent #1e90ff transparent;
                    cursor: nwse-resize;
                    z-index: 1000;
                }}

                #editor ::selection {{
                    background-color: #264f78;
                    color: inherit;
                }}
                
                @media (prefers-color-scheme: dark) {{
                    html, body {{
                        background-color: #1e1e1e;
                        color: #d4d4d4;
                    }}
                    .img-wrapper-active {{
                        outline-color: #3a8eff;
                    }}
                    .img-drag-handle {{
                        background-color: #3a8eff;
                        border-color: #222;
                    }}
                    .img-resize-handle {{
                        border-color: transparent transparent #3a8eff transparent;
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
            
            // Add a wrapper div with position relative to contain the image and handles
            const wrapper = document.createElement('div');
            wrapper.className = 'img-wrapper';
            wrapper.style.position = 'relative';
            wrapper.style.display = 'inline-block';
            wrapper.style.margin = '2px';
            
            // Add the image to the wrapper
            wrapper.appendChild(img);
            
            // Insert the wrapped image at current selection
            document.execCommand('insertHTML', false, wrapper.outerHTML);
            
            // After insertion, find the wrapper and set up handles
            setupImageHandles();
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage("changed");
            } catch(e) {
                console.log("Could not notify about changes:", e);
            }
        }

        // Set up image handles for all image wrappers
        function setupImageHandles() {
            // Remove any existing active handles first
            removeAllImageHandles();
            
            // Get all image wrappers
            const wrappers = document.querySelectorAll('.img-wrapper');
            
            wrappers.forEach(wrapper => {
                // Make sure the wrapper has position relative
                wrapper.style.position = 'relative';
                
                // Add the wrapper to the existing img elements if not already wrapped
                if (!wrapper.querySelector('img')) {
                    const img = wrapper.nextElementSibling;
                    if (img && img.tagName === 'IMG') {
                        wrapper.appendChild(img);
                    }
                }
                
                // Add click event to make the image active
                wrapper.addEventListener('click', activateImageHandles);
            });
            
            // Find all images that aren't in wrappers and wrap them
            const images = document.querySelectorAll('#editor img:not(.img-wrapper img)');
            images.forEach(img => {
                // Don't wrap images that are already in wrappers
                if (img.parentNode.className === 'img-wrapper') return;
                
                // Create wrapper
                const wrapper = document.createElement('div');
                wrapper.className = 'img-wrapper';
                wrapper.style.position = 'relative';
                wrapper.style.display = 'inline-block';
                wrapper.style.margin = '2px';
                
                // Replace the image with the wrapper containing the image
                img.parentNode.insertBefore(wrapper, img);
                wrapper.appendChild(img);
                
                // Add click event to make the image active
                wrapper.addEventListener('click', activateImageHandles);
            });
        }

        // Activate handles for a specific image wrapper
        function activateImageHandles(event) {
            // Prevent default behavior
            event.preventDefault();
            
            // Remove handles from all other images first
            removeAllImageHandles();
            
            // Get the wrapper (this could be the wrapper itself or an image inside it)
            let wrapper = this;
            if (this.tagName === 'IMG') {
                wrapper = this.parentNode;
            }
            
            // Add active class
            wrapper.classList.add('img-wrapper-active');
            
            // Create drag handle (square at top-left)
            const dragHandle = document.createElement('div');
            dragHandle.className = 'img-drag-handle';
            dragHandle.style.position = 'absolute';
            dragHandle.style.top = '0';
            dragHandle.style.left = '0';
            dragHandle.style.width = '10px';
            dragHandle.style.height = '10px';
            dragHandle.style.background = '#1e90ff';
            dragHandle.style.border = '1px solid white';
            dragHandle.style.cursor = 'move';
            dragHandle.style.zIndex = '1000';
            
            // Create resize handle (triangle at bottom-right)
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'img-resize-handle';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '0';
            resizeHandle.style.right = '0';
            resizeHandle.style.width = '0';
            resizeHandle.style.height = '0';
            resizeHandle.style.borderStyle = 'solid';
            resizeHandle.style.borderWidth = '0 0 10px 10px';
            resizeHandle.style.borderColor = 'transparent transparent #1e90ff transparent';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.zIndex = '1000';
            
            // Add handles to the wrapper
            wrapper.appendChild(dragHandle);
            wrapper.appendChild(resizeHandle);
            
            // Get the image inside the wrapper
            const img = wrapper.querySelector('img');
            
            // Setup drag functionality
            let startX, startY, startLeft, startTop;
            
            dragHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Get initial positions
                startX = e.clientX;
                startY = e.clientY;
                startLeft = wrapper.offsetLeft;
                startTop = wrapper.offsetTop;
                
                // Add mousemove and mouseup events to document
                document.addEventListener('mousemove', dragMove);
                document.addEventListener('mouseup', dragEnd);
            });
            
            function dragMove(e) {
                e.preventDefault();
                
                // Calculate new position
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                // Update wrapper position
                wrapper.style.position = 'relative';
                wrapper.style.left = (startLeft + dx) + 'px';
                wrapper.style.top = (startTop + dy) + 'px';
                
                // Notify content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about changes:", e);
                }
            }
            
            function dragEnd() {
                // Remove event listeners
                document.removeEventListener('mousemove', dragMove);
                document.removeEventListener('mouseup', dragEnd);
            }
            
            // Setup resize functionality
            let startWidth, startHeight, aspectRatio;
            
            resizeHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Get initial sizes
                startX = e.clientX;
                startY = e.clientY;
                startWidth = img.offsetWidth;
                startHeight = img.offsetHeight;
                aspectRatio = startWidth / startHeight;
                
                // Add mousemove and mouseup events to document
                document.addEventListener('mousemove', resizeMove);
                document.addEventListener('mouseup', resizeEnd);
            });
            
            function resizeMove(e) {
                e.preventDefault();
                
                // Calculate new dimensions
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                // Determine which dimension to prioritize based on the greater change
                if (Math.abs(dx) > Math.abs(dy)) {
                    // Prioritize width
                    const newWidth = Math.max(10, startWidth + dx);
                    img.width = newWidth;
                    img.height = newWidth / aspectRatio;
                } else {
                    // Prioritize height
                    const newHeight = Math.max(10, startHeight + dy);
                    img.height = newHeight;
                    img.width = newHeight * aspectRatio;
                }
                
                // Notify content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about changes:", e);
                }
            }
            
            function resizeEnd() {
                // Remove event listeners
                document.removeEventListener('mousemove', resizeMove);
                document.removeEventListener('mouseup', resizeEnd);
                
                // Notify that image properties changed
                try {
                    window.webkit.messageHandlers.imagePropertiesChanged.postMessage({
                        width: img.width,
                        height: img.height
                    });
                } catch(e) {
                    console.log("Could not notify about image properties change:", e);
                }
            }
            
            // When the image is clicked, notify that it was selected
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

        // Remove all image handles
        function removeAllImageHandles() {
            // Remove active class from all wrappers
            document.querySelectorAll('.img-wrapper-active').forEach(wrapper => {
                wrapper.classList.remove('img-wrapper-active');
            });
            
            // Remove all drag handles
            document.querySelectorAll('.img-drag-handle').forEach(handle => {
                handle.remove();
            });
            
            // Remove all resize handles
            document.querySelectorAll('.img-resize-handle').forEach(handle => {
                handle.remove();
            });
        }

        // Document click handler to deselect all images when clicking elsewhere
        document.addEventListener('click', function(e) {
            // If the click is not on an image or wrapper, remove all handles
            if (!e.target.closest('.img-wrapper') && e.target.tagName !== 'IMG') {
                removeAllImageHandles();
            }
        });

        // Initialize image handlers when the document is loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Setup all existing images
            setupImageHandles();
            
            // Add event listener to handle focus changes
            document.getElementById('editor').addEventListener('focus', function() {
                // Delayed setup to ensure the DOM is updated
                setTimeout(setupImageHandles, 100);
            });
        });
        """

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

    def _show_image_properties_dialog(self, win, file_path=None, img_props=None):
        """Show dialog to set image properties
        
        Args:
            win: Parent window
            file_path: Path to image file (for new images)
            img_props: Image properties dict (for editing existing images)
        """
        # Create dialog
        dialog = Adw.Window()
        dialog.set_title("Image Properties")
        dialog.set_transient_for(win)
        dialog.set_modal(True)
        dialog.set_default_size(400, 320)
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        
        # Variables to store original dimensions for aspect ratio
        original_width = 0
        original_height = 0
        aspect_ratio = 1.0
        
        # Create preview (optional - for small images)
        try:
            if file_path:
                # Load image for preview from file
                texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(file_path))
                picture = Gtk.Picture.new_for_file(Gio.File.new_for_path(file_path))
                
                # Get dimensions
                original_width = texture.get_width()
                original_height = texture.get_height()
            elif img_props and 'src' in img_props and img_props['src'].startswith('data:'):
                # This is a placeholder for when you want to edit an existing image
                # In a full implementation, you would need to create a temporary file
                # from the data URL and load it
                
                # For now, just show a placeholder
                picture = Gtk.Picture()
                picture.set_size_request(150, 100)
                
                # Set dimensions if available in img_props
                if 'width' in img_props and img_props['width']:
                    original_width = int(img_props['width'])
                if 'height' in img_props and img_props['height']:
                    original_height = int(img_props['height'])
            else:
                # Fallback
                raise Exception("No image source provided")
            
            # Calculate aspect ratio
            if original_width > 0 and original_height > 0:
                aspect_ratio = original_width / original_height
            
            # Scale down if too large
            if original_width > 300 or original_height > 200:
                scale = min(300 / original_width, 200 / original_height)
                picture.set_size_request(int(original_width * scale), int(original_height * scale))
            else:
                picture.set_size_request(original_width, original_height)
            
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
        if img_props and 'alt' in img_props:
            alt_entry.set_text(img_props['alt'])
        content_box.append(alt_entry)
        
        # Size options with aspect ratio lock
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)
        size_box.append(width_label)
        
        width_entry = Gtk.SpinButton.new_with_range(1, 2000, 1)
        width_entry.set_hexpand(True)
        if img_props and 'width' in img_props and img_props['width']:
            width_entry.set_value(int(img_props['width']))
        elif original_width > 0:
            width_entry.set_value(original_width)
        size_box.append(width_entry)
        
        height_label = Gtk.Label(label="Height:")
        height_label.set_halign(Gtk.Align.START)
        size_box.append(height_label)
        
        height_entry = Gtk.SpinButton.new_with_range(1, 2000, 1)
        height_entry.set_hexpand(True)
        if img_props and 'height' in img_props and img_props['height']:
            height_entry.set_value(int(img_props['height']))
        elif original_height > 0:
            height_entry.set_value(original_height)
        size_box.append(height_entry)
        
        content_box.append(size_box)
        
        # Lock aspect ratio checkbox
        lock_aspect_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        aspect_check = Gtk.CheckButton()
        aspect_check.set_label("Lock aspect ratio")
        aspect_check.set_active(True)  # Default to locked
        lock_aspect_box.append(aspect_check)
        
        content_box.append(lock_aspect_box)
        
        # Connect signals for width/height with aspect ratio
        width_handler_id = width_entry.connect("value-changed", lambda w: update_height() if aspect_check.get_active() else None)
        height_handler_id = height_entry.connect("value-changed", lambda h: update_width() if aspect_check.get_active() else None)
        
        # Functions to maintain aspect ratio
        def update_height():
            if aspect_ratio > 0:
                # Temporarily block the height signal to prevent recursion
                with height_entry.handler_block(height_handler_id):
                    new_height = width_entry.get_value() / aspect_ratio
                    height_entry.set_value(round(new_height))
        
        def update_width():
            if aspect_ratio > 0:
                # Temporarily block the width signal to prevent recursion
                with width_entry.handler_block(width_handler_id):
                    new_width = height_entry.get_value() * aspect_ratio
                    width_entry.set_value(round(new_width))
        
        # Add buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.destroy())
        button_box.append(cancel_button)
        
        if img_props:
            # For editing existing images
            apply_button = Gtk.Button(label="Apply")
            apply_button.add_css_class("suggested-action")
            apply_button.connect("clicked", lambda btn: self._update_existing_image(
                win,
                img_props,
                alt_entry.get_text(),
                int(width_entry.get_value()),
                int(height_entry.get_value()),
                dialog
            ))
            button_box.append(apply_button)
        else:
            # For inserting new images
            insert_button = Gtk.Button(label="Insert")
            insert_button.add_css_class("suggested-action")
            insert_button.connect("clicked", lambda btn: self._insert_image_to_editor(
                win, 
                file_path, 
                alt_entry.get_text(), 
                int(width_entry.get_value()), 
                int(height_entry.get_value()), 
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

    def _update_existing_image(self, win, img_props, alt_text, width, height, dialog):
        """Update an existing image in the editor"""
        try:
            # Create JavaScript to update the image
            js_code = f"""
            (function() {{
                // Get the currently selected image
                const activeWrapper = document.querySelector('.img-wrapper-active');
                if (!activeWrapper) return false;
                
                const img = activeWrapper.querySelector('img');
                if (!img) return false;
                
                // Update properties
                img.alt = "{alt_text}";
                img.width = {width};
                img.height = {height};
                
                // Remove handles to force a refresh
                removeAllImageHandles();
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                }} catch(e) {{
                    console.log("Could not notify about changes:", e);
                }}
                
                return true;
            }})();
            """
            
            # Execute the JavaScript
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            
            # Close the dialog
            dialog.destroy()
            
            # Update status
            win.statusbar.set_text("Image updated")
            
        except Exception as e:
            print(f"Error updating image: {e}")
            # Show error message
            error_dialog = Adw.MessageDialog(
                transient_for=win,
                title="Error",
                body=f"Could not update the image: {e}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def on_image_clicked(self, win, manager, message):
        """Handle when an image is clicked in the editor"""
        try:
            # Extract image properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties
            import json
            img_props = json.loads(properties)
            
            # Show image properties dialog for editing
            self._show_image_properties_dialog(win, None, img_props)
            
            # Update status
            win.statusbar.set_text("Image selected")
            
        except Exception as e:
            print(f"Error handling image click: {e}")

    def on_image_properties_changed(self, win, manager, message):
        """Handle image properties changed event"""
        try:
            # Extract properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties
            import json
            props = json.loads(properties)
            
            # Update status bar with new dimensions
            if 'width' in props and 'height' in props:
                win.statusbar.set_text(f"Image resized to {props['width']}×{props['height']}")
            
        except Exception as e:
            print(f"Error handling image properties change: {e}")

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
                
                /* Image wrapper and handle styles */
                .img-wrapper {{
                    position: relative;
                    display: inline-block;
                    margin: 2px;
                    box-sizing: border-box;
                    user-select: none;
                    -webkit-user-select: none;
                    -moz-user-select: none;
                    -ms-user-select: none;
                }}

                .img-wrapper-active {{
                    outline: 2px solid #1e90ff;
                    outline-offset: 2px;
                    z-index: 100;
                }}

                .img-wrapper img {{
                    display: block;
                    max-width: 100%;
                    user-select: none;
                    -webkit-user-select: none;
                }}

                .img-drag-handle {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 10px;
                    height: 10px;
                    background-color: #1e90ff;
                    border: 1px solid white;
                    cursor: move;
                    z-index: 1000;
                    pointer-events: auto;
                    user-select: none;
                    -webkit-user-select: none;
                }}

                .img-resize-handle {{
                    position: absolute;
                    bottom: 0;
                    right: 0;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    border-width: 0 0 10px 10px;
                    border-color: transparent transparent #1e90ff transparent;
                    cursor: nwse-resize;
                    z-index: 1000;
                    pointer-events: auto;
                    user-select: none;
                    -webkit-user-select: none;
                }}
                
                /* This ensures the wrapper DIV doesn't get affected by text editing */
                #editor [contenteditable="false"] {{
                    -webkit-user-modify: read-only;
                    -moz-user-modify: read-only;
                    user-modify: read-only;
                    cursor: default;
                }}

                /* Ensure proper cursor behavior */
                #editor [contenteditable="false"] img {{
                    cursor: pointer;
                }}

                #editor [contenteditable="false"] .img-drag-handle {{
                    cursor: move;
                }}

                #editor [contenteditable="false"] .img-resize-handle {{
                    cursor: nwse-resize;
                }}

                #editor ::selection {{
                    background-color: #264f78;
                    color: inherit;
                }}
                
                @media (prefers-color-scheme: dark) {{
                    html, body {{
                        background-color: #1e1e1e;
                        color: #d4d4d4;
                    }}
                    .img-wrapper-active {{
                        outline-color: #3a8eff;
                    }}
                    .img-drag-handle {{
                        background-color: #3a8eff;
                        border-color: #222;
                    }}
                    .img-resize-handle {{
                        border-color: transparent transparent #3a8eff transparent;
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
            
            // Add a wrapper div with position relative to contain the image and handles
            const wrapper = document.createElement('div');
            wrapper.className = 'img-wrapper';
            wrapper.style.position = 'relative';
            wrapper.style.display = 'inline-block';
            wrapper.style.margin = '2px';
            wrapper.contentEditable = 'false'; // Make the wrapper not editable
            
            // Add the image to the wrapper
            wrapper.appendChild(img);
            
            // Insert the wrapped image at current selection
            document.execCommand('insertHTML', false, wrapper.outerHTML);
            
            // After insertion, find the wrapper and set up handles
            setupImageHandles();
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage("changed");
            } catch(e) {
                console.log("Could not notify about changes:", e);
            }
        }

        // Set up image handles for all image wrappers
        function setupImageHandles() {
            // Remove any existing active handles first
            removeAllImageHandles();
            
            // Get all image wrappers
            const wrappers = document.querySelectorAll('.img-wrapper');
            
            wrappers.forEach(wrapper => {
                // Make sure the wrapper has position relative
                wrapper.style.position = 'relative';
                
                // Ensure wrapper is not editable
                wrapper.contentEditable = 'false';
                
                // Add the wrapper to the existing img elements if not already wrapped
                if (!wrapper.querySelector('img')) {
                    const img = wrapper.nextElementSibling;
                    if (img && img.tagName === 'IMG') {
                        wrapper.appendChild(img);
                    }
                }
                
                // Add click event to make the image active
                wrapper.addEventListener('click', activateImageHandles);
            });
            
            // Find all images that aren't in wrappers and wrap them
            const images = document.querySelectorAll('#editor img:not(.img-wrapper img)');
            images.forEach(img => {
                // Don't wrap images that are already in wrappers
                if (img.parentNode.className === 'img-wrapper') return;
                
                // Create wrapper
                const wrapper = document.createElement('div');
                wrapper.className = 'img-wrapper';
                wrapper.style.position = 'relative';
                wrapper.style.display = 'inline-block';
                wrapper.style.margin = '2px';
                wrapper.contentEditable = 'false'; // Make the wrapper not editable
                
                // Replace the image with the wrapper containing the image
                img.parentNode.insertBefore(wrapper, img);
                wrapper.appendChild(img);
                
                // Add click event to make the image active
                wrapper.addEventListener('click', activateImageHandles);
            });
        }

        // Activate handles for a specific image wrapper
        function activateImageHandles(event) {
            // Prevent default behavior
            event.preventDefault();
            event.stopPropagation();
            
            // Remove handles from all other images first
            removeAllImageHandles();
            
            // Get the wrapper (this could be the wrapper itself or an image inside it)
            let wrapper = this;
            if (this.tagName === 'IMG') {
                wrapper = this.parentNode;
            }
            
            // Add active class
            wrapper.classList.add('img-wrapper-active');
            
            // Create drag handle (square at top-left)
            const dragHandle = document.createElement('div');
            dragHandle.className = 'img-drag-handle';
            dragHandle.style.position = 'absolute';
            dragHandle.style.top = '0';
            dragHandle.style.left = '0';
            dragHandle.style.width = '10px';
            dragHandle.style.height = '10px';
            dragHandle.style.background = '#1e90ff';
            dragHandle.style.border = '1px solid white';
            dragHandle.style.cursor = 'move';
            dragHandle.style.zIndex = '1000';
            dragHandle.contentEditable = 'false'; // Make handle not editable
            
            // Create resize handle (triangle at bottom-right)
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'img-resize-handle';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '0';
            resizeHandle.style.right = '0';
            resizeHandle.style.width = '0';
            resizeHandle.style.height = '0';
            resizeHandle.style.borderStyle = 'solid';
            resizeHandle.style.borderWidth = '0 0 10px 10px';
            resizeHandle.style.borderColor = 'transparent transparent #1e90ff transparent';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.contentEditable = 'false'; // Make handle not editable
            
            // Add handles to the wrapper
            wrapper.appendChild(dragHandle);
            wrapper.appendChild(resizeHandle);
            
            // Get the image inside the wrapper
            const img = wrapper.querySelector('img');
            
            // Setup drag functionality
            let startX, startY, startLeft, startTop;
            
            dragHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Get initial positions
                startX = e.clientX;
                startY = e.clientY;
                startLeft = wrapper.offsetLeft;
                startTop = wrapper.offsetTop;
                
                // Add mousemove and mouseup events to document
                document.addEventListener('mousemove', dragMove);
                document.addEventListener('mouseup', dragEnd);
            });
            
            function dragMove(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Calculate new position
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                // Update wrapper position
                wrapper.style.position = 'relative';
                wrapper.style.left = (startLeft + dx) + 'px';
                wrapper.style.top = (startTop + dy) + 'px';
                
                // Notify content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about changes:", e);
                }
            }
            
            function dragEnd(e) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                
                // Remove event listeners
                document.removeEventListener('mousemove', dragMove);
                document.removeEventListener('mouseup', dragEnd);
            }
            
            // Setup resize functionality
            let startWidth, startHeight, aspectRatio;
            
            resizeHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Get initial sizes
                startX = e.clientX;
                startY = e.clientY;
                startWidth = img.offsetWidth;
                startHeight = img.offsetHeight;
                aspectRatio = startWidth / startHeight;
                
                // Add mousemove and mouseup events to document
                document.addEventListener('mousemove', resizeMove);
                document.addEventListener('mouseup', resizeEnd);
            });
            
            function resizeMove(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Calculate new dimensions
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                // Determine which dimension to prioritize based on the greater change
                if (Math.abs(dx) > Math.abs(dy)) {
                    // Prioritize width
                    const newWidth = Math.max(10, startWidth + dx);
                    img.width = newWidth;
                    img.height = newWidth / aspectRatio;
                } else {
                    // Prioritize height
                    const newHeight = Math.max(10, startHeight + dy);
                    img.height = newHeight;
                    img.width = newHeight * aspectRatio;
                }
                
                // Notify content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about changes:", e);
                }
            }
            
            function resizeEnd(e) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                
                // Remove event listeners
                document.removeEventListener('mousemove', resizeMove);
                document.removeEventListener('mouseup', resizeEnd);
                
                // Notify that image properties changed
                try {
                    window.webkit.messageHandlers.imagePropertiesChanged.postMessage({
                        width: img.width,
                        height: img.height
                    });
                } catch(e) {
                    console.log("Could not notify about image properties change:", e);
                }
            }
            
            // When the image is clicked, notify that it was selected
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

        // Remove all image handles
        function removeAllImageHandles() {
            // Remove active class from all wrappers
            document.querySelectorAll('.img-wrapper-active').forEach(wrapper => {
                wrapper.classList.remove('img-wrapper-active');
            });
            
            // Remove all drag handles
            document.querySelectorAll('.img-drag-handle').forEach(handle => {
                handle.remove();
            });
            
            // Remove all resize handles
            document.querySelectorAll('.img-resize-handle').forEach(handle => {
                handle.remove();
            });
        }

        // Document click handler to deselect all images when clicking elsewhere
        document.addEventListener('click', function(e) {
            // If the click is not on an image or wrapper, remove all handles
            if (!e.target.closest('.img-wrapper') && e.target.tagName !== 'IMG') {
                removeAllImageHandles();
            }
        });

        // Fix for cursor position issues near images
        document.addEventListener('keydown', function(e) {
            // If we're typing and there's an active image, deactivate it
            if (e.key.length === 1 || e.key === 'Delete' || e.key === 'Backspace') {
                removeAllImageHandles();
            }
        });

        // Initialize image handlers when the document is loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Setup all existing images
            setupImageHandles();
            
            // Add event listener to handle focus changes
            document.getElementById('editor').addEventListener('focus', function() {
                // Delayed setup to ensure the DOM is updated
                setTimeout(setupImageHandles, 100);
            });
        });
        
        // Block editing of non-editable elements
        document.addEventListener('beforeinput', function(e) {
            // Check if event target is inside a non-editable area
            let node = e.target;
            while (node && node !== document.body) {
                if (node.contentEditable === 'false') {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                node = node.parentNode;
            }
        }, true);
        
        // Prevent cursor from being placed inside non-editable elements
        document.addEventListener('mouseup', function(e) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return;
            
            const range = selection.getRangeAt(0);
            let node = range.startContainer;
            
            // Check if the selection is within a non-editable element
            while (node && node !== document.body) {
                if (node.contentEditable === 'false') {
                    // If inside a non-editable element, move cursor after it
                    const newRange = document.createRange();
                    newRange.setStartAfter(findOutermostNonEditable(node));
                    newRange.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(newRange);
                    break;
                }
                node = node.parentNode;
            }
        });
        
        // Helper to find the outermost non-editable parent
        function findOutermostNonEditable(node) {
            let result = node;
            let parent = node.parentNode;
            
            while (parent && parent !== document.body && parent.contentEditable === 'false') {
                result = parent;
                parent = parent.parentNode;
            }
            
            return result;
        }"""

##########
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
                
                // Add a wrapper div with position relative to contain the image and handles
                const wrapper = document.createElement('div');
                wrapper.className = 'img-wrapper';
                wrapper.style.position = 'relative';
                wrapper.style.display = 'inline-block';
                wrapper.style.margin = '2px';
                wrapper.contentEditable = 'false'; // Make the wrapper not editable
                
                // Add the image to the wrapper
                wrapper.appendChild(img);
                
                // Insert the wrapped image at current selection
                document.execCommand('insertHTML', false, wrapper.outerHTML);
                
                // After insertion, find the wrapper and set up handles
                setupImageHandles();
                
                // Notify that content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about changes:", e);
                }
            }

            // Set up image handles for all image wrappers
            function setupImageHandles() {
                // Remove any existing active handles first
                removeAllImageHandles();
                
                // Get all image wrappers
                const wrappers = document.querySelectorAll('.img-wrapper');
                
                wrappers.forEach(wrapper => {
                    // Make sure the wrapper has position relative
                    wrapper.style.position = 'relative';
                    
                    // Ensure wrapper is not editable
                    wrapper.contentEditable = 'false';
                    
                    // Add the wrapper to the existing img elements if not already wrapped
                    if (!wrapper.querySelector('img')) {
                        const img = wrapper.nextElementSibling;
                        if (img && img.tagName === 'IMG') {
                            wrapper.appendChild(img);
                        }
                    }
                    
                    // Add click event to make the image active
                    wrapper.addEventListener('click', activateImageHandles);
                });
                
                // Find all images that aren't in wrappers and wrap them
                const images = document.querySelectorAll('#editor img:not(.img-wrapper img)');
                images.forEach(img => {
                    // Don't wrap images that are already in wrappers
                    if (img.parentNode.className === 'img-wrapper') return;
                    
                    // Create wrapper
                    const wrapper = document.createElement('div');
                    wrapper.className = 'img-wrapper';
                    wrapper.style.position = 'relative';
                    wrapper.style.display = 'inline-block';
                    wrapper.style.margin = '2px';
                    wrapper.contentEditable = 'false'; // Make the wrapper not editable
                    
                    // Replace the image with the wrapper containing the image
                    img.parentNode.insertBefore(wrapper, img);
                    wrapper.appendChild(img);
                    
                    // Add click event to make the image active
                    wrapper.addEventListener('click', activateImageHandles);
                });
            }

            // Activate handles for a specific image wrapper
            function activateImageHandles(event) {
                // Prevent default behavior
                event.preventDefault();
                event.stopPropagation();
                
                // Remove handles from all other images first
                removeAllImageHandles();
                
                // Get the wrapper (this could be the wrapper itself or an image inside it)
                let wrapper = this;
                if (this.tagName === 'IMG') {
                    wrapper = this.parentNode;
                }
                
                // Add active class
                wrapper.classList.add('img-wrapper-active');
                
                // Create drag handle (square at top-left)
                const dragHandle = document.createElement('div');
                dragHandle.className = 'img-drag-handle';
                dragHandle.style.position = 'absolute';
                dragHandle.style.top = '0';
                dragHandle.style.left = '0';
                dragHandle.style.width = '10px';
                dragHandle.style.height = '10px';
                dragHandle.style.background = '#1e90ff';
                dragHandle.style.border = '1px solid white';
                dragHandle.style.cursor = 'move';
                dragHandle.style.zIndex = '1000';
                dragHandle.contentEditable = 'false'; // Make handle not editable
                
                // Create resize handle (triangle at bottom-right)
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'img-resize-handle';
                resizeHandle.style.position = 'absolute';
                resizeHandle.style.bottom = '0';
                resizeHandle.style.right = '0';
                resizeHandle.style.width = '0';
                resizeHandle.style.height = '0';
                resizeHandle.style.borderStyle = 'solid';
                resizeHandle.style.borderWidth = '0 0 10px 10px';
                resizeHandle.style.borderColor = 'transparent transparent #1e90ff transparent';
                resizeHandle.style.cursor = 'nwse-resize';
                resizeHandle.style.zIndex = '1000';
                resizeHandle.contentEditable = 'false'; // Make handle not editable
                
                // Add handles to the wrapper
                wrapper.appendChild(dragHandle);
                wrapper.appendChild(resizeHandle);
                
                // Get the image inside the wrapper
                const img = wrapper.querySelector('img');
                
                // Setup drag functionality
                let startX, startY, startLeft, startTop;
                
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Get initial positions
                    startX = e.clientX;
                    startY = e.clientY;
                    startLeft = wrapper.offsetLeft;
                    startTop = wrapper.offsetTop;
                    
                    // Add mousemove and mouseup events to document
                    document.addEventListener('mousemove', dragMove);
                    document.addEventListener('mouseup', dragEnd);
                });
                
                function dragMove(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Calculate new position
                    const dx = e.clientX - startX;
                    const dy = e.clientY - startY;
                    
                    // Update wrapper position
                    wrapper.style.position = 'relative';
                    wrapper.style.left = (startLeft + dx) + 'px';
                    wrapper.style.top = (startTop + dy) + 'px';
                    
                    // Notify content changed
                    try {
                        window.webkit.messageHandlers.contentChanged.postMessage("changed");
                    } catch(e) {
                        console.log("Could not notify about changes:", e);
                    }
                }
                
                function dragEnd(e) {
                    if (e) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    
                    // Remove event listeners
                    document.removeEventListener('mousemove', dragMove);
                    document.removeEventListener('mouseup', dragEnd);
                }
                
                // Setup resize functionality
                let startWidth, startHeight, aspectRatio;
                
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Get initial sizes
                    startX = e.clientX;
                    startY = e.clientY;
                    startWidth = img.offsetWidth;
                    startHeight = img.offsetHeight;
                    aspectRatio = startWidth / startHeight;
                    
                    // Add mousemove and mouseup events to document
                    document.addEventListener('mousemove', resizeMove);
                    document.addEventListener('mouseup', resizeEnd);
                });
                
                function resizeMove(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Calculate new dimensions
                    const dx = e.clientX - startX;
                    const dy = e.clientY - startY;
                    
                    // Determine which dimension to prioritize based on the greater change
                    if (Math.abs(dx) > Math.abs(dy)) {
                        // Prioritize width
                        const newWidth = Math.max(10, startWidth + dx);
                        img.width = newWidth;
                        img.height = newWidth / aspectRatio;
                    } else {
                        // Prioritize height
                        const newHeight = Math.max(10, startHeight + dy);
                        img.height = newHeight;
                        img.width = newHeight * aspectRatio;
                    }
                    
                    // Notify content changed
                    try {
                        window.webkit.messageHandlers.contentChanged.postMessage("changed");
                    } catch(e) {
                        console.log("Could not notify about changes:", e);
                    }
                }
                
                function resizeEnd(e) {
                    if (e) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    
                    // Remove event listeners
                    document.removeEventListener('mousemove', resizeMove);
                    document.removeEventListener('mouseup', resizeEnd);
                    
                    // Notify that image properties changed
                    try {
                        window.webkit.messageHandlers.imagePropertiesChanged.postMessage({
                            width: img.width,
                            height: img.height
                        });
                    } catch(e) {
                        console.log("Could not notify about image properties change:", e);
                    }
                }
                
                // When the image is clicked, notify that it was selected
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

            // Remove all image handles
            function removeAllImageHandles() {
                // Remove active class from all wrappers
                document.querySelectorAll('.img-wrapper-active').forEach(wrapper => {
                    wrapper.classList.remove('img-wrapper-active');
                });
                
                // Remove all drag handles
                document.querySelectorAll('.img-drag-handle').forEach(handle => {
                    handle.remove();
                });
                
                // Remove all resize handles
                document.querySelectorAll('.img-resize-handle').forEach(handle => {
                    handle.remove();
                });
            }

            // Document click handler to deselect all images when clicking elsewhere
            document.addEventListener('click', function(e) {
                // If the click is not on an image or wrapper, remove all handles
                if (!e.target.closest('.img-wrapper') && e.target.tagName !== 'IMG') {
                    removeAllImageHandles();
                }
            });

            // Fix for cursor position issues near images
            document.addEventListener('keydown', function(e) {
                // If we're typing and there's an active image, deactivate it
                if (e.key.length === 1 || e.key === 'Delete' || e.key === 'Backspace') {
                    removeAllImageHandles();
                }
            });

            // Block editing of non-editable elements
            document.addEventListener('beforeinput', function(e) {
                // Check if event target is inside a non-editable area
                let node = e.target;
                while (node && node !== document.body) {
                    if (node.contentEditable === 'false') {
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                    }
                    node = node.parentNode;
                }
            }, true);

            // Prevent cursor from being placed inside non-editable elements
            document.addEventListener('mouseup', function(e) {
                const selection = window.getSelection();
                if (!selection.rangeCount) return;
                
                const range = selection.getRangeAt(0);
                let node = range.startContainer;
                
                // Check if the selection is within a non-editable element
                while (node && node !== document.body) {
                    if (node.contentEditable === 'false') {
                        // If inside a non-editable element, move cursor after it
                        const newRange = document.createRange();
                        newRange.setStartAfter(findOutermostNonEditable(node));
                        newRange.collapse(true);
                        selection.removeAllRanges();
                        selection.addRange(newRange);
                        break;
                    }
                    node = node.parentNode;
                }
            });

            // Helper to find the outermost non-editable parent
            function findOutermostNonEditable(node) {
                let result = node;
                let parent = node.parentNode;
                
                while (parent && parent !== document.body && parent.contentEditable === 'false') {
                    result = parent;
                    parent = parent.parentNode;
                }
                
                return result;
            }
        """

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
                
                /* Image wrapper and handle styles */
                .img-wrapper {{
                    position: relative;
                    display: inline-block;
                    margin: 2px;
                    box-sizing: border-box;
                    user-select: none;
                    -webkit-user-select: none;
                    -moz-user-select: none;
                    -ms-user-select: none;
                }}

                .img-wrapper-active {{
                    outline: 2px solid #1e90ff;
                    outline-offset: 2px;
                    z-index: 100;
                }}

                .img-wrapper img {{
                    display: block;
                    max-width: 100%;
                    user-select: none;
                    -webkit-user-select: none;
                }}

                .img-drag-handle {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 10px;
                    height: 10px;
                    background-color: #1e90ff;
                    border: 1px solid white;
                    cursor: move;
                    z-index: 1000;
                    pointer-events: auto;
                    user-select: none;
                    -webkit-user-select: none;
                }}

                .img-resize-handle {{
                    position: absolute;
                    bottom: 0;
                    right: 0;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    border-width: 0 0 10px 10px;
                    border-color: transparent transparent #1e90ff transparent;
                    cursor: nwse-resize;
                    z-index: 1000;
                    pointer-events: auto;
                    user-select: none;
                    -webkit-user-select: none;
                }}
                
                /* This ensures the wrapper DIV doesn't get affected by text editing */
                #editor [contenteditable="false"] {{
                    -webkit-user-modify: read-only;
                    -moz-user-modify: read-only;
                    user-modify: read-only;
                    cursor: default;
                }}

                /* Ensure proper cursor behavior */
                #editor [contenteditable="false"] img {{
                    cursor: pointer;
                }}

                #editor [contenteditable="false"] .img-drag-handle {{
                    cursor: move;
                }}

                #editor [contenteditable="false"] .img-resize-handle {{
                    cursor: nwse-resize;
                }}

                #editor ::selection {{
                    background-color: #264f78;
                    color: inherit;
                }}
                
                @media (prefers-color-scheme: dark) {{
                    html, body {{
                        background-color: #1e1e1e;
                        color: #d4d4d4;
                    }}
                    .img-wrapper-active {{
                        outline-color: #3a8eff;
                    }}
                    .img-drag-handle {{
                        background-color: #3a8eff;
                        border-color: #222;
                    }}
                    .img-resize-handle {{
                        border-color: transparent transparent #3a8eff transparent;
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

    def _show_image_properties_dialog(self, win, file_path=None, img_props=None):
        """Show dialog to set image properties
        
        Args:
            win: Parent window
            file_path: Path to image file (for new images)
            img_props: Image properties dict (for editing existing images)
        """
        # Create dialog
        dialog = Adw.Window()
        dialog.set_title("Image Properties")
        dialog.set_transient_for(win)
        dialog.set_modal(True)
        dialog.set_default_size(400, 320)
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        
        # Variables to store original dimensions for aspect ratio
        original_width = 0
        original_height = 0
        aspect_ratio = 1.0
        
        # Create preview (optional - for small images)
        try:
            if file_path:
                # Load image for preview from file
                texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(file_path))
                picture = Gtk.Picture.new_for_file(Gio.File.new_for_path(file_path))
                
                # Get dimensions
                original_width = texture.get_width()
                original_height = texture.get_height()
            elif img_props and 'src' in img_props and img_props['src'].startswith('data:'):
                # This is a placeholder for when you want to edit an existing image
                # In a full implementation, you would need to create a temporary file
                # from the data URL and load it
                
                # For now, just show a placeholder
                picture = Gtk.Picture()
                picture.set_size_request(150, 100)
                
                # Set dimensions if available in img_props
                if 'width' in img_props and img_props['width']:
                    original_width = int(img_props['width'])
                if 'height' in img_props and img_props['height']:
                    original_height = int(img_props['height'])
            else:
                # Fallback
                raise Exception("No image source provided")
            
            # Calculate aspect ratio
            if original_width > 0 and original_height > 0:
                aspect_ratio = original_width / original_height
            
            # Scale down if too large
            if original_width > 300 or original_height > 200:
                scale = min(300 / original_width, 200 / original_height)
                picture.set_size_request(int(original_width * scale), int(original_height * scale))
            else:
                picture.set_size_request(original_width, original_height)
            
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
        if img_props and 'alt' in img_props:
            alt_entry.set_text(img_props['alt'])
        content_box.append(alt_entry)
        
        # Size options with aspect ratio lock
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)
        size_box.append(width_label)
        
        width_entry = Gtk.SpinButton.new_with_range(1, 2000, 1)
        width_entry.set_hexpand(True)
        if img_props and 'width' in img_props and img_props['width']:
            width_entry.set_value(int(img_props['width']))
        elif original_width > 0:
            width_entry.set_value(original_width)
        size_box.append(width_entry)
        
        height_label = Gtk.Label(label="Height:")
        height_label.set_halign(Gtk.Align.START)
        size_box.append(height_label)
        
        height_entry = Gtk.SpinButton.new_with_range(1, 2000, 1)
        height_entry.set_hexpand(True)
        if img_props and 'height' in img_props and img_props['height']:
            height_entry.set_value(int(img_props['height']))
        elif original_height > 0:
            height_entry.set_value(original_height)
        size_box.append(height_entry)
        
        content_box.append(size_box)
        
        # Lock aspect ratio checkbox
        lock_aspect_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        aspect_check = Gtk.CheckButton()
        aspect_check.set_label("Lock aspect ratio")
        aspect_check.set_active(True)  # Default to locked
        lock_aspect_box.append(aspect_check)
        
        content_box.append(lock_aspect_box)
        
        # Connect signals for width/height with aspect ratio
        width_handler_id = width_entry.connect("value-changed", lambda w: update_height() if aspect_check.get_active() else None)
        height_handler_id = height_entry.connect("value-changed", lambda h: update_width() if aspect_check.get_active() else None)
        
        # Functions to maintain aspect ratio
        def update_height():
            if aspect_ratio > 0:
                # Temporarily block the height signal to prevent recursion
                with height_entry.handler_block(height_handler_id):
                    new_height = width_entry.get_value() / aspect_ratio
                    height_entry.set_value(round(new_height))
        
        def update_width():
            if aspect_ratio > 0:
                # Temporarily block the width signal to prevent recursion
                with width_entry.handler_block(width_handler_id):
                    new_width = height_entry.get_value() * aspect_ratio
                    width_entry.set_value(round(new_width))
        
        # Add buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.destroy())
        button_box.append(cancel_button)
        
        if img_props:
            # For editing existing images
            apply_button = Gtk.Button(label="Apply")
            apply_button.add_css_class("suggested-action")
            apply_button.connect("clicked", lambda btn: self._update_existing_image(
                win,
                img_props,
                alt_entry.get_text(),
                int(width_entry.get_value()),
                int(height_entry.get_value()),
                dialog
            ))
            button_box.append(apply_button)
        else:
            # For inserting new images
            insert_button = Gtk.Button(label="Insert")
            insert_button.add_css_class("suggested-action")
            insert_button.connect("clicked", lambda btn: self._insert_image_to_editor(
                win, 
                file_path, 
                alt_entry.get_text(), 
                int(width_entry.get_value()), 
                int(height_entry.get_value()), 
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

    def _update_existing_image(self, win, img_props, alt_text, width, height, dialog):
        """Update an existing image in the editor"""
        try:
            # Create JavaScript to update the image
            js_code = f"""
            (function() {{
                // Get the currently selected image
                const activeWrapper = document.querySelector('.img-wrapper-active');
                if (!activeWrapper) return false;
                
                const img = activeWrapper.querySelector('img');
                if (!img) return false;
                
                // Update properties
                img.alt = "{alt_text}";
                img.width = {width};
                img.height = {height};
                
                // Remove handles to force a refresh
                removeAllImageHandles();
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                }} catch(e) {{
                    console.log("Could not notify about changes:", e);
                }}
                
                return true;
            }})();
            """
            
            # Execute the JavaScript
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            
            # Close the dialog
            dialog.destroy()
            
            # Update status
            win.statusbar.set_text("Image updated")
            
        except Exception as e:
            print(f"Error updating image: {e}")
            # Show error message
            error_dialog = Adw.MessageDialog(
                transient_for=win,
                title="Error",
                body=f"Could not update the image: {e}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def on_image_clicked(self, win, manager, message):
        """Handle when an image is clicked in the editor"""
        try:
            # Extract image properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties
            import json
            img_props = json.loads(properties)
            
            # Show image properties dialog for editing
            self._show_image_properties_dialog(win, None, img_props)
            
            # Update status
            win.statusbar.set_text("Image selected")
            
        except Exception as e:
            print(f"Error handling image click: {e}")

    def on_image_properties_changed(self, win, manager, message):
        """Handle image properties changed event"""
        try:
            # Extract properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties
            import json
            props = json.loads(properties)
            
            # Update status bar with new dimensions
            if 'width' in props and 'height' in props:
                win.statusbar.set_text(f"Image resized to {props['width']}×{props['height']}")
            
        except Exception as e:
            print(f"Error handling image properties change: {e}")

#######
    def load_image_for_editor(self, win, file_path):
        """Convert local file path to a URI that WebKit can access"""
        try:
            # Check if it's already a URL
            if file_path.startswith(('http://', 'https://')):
                return file_path
                    
            # Handle file:// URLs
            if file_path.startswith('file://'):
                return file_path
                    
            # Check if the file exists
            if os.path.exists(file_path):
                try:
                    # Get absolute path first
                    abs_path = os.path.abspath(file_path)
                    
                    # Use GLib to convert to URI with proper encoding
                    file_url = GLib.filename_to_uri(abs_path, None)
                    
                    print(f"Image URI created: {file_url}")
                    return file_url
                except Exception as e:
                    print(f"Error creating file URI: {e}")
                    
                    # More robust fallback with encoding
                    import urllib.parse
                    abs_path = os.path.abspath(file_path)
                    # Ensure the path is properly encoded
                    path_encoded = urllib.parse.quote(abs_path)
                    file_url = f"file://{path_encoded}"
                    print(f"Fallback image URI created: {file_url}")
                    return file_url
            else:
                print(f"File not found: {file_path}")
                win.statusbar.set_text(f"Error: File not found: {file_path}")
                return None
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

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



            
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
