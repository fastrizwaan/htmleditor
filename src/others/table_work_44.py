#!/usr/bin/env python3
import sys
import gi
import re
import os

# Hardware Accelerated Rendering (0); Software Rendering (1)
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

        # Window properties
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None
        
    def do_startup(self):
        """Initialize application and set up CSS provider"""
        Adw.Application.do_startup(self)
        self.setup_css_provider()

    def setup_css_provider(self):
        """Set up CSS provider for custom styling"""
        self.css_provider = Gtk.CssProvider()
        
        css_data = b"""
        .flat { background: none; }
        .flat:hover { background: rgba(127, 127, 127, 0.25); }
        .flat:checked { background: rgba(127, 127, 127, 0.25); }
        .suggested-action { background: #3584e4; color: white; }
        """
        
        try:
            self.css_provider.load_from_data(css_data)
        except Exception as e:
            print(f"Error loading CSS data: {e}")
            return
        
        try:
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except (AttributeError, TypeError) as e:
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
        GLib.timeout_add(500, lambda: self.set_initial_focus(win))
        
    def setup_headerbar_content(self, win):
        """Create simplified headerbar content (menu and window buttons)"""
        win.headerbar.set_margin_top(0)
        win.headerbar.set_margin_bottom(0)
        
        title_widget = Adw.WindowTitle()
        title_widget.set_title("Untitled - HTML Editor")
        win.title_widget = title_widget
        
        win.headerbar.set_title_widget(title_widget)

    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        insert_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        insert_group.add_css_class("linked")
        insert_group.set_margin_start(6)

        table_button = Gtk.Button(icon_name="table-symbolic")
        table_button.set_size_request(40, 36)
        table_button.set_tooltip_text("Insert Table")
        table_button.connect("clicked", lambda btn: self.on_insert_table_clicked(win, btn))

        text_box_button = Gtk.Button(icon_name="insert-text-symbolic")
        text_box_button.set_size_request(40, 36)
        text_box_button.set_tooltip_text("Insert Text Box")
        text_box_button.connect("clicked", lambda btn: self.on_insert_text_box_clicked(win, btn))

        image_button = Gtk.Button(icon_name="insert-image-symbolic")
        image_button.set_size_request(40, 36)
        image_button.set_tooltip_text("Insert Image")
        image_button.connect("clicked", lambda btn: self.on_insert_image_clicked(win, btn))

        link_button = Gtk.Button(icon_name="insert-link-symbolic")
        link_button.set_size_request(40, 36)
        link_button.set_tooltip_text("Insert link")
        link_button.connect("clicked", lambda btn: self.on_insert_link_clicked(win, btn))

        insert_group.append(table_button)
        insert_group.append(text_box_button)
        insert_group.append(image_button)
        insert_group.append(link_button)
        file_toolbar.append(insert_group)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar

    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return """
        function insertTable(rows, cols, hasHeader) {
            console.log('insertTable called with rows=' + rows + ', cols=' + cols + ', hasHeader=' + hasHeader);
            let tableHtml = '<table border="1">';
            if (hasHeader) {
                tableHtml += '<tr>';
                for (let i = 0; i < cols; i++) {
                    tableHtml += '<th contenteditable="true">Header ' + (i+1) + '</th>';
                }
                tableHtml += '</tr>';
                rows--;
            }
            for (let r = 0; r < rows; r++) {
                tableHtml += '<tr>';
                for (let c = 0; c < cols; c++) {
                    tableHtml += '<td contenteditable="true"><br></td>';
                }
                tableHtml += '</tr>';
            }
            tableHtml += '</table><p><br></p>';
            const editor = document.getElementById('editor');
            if (!editor) {
                console.error('Editor element not found');
                return;
            }
            try {
                editor.focus();
                const success = document.execCommand('insertHTML', false, tableHtml);
                if (!success) {
                    console.warn('document.execCommand failed, using innerHTML');
                    const range = document.getSelection().getRangeAt(0);
                    range.deleteContents();
                    const div = document.createElement('div');
                    div.innerHTML = tableHtml;
                    range.insertNode(div);
                }
                const tables = editor.querySelectorAll('table');
                const insertedTable = tables[tables.length - 1];
                const firstCell = insertedTable.querySelector('td, th');
                if (firstCell) {
                    const range = document.createRange();
                    range.selectNodeContents(firstCell);
                    range.collapse(true);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                    firstCell.focus();
                }
                console.log('Table insertion completed');
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify content change:", e);
                }
            } catch (e) {
                console.error('Error inserting table:', e);
            }
        }

        function getCurrentCell() {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return null;
            let node = selection.anchorNode;
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            while (node && node.tagName !== 'TD' && node.tagName !== 'TH') {
                node = node.parentNode;
            }
            return node && (node.tagName === 'TD' || node.tagName === 'TH') ? node : null;
        }

        function getRow(cell) {
            return cell.parentNode;
        }

        function getTable(cell) {
            let node = cell;
            while (node && node.tagName !== 'TABLE') {
                node = node.parentNode;
            }
            return node;
        }

        function getRowIndex(row) {
            return Array.prototype.indexOf.call(row.parentNode.children, row);
        }

        function getCellIndex(cell) {
            return Array.prototype.indexOf.call(cell.parentNode.children, cell);
        }

        function getNextCell(cell) {
            const row = getRow(cell);
            const table = getTable(cell);
            const rowIndex = getRowIndex(row);
            const cellIndex = getCellIndex(cell);
            if (cellIndex < row.children.length - 1) {
                return row.children[cellIndex + 1];
            } else if (rowIndex < table.rows.length - 1) {
                return table.rows[rowIndex + 1].cells[0];
            } else {
                const newRow = table.insertRow();
                for (let i = 0; i < row.children.length; i++) {
                    const newCell = newRow.insertCell();
                    newCell.innerHTML = '<br>';
                    newCell.setAttribute('contenteditable', 'true');
                }
                return newRow.cells[0];
            }
        }

        function getPreviousCell(cell) {
            const row = getRow(cell);
            const table = getTable(cell);
            const rowIndex = getRowIndex(row);
            const cellIndex = getCellIndex(cell);
            if (cellIndex > 0) {
                return row.children[cellIndex - 1];
            } else if (rowIndex > 0) {
                const prevRow = table.rows[rowIndex - 1];
                return prevRow.cells[prevRow.cells.length - 1];
            } else {
                return null;
            }
        }
        """

    def insert_text_box_js(self):
        return """ """

    def insert_image_js(self):
        return """ """

    def insert_link_js(self):
        return """ """

    def on_insert_table_clicked(self, win, btn):
        # Create a modal window as a dialog
        dialog = Gtk.Window(
            title="Insert Table",
            transient_for=win,
            modal=True,
            default_width=300,
            default_height=200
        )
        
        # Create a vertical box for content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        dialog.set_child(content_box)
        
        # Add input fields using a grid
        rows_label = Gtk.Label(label="Rows:")
        rows_label.set_halign(Gtk.Align.START)
        rows_entry = Gtk.SpinButton.new_with_range(1, 100, 1)
        rows_entry.set_value(3)
        
        cols_label = Gtk.Label(label="Columns:")
        cols_label.set_halign(Gtk.Align.START)
        cols_entry = Gtk.SpinButton.new_with_range(1, 100, 1)
        cols_entry.set_value(3)
        
        header_check = Gtk.CheckButton(label="Include header row")
        header_check.set_active(True)
        
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.attach(rows_label, 0, 0, 1, 1)
        grid.attach(rows_entry, 1, 0, 1, 1)
        grid.attach(cols_label, 0, 1, 1, 1)
        grid.attach(cols_entry, 1, 1, 1, 1)
        grid.attach(header_check, 0, 2, 2, 1)
        
        content_box.append(grid)
        
        # Create a horizontal box for buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        content_box.append(button_box)
        
        # Add Cancel and Insert buttons
        cancel_button = Gtk.Button(label="_Cancel")
        insert_button = Gtk.Button(label="_Insert")
        insert_button.add_css_class("suggested-action")
        button_box.append(cancel_button)
        button_box.append(insert_button)
        
        # Define the insert action with error handling
        def insert_table(_btn):
            try:
                rows = rows_entry.get_value_as_int()
                cols = cols_entry.get_value_as_int()
                has_header = header_check.get_active()
                js_code = f"""
                console.log('Attempting to insert table with rows={rows}, cols={cols}, hasHeader={str(has_header).lower()}');
                if (typeof insertTable === 'function') {{
                    insertTable({rows}, {cols}, {str(has_header).lower()});
                    console.log('Table inserted successfully');
                }} else {{
                    console.error('insertTable function not defined');
                }}
                """
                print(f"Executing JavaScript: {js_code}")
                win.webview.evaluate_javascript(
                    js_code,
                    -1,
                    None,
                    None,
                    None,
                    lambda obj, result, user_data: print("JavaScript executed successfully"),
                    lambda obj, result, error, user_data: print(f"JavaScript error: {error}")
                )
                dialog.close()
            except Exception as e:
                print(f"Error in insert_table: {e}")
                dialog.close()
        
        # Connect button signals
        insert_button.connect("clicked", insert_table)
        cancel_button.connect("clicked", lambda _btn: dialog.close())
        
        # Show the dialog
        dialog.present()

    def on_insert_text_box_clicked(self, win, btn):
        return
        
    def on_insert_image_clicked(self, win, btn):
        return

    def on_insert_link_clicked(self, win, btn):
        return

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

        function saveState() {{
            window.undoStack.push(window.lastContent);
            if (window.undoStack.length > 50) {{
                window.undoStack.shift();
            }}
        }}

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
            if (!editor) {
                console.error('Editor element not found in setContent');
                return;
            }
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
            if (!editor) {
                console.error('Editor element not found');
                return;
            }
            
            editor.setAttribute('tabindex', '0');
            editor.setAttribute('contenteditable', 'true');
            
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    e.stopPropagation();
                    const currentCell = getCurrentCell();
                    if (currentCell) {
                        let targetCell;
                        if (e.shiftKey) {
                            targetCell = getPreviousCell(currentCell);
                        } else {
                            targetCell = getNextCell(currentCell);
                        }
                        if (targetCell) {
                            const range = document.createRange();
                            range.selectNodeContents(targetCell);
                            range.collapse(true);
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            targetCell.focus();
                        }
                    } else {
                        document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
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
        
    def get_initial_html(self):
        return self.get_editor_html('<div><font face="Sans" style="font-size: 11pt;"><br></font></div>')
    
    def set_initial_focus(self, win):
        """Set focus to the WebView and its editor element after window is shown"""
        try:
            win.webview.grab_focus()
            
            js_code = """
            (function() {
                const editor = document.getElementById('editor');
                if (!editor) {
                    console.error('Editor element not found');
                    return false;
                }
                
                editor.focus();
                
                try {
                    const range = document.createRange();
                    const sel = window.getSelection();
                    
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
                    console.error("Error setting cursor position:", e);
                }
                
                return true;
            })();
            """
            
            win.webview.evaluate_javascript(
                js_code,
                -1,
                None,
                None,
                None,
                lambda obj, result, user_data: print("Initial focus JavaScript executed"),
                lambda obj, result, error, user_data: print(f"Initial focus JavaScript error: {error}")
            )
            return False
        except Exception as e:
            print(f"Error setting initial focus: {e}")
            return False

    def create_window(self):
        """Create a new window with all initialization"""
        win = Adw.ApplicationWindow(application=self)
        
        win.modified = False
        win.auto_save_enabled = False
        win.auto_save_interval = 60
        win.current_file = None
        win.auto_save_source_id = None
        
        win.set_default_size(800, 600)
        win.set_title("Untitled - HTML Editor")
        
        win.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.main_box.set_vexpand(True)
        win.main_box.set_hexpand(True)
        
        win.headerbar_revealer = Gtk.Revealer()
        win.headerbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.headerbar_revealer.set_margin_start(0)
        win.headerbar_revealer.set_margin_end(0)
        win.headerbar_revealer.set_margin_top(0)
        win.headerbar_revealer.set_margin_bottom(0)
        win.headerbar_revealer.set_transition_duration(250)
        win.headerbar_revealer.set_reveal_child(True)
        
        win.headerbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        win.headerbar = Adw.HeaderBar()
        win.headerbar.add_css_class("flat-header")
        self.setup_headerbar_content(win)
        win.headerbar_box.append(win.headerbar)
        
        win.file_toolbar_revealer = Gtk.Revealer()
        win.file_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.file_toolbar_revealer.set_transition_duration(250)
        win.file_toolbar_revealer.set_reveal_child(True)
        
        win.file_toolbar = self.create_file_toolbar(win)
        win.file_toolbar_revealer.set_child(win.file_toolbar)
        win.headerbar_box.append(win.file_toolbar_revealer)
        
        win.headerbar_revealer.set_child(win.headerbar_box)
        win.main_box.append(win.headerbar_revealer)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        win.webview = WebKit.WebView()
        win.webview.set_vexpand(True)
        win.webview.set_hexpand(True)
        
        # Connect load-changed to ensure HTML is loaded
        win.webview.connect("load-changed", self.on_webview_load_changed)
        
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_webview_key_pressed)
        win.webview.add_controller(key_controller)
        
        # Load initial HTML only once
        win.webview.load_html(self.get_initial_html(), None)
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
                        
        content_box.append(win.webview)

        win.statusbar_revealer = Gtk.Revealer()
        win.statusbar_revealer.add_css_class("flat-header")
        win.statusbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.statusbar_revealer.set_transition_duration(250)
        win.statusbar_revealer.set_reveal_child(True)
        
        statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        statusbar_box.set_margin_start(10)
        statusbar_box.set_margin_end(10)
        statusbar_box.set_margin_top(0)
        statusbar_box.set_margin_bottom(4)
        
        win.statusbar = Gtk.Label(label="Ready")
        win.statusbar.set_halign(Gtk.Align.START)
        win.statusbar.set_hexpand(True)
        statusbar_box.append(win.statusbar)
        
        win.statusbar_revealer.set_child(statusbar_box)
        content_box.append(win.statusbar_revealer)

        win.main_box.append(content_box)
        win.set_content(win.main_box)

        case_change_action = Gio.SimpleAction.new("change-case", GLib.VariantType.new("s"))
        case_change_action.connect("activate", lambda action, param: self.on_change_case(win, param.get_string()))
        win.add_action(case_change_action)
        
        self.windows.append(win)

        return win

    def on_webview_load_changed(self, webview, load_event):
        """Handle WebView load changes to ensure JavaScript is ready"""
        if load_event == WebKit.LoadEvent.FINISHED:
            print("WebView load finished")
            js_code = """
            if (document.getElementById('editor')) {
                console.log('Editor found, contenteditable=' + document.getElementById('editor').contentEditable);
            } else {
                console.error('Editor element not found');
            }
            if (typeof insertTable === 'function') {
                console.log('insertTable function is defined');
            } else {
                console.error('insertTable function not defined');
            }
            """
            webview.evaluate_javascript(
                js_code,
                -1,
                None,
                None,
                None,
                lambda obj, result, user_data: print("Load check JavaScript executed"),
                lambda obj, result, error, user_data: print(f"Load check JavaScript error: {error}")
            )

    def on_webview_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events on the webview"""
        if keyval == Gdk.KEY_ISO_Left_Tab or (keyval == Gdk.KEY_Tab and (state & Gdk.ModifierType.SHIFT_MASK)):
            return True
        return False

    def on_content_changed(self, win, manager, message):
        """Handle content changes from the editor"""
        win.modified = True
        self.update_window_title(win)
        win.statusbar.set_text("Content modified")

    def update_window_title(self, win):
        """Update window title to reflect modified state"""
        if win.current_file:
            filename = os.path.basename(win.current_file)
            title = f"{filename}{' *' if win.modified else ''} - HTML Editor"
        else:
            title = f"Untitled{' *' if win.modified else ''} - HTML Editor"
        win.set_title(title)

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
                    margin: 0;
                    padding: 0;
                    font-family: Sans;
                }}
                #editor {{
                    padding: 10px;
                    outline: none;
                    height: 100%;
                    box-sizing: border-box;
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
                table {{
                    border-collapse: collapse;
                    margin: 10px 0;
                }}
                td, th {{
                    border: 1px solid #ccc;
                    padding: 5px;
                    min-width: 100px;
                    vertical-align: top;
                }}
                @media (prefers-color-scheme: light) {{
                    html, body {{
                        background-color: #ffffff;
                        color: #000000;
                    }}
                }}
            </style>
            <script>
                window.initialContent = "{content}";
                {self.get_editor_js()}
            </script>
        </head>
        <body>
            <div id="editor" contenteditable="true"></div>
        </body>
        </html>
        """
