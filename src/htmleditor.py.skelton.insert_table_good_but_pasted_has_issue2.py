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
        """JavaScript for insert table with border-only dragging, cell-level text selection and copy-paste support"""
        return """
        /**
         * JavaScript for table insertion with border-only dragging, cell text selection and copy-paste support
         */
        function insertTable(rows, cols, hasHeader, borderWidth, width) {
            // Generate the table HTML
            let tableHTML = `<table contenteditable="true" style="border-collapse: collapse; border: ${borderWidth}px solid #ccc; width: ${width};" class="editable-table">`;
            
            // Create header row if requested
            if (hasHeader) {
                tableHTML += '<thead><tr>';
                for (let c = 0; c < cols; c++) {
                    tableHTML += `<th style="border: ${borderWidth}px solid #ccc; padding: 8px;">Header ${c+1}</th>`;
                }
                tableHTML += '</tr></thead>';
            }
            
            // Create table body
            tableHTML += '<tbody>';
            for (let r = 0; r < rows; r++) {
                tableHTML += '<tr>';
                for (let c = 0; c < cols; c++) {
                    tableHTML += `<td style="border: ${borderWidth}px solid #ccc; padding: 8px;">Cell ${r+1},${c+1}</td>`;
                }
                tableHTML += '</tr>';
            }
            tableHTML += '</tbody></table><p></p>';
            
            // Insert the table at the cursor position
            document.execCommand('insertHTML', false, tableHTML);
            
            // Find the newly inserted table and initialize dragging and resizing
            setTimeout(() => {
                const tables = document.querySelectorAll('table.editable-table:not(.table-initialized)');
                tables.forEach(table => {
                    initializeTable(table);
                    table.classList.add('table-initialized');
                });
                
                // Activate the most recently added table
                if (tables.length > 0) {
                    activateTable(tables[tables.length - 1]);
                }
            }, 10);
        }

        // Track the active table and its state
        let activeTable = null;
        let isDragging = false;
        let isResizing = false;
        let dragStartX, dragStartY, originalLeft, originalTop, originalWidth, originalHeight;

        // Function to set up event listeners for a table
        function initializeTable(table) {
            // Add the editable-table class if it doesn't have it
            if (!table.classList.contains('editable-table')) {
                table.classList.add('editable-table');
            }
            
            // Make the table position relative to support absolute positioning
            table.style.position = 'relative';
            
            // Create invisible drag border area (initially hidden, but will be functional when activated)
            const dragBorder = document.createElement('div');
            dragBorder.className = 'table-drag-border';
            dragBorder.style.display = 'none';
            dragBorder.style.position = 'absolute';
            dragBorder.style.top = '-8px';
            dragBorder.style.left = '-8px';
            dragBorder.style.right = '-8px';
            dragBorder.style.bottom = '-8px';
            dragBorder.style.zIndex = '999';
            dragBorder.style.pointerEvents = 'none'; // Initially no events
            
            // Create 4 drag handles, one for each side
            const sides = [
                { className: 'top', top: '-8px', left: '0', right: '0', height: '8px', cursor: 'move' },
                { className: 'right', top: '0', right: '-8px', bottom: '0', width: '8px', cursor: 'move' },
                { className: 'bottom', bottom: '-8px', left: '0', right: '0', height: '8px', cursor: 'move' },
                { className: 'left', top: '0', left: '-8px', bottom: '0', width: '8px', cursor: 'move' }
            ];
            
            sides.forEach(side => {
                const handle = document.createElement('div');
                handle.className = `table-border-handle table-border-${side.className}`;
                handle.style.display = 'none';
                handle.style.position = 'absolute';
                handle.style.zIndex = '1000';
                
                // Apply specific side properties
                Object.keys(side).forEach(key => {
                    if (key !== 'className') {
                        handle.style[key] = side[key];
                    }
                });
                
                // Handle drag start
                handle.addEventListener('mousedown', startDragging);
                table.appendChild(handle);
            });
            
            // Create corner handles
            const corners = [
                { className: 'top-left', top: '-8px', left: '-8px', width: '8px', height: '8px', cursor: 'move' },
                { className: 'top-right', top: '-8px', right: '-8px', width: '8px', height: '8px', cursor: 'move' },
                { className: 'bottom-left', bottom: '-8px', left: '-8px', width: '8px', height: '8px', cursor: 'move' }
                // Bottom-right is handled by resize handle
            ];
            
            corners.forEach(corner => {
                const handle = document.createElement('div');
                handle.className = `table-border-handle table-border-${corner.className}`;
                handle.style.display = 'none';
                handle.style.position = 'absolute';
                handle.style.backgroundColor = '#4a90e2';
                handle.style.borderRadius = '50%';
                handle.style.zIndex = '1000';
                
                // Apply specific corner properties
                Object.keys(corner).forEach(key => {
                    if (key !== 'className') {
                        handle.style[key] = corner[key];
                    }
                });
                
                // Handle drag start
                handle.addEventListener('mousedown', startDragging);
                table.appendChild(handle);
            });
            
            // Create resize handle (initially hidden)
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'table-resize-handle';
            resizeHandle.style.display = 'none';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.width = '30px';
            resizeHandle.style.height = '30px';
            resizeHandle.style.bottom = '-4px';
            resizeHandle.style.right = '-4px';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.backgroundImage = 'linear-gradient(135deg, transparent 50%, rgba(74, 144, 226, 0.7) 50%)';
            resizeHandle.style.zIndex = '1000';
            table.appendChild(resizeHandle);
            
            // Dragging function - bound to the context of the dragged table
            function startDragging(e) {
                e.preventDefault();
                e.stopPropagation();
                isDragging = true;
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                originalLeft = table.offsetLeft;
                originalTop = table.offsetTop;
                
                // Apply floating style
                table.style.position = 'absolute';
                table.style.left = originalLeft + 'px';
                table.style.top = originalTop + 'px';
                
                // Prevent selecting text while dragging
                document.body.style.userSelect = 'none';
            }
            
            // Add click listener to activate table, but without starting drag
            table.addEventListener('click', (e) => {
                // Only activate the table, don't start dragging
                activateTable(table);
                
                // Event propagation continues to allow normal cell editing
            });
            
            // Handle resize handle
            resizeHandle.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                isResizing = true;
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                originalWidth = table.offsetWidth;
                originalHeight = table.offsetHeight;
            });
            
            // Add a close button floating at the top-right of the table
            const closeButton = document.createElement('div');
            closeButton.className = 'table-close-button';
            closeButton.style.display = 'none';
            closeButton.style.position = 'absolute';
            closeButton.style.top = '-12px';
            closeButton.style.right = '-12px';
            closeButton.style.width = '24px';
            closeButton.style.height = '24px';
            closeButton.style.borderRadius = '50%';
            closeButton.style.backgroundColor = '#ff6b6b';
            closeButton.style.color = 'white';
            closeButton.style.display = 'flex';
            closeButton.style.alignItems = 'center';
            closeButton.style.justifyContent = 'center';
            closeButton.style.cursor = 'pointer';
            closeButton.style.fontWeight = 'bold';
            closeButton.style.fontSize = '14px';
            closeButton.style.zIndex = '1001';
            closeButton.style.boxShadow = '0 0 3px rgba(0, 0, 0, 0.3)';
            closeButton.innerHTML = '×';
            
            closeButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                table.remove();
            });
            
            table.appendChild(closeButton);
            
            // Setup cell-level selection
            setupCellLevelSelection(table);
            
            // Mark this table as initialized
            table.classList.add('table-initialized');
        }
        
        // Function to set up cell-level text selection
        function setupCellLevelSelection(table) {
            const cells = table.querySelectorAll('th, td');
            
            cells.forEach(cell => {
                // Handle Ctrl+A inside cells
                cell.addEventListener('keydown', function(e) {
                    if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
                        e.stopPropagation(); // Stop propagation to prevent selecting the whole document
                        e.preventDefault(); // Prevent default Ctrl+A behavior
                        
                        // Select all content in the current cell
                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(this);
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                });
                
                // Handle triple-click for cell selection
                let clickCount = 0;
                let clickTimer = null;
                
                cell.addEventListener('click', function(e) {
                    clickCount++;
                    
                    if (clickCount === 1) {
                        clickTimer = setTimeout(() => {
                            clickCount = 0;
                        }, 500); // Reset after 500ms
                    } else if (clickCount === 3) {
                        // Triple click detected, select all content in the cell
                        e.stopPropagation();
                        e.preventDefault();
                        
                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(this);
                        selection.removeAllRanges();
                        selection.addRange(range);
                        
                        clearTimeout(clickTimer);
                        clickCount = 0;
                    }
                });
            });
        }

        // Function to activate a table (show handles)
        function activateTable(table) {
            // Deactivate previous active table if exists
            if (activeTable && activeTable !== table) {
                deactivateTable(activeTable);
            }
            
            // Set this as the active table
            activeTable = table;
            
            // Show all border handles
            const borderHandles = table.querySelectorAll('.table-border-handle');
            borderHandles.forEach(handle => {
                handle.style.display = 'block';
            });
            
            // Show the resize handle
            const resizeHandle = table.querySelector('.table-resize-handle');
            if (resizeHandle) {
                resizeHandle.style.display = 'block';
            }
            
            // Show the close button
            const closeButton = table.querySelector('.table-close-button');
            if (closeButton) {
                closeButton.style.display = 'flex';
            }
            
            // Apply active style - subtle outline
            table.style.outline = '2px solid rgba(74, 144, 226, 0.5)';
            table.style.outlineOffset = '2px';
            
            // Notify system about table activation
            try {
                window.webkit.messageHandlers.tableActivated.postMessage('active');
            } catch(e) {
                console.log("Could not notify about table activation:", e);
            }
        }

        // Function to deactivate a table (hide handles)
        function deactivateTable(table) {
            // Hide all border handles
            const borderHandles = table.querySelectorAll('.table-border-handle');
            borderHandles.forEach(handle => {
                handle.style.display = 'none';
            });
            
            // Hide the resize handle
            const resizeHandle = table.querySelector('.table-resize-handle');
            if (resizeHandle) {
                resizeHandle.style.display = 'none';
            }
            
            // Hide the close button
            const closeButton = table.querySelector('.table-close-button');
            if (closeButton) {
                closeButton.style.display = 'none';
            }
            
            // Remove active style
            table.style.outline = '';
            table.style.outlineOffset = '';
        }
        
        // Setup observer to detect DOM changes (for pasted tables)
        function setupMutationObserver() {
            // Create a new observer
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach((node) => {
                            // Check if the added node is a table
                            if (node.nodeName === 'TABLE') {
                                if (!node.classList.contains('table-initialized')) {
                                    initializeTable(node);
                                }
                            } else if (node.nodeType === Node.ELEMENT_NODE) {
                                // Look for tables inside the added node
                                const tables = node.querySelectorAll('table:not(.table-initialized)');
                                tables.forEach(table => {
                                    initializeTable(table);
                                });
                            }
                        });
                    }
                });
            });
            
            // Start observing the document with the configured parameters
            observer.observe(document.getElementById('editor'), { 
                childList: true,
                subtree: true
            });
            
            return observer;
        }
        
        // Add handler for paste events (to catch pasted tables)
        function setupPasteHandling() {
            document.getElementById('editor').addEventListener('paste', (e) => {
                // Use a short timeout to let the paste complete first
                setTimeout(() => {
                    // Find and initialize any uninitalized tables
                    const tables = document.querySelectorAll('table:not(.table-initialized)');
                    tables.forEach(table => {
                        initializeTable(table);
                    });
                }, 10);
            });
        }
        
        // Setup global mouse event handlers
        document.addEventListener('mousemove', (e) => {
            if (isDragging && activeTable) {
                const dx = e.clientX - dragStartX;
                const dy = e.clientY - dragStartY;
                activeTable.style.left = (originalLeft + dx) + 'px';
                activeTable.style.top = (originalTop + dy) + 'px';
            } else if (isResizing && activeTable) {
                const dx = e.clientX - dragStartX;
                const dy = e.clientY - dragStartY;
                activeTable.style.width = (originalWidth + dx) + 'px';
                activeTable.style.height = (originalHeight + dy) + 'px';
            }
        });
        
        // Global mouse up handler
        document.addEventListener('mouseup', () => {
            isDragging = false;
            isResizing = false;
            document.body.style.userSelect = '';
        });
        
        // Click event outside tables to deactivate
        document.addEventListener('click', (e) => {
            if (!e.target.closest('table') && activeTable) {
                deactivateTable(activeTable);
                activeTable = null;
            }
        });
        
        // Initialize mutation observer once DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            setupMutationObserver();
            setupPasteHandling();
            
            // Initial scan for any tables already in the document
            const existingTables = document.querySelectorAll('table:not(.table-initialized)');
            existingTables.forEach(table => {
                initializeTable(table);
            });
        });
        """
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




         
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
