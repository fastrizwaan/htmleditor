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
    # First, let's implement the JavaScript for image handling with resize handles and activation

    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return f"""
        {self.image_theme_helpers_js()}
        {self.image_handles_css_js()}
        {self.image_insert_functions_js()}
        {self.image_activation_js()}
        {self.image_drag_resize_js()}
        {self.image_alignment_js()}
        {self.image_floating_js()}
        {self.image_border_style_js()}
        {self.image_event_handlers_js()}
        """

    def image_theme_helpers_js(self):
        """JavaScript helper functions for theme detection and colors"""
        return """
        // Function to get appropriate border color based on current theme for images
        function getImageBorderColor() {
            return isDarkMode() ? '#444' : '#ccc';
        }
        """

    def image_handles_css_js(self):
        """JavaScript that defines CSS for image handles with proper display properties"""
        return """
        // CSS for image handles
        const imageHandlesCSS = `
        /* Image drag handle - positioned in the top-left corner */
        .image-drag-handle {
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

        /* Image resize handle - triangular shape in bottom right */
        .image-resize-handle {
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
        
        /* Floating image styles */
        .floating-image {
            position: absolute !important;
            z-index: 50;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            cursor: grab;
        }
        
        .floating-image:active {
            cursor: grabbing;
        }
        
        .floating-image .image-drag-handle {
            width: 20px !important;
            height: 20px !important;
            border-radius: 3px;
            opacity: 0.9;
        }
        
        .floating-image:focus {
            outline: 2px solid #4e9eff;
        }
        
        .image-selected {
            outline: 2px solid #4e9eff;
            outline-offset: 2px;
            position: relative;
        }

        @media (prefers-color-scheme: dark) {
            .image-drag-handle {
                background-color: #0078d7;
            }
            .image-resize-handle {
                border-color: transparent transparent #0078d7 transparent;
            }
            .floating-image {
                box-shadow: 0 3px 10px rgba(0,0,0,0.5);
            }
            .floating-image .image-drag-handle {
                background-color: #0078d7;
            }
            .image-selected {
                outline-color: #0078d7;
            }
        }`;
        
        // Function to add the image handle styles to the document
        function addImageHandleStyles() {
            // Check if our style element already exists
            let styleElement = document.getElementById('image-handle-styles');
            
            // If not, create and append it
            if (!styleElement) {
                styleElement = document.createElement('style');
                styleElement.id = 'image-handle-styles';
                styleElement.textContent = imageHandlesCSS;
                document.head.appendChild(styleElement);
            } else {
                // If it exists, update the content
                styleElement.textContent = imageHandlesCSS;
            }
        }
        """

    def image_insert_functions_js(self):
        """JavaScript for inserting images with default properties"""
        return """
        // Function to insert an image at the current cursor position
        function insertImage(src, alt, width, height, isFloating) {
            // Create a new image element
            let imageWrapper = document.createElement('span');
            imageWrapper.className = 'editor-image-wrapper';
            imageWrapper.style.display = 'inline-block';
            imageWrapper.style.position = 'relative';
            imageWrapper.style.margin = '6px 6px 0 0';
            
            // Store margin values as attributes for later reference
            imageWrapper.setAttribute('data-margin-top', '6');
            imageWrapper.setAttribute('data-margin-right', '6');
            imageWrapper.setAttribute('data-margin-bottom', '0');
            imageWrapper.setAttribute('data-margin-left', '0');
            
            let img = document.createElement('img');
            
            // Set attributes
            img.src = src;
            img.alt = alt || '';
            
            // Set size if provided
            if (width) {
                img.width = width;
                img.setAttribute('data-original-width', width);
            }
            if (height) {
                img.height = height;
                img.setAttribute('data-original-height', height);
            }
            
            // Store original dimensions for resizing proportionally
            if (!img.hasAttribute('data-original-width') && img.width) {
                img.setAttribute('data-original-width', img.width);
            }
            if (!img.hasAttribute('data-original-height') && img.height) {
                img.setAttribute('data-original-height', img.height);
            }
            
            // Add the image to the wrapper
            imageWrapper.appendChild(img);
            
            // Make the wrapper floating if requested
            if (isFloating) {
                imageWrapper.classList.add('floating-image');
                setImageFloating(imageWrapper);
            }
            
            // Insert the wrapper at current selection
            document.execCommand('insertHTML', false, imageWrapper.outerHTML);
            
            // Find and activate the newly inserted image wrapper
            setTimeout(() => {
                const wrappers = document.querySelectorAll('.editor-image-wrapper');
                const newWrapper = wrappers[wrappers.length - 1];
                if (newWrapper) {
                    activateImage(newWrapper);
                    try {
                        window.webkit.messageHandlers.imageClicked.postMessage({
                            src: src,
                            alt: alt || '',
                            width: width || '',
                            height: height || ''
                        });
                    } catch(e) {
                        console.log("Could not notify about image click:", e);
                    }
                }
            }, 10);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage("changed");
            } catch(e) {
                console.log("Could not notify about changes:", e);
            }
        }
        """

    def image_activation_js(self):
        """JavaScript for image activation and deactivation"""
        return """
        // Variables for image handling
        var activeImage = null;
        var isImageDragging = false;
        var isImageResizing = false;
        var imageDragStartX = 0;
        var imageDragStartY = 0;
        var imageStartX = 0;
        var imageStartY = 0;
        var imageStartWidth = 0;
        var imageStartHeight = 0;
        
        // Function to find parent image element
        function findParentImage(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'IMG' || 
                    (element.classList && element.classList.contains('editor-image-wrapper'))) {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Function to activate an image (add handles)
        function activateImage(imageElement) {
            if (activeImage === imageElement) return; // Already active
            
            // Deactivate any previously active images
            if (activeImage && activeImage !== imageElement) {
                deactivateImage(activeImage);
            }
            
            // If we got an IMG element, use its parent wrapper if available
            if (imageElement.tagName === 'IMG' && 
                imageElement.parentNode && 
                imageElement.parentNode.classList && 
                imageElement.parentNode.classList.contains('editor-image-wrapper')) {
                imageElement = imageElement.parentNode;
            }
            
            // If we still have an IMG without wrapper, wrap it
            if (imageElement.tagName === 'IMG') {
                const wrapper = document.createElement('span');
                wrapper.className = 'editor-image-wrapper';
                wrapper.style.display = 'inline-block';
                wrapper.style.position = 'relative';
                
                // Insert wrapper before the image
                imageElement.parentNode.insertBefore(wrapper, imageElement);
                // Move the image into the wrapper
                wrapper.appendChild(imageElement);
                
                // Use the wrapper as our active element
                imageElement = wrapper;
            }
            
            activeImage = imageElement;
            
            // Add selected class
            activeImage.classList.add('image-selected');
            
            // Ensure the wrapper has editor-image-wrapper class
            if (!activeImage.classList.contains('editor-image-wrapper')) {
                activeImage.classList.add('editor-image-wrapper');
            }
            
            // Ensure the wrapper has position: relative for proper handle positioning (if not floating)
            if (!activeImage.classList.contains('floating-image')) {
                activeImage.style.position = 'relative';
            }
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return;
            
            // Store original dimensions if not already stored
            if (!imgElement.hasAttribute('data-original-width') && imgElement.width) {
                imgElement.setAttribute('data-original-width', imgElement.width);
            }
            if (!imgElement.hasAttribute('data-original-height') && imgElement.height) {
                imgElement.setAttribute('data-original-height', imgElement.height);
            }
            
            // Add resize handle if needed
            if (!activeImage.querySelector('.image-resize-handle')) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'image-resize-handle';
                
                // Make handle non-selectable and prevent focus
                resizeHandle.setAttribute('contenteditable', 'false');
                resizeHandle.setAttribute('unselectable', 'on');
                resizeHandle.setAttribute('tabindex', '-1');
                
                // Add event listener
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startImageResize(e, imageElement);
                }, true);
                
                activeImage.appendChild(resizeHandle);
            }
            
            // Add drag handle if needed
            if (!activeImage.querySelector('.image-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'image-drag-handle';
                dragHandle.innerHTML = '↕';
                
                // Set title based on whether it's a floating image or not
                if (activeImage.classList.contains('floating-image')) {
                    dragHandle.title = 'Drag to move image freely';
                } else {
                    dragHandle.title = 'Drag to reposition image between paragraphs';
                }
                
                // Make handle non-selectable and prevent focus
                dragHandle.setAttribute('contenteditable', 'false');
                dragHandle.setAttribute('unselectable', 'on');
                dragHandle.setAttribute('tabindex', '-1');
                
                // Add event listener
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startImageDrag(e, imageElement);
                }, true);
                
                activeImage.appendChild(dragHandle);
            }
            
            // Special styling for floating images
            if (activeImage.classList.contains('floating-image')) {
                enhanceImageDragHandles(activeImage);
            }
        }
        
        // Function to deactivate a specific image
        function deactivateImage(imageElement) {
            if (!imageElement) return;
            
            // Remove selected class
            imageElement.classList.remove('image-selected');
            
            // Remove handles
            const resizeHandle = imageElement.querySelector('.image-resize-handle');
            if (resizeHandle) resizeHandle.remove();
            
            const dragHandle = imageElement.querySelector('.image-drag-handle');
            if (dragHandle) dragHandle.remove();
            
            if (imageElement === activeImage) {
                activeImage = null;
            }
        }
        
        // Function to deactivate all images
        function deactivateAllImages() {
            const images = document.querySelectorAll('.editor-image-wrapper');
            
            images.forEach(image => {
                deactivateImage(image);
            });
            
            // Always notify that images are deactivated
            activeImage = null;
            try {
                window.webkit.messageHandlers.imagesDeactivated.postMessage('images-deactivated');
            } catch(e) {
                console.log("Could not notify about image deactivation:", e);
            }
        }
        """

    def image_drag_resize_js(self):
        """JavaScript for image dragging and resizing"""
        return """
        // Function to start image drag
        function startImageDrag(e, imageElement) {
            e.preventDefault();
            if (!imageElement) return;
            
            isImageDragging = true;
            activeImage = imageElement;
            imageDragStartX = e.clientX;
            imageDragStartY = e.clientY;
            
            // Set cursor based on whether the image is floating or not
            if (imageElement.classList.contains('floating-image')) {
                document.body.style.cursor = 'grabbing';
                
                // Store the initial position for floating images
                const style = window.getComputedStyle(imageElement);
                imageStartX = parseInt(style.left) || 0;
                imageStartY = parseInt(style.top) || 0;
            } else {
                document.body.style.cursor = 'move';
            }
        }
        
        // Function to move image
        function moveImage(e) {
            if (!isImageDragging || !activeImage) return;
            
            // Check if the image is a floating image
            if (activeImage.classList.contains('floating-image')) {
                // For floating images, move to the mouse position with offset
                const deltaX = e.clientX - imageDragStartX;
                const deltaY = e.clientY - imageDragStartY;
                
                // Update position
                activeImage.style.left = `${imageStartX + deltaX}px`;
                activeImage.style.top = `${imageStartY + deltaY}px`;
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            } else {
                const currentY = e.clientY;
                const deltaY = currentY - imageDragStartY;
                
                if (Math.abs(deltaY) > 30) {
                    const editor = document.getElementById('editor');
                    const blocks = Array.from(editor.children).filter(node => {
                        const style = window.getComputedStyle(node);
                        return style.display.includes('block') || node.tagName === 'TABLE' || 
                               node.classList.contains('editor-image-wrapper');
                    });
                    
                    const imageIndex = blocks.indexOf(activeImage);
                    
                    if (deltaY < 0 && imageIndex > 0) {
                        const targetElement = blocks[imageIndex - 1];
                        editor.insertBefore(activeImage, targetElement);
                        imageDragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    } 
                    else if (deltaY > 0 && imageIndex < blocks.length - 1) {
                        const targetElement = blocks[imageIndex + 1];
                        if (targetElement.nextSibling) {
                            editor.insertBefore(activeImage, targetElement.nextSibling);
                        } else {
                            editor.appendChild(activeImage);
                        }
                        imageDragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            }
        }
        
        // Function to start image resize
        function startImageResize(e, imageElement) {
            e.preventDefault();
            isImageResizing = true;
            activeImage = imageElement;
            imageDragStartX = e.clientX;
            imageDragStartY = e.clientY;
            
            // Find the actual IMG element
            const imgElement = imageElement.querySelector('img');
            if (!imgElement) return;
            
            // Store initial size
            imageStartWidth = imgElement.width || imgElement.offsetWidth;
            imageStartHeight = imgElement.height || imgElement.offsetHeight;
        }
        
        // Function to resize image
        function resizeImage(e) {
            if (!isImageResizing || !activeImage) return;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return;
            
            const deltaX = e.clientX - imageDragStartX;
            const deltaY = e.clientY - imageDragStartY;
            
            // Get original aspect ratio if stored
            let originalWidth = parseInt(imgElement.getAttribute('data-original-width'));
            let originalHeight = parseInt(imgElement.getAttribute('data-original-height'));
            let aspectRatio = originalWidth && originalHeight ? originalWidth / originalHeight : imageStartWidth / imageStartHeight;
            
            // Calculate new dimensions
            let newWidth = Math.max(20, imageStartWidth + deltaX);
            let newHeight = Math.round(newWidth / aspectRatio);
            
            // Apply new dimensions
            imgElement.width = newWidth;
            imgElement.height = newHeight;
            
            // Notify that the image has been resized
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """

    def image_alignment_js(self):
        """JavaScript for image alignment"""
        return """
        // Function to set image alignment
        function setImageAlignment(alignClass) {
            if (!activeImage) return;
            
            // Remove all alignment classes
            activeImage.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap', 'floating-image');
            
            // Add the requested alignment class
            activeImage.classList.add(alignClass);
            
            // Reset positioning if it was previously floating
            if (activeImage.style.position === 'absolute') {
                activeImage.style.position = 'relative';
                activeImage.style.top = '';
                activeImage.style.left = '';
                activeImage.style.zIndex = '';
            }
            
            // Update image display style based on alignment
            if (alignClass === 'left-align') {
                activeImage.style.display = 'inline-block';
                activeImage.style.float = 'left';
                activeImage.style.marginRight = '10px';
            } else if (alignClass === 'right-align') {
                activeImage.style.display = 'inline-block';
                activeImage.style.float = 'right';
                activeImage.style.marginLeft = '10px';
            } else if (alignClass === 'center-align') {
                activeImage.style.display = 'block';
                activeImage.style.float = 'none';
                activeImage.style.marginLeft = 'auto';
                activeImage.style.marginRight = 'auto';
            } else if (alignClass === 'no-wrap') {
                activeImage.style.display = 'block';
                activeImage.style.float = 'none';
                activeImage.style.marginLeft = '0';
                activeImage.style.marginRight = '0';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """
        
    def image_floating_js(self):
        """JavaScript for floating image functionality"""
        return """
        // Function to make an image floating (freely positionable)
        function setImageFloating(imageElement) {
            if (!imageElement && activeImage) {
                imageElement = activeImage;
            }
            
            if (!imageElement) return;
            
            // First, remove any alignment classes
            imageElement.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            
            // Reset any float styles
            imageElement.style.float = 'none';
            
            // Add floating class for special styling
            imageElement.classList.add('floating-image');
            
            // Set positioning to absolute
            imageElement.style.position = 'absolute';
            
            // Calculate initial position - center in the visible editor area
            const editorRect = document.getElementById('editor').getBoundingClientRect();
            const imageRect = imageElement.getBoundingClientRect();
            
            // Set initial position
            const editorScrollTop = document.getElementById('editor').scrollTop;
            
            // Position in the middle of the visible editor area
            const topPos = (editorRect.height / 2) - (imageRect.height / 2) + editorScrollTop;
            const leftPos = (editorRect.width / 2) - (imageRect.width / 2);
            
            imageElement.style.top = `${Math.max(topPos, editorScrollTop)}px`;
            imageElement.style.left = `${Math.max(leftPos, 0)}px`;
            
            // Enhance the drag handle for position control
            enhanceImageDragHandles(imageElement);
            
            // Ensure proper z-index to be above regular content
            imageElement.style.zIndex = "50";
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            // Activate the image to show handles
            if (imageElement !== activeImage) {
                activateImage(imageElement);
            }
        }
        
        // Add enhanced drag handling for floating images
        function enhanceImageDragHandles(imageElement) {
            if (!imageElement) return;
            
            // Find or create the drag handle
            let dragHandle = imageElement.querySelector('.image-drag-handle');
            if (!dragHandle) {
                // If it doesn't exist, we might need to activate the image first
                activateImage(imageElement);
                dragHandle = imageElement.querySelector('.image-drag-handle');
            }
            
            if (dragHandle) {
                // Update tooltip to reflect new functionality
                dragHandle.title = "Drag to move image freely";
                
                // Make the drag handle more visible for floating images
                dragHandle.style.width = "20px";
                dragHandle.style.height = "20px";
                dragHandle.style.backgroundColor = "#4e9eff";
                dragHandle.style.borderRadius = "3px";
                dragHandle.style.opacity = "0.9";
            }
        }
"""

    def image_border_style_js(self):
        """JavaScript for image border styling"""
        return """
        // Function to set image border style
        function setImageBorderStyle(style, width, color) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            // Get current values
            let currentStyle = imgElement.getAttribute('data-border-style');
            let currentWidth = imgElement.getAttribute('data-border-width');
            let currentColor = imgElement.getAttribute('data-border-color');
            
            // If attributes don't exist, try to get from computed style
            if (!currentStyle || !currentWidth || !currentColor) {
                const computedStyle = window.getComputedStyle(imgElement);
                
                // Try to get current style from computed style
                currentStyle = currentStyle || imgElement.style.borderStyle || computedStyle.borderStyle || 'solid';
                
                // Get current width
                if (!currentWidth) {
                    currentWidth = parseInt(imgElement.style.borderWidth) || 
                                  parseInt(computedStyle.borderWidth) || 0;
                }
                
                // Get current color
                currentColor = currentColor || imgElement.style.borderColor || 
                              computedStyle.borderColor || getImageBorderColor();
            }
            
            // Use provided values or fall back to current/default values
            const newStyle = (style !== null && style !== undefined && style !== '') ? style : currentStyle;
            const newWidth = (width !== null && width !== undefined && width !== '') ? width : currentWidth;
            const newColor = (color !== null && color !== undefined && color !== '') ? color : currentColor;
            
            // Apply the border
            if (newWidth > 0) {
                imgElement.style.border = `${newWidth}px ${newStyle} ${newColor}`;
            } else {
                imgElement.style.border = 'none';
            }
            
            // Store values as attributes
            imgElement.setAttribute('data-border-style', newStyle);
            imgElement.setAttribute('data-border-width', newWidth);
            imgElement.setAttribute('data-border-color', newColor);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set image border color
        function setImageBorderColor(color) {
            return setImageBorderStyle(null, null, color);
        }
        
        // Function to set image border width
        function setImageBorderWidth(width) {
            return setImageBorderStyle(null, width, null);
        }
        
        // Function to get current image border style
        function getImageBorderStyle() {
            if (!activeImage) return null;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return null;
            
            // First try to get from stored data attributes
            const storedStyle = imgElement.getAttribute('data-border-style');
            const storedWidth = imgElement.getAttribute('data-border-width');
            const storedColor = imgElement.getAttribute('data-border-color');
            
            if (storedStyle && storedWidth && storedColor) {
                return {
                    style: storedStyle,
                    width: parseInt(storedWidth),
                    color: storedColor
                };
            }
            
            // If not stored, get from computed style
            const computedStyle = window.getComputedStyle(imgElement);
            
            const result = {
                style: imgElement.style.borderStyle || computedStyle.borderStyle || 'solid',
                width: parseInt(imgElement.style.borderWidth) || parseInt(computedStyle.borderWidth) || 0,
                color: imgElement.style.borderColor || computedStyle.borderColor || getImageBorderColor()
            };
            
            // Store these values for future use
            imgElement.setAttribute('data-border-style', result.style);
            imgElement.setAttribute('data-border-width', result.width);
            imgElement.setAttribute('data-border-color', result.color);
            
            return result;
        }
        
        // Function to set image shadow
        function setImageShadow(enabled) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            if (enabled) {
                imgElement.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
            } else {
                imgElement.style.boxShadow = 'none';
            }
            
            // Store shadow state
            imgElement.setAttribute('data-shadow', enabled);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current image properties
        function getImageProperties() {
            if (!activeImage) return null;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return null;
            
            const borderStyle = getImageBorderStyle();
            const shadow = imgElement.getAttribute('data-shadow') === 'true' || 
                          window.getComputedStyle(imgElement).boxShadow !== 'none';
            
            return {
                src: imgElement.src,
                alt: imgElement.alt || '',
                width: imgElement.width || imgElement.offsetWidth,
                height: imgElement.height || imgElement.offsetHeight,
                originalWidth: parseInt(imgElement.getAttribute('data-original-width')) || 0,
                originalHeight: parseInt(imgElement.getAttribute('data-original-height')) || 0,
                border: borderStyle,
                shadow: shadow,
                alignment: getImageAlignment()
            };
        }
        
        // Function to get current image alignment
        function getImageAlignment() {
            if (!activeImage) return 'no-wrap';
            
            if (activeImage.classList.contains('left-align')) return 'left-align';
            if (activeImage.classList.contains('right-align')) return 'right-align';
            if (activeImage.classList.contains('center-align')) return 'center-align';
            if (activeImage.classList.contains('floating-image')) return 'floating-image';
            
            return 'no-wrap';
        }
        
        // Function to set image margins
        function setImageMargins(top, right, bottom, left) {
            if (!activeImage) return false;
            
            // Set margins individually if provided
            if (top !== undefined && top !== null) {
                activeImage.style.marginTop = top + 'px';
            }
            if (right !== undefined && right !== null) {
                activeImage.style.marginRight = right + 'px';
            }
            if (bottom !== undefined && bottom !== null) {
                activeImage.style.marginBottom = bottom + 'px';
            }
            if (left !== undefined && left !== null) {
                activeImage.style.marginLeft = left + 'px';
            }
            
            // Store margin values as attributes for later reference
            activeImage.setAttribute('data-margin-top', parseInt(activeImage.style.marginTop) || 0);
            activeImage.setAttribute('data-margin-right', parseInt(activeImage.style.marginRight) || 0);
            activeImage.setAttribute('data-margin-bottom', parseInt(activeImage.style.marginBottom) || 0);
            activeImage.setAttribute('data-margin-left', parseInt(activeImage.style.marginLeft) || 0);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current image margins
        function getImageMargins() {
            if (!activeImage) return null;
            
            // Try to get from stored attributes first
            const storedTop = activeImage.getAttribute('data-margin-top');
            const storedRight = activeImage.getAttribute('data-margin-right');
            const storedBottom = activeImage.getAttribute('data-margin-bottom');
            const storedLeft = activeImage.getAttribute('data-margin-left');
            
            if (storedTop !== null || storedRight !== null || storedBottom !== null || storedLeft !== null) {
                return {
                    top: parseInt(storedTop) || 0,
                    right: parseInt(storedRight) || 0,
                    bottom: parseInt(storedBottom) || 0,
                    left: parseInt(storedLeft) || 0
                };
            }
            
            // Otherwise get from computed style
            const computedStyle = window.getComputedStyle(activeImage);
            
            return {
                top: parseInt(computedStyle.marginTop) || 0,
                right: parseInt(computedStyle.marginRight) || 0,
                bottom: parseInt(computedStyle.marginBottom) || 0,
                left: parseInt(computedStyle.marginLeft) || 0
            };
        }
        
        // Function to set image color effects (like grayscale, sepia, etc.)
        function setImageColorEffect(effect) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            // Apply the selected effect
            switch (effect) {
                case 'none':
                    imgElement.style.filter = 'none';
                    break;
                case 'grayscale':
                    imgElement.style.filter = 'grayscale(100%)';
                    break;
                case 'sepia':
                    imgElement.style.filter = 'sepia(100%)';
                    break;
                case 'invert':
                    imgElement.style.filter = 'invert(100%)';
                    break;
                case 'brightness':
                    imgElement.style.filter = 'brightness(150%)';
                    break;
                case 'contrast':
                    imgElement.style.filter = 'contrast(150%)';
                    break;
                case 'blur':
                    imgElement.style.filter = 'blur(2px)';
                    break;
                default:
                    imgElement.style.filter = 'none';
            }
            
            // Store the effect
            imgElement.setAttribute('data-color-effect', effect);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current color effect
        function getImageColorEffect() {
            if (!activeImage) return 'none';
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return 'none';
            
            return imgElement.getAttribute('data-color-effect') || 'none';
        }
        
        // Function to apply rounded corners to the image
        function setImageRoundedCorners(radius) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            // Apply the border radius
            imgElement.style.borderRadius = `${radius}px`;
            
            // Store the radius
            imgElement.setAttribute('data-border-radius', radius);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current border radius
        function getImageBorderRadius() {
            if (!activeImage) return 0;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return 0;
            
            const radius = imgElement.getAttribute('data-border-radius');
            return radius ? parseInt(radius) : 0;
        }
        """
