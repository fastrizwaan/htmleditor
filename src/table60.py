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
        
        # Add key event controller to capture Shift+Tab
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_webview_key_pressed)
        win.webview.add_controller(key_controller)
        
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
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return """
        // Table state variables
        let currentTable = null;
        let selectionStart = null;
        let selectionEnd = null;
        let isSelecting = false;
        let isEditing = false;
        let currentEditCell = null;
        
        // Table insertion function
        function insertTable(rows, cols) {
            const table = document.createElement('table');
            table.style.borderCollapse = 'collapse';
            table.style.width = '100%';
            table.style.cursor = 'cell';
            table.setAttribute('contenteditable', 'false');
            
            // Create table rows and cells
            for (let i = 0; i < rows; i++) {
                const row = document.createElement('tr');
                for (let j = 0; j < cols; j++) {
                    const cell = document.createElement('td');
                    cell.style.border = '1px solid #ddd';
                    cell.style.padding = '8px';
                    cell.style.minWidth = '80px';
                    cell.style.minHeight = '25px';
                    cell.style.position = 'relative';
                    cell.style.outline = 'none';
                    cell.setAttribute('data-row', i);
                    cell.setAttribute('data-col', j);
                    cell.classList.add('table-cell');
                    
                    // Add cell content
                    const cellContent = document.createElement('div');
                    cellContent.classList.add('cell-content');
                    cellContent.style.minHeight = 'inherit';
                    cellContent.textContent = '';
                    cell.appendChild(cellContent);
                    
                    row.appendChild(cell);
                }
                table.appendChild(row);
            }
            
            // Insert table at current selection
            const editor = document.getElementById('editor');
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);
            
            // Wrap table in a div for better positioning
            const tableWrapper = document.createElement('div');
            tableWrapper.style.margin = '10px 0';
            tableWrapper.appendChild(table);
            
            range.insertNode(tableWrapper);
            range.collapse(false);
            
            // Initialize table event handlers
            initializeTableEvents(table);
            
            // Update undo stack
            saveState();
        }
        
        // Initialize table events
        function initializeTableEvents(table) {
            table.addEventListener('click', handleTableClick);
            table.addEventListener('dblclick', handleTableDoubleClick);
            table.addEventListener('mousedown', handleTableMouseDown);
            table.addEventListener('mousemove', handleTableMouseMove);
            table.addEventListener('mouseup', handleTableMouseUp);
            table.addEventListener('keydown', handleTableKeyDown);
            
            // Set as current table
            currentTable = table;
        }
        
        // Handle cell click - selection mode
        function handleTableClick(e) {
            const cell = e.target.closest('td');
            if (!cell) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            // If already editing, don't change mode
            if (isEditing && currentEditCell === cell) return;
            
            // Exit editing mode if clicking different cell
            if (isEditing) {
                exitEditMode();
            }
            
            // Enter selection mode
            clearSelection();
            selectCell(cell);
            cell.focus();
        }
        
        // Handle double click - enter edit mode
        function handleTableDoubleClick(e) {
            const cell = e.target.closest('td');
            if (!cell) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            enterEditMode(cell);
        }
        
        // Handle key events in table
        function handleTableKeyDown(e) {
            const cell = document.activeElement.closest('td');
            if (!cell) return;
            
            if (isEditing) {
                // Handle editing mode keys
                if (e.key === 'Escape') {
                    exitEditMode(true); // Cancel changes
                } else if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    exitEditMode();
                    // Move to next cell
                    const nextCell = getNextCell(cell, 'down');
                    if (nextCell) {
                        selectCell(nextCell);
                        nextCell.focus();
                    }
                }
            } else {
                // Handle selection mode keys
                if (e.key === 'Enter' || (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey)) {
                    e.preventDefault();
                    enterEditMode(cell, e.key.length === 1 ? e.key : null);
                } else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft' || 
                          e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    navigateTable(cell, e.key);
                }
            }
        }
        
        // Enter edit mode
        function enterEditMode(cell, initialChar = null) {
            if (isEditing) exitEditMode();
            
            isEditing = true;
            currentEditCell = cell;
            
            const cellContent = cell.querySelector('.cell-content');
            cellContent.setAttribute('contenteditable', 'true');
            cellContent.focus();
            
            // Clear selection highlight
            cell.classList.remove('selected');
            cell.style.border = '2px solid #0078d4';
            
            // If initial character, clear content and insert it
            if (initialChar) {
                cellContent.textContent = initialChar;
                // Move cursor to end
                const range = document.createRange();
                const sel = window.getSelection();
                range.selectNodeContents(cellContent);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
            } else {
                // Select all content
                const range = document.createRange();
                range.selectNodeContents(cellContent);
                const sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            }
        }
        
        // Exit edit mode
        function exitEditMode(cancel = false) {
            if (!isEditing) return;
            
            const cellContent = currentEditCell.querySelector('.cell-content');
            if (cancel) {
                // Restore original content (would need to implement)
            }
            
            cellContent.setAttribute('contenteditable', 'false');
            cellContent.blur();
            
            currentEditCell.style.border = '1px solid #ddd';
            isEditing = false;
            currentEditCell = null;
            
            // Save content changes
            saveState();
        }
        
        // Select single cell
        function selectCell(cell) {
            clearSelection();
            cell.classList.add('selected');
            cell.style.border = '2px solid #0078d4';
            addResizeHandle(cell);
            selectionStart = selectionEnd = cell;
        }
        
        // Clear selection
        function clearSelection() {
            if (currentTable) {
                currentTable.querySelectorAll('.selected').forEach(cell => {
                    cell.classList.remove('selected');
                    cell.style.border = '1px solid #ddd';
                    const handle = cell.querySelector('.resize-handle');
                    if (handle) handle.remove();
                });
            }
            selectionStart = selectionEnd = null;
        }
        
        // Add resize handle to cell
        function addResizeHandle(cell) {
            const handle = document.createElement('div');
            handle.className = 'resize-handle';
            handle.style.position = 'absolute';
            handle.style.right = '-4px';
            handle.style.bottom = '-4px';
            handle.style.width = '8px';
            handle.style.height = '8px';
            handle.style.background = '#0078d4';
            handle.style.cursor = 'crosshair';
            cell.appendChild(handle);
        }
        
        // Handle mouse down for selection
        function handleTableMouseDown(e) {
            const handle = e.target.closest('.resize-handle');
            if (handle) {
                e.preventDefault();
                isSelecting = true;
                return;
            }
        }
        
        // Handle mouse move for selection
        function handleTableMouseMove(e) {
            if (!isSelecting) return;
            
            const cell = e.target.closest('td');
            if (!cell || !selectionStart) return;
            
            // Update selection range
            selectionEnd = cell;
            updateSelectionRange();
        }
        
        // Handle mouse up for selection
        function handleTableMouseUp(e) {
            isSelecting = false;
        }
        
        // Update selection range between start and end cells
        function updateSelectionRange() {
            if (!selectionStart || !selectionEnd) return;
            
            clearSelection();
            
            const startRow = parseInt(selectionStart.getAttribute('data-row'));
            const startCol = parseInt(selectionStart.getAttribute('data-col'));
            const endRow = parseInt(selectionEnd.getAttribute('data-row'));
            const endCol = parseInt(selectionEnd.getAttribute('data-col'));
            
            const minRow = Math.min(startRow, endRow);
            const maxRow = Math.max(startRow, endRow);
            const minCol = Math.min(startCol, endCol);
            const maxCol = Math.max(startCol, endCol);
            
            for (let i = minRow; i <= maxRow; i++) {
                for (let j = minCol; j <= maxCol; j++) {
                    const cell = currentTable.querySelector(`td[data-row="${i}"][data-col="${j}"]`);
                    if (cell) {
                        cell.classList.add('selected');
                        cell.style.border = '2px solid #0078d4';
                        
                        // Add resize handle to bottom-right cell
                        if (i === maxRow && j === maxCol) {
                            addResizeHandle(cell);
                        }
                    }
                }
            }
        }
        
        // Navigate table with arrow keys
        function navigateTable(cell, key) {
            const nextCell = getNextCell(cell, key);
            if (nextCell) {
                selectCell(nextCell);
                nextCell.focus();
            }
        }
        
        // Get next cell based on arrow key
        function getNextCell(cell, direction) {
            const row = parseInt(cell.getAttribute('data-row'));
            const col = parseInt(cell.getAttribute('data-col'));
            
            let nextRow = row;
            let nextCol = col;
            
            switch (direction) {
                case 'ArrowRight':
                    nextCol++;
                    break;
                case 'ArrowLeft':
                    nextCol--;
                    break;
                case 'ArrowDown':
                case 'down':
                    nextRow++;
                    break;
                case 'ArrowUp':
                    nextRow--;
                    break;
            }
            
            return currentTable.querySelector(`td[data-row="${nextRow}"][data-col="${nextCol}"]`);
        }
        
        // Global click handler to exit edit mode when clicking outside
        document.addEventListener('click', function(e) {
            if (isEditing && !e.target.closest('td')) {
                exitEditMode();
            }
        });
        
        // Add CSS styles for table
        const style = document.createElement('style');
        style.textContent = `
            .table-cell.selected {
                background-color: rgba(0, 120, 212, 0.1);
            }
            .table-cell:focus {
                outline: none;
            }
            .resize-handle:hover {
                background-color: #005a9e !important;
            }
            .cell-content {
                outline: none;
                min-height: inherit;
                padding: 2px;
            }
            .cell-content[contenteditable="true"] {
                background-color: white;
            }
        `;
        document.head.appendChild(style);
        """

    def on_insert_table_clicked(self, win, btn):
        """Show table insertion dialog"""
        dialog = Adw.MessageDialog.new(win)
        dialog.set_heading("Insert Table")
        dialog.set_body("Choose table dimensions:")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("insert", "Insert")
        dialog.set_response_appearance("insert", Adw.ResponseAppearance.SUGGESTED)
        
        # Create dialog content
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Rows input
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_label = Gtk.Label(label="Rows:")
        row_spin = Gtk.SpinButton.new_with_range(1, 20, 1)
        row_spin.set_value(3)
        row_box.append(row_label)
        row_box.append(row_spin)
        
        # Columns input
        col_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        col_label = Gtk.Label(label="Columns:")
        col_spin = Gtk.SpinButton.new_with_range(1, 20, 1)
        col_spin.set_value(3)
        col_box.append(col_label)
        col_box.append(col_spin)
        
        box.append(row_box)
        box.append(col_box)
        
        dialog.set_extra_child(box)
        
        def on_response(dialog, response):
            if response == "insert":
                rows = int(row_spin.get_value())
                cols = int(col_spin.get_value())
                
                # Insert table using JavaScript
                js_code = f"insertTable({rows}, {cols});"
                win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
         
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