#########################
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return """
        let activeTable = null;
        let isResizing = false;
        let resizeData = null;
        let isDragging = false;
        let dragData = null;

        function insertTable(rows, cols, hasHeader) {
            console.log('insertTable called with rows=' + rows + ', cols=' + cols + ', hasHeader=' + hasHeader);
            let tableHtml = '<table class="resizable-table" border="1" style="min-width: 100px; margin: 10px 0;">';
            if (hasHeader) {
                tableHtml += '<tr>';
                for (let i = 0; i < cols; i++) {
                    tableHtml += '<th contenteditable="true">Header ' + (i+1) + '</th>';
                }
                tableHtml += '</tr>';
                rows--;
            }
            for (let r = 0; r < rows; r++) {
                tableHtml += '<tr>';
                for (let c = 0; c < cols; c++) {
                    tableHtml += '<td contenteditable="true"><br></td>';
                }
                tableHtml += '</tr>';
            }
            tableHtml += '</table><p><br></p>';
            const editor = document.getElementById('editor');
            if (!editor) {
                console.error('Editor element not found');
                return;
            }
            try {
                editor.focus();
                const success = document.execCommand('insertHTML', false, tableHtml);
                if (!success) {
                    console.warn('document.execCommand failed, using innerHTML');
                    const range = document.getSelection().getRangeAt(0);
                    range.deleteContents();
                    const div = document.createElement('div');
                    div.innerHTML = tableHtml;
                    range.insertNode(div);
                }
                const tables = editor.querySelectorAll('table');
                const insertedTable = tables[tables.length - 1];
                makeTableResizable(insertedTable);
                const firstCell = insertedTable.querySelector('td, th');
                if (firstCell) {
                    const range = document.createRange();
                    range.selectNodeContents(firstCell);
                    range.collapse(true);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                    firstCell.focus();
                }
                console.log('Table insertion completed');
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify content change:", e);
                }
            } catch (e) {
                console.error('Error inserting table:', e);
            }
        }

        function makeTableResizable(table) {
            if (!table || table.dataset.resizable === 'true') return;
            
            table.dataset.resizable = 'true';
            table.style.position = 'relative';
            
            // Create handles container
            const handleContainer = document.createElement('div');
            handleContainer.className = 'table-handles';
            handleContainer.contentEditable = 'false';
            handleContainer.style.position = 'absolute';
            handleContainer.style.top = '0';
            handleContainer.style.left = '0';
            handleContainer.style.width = '100%';
            handleContainer.style.height = '100%';
            handleContainer.style.pointerEvents = 'none';
            handleContainer.style.display = 'none';
            
            // Create move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.contentEditable = 'false';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '5px';
            moveHandle.style.left = '5px';
            moveHandle.style.width = '15px';
            moveHandle.style.height = '15px';
            moveHandle.style.backgroundColor = '#3584e4';
            moveHandle.style.borderRadius = '3px';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            
            // Create resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.contentEditable = 'false';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '1px';
            resizeHandle.style.right = '1px';
            resizeHandle.style.width = '0';
            resizeHandle.style.height = '0';
            resizeHandle.style.borderStyle = 'solid';
            resizeHandle.style.borderWidth = '0 0 10px 10px';
            resizeHandle.style.borderColor = 'transparent transparent #3584e4 transparent';
            resizeHandle.style.cursor = 'se-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            
            handleContainer.appendChild(moveHandle);
            handleContainer.appendChild(resizeHandle);
            table.style.position = 'relative';
            table.appendChild(handleContainer);
            
            // Add click handler to toggle handles
            table.addEventListener('click', function(e) {
                if (e.target.closest('.move-handle') || e.target.closest('.resize-handle')) {
                    return;
                }
                
                // Hide handles on all other tables
                document.querySelectorAll('.table-handles').forEach(handles => {
                    if (handles !== handleContainer) {
                        handles.style.display = 'none';
                    }
                });
                
                // Toggle handles for this table
                handleContainer.style.display = handleContainer.style.display === 'none' ? 'block' : 'none';
                activeTable = handleContainer.style.display === 'block' ? table : null;
            });
            
            // Add move functionality
            moveHandle.addEventListener('mousedown', startDragging);
            
            // Add resize functionality
            resizeHandle.addEventListener('mousedown', startResizing);
            
            // Make cells resizable
            table.querySelectorAll('td, th').forEach(cell => {
                makeCellResizable(cell);
            });
        }

        function makeCellResizable(cell) {
            cell.style.position = 'relative';
            cell.style.minWidth = '30px';
            cell.style.minHeight = '20px';
            
            // Create column resize handle
            const colResizeHandle = document.createElement('div');
            colResizeHandle.className = 'col-resize-handle';
            colResizeHandle.contentEditable = 'false';
            colResizeHandle.style.position = 'absolute';
            colResizeHandle.style.top = '0';
            colResizeHandle.style.right = '-3px';
            colResizeHandle.style.width = '6px';
            colResizeHandle.style.height = '100%';
            colResizeHandle.style.cursor = 'col-resize';
            colResizeHandle.style.zIndex = '999';
            
            // Create row resize handle
            const rowResizeHandle = document.createElement('div');
            rowResizeHandle.className = 'row-resize-handle';
            rowResizeHandle.contentEditable = 'false';
            rowResizeHandle.style.position = 'absolute';
            rowResizeHandle.style.left = '0';
            rowResizeHandle.style.bottom = '-3px';
            rowResizeHandle.style.width = '100%';
            rowResizeHandle.style.height = '6px';
            rowResizeHandle.style.cursor = 'row-resize';
            rowResizeHandle.style.zIndex = '999';
            
            cell.appendChild(colResizeHandle);
            cell.appendChild(rowResizeHandle);
            
            colResizeHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                startColumnResize(e, cell);
            });
            
            rowResizeHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                startRowResize(e, cell);
            });
        }

        function startDragging(e) {
            e.preventDefault();
            e.stopPropagation();
            isDragging = true;
            
            const table = e.target.closest('table');
            const rect = table.getBoundingClientRect();
            
            dragData = {
                table: table,
                startX: e.clientX,
                startY: e.clientY,
                tableStartX: rect.left,
                tableStartY: rect.top
            };
            
            document.addEventListener('mousemove', handleDragging);
            document.addEventListener('mouseup', stopDragging);
        }

        function handleDragging(e) {
            if (!isDragging || !dragData) return;
            
            const dx = e.clientX - dragData.startX;
            const dy = e.clientY - dragData.startY;
            
            const newLeft = dragData.tableStartX + dx;
            const newTop = dragData.tableStartY + dy;
            
            dragData.table.style.position = 'relative';
            dragData.table.style.left = dx + 'px';
            dragData.table.style.top = dy + 'px';
        }

        function stopDragging() {
            isDragging = false;
            dragData = null;
            document.removeEventListener('mousemove', handleDragging);
            document.removeEventListener('mouseup', stopDragging);
        }

        function startResizing(e) {
            e.preventDefault();
            e.stopPropagation();
            isResizing = true;
            
            const table = e.target.closest('table');
            const rect = table.getBoundingClientRect();
            
            resizeData = {
                table: table,
                startX: e.clientX,
                startY: e.clientY,
                startWidth: rect.width,
                startHeight: rect.height
            };
            
            document.addEventListener('mousemove', handleResizing);
            document.addEventListener('mouseup', stopResizing);
        }

        function handleResizing(e) {
            if (!isResizing || !resizeData) return;
            
            const dx = e.clientX - resizeData.startX;
            const dy = e.clientY - resizeData.startY;
            
            const newWidth = Math.max(100, resizeData.startWidth + dx);
            const newHeight = Math.max(50, resizeData.startHeight + dy);
            
            resizeData.table.style.width = newWidth + 'px';
            resizeData.table.style.height = newHeight + 'px';
        }

        function stopResizing() {
            isResizing = false;
            resizeData = null;
            document.removeEventListener('mousemove', handleResizing);
            document.removeEventListener('mouseup', stopResizing);
        }

        function startColumnResize(e, cell) {
            e.preventDefault();
            e.stopPropagation();
            
            const table = cell.closest('table');
            const colIndex = Array.from(cell.parentNode.children).indexOf(cell);
            
            resizeData = {
                table: table,
                colIndex: colIndex,
                startX: e.clientX,
                startWidth: cell.offsetWidth,
                minWidth: 30
            };
            
            document.addEventListener('mousemove', handleColumnResize);
            document.addEventListener('mouseup', stopColumnResize);
        }

        function handleColumnResize(e) {
            if (!resizeData) return;
            
            const dx = e.clientX - resizeData.startX;
            const newWidth = Math.max(resizeData.minWidth, resizeData.startWidth + dx);
            
            // Update all cells in the column
            const rows = resizeData.table.rows;
            for (let i = 0; i < rows.length; i++) {
                const cell = rows[i].cells[resizeData.colIndex];
                if (cell) {
                    cell.style.width = newWidth + 'px';
                    cell.style.minWidth = newWidth + 'px';
                }
            }
        }

        function stopColumnResize() {
            resizeData = null;
            document.removeEventListener('mousemove', handleColumnResize);
            document.removeEventListener('mouseup', stopColumnResize);
        }

        function startRowResize(e, cell) {
            e.preventDefault();
            e.stopPropagation();
            
            const row = cell.parentNode;
            
            resizeData = {
                row: row,
                startY: e.clientY,
                startHeight: row.offsetHeight,
                minHeight: 20
            };
            
            document.addEventListener('mousemove', handleRowResize);
            document.addEventListener('mouseup', stopRowResize);
        }

        function handleRowResize(e) {
            if (!resizeData) return;
            
            const dy = e.clientY - resizeData.startY;
            const newHeight = Math.max(resizeData.minHeight, resizeData.startHeight + dy);
            
            resizeData.row.style.height = newHeight + 'px';
            
            // Update all cells in the row
            Array.from(resizeData.row.cells).forEach(cell => {
                cell.style.height = newHeight + 'px';
                cell.style.minHeight = newHeight + 'px';
            });
        }

        function stopRowResize() {
            resizeData = null;
            document.removeEventListener('mousemove', handleRowResize);
            document.removeEventListener('mouseup', stopRowResize);
        }

        function getCurrentCell() {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return null;
            let node = selection.anchorNode;
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            while (node && node.tagName !== 'TD' && node.tagName !== 'TH') {
                node = node.parentNode;
            }
            return node && (node.tagName === 'TD' || node.tagName === 'TH') ? node : null;
        }

        function getRow(cell) {
            return cell.parentNode;
        }

        function getTable(cell) {
            let node = cell;
            while (node && node.tagName !== 'TABLE') {
                node = node.parentNode;
            }
            return node;
        }

        function getRowIndex(row) {
            return Array.prototype.indexOf.call(row.parentNode.children, row);
        }

        function getCellIndex(cell) {
            return Array.prototype.indexOf.call(cell.parentNode.children, cell);
        }

        function getNextCell(cell) {
            const row = getRow(cell);
            const table = getTable(cell);
            const rowIndex = getRowIndex(row);
            const cellIndex = getCellIndex(cell);
            if (cellIndex < row.children.length - 1) {
                return row.children[cellIndex + 1];
            } else if (rowIndex < table.rows.length - 1) {
                return table.rows[rowIndex + 1].cells[0];
            } else {
                const newRow = table.insertRow();
                for (let i = 0; i < row.children.length; i++) {
                    const newCell = newRow.insertCell();
                    newCell.innerHTML = '<br>';
                    newCell.setAttribute('contenteditable', 'true');
                    makeCellResizable(newCell);
                }
                return newRow.cells[0];
            }
        }

        function getPreviousCell(cell) {
            const row = getRow(cell);
            const table = getTable(cell);
            const rowIndex = getRowIndex(row);
            const cellIndex = getCellIndex(cell);
            if (cellIndex > 0) {
                return row.children[cellIndex - 1];
            } else if (rowIndex > 0) {
                const prevRow = table.rows[rowIndex - 1];
                return prevRow.cells[prevRow.cells.length - 1];
            } else {
                return null;
            }
        }
        """

    def insert_text_box_js(self):
        return """ """

    def insert_image_js(self):
        return """ """

    def insert_link_js(self):
        return """ """

    def on_insert_table_clicked(self, win, btn):
        # Create a modal window as a dialog
        dialog = Gtk.Window(
            title="Insert Table",
            transient_for=win,
            modal=True,
            default_width=300,
            default_height=200
        )
        
        # Create a vertical box for content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        dialog.set_child(content_box)
        
        # Add input fields using a grid
        rows_label = Gtk.Label(label="Rows:")
        rows_label.set_halign(Gtk.Align.START)
        rows_entry = Gtk.SpinButton.new_with_range(1, 100, 1)
        rows_entry.set_value(3)
        
        cols_label = Gtk.Label(label="Columns:")
        cols_label.set_halign(Gtk.Align.START)
        cols_entry = Gtk.SpinButton.new_with_range(1, 100, 1)
        cols_entry.set_value(3)
        
        header_check = Gtk.CheckButton(label="Include header row")
        header_check.set_active(True)
        
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.attach(rows_label, 0, 0, 1, 1)
        grid.attach(rows_entry, 1, 0, 1, 1)
        grid.attach(cols_label, 0, 1, 1, 1)
        grid.attach(cols_entry, 1, 1, 1, 1)
        grid.attach(header_check, 0, 2, 2, 1)
        
        content_box.append(grid)
        
        # Create a horizontal box for buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        content_box.append(button_box)
        
        # Add Cancel and Insert buttons
        cancel_button = Gtk.Button(label="_Cancel")
        insert_button = Gtk.Button(label="_Insert")
        insert_button.add_css_class("suggested-action")
        button_box.append(cancel_button)
        button_box.append(insert_button)
        
        # Define the insert action with error handling
        def insert_table(_btn):
            try:
                rows = rows_entry.get_value_as_int()
                cols = cols_entry.get_value_as_int()
                has_header = header_check.get_active()
                js_code = f"""
                console.log('Attempting to insert table with rows={rows}, cols={cols}, hasHeader={str(has_header).lower()}');
                if (typeof insertTable === 'function') {{
                    insertTable({rows}, {cols}, {str(has_header).lower()});
                    console.log('Table inserted successfully');
                }} else {{
                    console.error('insertTable function not defined');
                }}
                """
                print(f"Executing JavaScript: {js_code}")
                win.webview.evaluate_javascript(
                    js_code,
                    -1,
                    None,
                    None,
                    None,
                    lambda obj, result, user_data: print("JavaScript executed successfully"),
                    lambda obj, result, error, user_data: print(f"JavaScript error: {error}")
                )
                dialog.close()
            except Exception as e:
                print(f"Error in insert_table: {e}")
                dialog.close()
        
        # Connect button signals
        insert_button.connect("clicked", insert_table)
        cancel_button.connect("clicked", lambda _btn: dialog.close())
        
        # Show the dialog
        dialog.present()

    def on_insert_text_box_clicked(self, win, btn):
        return
        
    def on_insert_image_clicked(self, win, btn):
        return

    def on_insert_link_clicked(self, win, btn):
        return

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

        function saveState() {{
            window.undoStack.push(window.lastContent);
            if (window.undoStack.length > 50) {{
                window.undoStack.shift();
            }}
        }}

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
            if (!editor) {
                console.error('Editor element not found in setContent');
                return;
            }
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
            
            // Make any existing tables resizable
            editor.querySelectorAll('table').forEach(table => {
                makeTableResizable(table);
            });
        }
        """

    def init_editor_js(self):
        """JavaScript to initialize the editor and set up event listeners."""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            if (!editor) {
                console.error('Editor element not found');
                return;
            }
            
            editor.setAttribute('tabindex', '0');
            editor.setAttribute('contenteditable', 'true');
            
            // Click outside tables to hide handles
            document.addEventListener('click', function(e) {
                if (!e.target.closest('table') && !e.target.closest('.table-handles')) {
                    document.querySelectorAll('.table-handles').forEach(handles => {
                        handles.style.display = 'none';
                    });
                    activeTable = null;
                }
            });
            
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    e.stopPropagation();
                    const currentCell = getCurrentCell();
                    if (currentCell) {
                        let targetCell;
                        if (e.shiftKey) {
                            targetCell = getPreviousCell(currentCell);
                        } else {
                            targetCell = getNextCell(currentCell);
                        }
                        if (targetCell) {
                            const range = document.createRange();
                            range.selectNodeContents(targetCell);
                            range.collapse(true);
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            targetCell.focus();
                        }
                    } else {
                        document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
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
            
            // Make existing tables resizable on paste
            editor.addEventListener('paste', function(e) {
                setTimeout(() => {
                    editor.querySelectorAll('table').forEach(table => {
                        if (table.dataset.resizable !== 'true') {
                            makeTableResizable(table);
                        }
                    });
                }, 100);
            });
        });
        """
         
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())