########################
    # Now let's implement the image toolbar and event handlers for the HTML Editor

    def on_image_clicked(self, win, manager, message):
        """Handle when an image is clicked in the editor"""
        try:
            # Extract image properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties (this is a simplified version)
            import json
            img_props = json.loads(properties)
            
            # Show the image toolbar
            win.image_toolbar_revealer.set_reveal_child(True)
            
            # Update status
            win.statusbar.set_text("Image selected")
            
            # Update margin controls with current image margins
            js_code = """
            (function() {
                const margins = getImageMargins();
                return win
     JSON.stringify(margins);
            })();
            """
            
            win.webview.evaluate_javascript(
                js_code,
                -1, None, None, None,
                lambda webview, result, data: self._update_image_margin_controls(win, webview, result),
                None
            )
            
        except Exception as e:
            print(f"Error handling image click: {e}")

    def on_image_deleted(self, win, manager, message):
        """Handle image deleted event from editor"""
        win.image_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("Image deleted")

    def on_images_deactivated(self, win, manager, message):
        """Handle event when all images are deactivated"""
        win.image_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("No image selected")

    def _update_image_margin_controls(self, win, webview, result):
        """Update margin controls with current image margins"""
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
                
                if hasattr(win, 'image_margin_controls') and isinstance(margins, dict):
                    for side in ['top', 'right', 'bottom', 'left']:
                        if side in win.image_margin_controls and side in margins:
                            win.image_margin_controls[side].set_value(margins[side])
        except Exception as e:
            print(f"Error updating image margin controls: {e}")

    def on_image_margin_changed(self, win, side, value):
        """Apply margin change to the active image"""
        js_code = f"""
        (function() {{
            // Pass all four sides with the updated value for the specified side
            const margins = getImageMargins() || {{ top: 0, right: 0, bottom: 0, left: 0 }};
            margins.{side} = {value};
            setImageMargins(margins.top, margins.right, margins.bottom, margins.left);
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied {side} margin: {value}px")

    def create_image_toolbar(self, win):
        """Create a toolbar for image editing"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        
        # Image operations label
        image_label = Gtk.Label(label="Image:")
        image_label.set_margin_end(10)
        toolbar.append(image_label)
        
        # Size controls
        size_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        size_group.add_css_class("linked")
        
        # Reset size button
        reset_size_button = Gtk.Button(icon_name="edit-undo-symbolic")
        reset_size_button.set_tooltip_text("Reset to original size")
        reset_size_button.connect("clicked", lambda btn: self.on_reset_image_size_clicked(win))
        size_group.append(reset_size_button)
        
        # Add size group to toolbar
        toolbar.append(size_group)
        
        # Small separator
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator1.set_margin_start(5)
        separator1.set_margin_end(5)
        toolbar.append(separator1)
        
        # Border controls
        border_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Border label
        border_label = Gtk.Label(label="Border:")
        border_label.set_margin_end(5)
        border_group.append(border_label)
        
        # Border width spinner
        border_adjustment = Gtk.Adjustment(value=1, lower=0, upper=10, step_increment=1)
        border_spin = Gtk.SpinButton()
        border_spin.set_tooltip_text("Border width")
        border_spin.set_adjustment(border_adjustment)
        border_spin.connect("value-changed", lambda spin: self.on_image_border_width_changed(win, spin.get_value_as_int()))
        border_group.append(border_spin)
        
        # Border style dropdown
        border_style = Gtk.DropDown()
        border_style.set_tooltip_text("Border style")
        border_styles = Gtk.StringList()
        for style in ["solid", "dashed", "dotted", "double"]:
            border_styles.append(style)
        border_style.set_model(border_styles)
        border_style.set_selected(0)  # Default to solid
        border_style.connect("notify::selected", lambda dd, p: self.on_image_border_style_changed(
            win, border_styles.get_string(dd.get_selected())))
        border_group.append(border_style)
        
        # Add border group to toolbar
        toolbar.append(border_group)
        
        # Separator
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator2.set_margin_start(5)
        separator2.set_margin_end(5)
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
        align_left_button.connect("clicked", lambda btn: self.on_image_align_left(win))
        align_group.append(align_left_button)
        
        # Center alignment
        align_center_button = Gtk.Button(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Center (no text wrap)")
        align_center_button.connect("clicked", lambda btn: self.on_image_align_center(win))
        align_group.append(align_center_button)
        
        # Right alignment
        align_right_button = Gtk.Button(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right (text wraps around left)")
        align_right_button.connect("clicked", lambda btn: self.on_image_align_right(win))
        align_group.append(align_right_button)
        
        # Full width (no wrap)
        full_width_button = Gtk.Button(icon_name="format-justify-fill-symbolic")
        full_width_button.set_tooltip_text("Full Width (no text wrap)")
        full_width_button.connect("clicked", lambda btn: self.on_image_full_width(win))
        align_group.append(full_width_button)
        
        # Add alignment group to toolbar
        toolbar.append(align_group)
        
        # Float button
        float_button = Gtk.Button(icon_name="overlapping-windows-symbolic")
        float_button.set_tooltip_text("Make image float freely in editor")
        float_button.set_margin_start(5)
        float_button.connect("clicked", lambda btn: self.on_image_float_clicked(win))
        toolbar.append(float_button)
        
        # Layer control options (like Z-index)
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator3.set_margin_start(10)
        separator3.set_margin_end(10)
        toolbar.append(separator3)
        
        layer_label = Gtk.Label(label="Layer:")
        layer_label.set_margin_end(5)
        toolbar.append(layer_label)
        
        # Create a group for layer control buttons
        layer_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        layer_group.add_css_class("linked")
        
        # Bring forward button (increase z-index)
        bring_forward_button = Gtk.Button(icon_name="go-up-symbolic")
        bring_forward_button.set_tooltip_text("Bring Forward (place above other elements)")
        bring_forward_button.connect("clicked", lambda btn: self.on_image_bring_forward_clicked(win))
        layer_group.append(bring_forward_button)
        
        # Send backward button (decrease z-index)
        send_backward_button = Gtk.Button(icon_name="go-down-symbolic")
        send_backward_button.set_tooltip_text("Send Backward (place beneath other elements)")
        send_backward_button.connect("clicked", lambda btn: self.on_image_send_backward_clicked(win))
        layer_group.append(send_backward_button)
        
        # Add layer control group to toolbar
        toolbar.append(layer_group)
        
        # Delete button
        separator4 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator4.set_margin_start(10)
        separator4.set_margin_end(10)
        toolbar.append(separator4)
        
        delete_button = Gtk.Button(icon_name="edit-delete-symbolic")
        delete_button.set_tooltip_text("Delete image")
        delete_button.connect("clicked", lambda btn: self.on_delete_image_clicked(win))
        toolbar.append(delete_button)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Close button
        close_button = Gtk.Button(icon_name="window-close-symbolic")
        close_button.set_tooltip_text("Close image toolbar")
        close_button.connect("clicked", lambda btn: self.on_close_image_toolbar_clicked(win))
        toolbar.append(close_button)
        
        return toolbar

    # Image operation methods
    def on_reset_image_size_clicked(self, win):
        """Reset image to its original size"""
        js_code = "resetImageSize();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image reset to original size")

    def on_image_border_width_changed(self, win, width):
        """Change image border width"""
        js_code = f"setImageBorderWidth({width});"
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Image border width: {width}px")

    def on_image_border_style_changed(self, win, style):
        """Change image border style"""
        js_code = f"setImageBorderStyle('{style}', null, null);"
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Image border style: {style}")

    def on_image_align_left(self, win):
        """Align image to the left with text wrapping around right"""
        js_code = "setImageAlignment('left-align');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image aligned left")

    def on_image_align_center(self, win):
        """Align image to the center with no text wrapping"""
        js_code = "setImageAlignment('center-align');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image aligned center")

    def on_image_align_right(self, win):
        """Align image to the right with text wrapping around left"""
        js_code = "setImageAlignment('right-align');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image aligned right")

    def on_image_full_width(self, win):
        """Make image full width with no text wrapping"""
        js_code = "setImageAlignment('no-wrap');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image set to full width")

    def on_image_float_clicked(self, win):
        """Make image float freely in the editor"""
        js_code = "setImageFloating();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image is now floating")

    def on_image_bring_forward_clicked(self, win):
        """Bring the image forward in the z-order"""
        js_code = "bringImageForward();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image brought forward")

    def on_image_send_backward_clicked(self, win):
        """Send the image backward in the z-order"""
        js_code = "sendImageBackward();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image sent backward")

    def on_delete_image_clicked(self, win):
        """Delete the active image"""
        js_code = "deleteImage();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image deleted")

    def on_close_image_toolbar_clicked(self, win):
        """Hide the image toolbar and deactivate images"""
        win.image_toolbar_revealer.set_reveal_child(False)
        js_code = "deactivateAllImages();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image toolbar closed")

    # Now let's add the necessary modifications to the main application
    def create_window(self):
        """Modify the create_window method to include image toolbar"""
        # Create window as before
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
        
        # Create a revealer for the table toolbar
        win.image_toolbar_revealer = Gtk.Revealer()
        win.image_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.image_toolbar_revealer.set_transition_duration(250)
        win.image_toolbar_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create and add the table toolbar
        image_toolbar = self.create_image_toolbar(win)
        win.image_toolbar_revealer.set_child(image_toolbar)
        win.main_box.append(win.image_toolbar_revealer)
        
        # Create a revealer for the image toolbar
        win.image_toolbar_revealer = Gtk.Revealer()
        win.image_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.image_toolbar_revealer.set_transition_duration(250)
        win.image_toolbar_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create and add the image toolbar
        image_toolbar = self.create_image_toolbar(win)
        win.image_toolbar_revealer.set_child(image_toolbar)
        win.main_box.append(win.image_toolbar_revealer)
        
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
            
            # Table-related message handlers
            user_content_manager.register_script_message_handler("tableClicked")
            user_content_manager.register_script_message_handler("tableDeleted")
            user_content_manager.register_script_message_handler("tablesDeactivated")
            
            user_content_manager.connect("script-message-received::tableClicked", 
                                        lambda mgr, res: self.on_table_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::tableDeleted", 
                                        lambda mgr, res: self.on_table_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::tablesDeactivated", 
                                        lambda mgr, res: self.on_tables_deactivated(win, mgr, res))
            
            # Add Image-related message handlers
            user_content_manager.register_script_message_handler("imageClicked")
            user_content_manager.register_script_message_handler("imageDeleted")
            user_content_manager.register_script_message_handler("imagesDeactivated")
            
            user_content_manager.connect("script-message-received::imageClicked", 
                                        lambda mgr, res: self.on_image_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::imageDeleted", 
                                        lambda mgr, res: self.on_image_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::imagesDeactivated", 
                                        lambda mgr, res: self.on_images_deactivated(win, mgr, res))
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
        
        return# First, let's implement the JavaScript for image handling with resize handles and activation

    # Now let's implement the Python functions to handle the UI and interaction

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
            
            # Store original dimensions for later use
            content_box.original_width = img_width
            content_box.original_height = img_height
        except Exception as e:
            print(f"Error creating preview: {e}")
            # Add label instead of preview
            preview_label = Gtk.Label(label="Image Preview Not Available")
            preview_label.set_halign(Gtk.Align.CENTER)
            content_box.append(preview_label)
            
            # Set default dimensions
            content_box.original_width = 0
            content_box.original_height = 0
        
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
        if content_box.original_width:
            width_entry.set_text(str(content_box.original_width))
        width_entry.set_hexpand(True)
        size_box.append(width_entry)
        
        height_label = Gtk.Label(label="Height:")
        height_label.set_halign(Gtk.Align.START)
        size_box.append(height_label)
        
        height_entry = Gtk.Entry()
        height_entry.set_placeholder_text("Auto")
        if content_box.original_height:
            height_entry.set_text(str(content_box.original_height))
        height_entry.set_hexpand(True)
        size_box.append(height_entry)
        
        content_box.append(size_box)
        
        # Border options
        border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        border_check = Gtk.CheckButton(label="Add Border")
        border_check.set_active(False)
        border_box.append(border_check)
        
        border_width = Gtk.SpinButton()
        border_width.set_adjustment(Gtk.Adjustment(value=1, lower=1, upper=10, step_increment=1))
        border_width.set_sensitive(False)
        border_box.append(border_width)
        
        # Connect border checkbox to enable/disable width spinner
        border_check.connect("toggled", lambda cb: border_width.set_sensitive(cb.get_active()))
        
        content_box.append(border_box)
        
        # Positioning options
        position_label = Gtk.Label(label="Position:")
        position_label.set_halign(Gtk.Align.START)
        content_box.append(position_label)
        
        position_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        position_box.add_css_class("linked")
        
        # Create position radio buttons with icons
        positions = [
            {"icon": "format-justify-left-symbolic", "tooltip": "Align Left (text wraps around right)", "value": "left"},
            {"icon": "format-justify-center-symbolic", "tooltip": "Center", "value": "center"},
            {"icon": "format-justify-right-symbolic", "tooltip": "Align Right (text wraps around left)", "value": "right"},
            {"icon": "format-justify-fill-symbolic", "tooltip": "Full Width", "value": "block"},
            {"icon": "overlapping-windows-symbolic", "tooltip": "Free Floating", "value": "floating"}
        ]
        
        # Create a ToggleButton set for position
        first_position_button = None
        for i, pos in enumerate(positions):
            button = Gtk.ToggleButton(icon_name=pos["icon"])
            button.set_tooltip_text(pos["tooltip"])
            button.position_value = pos["value"]
            position_box.append(button)
            
            # First one should be active by default
            if i == 0:
                button.set_active(True)
                first_position_button = button
            
            # Connect to handle mutual exclusivity
            button.connect("toggled", lambda btn: self._on_position_button_toggled(btn, position_box) if btn.get_active() else None)
        
        content_box.append(position_box)
        content_box.position_buttons = position_box
        
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
            border_check.get_active(),
            border_width.get_value_as_int() if border_check.get_active() else 0,
            self._get_selected_position(position_box),
            dialog
        ))
        button_box.append(insert_button)
        
        content_box.append(button_box)
        
        # Set content and show dialog
        dialog.set_content(content_box)
        dialog.present()

    def _on_position_button_toggled(self, button, position_box):
        """Handle position button toggling to maintain mutual exclusivity"""
        if button.get_active():
            # Deactivate all other buttons
            for child in position_box:
                if child != button and isinstance(child, Gtk.ToggleButton):
                    child.set_active(False)

    def _get_selected_position(self, position_box):
        """Get the selected position value from the position button box"""
        for child in position_box:
            if isinstance(child, Gtk.ToggleButton) and child.get_active():
                return child.position_value
        return "left"  # Default if none selected

    def _insert_image_to_editor(self, win, file_path, alt_text, width, height, has_border, border_width, position, dialog):
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
            
            # Check if width/height are valid
            try:
                width_val = int(width) if width else 0
            except ValueError:
                width_val = 0
                
            try:
                height_val = int(height) if height else 0
            except ValueError:
                height_val = 0
            
            # Determine if image should be floating
            is_floating = (position == "floating")
            
            # Create JavaScript to insert the image
            js_code = f"""
            (function() {{
                insertImage(
                    "{data_url}", 
                    "{alt_text}", 
                    {width_val}, 
                    {height_val},
                    {str(is_floating).lower()}
                );
                
                // If not floating, set the alignment after insertion
                setTimeout(() => {{
                    if (activeImage) {{
                        // Apply border if requested
                        if ({str(has_border).lower()}) {{
                            setImageBorderStyle('solid', {border_width}, getImageBorderColor());
                        }}
                        
                        // Apply alignment if not floating
                        if (!{str(is_floating).lower()}) {{
                            const alignMap = {{
                                'left': 'left-align',
                                'center': 'center-align',
                                'right': 'right-align',
                                'block': 'no-wrap'
                            }};
                            
                            setImageAlignment(alignMap['{position}'] || 'no-wrap');
                        }}
                    }}
                }}, 50);
                
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

    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return f"""
        {self.image_theme_helpers_js()}
        {self.image_handles_css_js()}
        {self.image_insert_functions_js()}
        {self.image_activation_js()}
        {self.image_drag_resize_js()}
        {self.image_alignment_js()}
        {self.image_floating_js()}
        {self.image_border_style_js()}
        {self.image_event_handlers_js()}
        """

    def image_theme_helpers_js(self):
        """JavaScript helper functions for theme detection and colors"""
        return """
        // Function to get appropriate border color based on current theme for images
        function getImageBorderColor() {
            return isDarkMode() ? '#444' : '#ccc';
        }
        """

    def image_handles_css_js(self):
        """JavaScript that defines CSS for image handles with proper display properties"""
        return """
        // CSS for image handles
        const imageHandlesCSS = `
        /* Image drag handle - positioned in the top-left corner */
        .image-drag-handle {
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

        /* Image resize handle - triangular shape in bottom right */
        .image-resize-handle {
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
        
        /* Floating image styles */
        .floating-image {
            position: absolute !important;
            z-index: 50;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            cursor: grab;
        }
        
        .floating-image:active {
            cursor: grabbing;
        }
        
        .floating-image .image-drag-handle {
            width: 20px !important;
            height: 20px !important;
            border-radius: 3px;
            opacity: 0.9;
        }
        
        .floating-image:focus {
            outline: 2px solid #4e9eff;
        }
        
        .image-selected {
            outline: 2px solid #4e9eff;
            outline-offset: 2px;
            position: relative;
        }

        @media (prefers-color-scheme: dark) {
            .image-drag-handle {
                background-color: #0078d7;
            }
            .image-resize-handle {
                border-color: transparent transparent #0078d7 transparent;
            }
            .floating-image {
                box-shadow: 0 3px 10px rgba(0,0,0,0.5);
            }
            .floating-image .image-drag-handle {
                background-color: #0078d7;
            }
            .image-selected {
                outline-color: #0078d7;
            }
        }`;
        
        // Function to add the image handle styles to the document
        function addImageHandleStyles() {
            // Check if our style element already exists
            let styleElement = document.getElementById('image-handle-styles');
            
            // If not, create and append it
            if (!styleElement) {
                styleElement = document.createElement('style');
                styleElement.id = 'image-handle-styles';
                styleElement.textContent = imageHandlesCSS;
                document.head.appendChild(styleElement);
            } else {
                // If it exists, update the content
                styleElement.textContent = imageHandlesCSS;
            }
        }
        """

    def image_insert_functions_js(self):
        """JavaScript for inserting images with default properties"""
        return """
        // Function to insert an image at the current cursor position
        function insertImage(src, alt, width, height, isFloating) {
            // Create a new image element
            let imageWrapper = document.createElement('span');
            imageWrapper.className = 'editor-image-wrapper';
            imageWrapper.style.display = 'inline-block';
            imageWrapper.style.position = 'relative';
            imageWrapper.style.margin = '6px 6px 0 0';
            
            // Store margin values as attributes for later reference
            imageWrapper.setAttribute('data-margin-top', '6');
            imageWrapper.setAttribute('data-margin-right', '6');
            imageWrapper.setAttribute('data-margin-bottom', '0');
            imageWrapper.setAttribute('data-margin-left', '0');
            
            let img = document.createElement('img');
            
            // Set attributes
            img.src = src;
            img.alt = alt || '';
            
            // Set size if provided
            if (width) {
                img.width = width;
                img.setAttribute('data-original-width', width);
            }
            if (height) {
                img.height = height;
                img.setAttribute('data-original-height', height);
            }
            
            // Store original dimensions for resizing proportionally
            if (!img.hasAttribute('data-original-width') && img.width) {
                img.setAttribute('data-original-width', img.width);
            }
            if (!img.hasAttribute('data-original-height') && img.height) {
                img.setAttribute('data-original-height', img.height);
            }
            
            // Add the image to the wrapper
            imageWrapper.appendChild(img);
            
            // Make the wrapper floating if requested
            if (isFloating) {
                imageWrapper.classList.add('floating-image');
                setImageFloating(imageWrapper);
            }
            
            // Insert the wrapper at current selection
            document.execCommand('insertHTML', false, imageWrapper.outerHTML);
            
            // Find and activate the newly inserted image wrapper
            setTimeout(() => {
                const wrappers = document.querySelectorAll('.editor-image-wrapper');
                const newWrapper = wrappers[wrappers.length - 1];
                if (newWrapper) {
                    activateImage(newWrapper);
                    try {
                        window.webkit.messageHandlers.imageClicked.postMessage({
                            src: src,
                            alt: alt || '',
                            width: width || '',
                            height: height || ''
                        });
                    } catch(e) {
                        console.log("Could not notify about image click:", e);
                    }
                }
            }, 10);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage("changed");
            } catch(e) {
                console.log("Could not notify about changes:", e);
            }
        }
        """

    def image_activation_js(self):
        """JavaScript for image activation and deactivation"""
        return """
        // Variables for image handling
        var activeImage = null;
        var isImageDragging = false;
        var isImageResizing = false;
        var imageDragStartX = 0;
        var imageDragStartY = 0;
        var imageStartX = 0;
        var imageStartY = 0;
        var imageStartWidth = 0;
        var imageStartHeight = 0;
        
        // Function to find parent image element
        function findParentImage(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'IMG' || 
                    (element.classList && element.classList.contains('editor-image-wrapper'))) {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Function to activate an image (add handles)
        function activateImage(imageElement) {
            if (activeImage === imageElement) return; // Already active
            
            // Deactivate any previously active images
            if (activeImage && activeImage !== imageElement) {
                deactivateImage(activeImage);
            }
            
            // If we got an IMG element, use its parent wrapper if available
            if (imageElement.tagName === 'IMG' && 
                imageElement.parentNode && 
                imageElement.parentNode.classList && 
                imageElement.parentNode.classList.contains('editor-image-wrapper')) {
                imageElement = imageElement.parentNode;
            }
            
            // If we still have an IMG without wrapper, wrap it
            if (imageElement.tagName === 'IMG') {
                const wrapper = document.createElement('span');
                wrapper.className = 'editor-image-wrapper';
                wrapper.style.display = 'inline-block';
                wrapper.style.position = 'relative';
                
                // Insert wrapper before the image
                imageElement.parentNode.insertBefore(wrapper, imageElement);
                // Move the image into the wrapper
                wrapper.appendChild(imageElement);
                
                // Use the wrapper as our active element
                imageElement = wrapper;
            }
            
            activeImage = imageElement;
            
            // Add selected class
            activeImage.classList.add('image-selected');
            
            // Ensure the wrapper has editor-image-wrapper class
            if (!activeImage.classList.contains('editor-image-wrapper')) {
                activeImage.classList.add('editor-image-wrapper');
            }
            
            // Ensure the wrapper has position: relative for proper handle positioning (if not floating)
            if (!activeImage.classList.contains('floating-image')) {
                activeImage.style.position = 'relative';
            }
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return;
            
            // Store original dimensions if not already stored
            if (!imgElement.hasAttribute('data-original-width') && imgElement.width) {
                imgElement.setAttribute('data-original-width', imgElement.width);
            }
            if (!imgElement.hasAttribute('data-original-height') && imgElement.height) {
                imgElement.setAttribute('data-original-height', imgElement.height);
            }
            
            // Add resize handle if needed
            if (!activeImage.querySelector('.image-resize-handle')) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'image-resize-handle';
                
                // Make handle non-selectable and prevent focus
                resizeHandle.setAttribute('contenteditable', 'false');
                resizeHandle.setAttribute('unselectable', 'on');
                resizeHandle.setAttribute('tabindex', '-1');
                
                // Add event listener
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startImageResize(e, imageElement);
                }, true);
                
                activeImage.appendChild(resizeHandle);
            }
            
            // Add drag handle if needed
            if (!activeImage.querySelector('.image-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'image-drag-handle';
                dragHandle.innerHTML = '↕';
                
                // Set title based on whether it's a floating image or not
                if (activeImage.classList.contains('floating-image')) {
                    dragHandle.title = 'Drag to move image freely';
                } else {
                    dragHandle.title = 'Drag to reposition image between paragraphs';
                }
                
                // Make handle non-selectable and prevent focus
                dragHandle.setAttribute('contenteditable', 'false');
                dragHandle.setAttribute('unselectable', 'on');
                dragHandle.setAttribute('tabindex', '-1');
                
                // Add event listener
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startImageDrag(e, imageElement);
                }, true);
                
                activeImage.appendChild(dragHandle);
            }
            
            // Special styling for floating images
            if (activeImage.classList.contains('floating-image')) {
                enhanceImageDragHandles(activeImage);
            }
        }
        
        // Function to deactivate a specific image
        function deactivateImage(imageElement) {
            if (!imageElement) return;
            
            // Remove selected class
            imageElement.classList.remove('image-selected');
            
            // Remove handles
            const resizeHandle = imageElement.querySelector('.image-resize-handle');
            if (resizeHandle) resizeHandle.remove();
            
            const dragHandle = imageElement.querySelector('.image-drag-handle');
            if (dragHandle) dragHandle.remove();
            
            if (imageElement === activeImage) {
                activeImage = null;
            }
        }
        
        // Function to deactivate all images
        function deactivateAllImages() {
            const images = document.querySelectorAll('.editor-image-wrapper');
            
            images.forEach(image => {
                deactivateImage(image);
            });
            
            // Always notify that images are deactivated
            activeImage = null;
            try {
                window.webkit.messageHandlers.imagesDeactivated.postMessage('images-deactivated');
            } catch(e) {
                console.log("Could not notify about image deactivation:", e);
            }
        }
        """

    def image_drag_resize_js(self):
        """JavaScript for image dragging and resizing"""
        return """
        // Function to start image drag
        function startImageDrag(e, imageElement) {
            e.preventDefault();
            if (!imageElement) return;
            
            isImageDragging = true;
            activeImage = imageElement;
            imageDragStartX = e.clientX;
            imageDragStartY = e.clientY;
            
            // Set cursor based on whether the image is floating or not
            if (imageElement.classList.contains('floating-image')) {
                document.body.style.cursor = 'grabbing';
                
                // Store the initial position for floating images
                const style = window.getComputedStyle(imageElement);
                imageStartX = parseInt(style.left) || 0;
                imageStartY = parseInt(style.top) || 0;
            } else {
                document.body.style.cursor = 'move';
            }
        }
        
        // Function to move image
        function moveImage(e) {
            if (!isImageDragging || !activeImage) return;
            
            // Check if the image is a floating image
            if (activeImage.classList.contains('floating-image')) {
                // For floating images, move to the mouse position with offset
                const deltaX = e.clientX - imageDragStartX;
                const deltaY = e.clientY - imageDragStartY;
                
                // Update position
                activeImage.style.left = `${imageStartX + deltaX}px`;
                activeImage.style.top = `${imageStartY + deltaY}px`;
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            } else {
                const currentY = e.clientY;
                const deltaY = currentY - imageDragStartY;
                
                if (Math.abs(deltaY) > 30) {
                    const editor = document.getElementById('editor');
                    const blocks = Array.from(editor.children).filter(node => {
                        const style = window.getComputedStyle(node);
                        return style.display.includes('block') || node.tagName === 'TABLE' || 
                               node.classList.contains('editor-image-wrapper');
                    });
                    
                    const imageIndex = blocks.indexOf(activeImage);
                    
                    if (deltaY < 0 && imageIndex > 0) {
                        const targetElement = blocks[imageIndex - 1];
                        editor.insertBefore(activeImage, targetElement);
                        imageDragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    } 
                    else if (deltaY > 0 && imageIndex < blocks.length - 1) {
                        const targetElement = blocks[imageIndex + 1];
                        if (targetElement.nextSibling) {
                            editor.insertBefore(activeImage, targetElement.nextSibling);
                        } else {
                            editor.appendChild(activeImage);
                        }
                        imageDragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            }
        }
        
        // Function to start image resize
        function startImageResize(e, imageElement) {
            e.preventDefault();
            isImageResizing = true;
            activeImage = imageElement;
            imageDragStartX = e.clientX;
            imageDragStartY = e.clientY;
            
            // Find the actual IMG element
            const imgElement = imageElement.querySelector('img');
            if (!imgElement) return;
            
            // Store initial size
            imageStartWidth = imgElement.width || imgElement.offsetWidth;
            imageStartHeight = imgElement.height || imgElement.offsetHeight;
        }
        
        // Function to resize image
        function resizeImage(e) {
            if (!isImageResizing || !activeImage) return;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return;
            
            const deltaX = e.clientX - imageDragStartX;
            const deltaY = e.clientY - imageDragStartY;
            
            // Get original aspect ratio if stored
            let originalWidth = parseInt(imgElement.getAttribute('data-original-width'));
            let originalHeight = parseInt(imgElement.getAttribute('data-original-height'));
            let aspectRatio = originalWidth && originalHeight ? originalWidth / originalHeight : imageStartWidth / imageStartHeight;
            
            // Calculate new dimensions
            let newWidth = Math.max(20, imageStartWidth + deltaX);
            let newHeight = Math.round(newWidth / aspectRatio);
            
            // Apply new dimensions
            imgElement.width = newWidth;
            imgElement.height = newHeight;
            
            // Notify that the image has been resized
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """

    def image_alignment_js(self):
        """JavaScript for image alignment"""
        return """
        // Function to set image alignment
        function setImageAlignment(alignClass) {
            if (!activeImage) return;
            
            // Remove all alignment classes
            activeImage.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap', 'floating-image');
            
            // Add the requested alignment class
            activeImage.classList.add(alignClass);
            
            // Reset positioning if it was previously floating
            if (activeImage.style.position === 'absolute') {
                activeImage.style.position = 'relative';
                activeImage.style.top = '';
                activeImage.style.left = '';
                activeImage.style.zIndex = '';
            }
            
            // Update image display style based on alignment
            if (alignClass === 'left-align') {
                activeImage.style.display = 'inline-block';
                activeImage.style.float = 'left';
                activeImage.style.marginRight = '10px';
            } else if (alignClass === 'right-align') {
                activeImage.style.display = 'inline-block';
                activeImage.style.float = 'right';
                activeImage.style.marginLeft = '10px';
            } else if (alignClass === 'center-align') {
                activeImage.style.display = 'block';
                activeImage.style.float = 'none';
                activeImage.style.marginLeft = 'auto';
                activeImage.style.marginRight = 'auto';
            } else if (alignClass === 'no-wrap') {
                activeImage.style.display = 'block';
                activeImage.style.float = 'none';
                activeImage.style.marginLeft = '0';
                activeImage.style.marginRight = '0';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """
        
    def image_floating_js(self):
        """JavaScript for floating image functionality"""
        return """
        // Function to make an image floating (freely positionable)
        function setImageFloating(imageElement) {
            if (!imageElement && activeImage) {
                imageElement = activeImage;
            }
            
            if (!imageElement) return;
            
            // First, remove any alignment classes
            imageElement.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            
            // Reset any float styles
            imageElement.style.float = 'none';
            
            // Add floating class for special styling
            imageElement.classList.add('floating-image');
            
            // Set positioning to absolute
            imageElement.style.position = 'absolute';
            
            // Calculate initial position - center in the visible editor area
            const editorRect = document.getElementById('editor').getBoundingClientRect();
            const imageRect = imageElement.getBoundingClientRect();
            
            // Set initial position
            const editorScrollTop = document.getElementById('editor').scrollTop;
            
            // Position in the middle of the visible editor area
            const topPos = (editorRect.height / 2) - (imageRect.height / 2) + editorScrollTop;
            const leftPos = (editorRect.width / 2) - (imageRect.width / 2);
            
            imageElement.style.top = `${Math.max(topPos, editorScrollTop)}px`;
            imageElement.style.left = `${Math.max(leftPos, 0)}px`;
            
            // Enhance the drag handle for position control
            enhanceImageDragHandles(imageElement);
            
            // Ensure proper z-index to be above regular content
            imageElement.style.zIndex = "50";
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            // Activate the image to show handles
            if (imageElement !== activeImage) {
                activateImage(imageElement);
            }
        }
        
        // Add enhanced drag handling for floating images
        function enhanceImageDragHandles(imageElement) {
            if (!imageElement) return;
            
            // Find or create the drag handle
            let dragHandle = imageElement.querySelector('.image-drag-handle');
            if (!dragHandle) {
                // If it doesn't exist, we might need to activate the image first
                activateImage(imageElement);
                dragHandle = imageElement.querySelector('.image-drag-handle');
            }
            
            if (dragHandle) {
                // Update tooltip to reflect new functionality
                dragHandle.title = "Drag to move image freely";
                
                // Make the drag handle more visible for floating images
                dragHandle.style.width = "20px";
                dragHandle.style.height = "20px";
                dragHandle.style.backgroundColor = "#4e9eff";
                dragHandle.style.borderRadius = "3px";
                dragHandle.style.opacity = "0.9";
            }
        }
        """

    def image_border_style_js(self):
        """JavaScript for image border styling"""
        return """
        // Function to set image border style
        function setImageBorderStyle(style, width, color) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            // Get current values
            let currentStyle = imgElement.getAttribute('data-border-style');
            let currentWidth = imgElement.getAttribute('data-border-width');
            let currentColor = imgElement.getAttribute('data-border-color');
            
            // If attributes don't exist, try to get from computed style
            if (!currentStyle || !currentWidth || !currentColor) {
                const computedStyle = window.getComputedStyle(imgElement);
                
                // Try to get current style from computed style
                currentStyle = currentStyle || imgElement.style.borderStyle || computedStyle.borderStyle || 'solid';
                
                // Get current width
                if (!currentWidth) {
                    currentWidth = parseInt(imgElement.style.borderWidth) || 
                                  parseInt(computedStyle.borderWidth) || 0;
                }
                
                // Get current color
                currentColor = currentColor || imgElement.style.borderColor || 
                              computedStyle.borderColor || getImageBorderColor();
            }
            
            // Use provided values or fall back to current/default values
            const newStyle = (style !== null && style !== undefined && style !== '') ? style : currentStyle;
            const newWidth = (width !== null && width !== undefined && width !== '') ? width : currentWidth;
            const newColor = (color !== null && color !== undefined && color !== '') ? color : currentColor;
            
            // Apply the border
            if (newWidth > 0) {
                imgElement.style.border = `${newWidth}px ${newStyle} ${newColor}`;
            } else {
                imgElement.style.border = 'none';
            }
            
            // Store values as attributes
            imgElement.setAttribute('data-border-style', newStyle);
            imgElement.setAttribute('data-border-width', newWidth);
            imgElement.setAttribute('data-border-color', newColor);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set image border color
        function setImageBorderColor(color) {
            return setImageBorderStyle(null, null, color);
        }
        
        // Function to set image border width
        function setImageBorderWidth(width) {
            return setImageBorderStyle(null, width, null);
        }
        
        // Function to get current image border style
        function getImageBorderStyle() {
            if (!activeImage) return null;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return null;
            
            // First try to get from stored data attributes
            const storedStyle = imgElement.getAttribute('data-border-style');
            const storedWidth = imgElement.getAttribute('data-border-width');
            const storedColor = imgElement.getAttribute('data-border-color');
            
            if (storedStyle && storedWidth && storedColor) {
                return {
                    style: storedStyle,
                    width: parseInt(storedWidth),
                    color: storedColor
                };
            }
            
            // If not stored, get from computed style
            const computedStyle = window.getComputedStyle(imgElement);
            
            const result = {
                style: imgElement.style.borderStyle || computedStyle.borderStyle || 'solid',
                width: parseInt(imgElement.style.borderWidth) || parseInt(computedStyle.borderWidth) || 0,
                color: imgElement.style.borderColor || computedStyle.borderColor || getImageBorderColor()
            };
            
            // Store these values for future use
            imgElement.setAttribute('data-border-style', result.style);
            imgElement.setAttribute('data-border-width', result.width);
            imgElement.setAttribute('data-border-color', result.color);
            
            return result;
        }
        
        // Function to set image shadow
        function setImageShadow(enabled) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            if (enabled) {
                imgElement.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
            } else {
                imgElement.style.boxShadow = 'none';
            }
            
            // Store shadow state
            imgElement.setAttribute('data-shadow', enabled);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current image properties
        function getImageProperties() {
            if (!activeImage) return null;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return null;
            
            const borderStyle = getImageBorderStyle();
            const shadow = imgElement.getAttribute('data-shadow') === 'true' || 
                          window.getComputedStyle(imgElement).boxShadow !== 'none';
            
            return {
                src: imgElement.src,
                alt: imgElement.alt || '',
                width: imgElement.width || imgElement.offsetWidth,
                height: imgElement.height || imgElement.offsetHeight,
                originalWidth: parseInt(imgElement.getAttribute('data-original-width')) || 0,
                originalHeight: parseInt(imgElement.getAttribute('data-original-height')) || 0,
                border: borderStyle,
                shadow: shadow,
                alignment: getImageAlignment()
            };
        }
        
        // Function to get current image alignment
        function getImageAlignment() {
            if (!activeImage) return 'no-wrap';
            
            if (activeImage.classList.contains('left-align')) return 'left-align';
            if (activeImage.classList.contains('right-align')) return 'right-align';
            if (activeImage.classList.contains('center-align')) return 'center-align';
            if (activeImage.classList.contains('floating-image')) return 'floating-image';
            
            return 'no-wrap';
        }
        
        // Function to set image margins
        function setImageMargins(top, right, bottom, left) {
            if (!activeImage) return false;
            
            // Set margins individually if provided
            if (top !== undefined && top !== null) {
                activeImage.style.marginTop = top + 'px';
            }
            if (right !== undefined && right !== null) {
                activeImage.style.marginRight = right + 'px';
            }
            if (bottom !== undefined && bottom !== null) {
                activeImage.style.marginBottom = bottom + 'px';
            }
            if (left !== undefined && left !== null) {
                activeImage.style.marginLeft = left + 'px';
            }
            
            // Store margin values as attributes for later reference
            activeImage.setAttribute('data-margin-top', parseInt(activeImage.style.marginTop) || 0);
            activeImage.setAttribute('data-margin-right', parseInt(activeImage.style.marginRight) || 0);
            activeImage.setAttribute('data-margin-bottom', parseInt(activeImage.style.marginBottom) || 0);
            activeImage.setAttribute('data-margin-left', parseInt(activeImage.style.marginLeft) || 0);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current image margins
        function getImageMargins() {
            if (!activeImage) return null;
            
            // Try to get from stored attributes first
            const storedTop = activeImage.getAttribute('data-margin-top');
            const storedRight = activeImage.getAttribute('data-margin-right');
            const storedBottom = activeImage.getAttribute('data-margin-bottom');
            const storedLeft = activeImage.getAttribute('data-margin-left');
            
            if (storedTop !== null || storedRight !== null || storedBottom !== null || storedLeft !== null) {
                return {
                    top: parseInt(storedTop) || 0,
                    right: parseInt(storedRight) || 0,
                    bottom: parseInt(storedBottom) || 0,
                    left: parseInt(storedLeft) || 0
                };
            }
            
            // Otherwise get from computed style
            const computedStyle = window.getComputedStyle(activeImage);
            
            return {
                top: parseInt(computedStyle.marginTop) || 0,
                right: parseInt(computedStyle.marginRight) || 0,
                bottom: parseInt(computedStyle.marginBottom) || 0,
                left: parseInt(computedStyle.marginLeft) || 0
            };
        }
        
        // Function to set image color effects (like grayscale, sepia, etc.)
        function setImageColorEffect(effect) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            // Apply the selected effect
            switch (effect) {
                case 'none':
                    imgElement.style.filter = 'none';
                    break;
                case 'grayscale':
                    imgElement.style.filter = 'grayscale(100%)';
                    break;
                case 'sepia':
                    imgElement.style.filter = 'sepia(100%)';
                    break;
                case 'invert':
                    imgElement.style.filter = 'invert(100%)';
                    break;
                case 'brightness':
                    imgElement.style.filter = 'brightness(150%)';
                    break;
                case 'contrast':
                    imgElement.style.filter = 'contrast(150%)';
                    break;
                case 'blur':
                    imgElement.style.filter = 'blur(2px)';
                    break;
                default:
                    imgElement.style.filter = 'none';
            }
            
            // Store the effect
            imgElement.setAttribute('data-color-effect', effect);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current color effect
        function getImageColorEffect() {
            if (!activeImage) return 'none';
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return 'none';
            
            return imgElement.getAttribute('data-color-effect') || 'none';
        }
        
        // Function to apply rounded corners to the image
        function setImageRoundedCorners(radius) {
            if (!activeImage) return false;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return false;
            
            // Apply the border radius
            imgElement.style.borderRadius = `${radius}px`;
            
            // Store the radius
            imgElement.setAttribute('data-border-radius', radius);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current border radius
        function getImageBorderRadius() {
            if (!activeImage) return 0;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return 0;
            
            const radius = imgElement.getAttribute('data-border-radius');
            return radius ? parseInt(radius) : 0;
        }
        """
#
    # Now let's implement the image toolbar and event handlers for the HTML Editor

    def on_image_clicked(self, win, manager, message):
        """Handle when an image is clicked in the editor"""
        try:
            # Extract image properties from the message
            js_result = message.get_js_value()
            properties = js_result.to_string()
            
            # Parse the properties (this is a simplified version)
            import json
            img_props = json.loads(properties)
            
            # Show the image toolbar
            win.image_toolbar_revealer.set_reveal_child(True)
            
            # Update status
            win.statusbar.set_text("Image selected")
            
            # Update margin controls with current image margins
            js_code = """
            (function() {
                const margins = getImageMargins();
                return win
     JSON.stringify(margins);
            })();
            """
            
            win.webview.evaluate_javascript(
                js_code,
                -1, None, None, None,
                lambda webview, result, data: self._update_image_margin_controls(win, webview, result),
                None
            )
            
        except Exception as e:
            print(f"Error handling image click: {e}")

    def on_image_deleted(self, win, manager, message):
        """Handle image deleted event from editor"""
        win.image_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("Image deleted")

    def on_images_deactivated(self, win, manager, message):
        """Handle event when all images are deactivated"""
        win.image_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("No image selected")

    def _update_image_margin_controls(self, win, webview, result):
        """Update margin controls with current image margins"""
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
                
                if hasattr(win, 'image_margin_controls') and isinstance(margins, dict):
                    for side in ['top', 'right', 'bottom', 'left']:
                        if side in win.image_margin_controls and side in margins:
                            win.image_margin_controls[side].set_value(margins[side])
        except Exception as e:
            print(f"Error updating image margin controls: {e}")

    def on_image_margin_changed(self, win, side, value):
        """Apply margin change to the active image"""
        js_code = f"""
        (function() {{
            // Pass all four sides with the updated value for the specified side
            const margins = getImageMargins() || {{ top: 0, right: 0, bottom: 0, left: 0 }};
            margins.{side} = {value};
            setImageMargins(margins.top, margins.right, margins.bottom, margins.left);
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied {side} margin: {value}px")

    def create_image_toolbar(self, win):
        """Create a toolbar for image editing"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        
        # Image operations label
        image_label = Gtk.Label(label="Image:")
        image_label.set_margin_end(10)
        toolbar.append(image_label)
        
        # Size controls
        size_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        size_group.add_css_class("linked")
        
        # Reset size button
        reset_size_button = Gtk.Button(icon_name="edit-undo-symbolic")
        reset_size_button.set_tooltip_text("Reset to original size")
        reset_size_button.connect("clicked", lambda btn: self.on_reset_image_size_clicked(win))
        size_group.append(reset_size_button)
        
        # Add size group to toolbar
        toolbar.append(size_group)
        
        # Small separator
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator1.set_margin_start(5)
        separator1.set_margin_end(5)
        toolbar.append(separator1)
        
        # Border controls
        border_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Border label
        border_label = Gtk.Label(label="Border:")
        border_label.set_margin_end(5)
        border_group.append(border_label)
        
        # Border width spinner
        border_adjustment = Gtk.Adjustment(value=1, lower=0, upper=10, step_increment=1)
        border_spin = Gtk.SpinButton()
        border_spin.set_tooltip_text("Border width")
        border_spin.set_adjustment(border_adjustment)
        border_spin.connect("value-changed", lambda spin: self.on_image_border_width_changed(win, spin.get_value_as_int()))
        border_group.append(border_spin)
        
        # Border style dropdown
        border_style = Gtk.DropDown()
        border_style.set_tooltip_text("Border style")
        border_styles = Gtk.StringList()
        for style in ["solid", "dashed", "dotted", "double"]:
            border_styles.append(style)
        border_style.set_model(border_styles)
        border_style.set_selected(0)  # Default to solid
        border_style.connect("notify::selected", lambda dd, p: self.on_image_border_style_changed(
            win, border_styles.get_string(dd.get_selected())))
        border_group.append(border_style)
        
        # Add border group to toolbar
        toolbar.append(border_group)
        
        # Separator
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator2.set_margin_start(5)
        separator2.set_margin_end(5)
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
        align_left_button.connect("clicked", lambda btn: self.on_image_align_left(win))
        align_group.append(align_left_button)
        
        # Center alignment
        align_center_button = Gtk.Button(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Center (no text wrap)")
        align_center_button.connect("clicked", lambda btn: self.on_image_align_center(win))
        align_group.append(align_center_button)
        
        # Right alignment
        align_right_button = Gtk.Button(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right (text wraps around left)")
        align_right_button.connect("clicked", lambda btn: self.on_image_align_right(win))
        align_group.append(align_right_button)
        
        # Full width (no wrap)
        full_width_button = Gtk.Button(icon_name="format-justify-fill-symbolic")
        full_width_button.set_tooltip_text("Full Width (no text wrap)")
        full_width_button.connect("clicked", lambda btn: self.on_image_full_width(win))
        align_group.append(full_width_button)
        
        # Add alignment group to toolbar
        toolbar.append(align_group)
        
        # Float button
        float_button = Gtk.Button(icon_name="overlapping-windows-symbolic")
        float_button.set_tooltip_text("Make image float freely in editor")
        float_button.set_margin_start(5)
        float_button.connect("clicked", lambda btn: self.on_image_float_clicked(win))
        toolbar.append(float_button)
        
        # Layer control options (like Z-index)
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator3.set_margin_start(10)
        separator3.set_margin_end(10)
        toolbar.append(separator3)
        
        layer_label = Gtk.Label(label="Layer:")
        layer_label.set_margin_end(5)
        toolbar.append(layer_label)
        
        # Create a group for layer control buttons
        layer_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        layer_group.add_css_class("linked")
        
        # Bring forward button (increase z-index)
        bring_forward_button = Gtk.Button(icon_name="go-up-symbolic")
        bring_forward_button.set_tooltip_text("Bring Forward (place above other elements)")
        bring_forward_button.connect("clicked", lambda btn: self.on_image_bring_forward_clicked(win))
        layer_group.append(bring_forward_button)
        
        # Send backward button (decrease z-index)
        send_backward_button = Gtk.Button(icon_name="go-down-symbolic")
        send_backward_button.set_tooltip_text("Send Backward (place beneath other elements)")
        send_backward_button.connect("clicked", lambda btn: self.on_image_send_backward_clicked(win))
        layer_group.append(send_backward_button)
        
        # Add layer control group to toolbar
        toolbar.append(layer_group)
        
        # Delete button
        separator4 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator4.set_margin_start(10)
        separator4.set_margin_end(10)
        toolbar.append(separator4)
        
        delete_button = Gtk.Button(icon_name="edit-delete-symbolic")
        delete_button.set_tooltip_text("Delete image")
        delete_button.connect("clicked", lambda btn: self.on_delete_image_clicked(win))
        toolbar.append(delete_button)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Close button
        close_button = Gtk.Button(icon_name="window-close-symbolic")
        close_button.set_tooltip_text("Close image toolbar")
        close_button.connect("clicked", lambda btn: self.on_close_image_toolbar_clicked(win))
        toolbar.append(close_button)
        
        return toolbar

    # Image operation methods
    def on_reset_image_size_clicked(self, win):
        """Reset image to its original size"""
        js_code = "resetImageSize();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image reset to original size")

    def on_image_border_width_changed(self, win, width):
        """Change image border width"""
        js_code = f"setImageBorderWidth({width});"
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Image border width: {width}px")

    def on_image_border_style_changed(self, win, style):
        """Change image border style"""
        js_code = f"setImageBorderStyle('{style}', null, null);"
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Image border style: {style}")

    def on_image_align_left(self, win):
        """Align image to the left with text wrapping around right"""
        js_code = "setImageAlignment('left-align');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image aligned left")

    def on_image_align_center(self, win):
        """Align image to the center with no text wrapping"""
        js_code = "setImageAlignment('center-align');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image aligned center")

    def on_image_align_right(self, win):
        """Align image to the right with text wrapping around left"""
        js_code = "setImageAlignment('right-align');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image aligned right")

    def on_image_full_width(self, win):
        """Make image full width with no text wrapping"""
        js_code = "setImageAlignment('no-wrap');"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image set to full width")

    def on_image_float_clicked(self, win):
        """Make image float freely in the editor"""
        js_code = "setImageFloating();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image is now floating")

    def on_image_bring_forward_clicked(self, win):
        """Bring the image forward in the z-order"""
        js_code = "bringImageForward();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image brought forward")

    def on_image_send_backward_clicked(self, win):
        """Send the image backward in the z-order"""
        js_code = "sendImageBackward();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image sent backward")

    def on_delete_image_clicked(self, win):
        """Delete the active image"""
        js_code = "deleteImage();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image deleted")

    def on_close_image_toolbar_clicked(self, win):
        """Hide the image toolbar and deactivate images"""
        win.image_toolbar_revealer.set_reveal_child(False)
        js_code = "deactivateAllImages();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Image toolbar closed")

    # Now let's add the necessary modifications to the main application
    def create_window(self):
        """Modify the create_window method to include image toolbar"""
        # Create window as before
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
        
        # Create a revealer for the table toolbar
        win.image_toolbar_revealer = Gtk.Revealer()
        win.image_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.image_toolbar_revealer.set_transition_duration(250)
        win.image_toolbar_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create and add the table toolbar
        image_toolbar = self.create_image_toolbar(win)
        win.image_toolbar_revealer.set_child(image_toolbar)
        win.main_box.append(win.image_toolbar_revealer)
        
        # Create a revealer for the image toolbar
        win.image_toolbar_revealer = Gtk.Revealer()
        win.image_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.image_toolbar_revealer.set_transition_duration(250)
        win.image_toolbar_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create and add the image toolbar
        image_toolbar = self.create_image_toolbar(win)
        win.image_toolbar_revealer.set_child(image_toolbar)
        win.main_box.append(win.image_toolbar_revealer)
        
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
            
            # Table-related message handlers
            user_content_manager.register_script_message_handler("tableClicked")
            user_content_manager.register_script_message_handler("tableDeleted")
            user_content_manager.register_script_message_handler("tablesDeactivated")
            
            user_content_manager.connect("script-message-received::tableClicked", 
                                        lambda mgr, res: self.on_table_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::tableDeleted", 
                                        lambda mgr, res: self.on_table_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::tablesDeactivated", 
                                        lambda mgr, res: self.on_tables_deactivated(win, mgr, res))
            
            # Add Image-related message handlers
            user_content_manager.register_script_message_handler("imageClicked")
            user_content_manager.register_script_message_handler("imageDeleted")
            user_content_manager.register_script_message_handler("imagesDeactivated")
            
            user_content_manager.connect("script-message-received::imageClicked", 
                                        lambda mgr, res: self.on_image_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::imageDeleted", 
                                        lambda mgr, res: self.on_image_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::imagesDeactivated", 
                                        lambda mgr, res: self.on_images_deactivated(win, mgr, res))
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
        
        return  win # First, let's implement the JavaScript for image handling with resize handles and activation

    # Now let's implement the Python functions to handle the UI and interaction

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
            
            # Store original dimensions for later use
            content_box.original_width = img_width
            content_box.original_height = img_height
        except Exception as e:
            print(f"Error creating preview: {e}")
            # Add label instead of preview
            preview_label = Gtk.Label(label="Image Preview Not Available")
            preview_label.set_halign(Gtk.Align.CENTER)
            content_box.append(preview_label)
            
            # Set default dimensions
            content_box.original_width = 0
            content_box.original_height = 0
        
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
        if content_box.original_width:
            width_entry.set_text(str(content_box.original_width))
        width_entry.set_hexpand(True)
        size_box.append(width_entry)
        
        height_label = Gtk.Label(label="Height:")
        height_label.set_halign(Gtk.Align.START)
        size_box.append(height_label)
        
        height_entry = Gtk.Entry()
        height_entry.set_placeholder_text("Auto")
        if content_box.original_height:
            height_entry.set_text(str(content_box.original_height))
        height_entry.set_hexpand(True)
        size_box.append(height_entry)
        
        content_box.append(size_box)
        
        # Border options
        border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        border_check = Gtk.CheckButton(label="Add Border")
        border_check.set_active(False)
        border_box.append(border_check)
        
        border_width = Gtk.SpinButton()
        border_width.set_adjustment(Gtk.Adjustment(value=1, lower=1, upper=10, step_increment=1))
        border_width.set_sensitive(False)
        border_box.append(border_width)
        
        # Connect border checkbox to enable/disable width spinner
        border_check.connect("toggled", lambda cb: border_width.set_sensitive(cb.get_active()))
        
        content_box.append(border_box)
        
        # Positioning options
        position_label = Gtk.Label(label="Position:")
        position_label.set_halign(Gtk.Align.START)
        content_box.append(position_label)
        
        position_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        position_box.add_css_class("linked")
        
        # Create position radio buttons with icons
        positions = [
            {"icon": "format-justify-left-symbolic", "tooltip": "Align Left (text wraps around right)", "value": "left"},
            {"icon": "format-justify-center-symbolic", "tooltip": "Center", "value": "center"},
            {"icon": "format-justify-right-symbolic", "tooltip": "Align Right (text wraps around left)", "value": "right"},
            {"icon": "format-justify-fill-symbolic", "tooltip": "Full Width", "value": "block"},
            {"icon": "overlapping-windows-symbolic", "tooltip": "Free Floating", "value": "floating"}
        ]
        
        # Create a ToggleButton set for position
        first_position_button = None
        for i, pos in enumerate(positions):
            button = Gtk.ToggleButton(icon_name=pos["icon"])
            button.set_tooltip_text(pos["tooltip"])
            button.position_value = pos["value"]
            position_box.append(button)
            
            # First one should be active by default
            if i == 0:
                button.set_active(True)
                first_position_button = button
            
            # Connect to handle mutual exclusivity
            button.connect("toggled", lambda btn: self._on_position_button_toggled(btn, position_box) if btn.get_active() else None)
        
        content_box.append(position_box)
        content_box.position_buttons = position_box
        
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
            border_check.get_active(),
            border_width.get_value_as_int() if border_check.get_active() else 0,
            self._get_selected_position(position_box),
            dialog
        ))
        button_box.append(insert_button)
        
        content_box.append(button_box)
        
        # Set content and show dialog
        dialog.set_content(content_box)
        dialog.present()

    def _on_position_button_toggled(self, button, position_box):
        """Handle position button toggling to maintain mutual exclusivity"""
        if button.get_active():
            # Deactivate all other buttons
            for child in position_box:
                if child != button and isinstance(child, Gtk.ToggleButton):
                    child.set_active(False)

    def _get_selected_position(self, position_box):
        """Get the selected position value from the position button box"""
        for child in position_box:
            if isinstance(child, Gtk.ToggleButton) and child.get_active():
                return child.position_value
        return "left"  # Default if none selected

    def _insert_image_to_editor(self, win, file_path, alt_text, width, height, has_border, border_width, position, dialog):
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
            
            # Check if width/height are valid
            try:
                width_val = int(width) if width else 0
            except ValueError:
                width_val = 0
                
            try:
                height_val = int(height) if height else 0
            except ValueError:
                height_val = 0
            
            # Determine if image should be floating
            is_floating = (position == "floating")
            
            # Create JavaScript to insert the image
            js_code = f"""
            (function() {{
                insertImage(
                    "{data_url}", 
                    "{alt_text}", 
                    {width_val}, 
                    {height_val},
                    {str(is_floating).lower()}
                );
                
                // If not floating, set the alignment after insertion
                setTimeout(() => {{
                    if (activeImage) {{
                        // Apply border if requested
                        if ({str(has_border).lower()}) {{
                            setImageBorderStyle('solid', {border_width}, getImageBorderColor());
                        }}
                        
                        // Apply alignment if not floating
                        if (!{str(is_floating).lower()}) {{
                            const alignMap = {{
                                'left': 'left-align',
                                'center': 'center-align',
                                'right': 'right-align',
                                'block': 'no-wrap'
                            }};
                            
                            setImageAlignment(alignMap['{position}'] || 'no-wrap');
                        }}
                    }}
                }}, 50);
                
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

    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return f"""
        {self.image_theme_helpers_js()}
        {self.image_handles_css_js()}
        {self.image_insert_functions_js()}
        {self.image_activation_js()}
        {self.image_drag_resize_js()}
        {self.image_alignment_js()}
        {self.image_floating_js()}
        {self.image_border_style_js()}
        {self.image_event_handlers_js()}
        """

    def image_theme_helpers_js(self):
        """JavaScript helper functions for theme detection and colors"""
        return """
        // Function to get appropriate border color based on current theme for images
        function getImageBorderColor() {
            return isDarkMode() ? '#444' : '#ccc';
        }
        """

    def image_handles_css_js(self):
        """JavaScript that defines CSS for image handles with proper display properties"""
        return """
        // CSS for image handles
        const imageHandlesCSS = `
        /* Image drag handle - positioned in the top-left corner */
        .image-drag-handle {
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

        /* Image resize handle - triangular shape in bottom right */
        .image-resize-handle {
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
        
        /* Floating image styles */
        .floating-image {
            position: absolute !important;
            z-index: 50;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            cursor: grab;
        }
        
        .floating-image:active {
            cursor: grabbing;
        }
        
        .floating-image .image-drag-handle {
            width: 20px !important;
            height: 20px !important;
            border-radius: 3px;
            opacity: 0.9;
        }
        
        .floating-image:focus {
            outline: 2px solid #4e9eff;
        }
        
        .image-selected {
            outline: 2px solid #4e9eff;
            outline-offset: 2px;
            position: relative;
        }

        @media (prefers-color-scheme: dark) {
            .image-drag-handle {
                background-color: #0078d7;
            }
            .image-resize-handle {
                border-color: transparent transparent #0078d7 transparent;
            }
            .floating-image {
                box-shadow: 0 3px 10px rgba(0,0,0,0.5);
            }
            .floating-image .image-drag-handle {
                background-color: #0078d7;
            }
            .image-selected {
                outline-color: #0078d7;
            }
        }`;
        
        // Function to add the image handle styles to the document
        function addImageHandleStyles() {
            // Check if our style element already exists
            let styleElement = document.getElementById('image-handle-styles');
            
            // If not, create and append it
            if (!styleElement) {
                styleElement = document.createElement('style');
                styleElement.id = 'image-handle-styles';
                styleElement.textContent = imageHandlesCSS;
                document.head.appendChild(styleElement);
            } else {
                // If it exists, update the content
                styleElement.textContent = imageHandlesCSS;
            }
        }
        """

    def image_insert_functions_js(self):
        """JavaScript for inserting images with default properties"""
        return """
        // Function to insert an image at the current cursor position
        function insertImage(src, alt, width, height, isFloating) {
            // Create a new image element
            let imageWrapper = document.createElement('span');
            imageWrapper.className = 'editor-image-wrapper';
            imageWrapper.style.display = 'inline-block';
            imageWrapper.style.position = 'relative';
            imageWrapper.style.margin = '6px 6px 0 0';
            
            // Store margin values as attributes for later reference
            imageWrapper.setAttribute('data-margin-top', '6');
            imageWrapper.setAttribute('data-margin-right', '6');
            imageWrapper.setAttribute('data-margin-bottom', '0');
            imageWrapper.setAttribute('data-margin-left', '0');
            
            let img = document.createElement('img');
            
            // Set attributes
            img.src = src;
            img.alt = alt || '';
            
            // Set size if provided
            if (width) {
                img.width = width;
                img.setAttribute('data-original-width', width);
            }
            if (height) {
                img.height = height;
                img.setAttribute('data-original-height', height);
            }
            
            // Store original dimensions for resizing proportionally
            if (!img.hasAttribute('data-original-width') && img.width) {
                img.setAttribute('data-original-width', img.width);
            }
            if (!img.hasAttribute('data-original-height') && img.height) {
                img.setAttribute('data-original-height', img.height);
            }
            
            // Add the image to the wrapper
            imageWrapper.appendChild(img);
            
            // Make the wrapper floating if requested
            if (isFloating) {
                imageWrapper.classList.add('floating-image');
                setImageFloating(imageWrapper);
            }
            
            // Insert the wrapper at current selection
            document.execCommand('insertHTML', false, imageWrapper.outerHTML);
            
            // Find and activate the newly inserted image wrapper
            setTimeout(() => {
                const wrappers = document.querySelectorAll('.editor-image-wrapper');
                const newWrapper = wrappers[wrappers.length - 1];
                if (newWrapper) {
                    activateImage(newWrapper);
                    try {
                        window.webkit.messageHandlers.imageClicked.postMessage({
                            src: src,
                            alt: alt || '',
                            width: width || '',
                            height: height || ''
                        });
                    } catch(e) {
                        console.log("Could not notify about image click:", e);
                    }
                }
            }, 10);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage("changed");
            } catch(e) {
                console.log("Could not notify about changes:", e);
            }
        }
        """

    def image_activation_js(self):
        """JavaScript for image activation and deactivation"""
        return """
        // Variables for image handling
        var activeImage = null;
        var isImageDragging = false;
        var isImageResizing = false;
        var imageDragStartX = 0;
        var imageDragStartY = 0;
        var imageStartX = 0;
        var imageStartY = 0;
        var imageStartWidth = 0;
        var imageStartHeight = 0;
        
        // Function to find parent image element
        function findParentImage(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'IMG' || 
                    (element.classList && element.classList.contains('editor-image-wrapper'))) {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Function to activate an image (add handles)
        function activateImage(imageElement) {
            if (activeImage === imageElement) return; // Already active
            
            // Deactivate any previously active images
            if (activeImage && activeImage !== imageElement) {
                deactivateImage(activeImage);
            }
            
            // If we got an IMG element, use its parent wrapper if available
            if (imageElement.tagName === 'IMG' && 
                imageElement.parentNode && 
                imageElement.parentNode.classList && 
                imageElement.parentNode.classList.contains('editor-image-wrapper')) {
                imageElement = imageElement.parentNode;
            }
            
            // If we still have an IMG without wrapper, wrap it
            if (imageElement.tagName === 'IMG') {
                const wrapper = document.createElement('span');
                wrapper.className = 'editor-image-wrapper';
                wrapper.style.display = 'inline-block';
                wrapper.style.position = 'relative';
                
                // Insert wrapper before the image
                imageElement.parentNode.insertBefore(wrapper, imageElement);
                // Move the image into the wrapper
                wrapper.appendChild(imageElement);
                
                // Use the wrapper as our active element
                imageElement = wrapper;
            }
            
            activeImage = imageElement;
            
            // Add selected class
            activeImage.classList.add('image-selected');
            
            // Ensure the wrapper has editor-image-wrapper class
            if (!activeImage.classList.contains('editor-image-wrapper')) {
                activeImage.classList.add('editor-image-wrapper');
            }
            
            // Ensure the wrapper has position: relative for proper handle positioning (if not floating)
            if (!activeImage.classList.contains('floating-image')) {
                activeImage.style.position = 'relative';
            }
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return;
            
            // Store original dimensions if not already stored
            if (!imgElement.hasAttribute('data-original-width') && imgElement.width) {
                imgElement.setAttribute('data-original-width', imgElement.width);
            }
            if (!imgElement.hasAttribute('data-original-height') && imgElement.height) {
                imgElement.setAttribute('data-original-height', imgElement.height);
            }
            
            // Add resize handle if needed
            if (!activeImage.querySelector('.image-resize-handle')) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'image-resize-handle';
                
                // Make handle non-selectable and prevent focus
                resizeHandle.setAttribute('contenteditable', 'false');
                resizeHandle.setAttribute('unselectable', 'on');
                resizeHandle.setAttribute('tabindex', '-1');
                
                // Add event listener
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startImageResize(e, imageElement);
                }, true);
                
                activeImage.appendChild(resizeHandle);
            }
            
            // Add drag handle if needed
            if (!activeImage.querySelector('.image-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'image-drag-handle';
                dragHandle.innerHTML = '↕';
                
                // Set title based on whether it's a floating image or not
                if (activeImage.classList.contains('floating-image')) {
                    dragHandle.title = 'Drag to move image freely';
                } else {
                    dragHandle.title = 'Drag to reposition image between paragraphs';
                }
                
                // Make handle non-selectable and prevent focus
                dragHandle.setAttribute('contenteditable', 'false');
                dragHandle.setAttribute('unselectable', 'on');
                dragHandle.setAttribute('tabindex', '-1');
                
                // Add event listener
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startImageDrag(e, imageElement);
                }, true);
                
                activeImage.appendChild(dragHandle);
            }
            
            // Special styling for floating images
            if (activeImage.classList.contains('floating-image')) {
                enhanceImageDragHandles(activeImage);
            }
        }
        
        // Function to deactivate a specific image
        function deactivateImage(imageElement) {
            if (!imageElement) return;
            
            // Remove selected class
            imageElement.classList.remove('image-selected');
            
            // Remove handles
            const resizeHandle = imageElement.querySelector('.image-resize-handle');
            if (resizeHandle) resizeHandle.remove();
            
            const dragHandle = imageElement.querySelector('.image-drag-handle');
            if (dragHandle) dragHandle.remove();
            
            if (imageElement === activeImage) {
                activeImage = null;
            }
        }
        
        // Function to deactivate all images
        function deactivateAllImages() {
            const images = document.querySelectorAll('.editor-image-wrapper');
            
            images.forEach(image => {
                deactivateImage(image);
            });
            
            // Always notify that images are deactivated
            activeImage = null;
            try {
                window.webkit.messageHandlers.imagesDeactivated.postMessage('images-deactivated');
            } catch(e) {
                console.log("Could not notify about image deactivation:", e);
            }
        }
        """

    def image_drag_resize_js(self):
        """JavaScript for image dragging and resizing"""
        return """
        // Function to start image drag
        function startImageDrag(e, imageElement) {
            e.preventDefault();
            if (!imageElement) return;
            
            isImageDragging = true;
            activeImage = imageElement;
            imageDragStartX = e.clientX;
            imageDragStartY = e.clientY;
            
            // Set cursor based on whether the image is floating or not
            if (imageElement.classList.contains('floating-image')) {
                document.body.style.cursor = 'grabbing';
                
                // Store the initial position for floating images
                const style = window.getComputedStyle(imageElement);
                imageStartX = parseInt(style.left) || 0;
                imageStartY = parseInt(style.top) || 0;
            } else {
                document.body.style.cursor = 'move';
            }
        }
        
        // Function to move image
        function moveImage(e) {
            if (!isImageDragging || !activeImage) return;
            
            // Check if the image is a floating image
            if (activeImage.classList.contains('floating-image')) {
                // For floating images, move to the mouse position with offset
                const deltaX = e.clientX - imageDragStartX;
                const deltaY = e.clientY - imageDragStartY;
                
                // Update position
                activeImage.style.left = `${imageStartX + deltaX}px`;
                activeImage.style.top = `${imageStartY + deltaY}px`;
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            } else {
                const currentY = e.clientY;
                const deltaY = currentY - imageDragStartY;
                
                if (Math.abs(deltaY) > 30) {
                    const editor = document.getElementById('editor');
                    const blocks = Array.from(editor.children).filter(node => {
                        const style = window.getComputedStyle(node);
                        return style.display.includes('block') || node.tagName === 'TABLE' || 
                               node.classList.contains('editor-image-wrapper');
                    });
                    
                    const imageIndex = blocks.indexOf(activeImage);
                    
                    if (deltaY < 0 && imageIndex > 0) {
                        const targetElement = blocks[imageIndex - 1];
                        editor.insertBefore(activeImage, targetElement);
                        imageDragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    } 
                    else if (deltaY > 0 && imageIndex < blocks.length - 1) {
                        const targetElement = blocks[imageIndex + 1];
                        if (targetElement.nextSibling) {
                            editor.insertBefore(activeImage, targetElement.nextSibling);
                        } else {
                            editor.appendChild(activeImage);
                        }
                        imageDragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            }
        }
        
        // Function to start image resize
        function startImageResize(e, imageElement) {
            e.preventDefault();
            isImageResizing = true;
            activeImage = imageElement;
            imageDragStartX = e.clientX;
            imageDragStartY = e.clientY;
            
            // Find the actual IMG element
            const imgElement = imageElement.querySelector('img');
            if (!imgElement) return;
            
            // Store initial size
            imageStartWidth = imgElement.width || imgElement.offsetWidth;
            imageStartHeight = imgElement.height || imgElement.offsetHeight;
        }
        
        // Function to resize image
        function resizeImage(e) {
            if (!isImageResizing || !activeImage) return;
            
            // Find the actual IMG element
            const imgElement = activeImage.querySelector('img');
            if (!imgElement) return;
            
            const deltaX = e.clientX - imageDragStartX;
            const deltaY = e.clientY - imageDragStartY;
            
            // Get original aspect ratio if stored
            let originalWidth = parseInt(imgElement.getAttribute('data-original-width'));
            let originalHeight = parseInt(imgElement.getAttribute('data-original-height'));
            let aspectRatio = originalWidth && originalHeight ? originalWidth / originalHeight : imageStartWidth / imageStartHeight;
            
            // Calculate new dimensions
            let newWidth = Math.max(20, imageStartWidth + deltaX);
            let newHeight = Math.round(newWidth / aspectRatio);
            
            // Apply new dimensions
            imgElement.width = newWidth;
            imgElement.height = newHeight;
            
            // Notify that the image has been resized
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """

    def image_alignment_js(self):
        """JavaScript for image alignment"""
        return """
        // Function to set image alignment
        function setImageAlignment(alignClass) {
            if (!activeImage) return;
            
            // Remove all alignment classes
            activeImage.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap', 'floating-image');
            
            // Add the requested alignment class
            activeImage.classList.add(alignClass);
            
            // Reset positioning if it was previously floating
            if (activeImage.style.position === 'absolute') {
                activeImage.style.position = 'relative';
                activeImage.style.top = '';
                activeImage.style.left = '';
                activeImage.style.zIndex = '';
            }
            
            // Update image display style based on alignment
            if (alignClass === 'left-align') {
                activeImage.style.display = 'inline-block';
                activeImage.style.float = 'left';
                activeImage.style.marginRight = '10px';
            } else if (alignClass === 'right-align') {
                activeImage.style.display = 'inline-block';
                activeImage.style.float = 'right';
                activeImage.style.marginLeft = '10px';
            } else if (alignClass === 'center-align') {
                activeImage.style.display = 'block';
                activeImage.style.float = 'none';
                activeImage.style.marginLeft = 'auto';
                activeImage.style.marginRight = 'auto';
            } else if (alignClass === 'no-wrap') {
                activeImage.style.display = 'block';
                activeImage.style.float = 'none';
                activeImage.style.marginLeft = '0';
                activeImage.style.marginRight = '0';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """
        
    def image_floating_js(self):
        """JavaScript for floating image functionality"""
        return """
        // Function to make an image floating (freely positionable)
        function setImageFloating(imageElement) {
            if (!imageElement && activeImage) {
                imageElement = activeImage;
            }
            
            if (!imageElement) return;
            
            // First, remove any alignment classes
            imageElement.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            
            // Reset any float styles
            imageElement.style.float = 'none';
            
            // Add floating class for special styling
            imageElement.classList.add('floating-image');
            
            // Set positioning to absolute
            imageElement.style.position = 'absolute';
            
            // Calculate initial position - center in the visible editor area
            const editorRect = document.getElementById('editor').getBoundingClientRect();
            const imageRect = imageElement.getBoundingClientRect();
            
            // Set initial position
            const editorScrollTop = document.getElementById('editor').scrollTop;
            
            // Position in the middle of the visible editor area
            const topPos = (editorRect.height / 2) - (imageRect.height / 2) + editorScrollTop;
            const leftPos = (editorRect.width / 2) - (imageRect.width / 2);
            
            imageElement.style.top = `${Math.max(topPos, editorScrollTop)}px`;
            imageElement.style.left = `${Math.max(leftPos, 0)}px`;
            
            // Enhance the drag handle for position control
            enhanceImageDragHandles(imageElement);
            
            // Ensure proper z-index to be above regular content
            imageElement.style.zIndex = "50";
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            // Activate the image to show handles
            if (imageElement !== activeImage) {
                activateImage(imageElement);
            }
        }
        
        // Add enhanced drag handling for floating images
        function enhanceImageDragHandles(imageElement) {
            if (!imageElement) return;
            
            // Find or create the drag handle
            let dragHandle = imageElement.querySelector('.image-drag-handle');
            if (!dragHandle) {
                // If it doesn't exist, we might need to activate the image first
                activateImage(imageElement);
                dragHandle = imageElement.querySelector('.image-drag-handle');
            }
            
            if (dragHandle) {
                // Update tooltip to reflect new functionality
                dragHandle.title = "Drag to move image freely";
                
                // Make the drag handle more visible for floating images
                dragHandle.style.width = "20px";
                dragHandle.style.height = "20px";
                dragHandle.style.backgroundColor = "#4e9eff";
                dragHandle.style.borderRadius = "3px";
                dragHandle.style.opacity = "0.9";
            }
        }
        """

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
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
