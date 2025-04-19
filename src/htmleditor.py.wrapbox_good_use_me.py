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

# Import file operation functions directly
import file_operations # open, save, save as
import find
import formatting_operations

class HTMLEditorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='io.github.fastrizwaan.htmleditor',
                        flags=Gio.ApplicationFlags.HANDLES_OPEN,
                        **kwargs)
        self.windows = []  # Track all open windows
        self.window_buttons = {}  # Track window menu buttons {window_id: button}
        self.connect('activate', self.on_activate)
        self.connect("open", self.on_open)
        
        # Window properties (migrated from HTMLEditorWindow)
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None
        
        # Import methods from file_operations module
        file_operation_methods = [
            # File opening methods
            'on_open_clicked', 'on_open_new_window_response',
            'on_open_current_window_response', 'load_file',
            '_process_image_references', '_get_mime_type', 'cleanup_temp_files',
            'convert_with_libreoffice', 'show_loading_dialog',
            
            # File saving methods
            'on_save_clicked', 'show_format_selection_dialog', 'on_save_as_clicked', 'show_custom_save_dialog',
            '_create_custom_save_dialog', '_get_shortened_path',
            '_on_browse_clicked','_on_dialog_response', '_on_format_selection_response',
            '_on_folder_selected', 'show_save_as_warning_dialog', '_on_save_warning_response',
            '_get_file_path_from_dialog', 'show_conversion_notification', 
            'update_save_sensitivity', 
            
            
            # Format-specific save methods
            'save_as_mhtml', 'save_webkit_callback', 'save_as_html',
            'save_as_text','save_as_markdown', '_simple_markdown_to_html',

            # Save as PDF
            'save_as_pdf', '_save_pdf_step1', '_save_pdf_step2', '_pdf_save_success',
            '_pdf_save_cleanup', '_cleanup_temp_dir', 'set_secondary_text'
            # Callback handlers
            'save_html_callback', 'save_text_callback',
            'save_markdown_callback', 'save_completion_callback',
            
            # Legacy methods for backward compatibility
            '_on_save_response', '_on_save_as_response', '_on_get_html_content',
            '_on_file_saved',
            
            # webkit
            '_on_editor_ready_for_mhtml', '_check_mhtml_load_status', 
            '_handle_mhtml_load_check', '_check_mhtml_load_error',
            'load_mhtml_with_webkit', '_load_mhtml_file', '_process_mhtml_resources',
            '_extract_mhtml_content', '_on_mhtml_content_extracted',
        ]
        
        # Import methods from file_operations
        for method_name in file_operation_methods:
            if hasattr(file_operations, method_name):
                setattr(self, method_name, getattr(file_operations, method_name).__get__(self, HTMLEditorApp))
                
        # Import methods from find module
        find_methods = [
            'create_find_bar', 'on_find_shortcut', 'on_find_clicked',
            'on_close_find_clicked', 'on_case_sensitive_toggled',
            'on_find_text_changed', 'on_search_result', 'on_find_next_clicked',
            'on_find_previous_clicked', 'on_replace_clicked', 
            'on_replace_all_clicked', 'on_replace_all_result', 
            'on_find_key_pressed', 'on_find_button_toggled',
            'populate_find_field_from_selection', '_on_get_selection_for_find',
            'search_functions_js'
        ]
        
        # Import methods from find module
        for method_name in find_methods:
            if hasattr(find, method_name):
                setattr(self, method_name, getattr(find, method_name).__get__(self, HTMLEditorApp))

        # Import methods from formatting_toolbar module
        formatting_toolbar_methods = [
            'create_formatting_toolbar', 'on_bold_shortcut', 'on_italic_shortcut',
            'on_underline_shortcut', 'on_strikeout_shortcut', 'on_subscript_shortcut',
            'on_superscript_shortcut', 'on_bold_toggled', 'on_italic_toggled',
            'on_underline_toggled', 'on_strikeout_toggled', 'on_subscript_toggled',
            'on_superscript_toggled', 'on_formatting_changed', 'on_indent_clicked',
            'on_outdent_clicked', 'on_bullet_list_toggled', 'on_numbered_list_toggled',
            '_update_alignment_buttons', 'on_align_left_toggled', 'on_align_center_toggled',
            'on_align_right_toggled', 'on_align_justify_toggled', '_update_alignment_buttons',
            'selection_change_js', 'on_paragraph_style_changed', 'on_font_changed',
            'on_font_size_changed', 'cleanup_editor_tags', 'create_color_button',
            'on_font_color_button_clicked', 'on_font_color_selected', 'on_font_color_automatic_clicked',
            'on_more_font_colors_clicked', 'on_font_color_dialog_response', 'apply_font_color',
            'on_bg_color_button_clicked', 'on_bg_color_selected', 'on_bg_color_automatic_clicked',
            'on_more_bg_colors_clicked', 'on_bg_color_dialog_response', 'apply_bg_color',
            'set_box_color', 'on_clear_formatting_clicked', 'on_change_case',
        ]

        # Import methods from formatting_toolbar module
        for method_name in formatting_toolbar_methods:
            if hasattr(formatting_operations, method_name):
                setattr(self, method_name, getattr(formatting_operations, method_name).__get__(self, HTMLEditorApp))
        
    def do_startup(self):
        """Initialize application and set up CSS provider"""
        Adw.Application.do_startup(self)
        
        # Set up CSS provider
        self.setup_css_provider()
        
        # Create actions
        self.create_actions()


    def setup_css_provider(self):
        """Set up CSS provider for custom styling"""
        self.css_provider = Gtk.CssProvider()
        
        css_data = b"""
.toolbar-container { padding: 0px 0px; background-color: rgba(127, 127, 127, 0.05); }
.flat { background: none; }
.flat:hover { background: rgba(127, 127, 127, 0.25); }
.flat:checked { background: rgba(127, 127, 127, 0.25); }
colorbutton.flat, colorbutton.flat button { background: none; }
colorbutton.flat:hover, colorbutton.flat button:hover { background: rgba(127, 127, 127, 0.25); }
dropdown.flat, dropdown.flat button { background: none; border-radius: 5px; }
dropdown.flat:hover { background: rgba(127, 127, 127, 0.25); }
.flat-header { background: rgba(127, 127, 127, 0.05); border: none; box-shadow: none; padding: 0px; }
.button-box button { min-width: 80px; min-height: 36px; }
.highlighted { background-color: rgba(127, 127, 127, 0.15); }
.toolbar-group { margin: 0px 3px; }
.toolbar-separator { min-height: 0px; min-width: 1px; background-color: alpha(currentColor, 0.15); margin: 0px 0px; }
.color-indicator { min-height: 2px; min-width: 16px; margin-top: 1px; margin-bottom: 0px; border-radius: 2px; }
.color-box { padding: 0px; }
.linked button               {background-color: rgba(127, 127, 127, 0.10); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:hover         {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.30);}
.linked button:active        {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:checked       {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:checked:hover {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.30);}
.linked splitbutton > menubutton > button.toggle {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton > button  {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton:first-child > button  {
    border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}

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
        
        self.update_window_menu()


    def on_open(self, app, files, n_files, hint):
        """Handle file opening"""
        windows_added = False
        
        for file in files:
            file_path = file.get_path()
            existing_win = None
            for win in self.windows:
                if hasattr(win, 'current_file') and win.current_file and win.current_file.get_path() == file_path:
                    existing_win = win
                    break
            
            if existing_win:
                existing_win.present()
            else:
                win = self.create_window()
                self.load_file(win, file_path)
                win.present()
                windows_added = True
                
        if windows_added:
            self.update_window_menu()
                
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
        
        # Create toolbar container with FlowBox
        win.toolbars_flowbox = Gtk.FlowBox()
        win.toolbars_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        win.toolbars_flowbox.set_max_children_per_line(100)
        win.toolbars_flowbox.add_css_class("toolbar-container")
        
        # Create file toolbar group
        win.file_toolbar_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        win.file_toolbar_group.add_css_class("toolbar-group-container")
        
        # Create file operations group
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        file_group.add_css_class("toolbar-group")
        for icon, handler in [
            ("document-new-symbolic", self.on_new_clicked), 
            ("document-open-symbolic", self.on_open_clicked),
            ("document-save-symbolic", self.on_save_clicked), 
            ("document-save-as-symbolic", self.on_save_as_clicked),
        ]:
            btn = Gtk.Button(icon_name=icon)
            btn.set_tooltip_text(icon.split("-")[1].capitalize())
            btn.add_css_class("flat")
            btn.set_size_request(40, 36)
            btn.connect("clicked", lambda b, h=handler: h(win, b))
            file_group.append(btn)
        win.file_toolbar_group.append(file_group)
        
        # Create edit operations group
        edit_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        edit_group.add_css_class("toolbar-group")
        for icon, handler in [
            ("edit-cut-symbolic", self.on_cut_clicked), 
            ("edit-copy-symbolic", self.on_copy_clicked),
            ("edit-paste-symbolic", self.on_paste_clicked), 
            ("edit-undo-symbolic", self.on_undo_clicked),
            ("edit-redo-symbolic", self.on_redo_clicked)
        ]:
            btn = Gtk.Button(icon_name=icon)
            btn.set_tooltip_text(icon.split("-")[1].capitalize())
            btn.add_css_class("flat")
            btn.set_size_request(40, 36)
            if icon == "edit-undo-symbolic":
                win.undo_button = btn
                win.undo_button.set_sensitive(False)
            elif icon == "edit-redo-symbolic":
                win.redo_button = btn
                win.redo_button.set_sensitive(False)
            btn.connect("clicked", lambda b, h=handler: h(win, b))
            edit_group.append(btn)
        win.file_toolbar_group.append(edit_group)
        
        # Create find button
        view_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        view_group.add_css_class("toolbar-group")
        
        win.find_button = Gtk.ToggleButton()
        find_icon = Gtk.Image.new_from_icon_name("edit-find-replace-symbolic")
        win.find_button.set_child(find_icon)
        win.find_button.set_tooltip_text("Find and Replace (Ctrl+F)")
        win.find_button.add_css_class("flat")
        win.find_button.set_size_request(40, 36)
        win.find_button_handler_id = win.find_button.connect("toggled", lambda btn: self.on_find_button_toggled(win, btn))
        view_group.append(win.find_button)
        
        # Add dark mode button
        win.dark_mode_btn = Gtk.ToggleButton(icon_name="display-brightness")
        win.dark_mode_btn.connect("toggled", lambda btn: self.on_dark_mode_toggled(win, btn) if hasattr(self, "on_dark_mode_toggled") else None)
        win.dark_mode_btn.add_css_class("flat")
        win.dark_mode_btn.set_size_request(40, 36)
        view_group.append(win.dark_mode_btn)
        
        win.file_toolbar_group.append(view_group)
        
        # Add file toolbar group to the flowbox
        win.toolbars_flowbox.insert(win.file_toolbar_group, -1)
        
        # Create formatting toolbar group
        win.formatting_toolbar_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        win.formatting_toolbar_group.add_css_class("toolbar-group-container")
        
        # Create the formatting toolbar - using the existing method
        toolbar = self.create_formatting_toolbar(win)
        win.formatting_toolbar_group.append(toolbar)
        
        # Add formatting toolbar group to the flowbox
        win.toolbars_flowbox.insert(win.formatting_toolbar_group, -1)
        
        # Add the toolbar flowbox to a revealer for toggle functionality
        win.formatting_toolbar_revealer = Gtk.Revealer()
        win.formatting_toolbar_revealer.set_margin_start(0)
        win.formatting_toolbar_revealer.set_margin_end(0)
        win.formatting_toolbar_revealer.set_margin_top(0)
        win.formatting_toolbar_revealer.set_margin_bottom(0)
        win.formatting_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.formatting_toolbar_revealer.set_transition_duration(250)
        win.formatting_toolbar_revealer.set_reveal_child(True)  # Visible by default
        win.formatting_toolbar_revealer.set_child(win.toolbars_flowbox)
        
        win.headerbar_box.append(win.formatting_toolbar_revealer)
        
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
            
            # Add handler for formatting changes
            user_content_manager.register_script_message_handler("formattingChanged")
            user_content_manager.connect("script-message-received::formattingChanged", 
                                        lambda mgr, res: self.on_formatting_changed(win, mgr, res))
        except:
            print("Warning: Could not set up JavaScript message handlers")
                    
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        # Find bar with revealer
        win.find_bar = self.create_find_bar(win)
        content_box.append(win.find_bar)
        
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
        
        # Add the statusbar to its revealer
        win.statusbar_revealer.set_child(statusbar_box)
        content_box.append(win.statusbar_revealer)

        win.main_box.append(content_box)
        win.set_content(win.main_box)

        self.setup_keyboard_shortcuts(win)
        # Add case change action to the window
        case_change_action = Gio.SimpleAction.new("change-case", GLib.VariantType.new("s"))
        case_change_action.connect("activate", lambda action, param: self.on_change_case(win, param.get_string()))
        win.add_action(case_change_action)
        
        win.connect("close-request", self.on_window_close_request)

        # Add to windows list
        self.windows.append(win)
        self.setup_spacing_actions(win)
        
        return win
                    
    def setup_headerbar_content(self, win):
        """Create simplified headerbar content (menu and window buttons)"""
        win.headerbar.set_margin_top(0)
        win.headerbar.set_margin_bottom(0)
        # Create menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.add_css_class("flat")  # Add flat style
        
        menu = Gio.Menu()
        
        # File menu section
        file_section = Gio.Menu()
        file_section.append("New Window", "app.new-window")
        file_section.append("Open", "app.open") # You'll need to add this action
        file_section.append("Save", "app.save") # You'll need to add this action
        file_section.append("Save As", "app.save-as") # You'll need to add this action
        menu.append_section("File", file_section)
        
        # View menu section
        view_section = Gio.Menu()
        view_section.append("Show/Hide File Toolbar", "app.toggle-file-toolbar") # You'll need to add this action
        view_section.append("Show/Hide Format Toolbar", "app.toggle-format-toolbar") # You'll need to add this action
        view_section.append("Show/Hide Statusbar", "app.toggle-statusbar") # You'll need to add this action
        menu.append_section("View", view_section)
        
        # App menu section
        app_section = Gio.Menu()
        app_section.append("Preferences", "app.preferences")
        app_section.append("About", "app.about")
        app_section.append("Quit", "app.quit")
        menu.append_section("Application", app_section)
        
        menu_button.set_menu_model(menu)
        
        # Set up the window title widget (can be customized further)
        title_widget = Adw.WindowTitle()
        title_widget.set_title("Untitled  - HTML Editor")
#        title_widget.set_subtitle("Untitled")  # Will be updated with document name
        win.title_widget = title_widget  # Store for later updates
        
        # Save reference to update title 
        win.headerbar.set_title_widget(title_widget)
        
        # Add buttons to header bar
        win.headerbar.pack_start(menu_button)
        
        # Create window menu button on the right side
        self.add_window_menu_button(win)
            
    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        # --- File operations group (New, Open, Save, Save As) ---
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_group.add_css_class("linked")  # Apply linked styling
        file_group.set_margin_start(4)

        # New button
        new_button = Gtk.Button(icon_name="document-new-symbolic")
        new_button.set_tooltip_text("New Document in New Window")
        new_button.connect("clicked", lambda btn: self.on_new_clicked(win, btn))
        # Set size request to match formatting toolbar buttons
        new_button.set_size_request(40, 36)

        # Open button
        open_button = Gtk.Button(icon_name="document-open-symbolic")
        open_button.set_tooltip_text("Open File in New Window")
        open_button.connect("clicked", lambda btn: self.on_open_clicked(win, btn))
        open_button.set_size_request(40, 36)

        # Save button
        save_button = Gtk.Button(icon_name="document-save-symbolic")
        save_button.set_tooltip_text("Save File")
        save_button.connect("clicked", lambda btn: self.on_save_clicked(win, btn))
        save_button.set_size_request(40, 36)

        # Save As button
        save_as_button = Gtk.Button(icon_name="document-save-as-symbolic")
        save_as_button.set_tooltip_text("Save File As")
        save_as_button.connect("clicked", lambda btn: self.on_save_as_clicked(win, btn))
        save_as_button.set_size_request(40, 36)

        # Add buttons to file group
        file_group.append(new_button)
        file_group.append(open_button)
        file_group.append(save_button)
        file_group.append(save_as_button)
        
        # Add file group to toolbar
        file_toolbar.append(file_group)
        
        # --- Edit operations group (Cut, Copy, Paste, Print) ---
        edit_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        edit_group.add_css_class("linked")  # Apply linked styling
        edit_group.set_margin_start(6)
        
        # Cut button
        cut_button = Gtk.Button(icon_name="edit-cut-symbolic")
        cut_button.set_tooltip_text("Cut")
        cut_button.connect("clicked", lambda btn: self.on_cut_clicked(win, btn))

        # Copy button
        copy_button = Gtk.Button(icon_name="edit-copy-symbolic")
        copy_button.set_tooltip_text("Copy")
        copy_button.connect("clicked", lambda btn: self.on_copy_clicked(win, btn))

        # Paste button
        paste_button = Gtk.Button(icon_name="edit-paste-symbolic")
        paste_button.set_tooltip_text("Paste")
        paste_button.connect("clicked", lambda btn: self.on_paste_clicked(win, btn))
        
        # Print button
        print_button = Gtk.Button(icon_name="document-print-symbolic")
        print_button.set_tooltip_text("Print Document")
        print_button.connect("clicked", lambda btn: self.on_print_clicked(win, btn) if hasattr(self, "on_print_clicked") else None)
        
        # Add buttons to edit group
        edit_group.append(cut_button)
        edit_group.append(copy_button)
        edit_group.append(paste_button)
        edit_group.append(print_button)
        
        # Add edit group to toolbar
        file_toolbar.append(edit_group)
        
        # --- History operations group (Undo, Redo, Find) ---
        history_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        history_group.add_css_class("linked")  # Apply linked styling
        history_group.set_margin_start(6)
        
        # Undo button
        win.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        win.undo_button.set_tooltip_text("Undo")
        win.undo_button.connect("clicked", lambda btn: self.on_undo_clicked(win, btn))
        win.undo_button.set_sensitive(False)  # Initially disabled
        
        # Redo button
        win.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        win.redo_button.set_tooltip_text("Redo")
        win.redo_button.connect("clicked", lambda btn: self.on_redo_clicked(win, btn))
        win.redo_button.set_sensitive(False)  # Initially disabled
        
        # Find-Replace toggle button
        win.find_button = Gtk.ToggleButton()
        find_icon = Gtk.Image.new_from_icon_name("edit-find-replace-symbolic")
        win.find_button.set_child(find_icon)
        win.find_button.set_tooltip_text("Find and Replace (Ctrl+F)")
        win.find_button_handler_id = win.find_button.connect("toggled", lambda btn: self.on_find_button_toggled(win, btn))

        # Add buttons to history group
        history_group.append(win.undo_button)
        history_group.append(win.redo_button)
        history_group.append(win.find_button)
        
        # Add history group to toolbar
        file_toolbar.append(history_group)
        
        # --- Spacing operations group (Line Spacing, Paragraph Spacing) ---
        spacing_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        spacing_group.add_css_class("linked")  # Apply linked styling
        spacing_group.set_margin_start(6)
        
        # Line spacing button menu
        line_spacing_button = Gtk.MenuButton(icon_name="line_space_new")
        line_spacing_button.set_size_request(40, 36)
        line_spacing_button.set_tooltip_text("Line Spacing")
        line_spacing_button.add_css_class("flat")
        
        # Create line spacing menu
        line_spacing_menu = Gio.Menu()
        
        # Add line spacing options
        line_spacing_menu.append("Single (1.0)", "win.line-spacing('1.0')")
        line_spacing_menu.append("1.5 Lines", "win.line-spacing('1.5')")
        line_spacing_menu.append("Double (2.0)", "win.line-spacing('2.0')")
        line_spacing_menu.append("Custom...", "win.line-spacing-dialog")
        
        line_spacing_button.set_menu_model(line_spacing_menu)
        
        # Paragraph spacing button menu
        para_spacing_button = Gtk.MenuButton(icon_name="paragraph_line_spacing")
        para_spacing_button.set_size_request(40, 36)
        para_spacing_button.set_tooltip_text("Paragraph Spacing")
        para_spacing_button.add_css_class("flat")
        
        # Create paragraph spacing menu
        para_spacing_menu = Gio.Menu()
        
        # Add paragraph spacing options
        para_spacing_menu.append("None", "win.paragraph-spacing('0')")
        para_spacing_menu.append("Small (5px)", "win.paragraph-spacing('5')")
        para_spacing_menu.append("Medium (15px)", "win.paragraph-spacing('15')")
        para_spacing_menu.append("Large (30px)", "win.paragraph-spacing('30')")
        para_spacing_menu.append("Custom...", "win.paragraph-spacing-dialog")
        
        para_spacing_button.set_menu_model(para_spacing_menu)
        
        # Column layout button menu
        column_button = Gtk.MenuButton(icon_name="columns-symbolic")
        column_button.set_size_request(40, 36)
        column_button.set_tooltip_text("Column Layout")
        column_button.add_css_class("flat")
        
        # Create column menu
        column_menu = Gio.Menu()
        
        # Add column options
        column_menu.append("Single Column", "win.set-columns('1')")
        column_menu.append("Two Columns", "win.set-columns('2')")
        column_menu.append("Three Columns", "win.set-columns('3')")
        column_menu.append("Four Columns", "win.set-columns('4')")
        column_menu.append("Remove Columns", "win.set-columns('0')")
        
        column_button.set_menu_model(column_menu)
        
        # Add buttons to spacing group
        spacing_group.append(line_spacing_button)
        spacing_group.append(para_spacing_button)
        spacing_group.append(column_button)
        
        # Add spacing group to toolbar
        file_toolbar.append(spacing_group)        

        
        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar


    def on_cut_clicked(self, win, btn):
        """Handle cut button click"""
        self.execute_js(win, """
            (function() {
                let sel = window.getSelection();
                if (sel.rangeCount) {
                    document.execCommand('cut');
                    return true;
                }
                return false;
            })();
        """)
        win.statusbar.set_text("Cut to clipboard")

    def on_copy_clicked(self, win, btn):
        """Handle copy button click"""
        self.execute_js(win, """
            (function() {
                let sel = window.getSelection();
                if (sel.rangeCount) {
                    document.execCommand('copy');
                    return true;
                }
                return false;
            })();
        """)
        win.statusbar.set_text("Copied to clipboard")

    def on_paste_clicked(self, win, btn):
        """Handle paste button click"""
        # Try to get text from clipboard
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.read_text_async(None, self.on_text_received, win)
        win.statusbar.set_text("Pasting from clipboard...")

    def on_text_received(self, clipboard, result, win):
        """Handle clipboard text retrieval"""
        try:
            text = clipboard.read_text_finish(result)
            if text:
                # Escape text for JavaScript
                import json
                text_json = json.dumps(text)
                # Insert the text at cursor position
                self.execute_js(win, f"""
                    (function() {{
                        document.execCommand('insertText', false, {text_json});
                        return true;
                    }})();
                """)
                win.statusbar.set_text("Pasted from clipboard")
            else:
                win.statusbar.set_text("No text in clipboard")
        except GLib.Error as e:
            print("Paste error:", e.message)
            win.statusbar.set_text(f"Paste failed: {e.message}")
            
    def on_zoom_changed(self, win, scale, zoom_button):
        """Handle zoom scale change"""
        zoom_level = int(scale.get_value())
        zoom_button.set_label(f"{zoom_level}%")
        win.zoom_level = zoom_level
        
        # Apply zoom to the editor
        self.apply_zoom(win, zoom_level)

    def on_zoom_preset_clicked(self, win, preset, scale, zoom_button, popover):
        """Handle zoom preset button click"""
        scale.set_value(preset)
        zoom_button.set_label(f"{preset}%")
        win.zoom_level = preset
        
        # Apply zoom to the editor
        self.apply_zoom(win, preset)
        
        # Close the popover
        popover.popdown()

    def apply_zoom(self, win, zoom_level):
        """Apply zoom level to the editor"""
        # Convert percentage to scale factor (1.0 = 100%)
        scale_factor = zoom_level / 100.0
        
        # Apply zoom using JavaScript
        js_code = f"""
        (function() {{
            document.body.style.zoom = "{scale_factor}";
            document.getElementById('editor').style.zoom = "{scale_factor}";
            return true;
        }})();
        """
        
        self.execute_js(win, js_code)
        #win.statusbar.set_text(f"Zoom level: {zoom_level}%")    
        



        
    def setup_keyboard_shortcuts(self, win):
        """Setup keyboard shortcuts for the window"""
        # Create a shortcut controller
        controller = Gtk.ShortcutController()
        
        # Create Ctrl+T shortcut for toggling the toolbar
        trigger_toolbar = Gtk.ShortcutTrigger.parse_string("<Control>t")
        action_toolbar = Gtk.CallbackAction.new(lambda *args: self.toggle_formatting_toolbar(win, *args))
        shortcut_toolbar = Gtk.Shortcut.new(trigger_toolbar, action_toolbar)
        controller.add_shortcut(shortcut_toolbar)
        
        # Create Ctrl+Shift+F shortcut for toggling the file toolbar
        trigger_file_toolbar = Gtk.ShortcutTrigger.parse_string("<Control><Shift>f")
        action_file_toolbar = Gtk.CallbackAction.new(lambda *args: self.toggle_file_toolbar(win, *args))
        shortcut_file_toolbar = Gtk.Shortcut.new(trigger_file_toolbar, action_file_toolbar)
        controller.add_shortcut(shortcut_file_toolbar)

        # Create Ctrl+P shortcut for print
        trigger_print = Gtk.ShortcutTrigger.parse_string("<Control>p")
        action_print = Gtk.CallbackAction.new(lambda *args: self.on_print_clicked(win, None))
        shortcut_print = Gtk.Shortcut.new(trigger_print, action_print)
        controller.add_shortcut(shortcut_print)
        
        # Create Ctrl+F shortcut for find
        trigger_find = Gtk.ShortcutTrigger.parse_string("<Control>f")
        action_find = Gtk.CallbackAction.new(lambda *args: self.on_find_shortcut(win, *args))
        shortcut_find = Gtk.Shortcut.new(trigger_find, action_find)
        controller.add_shortcut(shortcut_find)
        
        # Create Ctrl+Shift+S shortcut for toggling the statusbar
        trigger_statusbar = Gtk.ShortcutTrigger.parse_string("<Control><Shift>s")
        action_statusbar = Gtk.CallbackAction.new(lambda *args: self.toggle_statusbar(win, *args))
        shortcut_statusbar = Gtk.Shortcut.new(trigger_statusbar, action_statusbar)
        controller.add_shortcut(shortcut_statusbar)
        
        # Create Ctrl+Shift+H shortcut for toggling the headerbar
        trigger_headerbar = Gtk.ShortcutTrigger.parse_string("<Control><Shift>h")
        action_headerbar = Gtk.CallbackAction.new(lambda *args: self.toggle_headerbar(win, *args))
        shortcut_headerbar = Gtk.Shortcut.new(trigger_headerbar, action_headerbar)
        controller.add_shortcut(shortcut_headerbar)
        
        # Create Ctrl+Z shortcut for undo
        trigger_undo = Gtk.ShortcutTrigger.parse_string("<Control>z")
        action_undo = Gtk.CallbackAction.new(lambda *args: self.on_undo_shortcut(win, *args))
        shortcut_undo = Gtk.Shortcut.new(trigger_undo, action_undo)
        controller.add_shortcut(shortcut_undo)
        
        # Create Ctrl+Y shortcut for redo
        trigger_redo = Gtk.ShortcutTrigger.parse_string("<Control>y")
        action_redo = Gtk.CallbackAction.new(lambda *args: self.on_redo_shortcut(win, *args))
        shortcut_redo = Gtk.Shortcut.new(trigger_redo, action_redo)
        controller.add_shortcut(shortcut_redo)
        
        # Create Ctrl+W shortcut for closing current window
        trigger_close = Gtk.ShortcutTrigger.parse_string("<Control>w")
        action_close = Gtk.CallbackAction.new(lambda *args: self.on_close_shortcut(win, *args))
        shortcut_close = Gtk.Shortcut.new(trigger_close, action_close)
        controller.add_shortcut(shortcut_close)
        
        # Create Ctrl+Shift+W shortcut for closing other windows
        trigger_close_others = Gtk.ShortcutTrigger.parse_string("<Control><Shift>w")
        action_close_others = Gtk.CallbackAction.new(lambda *args: self.on_close_others_shortcut(win, *args))
        shortcut_close_others = Gtk.Shortcut.new(trigger_close_others, action_close_others)
        controller.add_shortcut(shortcut_close_others)
        
        # FORMATTING SHORTCUTS
        
        # Ctrl+B for Bold
        trigger_bold = Gtk.ShortcutTrigger.parse_string("<Control>b")
        action_bold = Gtk.CallbackAction.new(lambda *args: self.on_bold_shortcut(win, *args))
        shortcut_bold = Gtk.Shortcut.new(trigger_bold, action_bold)
        controller.add_shortcut(shortcut_bold)
        
        # Ctrl+I for Italic
        trigger_italic = Gtk.ShortcutTrigger.parse_string("<Control>i")
        action_italic = Gtk.CallbackAction.new(lambda *args: self.on_italic_shortcut(win, *args))
        shortcut_italic = Gtk.Shortcut.new(trigger_italic, action_italic)
        controller.add_shortcut(shortcut_italic)
        
        # Ctrl+U for Underline
        trigger_underline = Gtk.ShortcutTrigger.parse_string("<Control>u")
        action_underline = Gtk.CallbackAction.new(lambda *args: self.on_underline_shortcut(win, *args))
        shortcut_underline = Gtk.Shortcut.new(trigger_underline, action_underline)
        controller.add_shortcut(shortcut_underline)       
        
        # Ctrl+Shift+X for Strikeout
        trigger_strikeout = Gtk.ShortcutTrigger.parse_string("<Control><Shift>x")
        action_strikeout = Gtk.CallbackAction.new(lambda *args: self.on_strikeout_shortcut(win, *args))
        shortcut_strikeout = Gtk.Shortcut.new(trigger_strikeout, action_strikeout)
        controller.add_shortcut(shortcut_strikeout)

        # Create Ctrl+= shortcut for subscript (standard shortcut)
        trigger_subscript = Gtk.ShortcutTrigger.parse_string("<Control>equal")
        action_subscript = Gtk.CallbackAction.new(lambda *args: self.on_subscript_shortcut(win, *args))
        shortcut_subscript = Gtk.Shortcut.new(trigger_subscript, action_subscript)
        controller.add_shortcut(shortcut_subscript)
        
        # Create Ctrl++ (or Ctrl+Shift+=) shortcut for superscript (standard shortcut)
        # We'll add both variants to ensure compatibility across different keyboard layouts
        
        # Variant 1: Ctrl++
        trigger_superscript1 = Gtk.ShortcutTrigger.parse_string("<Control>plus")
        action_superscript1 = Gtk.CallbackAction.new(lambda *args: self.on_superscript_shortcut(win, *args))
        shortcut_superscript1 = Gtk.Shortcut.new(trigger_superscript1, action_superscript1)
        controller.add_shortcut(shortcut_superscript1)
        
        # Variant 2: Ctrl+Shift+=
        trigger_superscript2 = Gtk.ShortcutTrigger.parse_string("<Control><Shift>equal")
        action_superscript2 = Gtk.CallbackAction.new(lambda *args: self.on_superscript_shortcut(win, *args))
        shortcut_superscript2 = Gtk.Shortcut.new(trigger_superscript2, action_superscript2)
        controller.add_shortcut(shortcut_superscript2)
        
                
        # Add controller to the window
        win.add_controller(controller)
        
        # Make it capture events at the capture phase
        controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        
        # Make shortcut work regardless of who has focus
        controller.set_scope(Gtk.ShortcutScope.GLOBAL)


                        
    def toggle_file_toolbar(self, win, *args):
        """Toggle the visibility of the file toolbar with animation"""
        is_revealed = win.file_toolbar_revealer.get_reveal_child()
        win.file_toolbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"File Toolbar {status}")
        return True         
             
    def toggle_formatting_toolbar(self, win, *args):
        """Toggle the visibility of the toolbar with animation"""
        is_revealed = win.formatting_toolbar_revealer.get_reveal_child()
        win.formatting_toolbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"Formatting Toolbar {status}")
        return True
        
    def toggle_statusbar(self, win, *args):
        """Toggle the visibility of the statusbar with animation"""
        is_revealed = win.statusbar_revealer.get_reveal_child()
        win.statusbar_revealer.set_reveal_child(not is_revealed)
        if not is_revealed:
            win.statusbar.set_text("Statusbar shown")
        return True
    
    def toggle_headerbar(self, win, *args):
        """Toggle the visibility of the headerbar with animation"""
        is_revealed = win.headerbar_revealer.get_reveal_child()
        win.headerbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"Headerbar {status}")
        return True

    def on_close_shortcut(self, win, *args):
        """Handle Ctrl+W shortcut to close current window"""
        win.close()
        return True

    def on_close_others_shortcut(self, win, *args):
        """Handle Ctrl+Shift+W shortcut to close other windows"""
        self.on_close_other_windows(None, None)
        return True

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

        {self.save_state_js()}
        {self.perform_undo_js()}
        {self.perform_redo_js()}
        {self.find_last_text_node_js()}
        {self.get_stack_sizes_js()}
        {self.set_content_js()}
        {self.selection_change_js()}
        {self.search_functions_js()}
        {self.init_editor_js()}
        """


    
    def save_state_js(self):
        """JavaScript to save the editor state to the undo stack."""
        return """
        function saveState() {
            window.undoStack.push(document.getElementById('editor').innerHTML);
            if (window.undoStack.length > 100) {
                window.undoStack.shift();
            }
        }
        """

    def perform_undo_js(self):
        """JavaScript to perform an undo operation."""
        return """
        function performUndo() {
            const editor = document.getElementById('editor');
            if (window.undoStack.length > 1) {
                let selection = window.getSelection();
                let range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
                let cursorNode = range ? range.startContainer : null;
                let cursorOffset = range ? range.startOffset : 0;

                window.redoStack.push(window.undoStack.pop());
                window.isUndoRedo = true;
                editor.innerHTML = window.undoStack[window.undoStack.length - 1];
                window.lastContent = editor.innerHTML;
                window.isUndoRedo = false;

                editor.focus();
                try {
                    const newRange = document.createRange();
                    const sel = window.getSelection();
                    const textNode = findLastTextNode(editor) || editor;
                    const offset = textNode.nodeType === 3 ? textNode.length : 0;
                    newRange.setStart(textNode, offset);
                    newRange.setEnd(textNode, offset);
                    sel.removeAllRanges();
                    sel.addRange(newRange);
                } catch (e) {
                    console.log("Could not restore cursor position:", e);
                }
                return { success: true, isInitialState: window.undoStack.length === 1 };
            }
            return { success: false, isInitialState: window.undoStack.length === 1 };
        }
        """

    def perform_redo_js(self):
        """JavaScript to perform a redo operation."""
        return """
        function performRedo() {
            const editor = document.getElementById('editor');
            if (window.redoStack.length > 0) {
                let selection = window.getSelection();
                let range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
                let cursorNode = range ? range.startContainer : null;
                let cursorOffset = range ? range.startOffset : 0;

                const state = window.redoStack.pop();
                window.undoStack.push(state);
                window.isUndoRedo = true;
                editor.innerHTML = state;
                window.lastContent = editor.innerHTML;
                window.isUndoRedo = false;

                editor.focus();
                try {
                    const newRange = document.createRange();
                    const sel = window.getSelection();
                    const textNode = findLastTextNode(editor) || editor;
                    const offset = textNode.nodeType === 3 ? textNode.length : 0;
                    newRange.setStart(textNode, offset);
                    newRange.setEnd(textNode, offset);
                    sel.removeAllRanges();
                    sel.addRange(newRange);
                } catch (e) {
                    console.log("Could not restore cursor position:", e);
                }
                return { success: true, isInitialState: window.undoStack.length === 1 };
            }
            return { success: false, isInitialState: window.undoStack.length === 1 };
        }
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

    def get_stack_sizes_js(self):
        """JavaScript to get the sizes of undo and redo stacks."""
        return """
        function getStackSizes() {
            return {
                undoSize: window.undoStack.length,
                redoSize: window.redoStack.length
            };
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

    def selection_change_js(self):
        """JavaScript to track selection changes and update formatting buttons"""
        return """
        function updateFormattingState() {
            try {
                // Get basic formatting states
                const isBold = document.queryCommandState('bold');
                const isItalic = document.queryCommandState('italic');
                const isUnderline = document.queryCommandState('underline');
                const isStrikeThrough = document.queryCommandState('strikeThrough');
                const isSubscript = document.queryCommandState('subscript');
                const isSuperscript = document.queryCommandState('superscript');
                
                // Get the current paragraph formatting
                let paragraphStyle = 'Normal'; // Default
                const selection = window.getSelection();
                let fontFamily = '';
                let fontSize = '';
                
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    const node = range.commonAncestorContainer;
                    
                    // Find the closest block element
                    const getNodeName = (node) => {
                        return node.nodeType === 1 ? node.nodeName.toLowerCase() : null;
                    };
                    
                    const getParentBlockElement = (node) => {
                        if (node.nodeType === 3) { // Text node
                            return getParentBlockElement(node.parentNode);
                        }
                        const tagName = getNodeName(node);
                        if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'].includes(tagName)) {
                            return node;
                        }
                        if (node.parentNode && node.parentNode.id !== 'editor') {
                            return getParentBlockElement(node.parentNode);
                        }
                        return null;
                    };
                    
                    const blockElement = getParentBlockElement(node);
                    if (blockElement) {
                        const tagName = getNodeName(blockElement);
                        switch (tagName) {
                            case 'h1': paragraphStyle = 'Heading 1'; break;
                            case 'h2': paragraphStyle = 'Heading 2'; break;
                            case 'h3': paragraphStyle = 'Heading 3'; break;
                            case 'h4': paragraphStyle = 'Heading 4'; break;
                            case 'h5': paragraphStyle = 'Heading 5'; break;
                            case 'h6': paragraphStyle = 'Heading 6'; break;
                            default: paragraphStyle = 'Normal'; break;
                        }
                    }
                    
                    // Enhanced font size detection
                    // Start with the deepest element at cursor/selection
                    let currentElement = node;
                    if (currentElement.nodeType === 3) { // Text node
                        currentElement = currentElement.parentNode;
                    }
                    
                    // Work our way up the DOM tree to find font-size styles
                    while (currentElement && currentElement !== editor) {
                        // Check for inline font size
                        if (currentElement.style && currentElement.style.fontSize) {
                            fontSize = currentElement.style.fontSize;
                            break;
                        }
                        
                        // Check for font elements with size attribute
                        if (currentElement.tagName && currentElement.tagName.toLowerCase() === 'font' && currentElement.hasAttribute('size')) {
                            // This is a rough conversion from HTML font size (1-7) to points
                            const htmlSize = parseInt(currentElement.getAttribute('size'));
                            const sizeMap = {1: '8', 2: '10', 3: '12', 4: '14', 5: '18', 6: '24', 7: '36'};
                            fontSize = sizeMap[htmlSize] || '12';
                            break;
                        }
                        
                        // If we haven't found a font size yet, move up to parent
                        currentElement = currentElement.parentNode;
                    }
                    
                    // If we still don't have a font size, get it from computed style
                    if (!fontSize) {
                        // Use computed style as a fallback
                        const computedStyle = window.getComputedStyle(node.nodeType === 3 ? node.parentNode : node);
                        fontSize = computedStyle.fontSize;
                    }
                    
                    // Convert pixel sizes to points (approximate)
                    if (fontSize.endsWith('px')) {
                        const pxValue = parseFloat(fontSize);
                        fontSize = Math.round(pxValue * 0.75).toString();
                    } else if (fontSize.endsWith('pt')) {
                        fontSize = fontSize.replace('pt', '');
                    } else {
                        // For other units or no units, try to extract just the number
                        fontSize = fontSize.replace(/[^0-9.]/g, '');
                    }
                    
                    // Get font family using a similar approach
                    currentElement = node;
                    if (currentElement.nodeType === 3) {
                        currentElement = currentElement.parentNode;
                    }
                    
                    while (currentElement && currentElement !== editor) {
                        if (currentElement.style && currentElement.style.fontFamily) {
                            fontFamily = currentElement.style.fontFamily;
                            // Clean up quotes and fallbacks
                            fontFamily = fontFamily.split(',')[0].replace(/["']/g, '');
                            break;
                        }
                        
                        // Check for font elements with face attribute
                        if (currentElement.tagName && currentElement.tagName.toLowerCase() === 'font' && currentElement.hasAttribute('face')) {
                            fontFamily = currentElement.getAttribute('face');
                            break;
                        }
                        
                        currentElement = currentElement.parentNode;
                    }
                    
                    // If we still don't have a font family, get it from computed style
                    if (!fontFamily) {
                        const computedStyle = window.getComputedStyle(node.nodeType === 3 ? node.parentNode : node);
                        fontFamily = computedStyle.fontFamily.split(',')[0].replace(/["']/g, '');
                    }
                }
                
                // Send the state to Python - MAKE SURE subscript and superscript are included here
                window.webkit.messageHandlers.formattingChanged.postMessage(
                    JSON.stringify({
                        bold: isBold, 
                        italic: isItalic, 
                        underline: isUnderline,
                        strikeThrough: isStrikeThrough,
                        subscript: isSubscript,
                        superscript: isSuperscript,
                        paragraphStyle: paragraphStyle,
                        fontFamily: fontFamily,
                        fontSize: fontSize
                    })
                );
            } catch(e) {
                console.log("Error updating formatting state:", e);
            }
        }
        
        document.addEventListener('selectionchange', function() {
            // Only update if the selection is in our editor
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const editor = document.getElementById('editor');
                
                // Check if the selection is within our editor
                if (editor.contains(range.commonAncestorContainer)) {
                    updateFormattingState();
                }
            }
        });
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
    
    def extract_body_content(self, html):
        """Extract content from the body or just return the HTML if parsing fails"""
        try:
            # Simple regex to extract content between body tags
            import re
            body_match = re.search(r'<body[^>]*>([\s\S]*)<\/body>', html)
            if body_match:
                return body_match.group(1)
            return html
        except Exception:
            # In case of any error, return the original HTML
            return html
    
    # Undo/Redo related methods
    def on_content_changed(self, win, manager, result):
        # Check current modified state before changing it
        was_modified = win.modified
        
        # Set new state and update window title
        win.modified = True
        self.update_window_title(win)
        self.update_undo_redo_state(win)
        
        # Only update window menu if the modified state changed
        if not was_modified:  # If it wasn't modified before but now is
            self.update_window_menu()
        
    def update_undo_redo_state(self, win):
        try:
            # Get stack sizes to update button states
            win.webview.evaluate_javascript(
                "JSON.stringify(getStackSizes());",  # Ensure we get a proper JSON string
                -1, None, None, None,
                lambda webview, result, data: self._on_get_stack_sizes(win, webview, result, data), 
                None
            )
        except Exception as e:
            print(f"Error updating undo/redo state: {e}")
            # Fallback - enable buttons
            win.undo_button.set_sensitive(True)
            win.redo_button.set_sensitive(False)
        
    def _on_get_stack_sizes(self, win, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                # Try different approaches to get the result based on WebKit version
                try:
                    # Newer WebKit APIs
                    if hasattr(js_result, 'get_js_value'):
                        stack_sizes = js_result.get_js_value().to_string()
                    # Direct value access - works in some WebKit versions
                    elif hasattr(js_result, 'to_string'):
                        stack_sizes = js_result.to_string()
                    elif hasattr(js_result, 'get_string'):
                        stack_sizes = js_result.get_string()
                    else:
                        # Fallback - try converting to string directly
                        stack_sizes = str(js_result)
                    
                    # Parse the JSON result
                    import json
                    try:
                        # Remove any surrounding quotes if present
                        if stack_sizes.startswith('"') and stack_sizes.endswith('"'):
                            stack_sizes = stack_sizes[1:-1]
                        
                        # Try to parse as JSON
                        sizes = json.loads(stack_sizes)
                        # Update button states
                        win.undo_button.set_sensitive(sizes.get('undoSize', 0) > 1)
                        win.redo_button.set_sensitive(sizes.get('redoSize', 0) > 0)
                    except json.JSONDecodeError as je:
                        print(f"Error parsing JSON: {je}, value was: {stack_sizes}")
                        # Set reasonable defaults
                        win.undo_button.set_sensitive(True)
                        win.redo_button.set_sensitive(False)
                except Exception as inner_e:
                    print(f"Inner error processing JS result: {inner_e}")
                    # Set reasonable defaults
                    win.undo_button.set_sensitive(True)
                    win.redo_button.set_sensitive(False)
        except Exception as e:
            print(f"Error getting stack sizes: {e}")
            # Set reasonable defaults in case of error
            win.undo_button.set_sensitive(True)
            win.redo_button.set_sensitive(False)
            
    def on_undo_clicked(self, win, button):
        self.perform_undo(win)
        
    def on_redo_clicked(self, win, button):
        self.perform_redo(win)
        
    def on_undo_shortcut(self, win, *args):
        self.perform_undo(win)
        return True
        
    def on_redo_shortcut(self, win, *args):
        self.perform_redo(win)
        return True
        
    def perform_undo(self, win):
        try:
            win.webview.evaluate_javascript(
                "JSON.stringify(performUndo());",
                -1, None, None, None,
                lambda webview, result, data: self._on_undo_redo_performed(win, webview, result, data),
                "undo"
            )
            win.statusbar.set_text("Undo performed")
        except Exception as e:
            print(f"Error during undo: {e}")
            win.statusbar.set_text("Undo failed")
        
    def perform_redo(self, win):
        try:
            win.webview.evaluate_javascript(
                "JSON.stringify(performRedo());",
                -1, None, None, None,
                lambda webview, result, data: self._on_undo_redo_performed(win, webview, result, data),
                "redo"
            )
            win.statusbar.set_text("Redo performed")
        except Exception as e:
            print(f"Error during redo: {e}")
            win.statusbar.set_text("Redo failed")

    def _on_undo_redo_performed(self, win, webview, result, operation):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                result_str = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                              js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                import json
                result_data = json.loads(result_str)
                success = result_data.get('success', False)
                is_initial_state = result_data.get('isInitialState', False)

                if success:
                    win.statusbar.set_text(f"{operation.capitalize()} performed")
                    
                    # Check current modified state before changing it
                    was_modified = win.modified
                    
                    # Determine new state based on operation and result
                    new_modified_state = not (operation == "undo" and is_initial_state)
                    
                    # Set new state if it's different
                    if win.modified != new_modified_state:
                        win.modified = new_modified_state
                        self.update_window_title(win)
                        
                        # Only update window menu if modified state changed
                        self.update_window_menu()
                    
                    self.update_undo_redo_state(win)
                else:
                    win.statusbar.set_text(f"No more {operation} actions available")
        except Exception as e:
            print(f"Error during {operation}: {e}")
            win.statusbar.set_text(f"{operation.capitalize()} failed")
            
    # Event handlers
    def on_new_clicked(self, win, button):
        # Create a new window with a blank document
        new_win = self.create_window()
        new_win.present()
        GLib.timeout_add(500, lambda: self.set_initial_focus(new_win))
        self.update_window_menu()
        new_win.statusbar.set_text("New document created")
    
    def get_menu_title(self, win):
        if win.current_file:
            # Get the path as a string
            if hasattr(win.current_file, 'get_path'):
                path = win.current_file.get_path()
            else:
                path = win.current_file
            # Extract filename without extension and show modified marker
            filename = os.path.splitext(os.path.basename(path))[0]
            return f"{'  ⃰' if win.modified else ''}{filename}"
        else:
            return f"{'  ⃰' if win.modified else ''}Untitled"

    def update_window_title(self, win):
        """Update window title to show document name (without extension) and modified status"""
        if win.current_file:
            # Get the path as a string
            if hasattr(win.current_file, 'get_path'):
                path = win.current_file.get_path()
            else:
                path = win.current_file
            # Extract filename without extension
            filename = os.path.splitext(os.path.basename(path))[0]
            title = f"{'  ⃰' if win.modified else ''}{filename}"
            win.set_title(f"{title} - HTML Editor")
            
            # Update the title widget if it exists
            if hasattr(win, 'title_widget'):
                win.title_widget.set_title(f"{'  ⃰' if win.modified else ''}{filename} - HTML Editor")
        else:
            title = f"{'  ⃰' if win.modified else ''}Untitled"
            win.set_title(f"{title} - HTML Editor")
            
            # Update the title widget if it exists
            if hasattr(win, 'title_widget'):
                win.title_widget.set_title(f"{'  ⃰' if win.modified else ''}Untitled  - HTML Editor")


    # Window Close Request
    def on_window_close_request(self, win, *args):
        """Handle window close request with save confirmation if needed"""
        if win.modified:
            # Show confirmation dialog
            self.show_save_confirmation_dialog(win, lambda response: self._handle_close_confirmation(win, response))
            # Return True to stop the default close handler
            return True
        else:
            # No unsaved changes, proceed with closing
            self.remove_window(win)
            return False

    def _handle_close_confirmation(self, win, response):
        """Handle the response from the save confirmation dialog"""
        if response == "save":
            # Save and then close
            if win.current_file:
                # We have a file path, save directly
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_before_close(win, webview, result, data),
                    None
                )
            else:
                # No file path, show save dialog
                dialog = Gtk.FileDialog()
                dialog.set_title("Save Before Closing")
                
                filter = Gtk.FileFilter()
                filter.set_name("HTML files")
                filter.add_pattern("*.html")
                filter.add_pattern("*.htm")
                
                filters = Gio.ListStore.new(Gtk.FileFilter)
                filters.append(filter)
                
                dialog.set_filters(filters)
                dialog.save(win, None, lambda dialog, result: self._on_save_response_before_close(win, dialog, result))
        elif response == "discard":
            # Mark as unmodified before closing
            win.modified = False
            
            # Close without saving
            self.remove_window(win)
            win.close()
        # If response is "cancel", do nothing and keep the window open

    def _on_save_before_close(self, win, webview, result, data):
        """Save the content and then close the window"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                               js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                
                # Define a callback that will close the window after saving
                def after_save(file, result):
                    try:
                        success, _ = file.replace_contents_finish(result)
                        if success:
                            win.modified = False  # Mark as unmodified
                            self.update_window_title(win)
                            # Now close the window
                            self.remove_window(win)
                            win.close()
                    except Exception as e:
                        print(f"Error during save before close: {e}")
                        # Close anyway in case of error
                        self.remove_window(win)
                        win.close()
                
                self.save_html_content(win, editor_content, win.current_file, after_save)
        except Exception as e:
            print(f"Error getting HTML content: {e}")
            # Close anyway in case of error
            self.remove_window(win)
            win.close()

    def _on_saved_close_window(self, file, result):
        """After saving, close the window"""
        try:
            success, _ = file.replace_contents_finish(result)
            # Find the window with this file
            for win in self.windows:
                if win.current_file and win.current_file.equal(file):
                    self.remove_window(win)
                    win.close()
                    break
        except Exception as e:
            print(f"Error saving before close: {e}")

    def _on_save_response_before_close(self, win, dialog, result):
        """Handle save dialog response before closing"""
        try:
            file = dialog.save_finish(result)
            if file:
                win.current_file = file
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_before_close(win, webview, result, data),
                    None
                )
            else:
                # User cancelled save dialog, keep window open
                pass
        except GLib.Error as error:
            if error.domain != 'gtk-dialog-error-quark' or error.code != 2:  # Ignore cancel
                print(f"Error saving file: {error.message}")
            # Keep window open

    def show_save_confirmation_dialog(self, win, callback):
        """Show dialog asking if user wants to save changes before closing"""
        dialog = Adw.Dialog.new()
        dialog.set_title("Unsaved Changes")
        dialog.set_content_width(400)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Warning icon
        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        warning_icon.set_pixel_size(48)
        warning_icon.set_margin_bottom(12)
        content_box.append(warning_icon)
        
        # Message
        document_name = "Untitled"
        if win.current_file:
            path = win.current_file.get_path() if hasattr(win.current_file, 'get_path') else win.current_file
            document_name = os.path.splitext(os.path.basename(path))[0]
            
        message_label = Gtk.Label()
        message_label.set_markup(f"<b>Save changes to \"{document_name}\" before closing?</b>")
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        description_label = Gtk.Label(label="If you don't save, your changes will be lost.")
        description_label.set_wrap(True)
        description_label.set_max_width_chars(40)
        content_box.append(description_label)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        # Discard button
        discard_button = Gtk.Button(label="Discard")
        discard_button.add_css_class("destructive-action")
        discard_button.connect("clicked", lambda btn: [dialog.close(), callback("discard")])
        button_box.append(discard_button)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: [dialog.close(), callback("cancel")])
        button_box.append(cancel_button)
        
        # Save button
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", lambda btn: [dialog.close(), callback("save")])
        button_box.append(save_button)
        
        content_box.append(button_box)
        
        # Present the dialog
        dialog.set_child(content_box)
        dialog.present(win)

    def create_actions(self):
        """Set up application actions"""
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)
        
        # New window action
        new_window_action = Gio.SimpleAction.new("new-window", None)
        new_window_action.connect("activate", self.on_new_window)
        self.add_action(new_window_action)
        
        # Close other windows action
        close_other_windows_action = Gio.SimpleAction.new("close-other-windows", None)
        close_other_windows_action.connect("activate", self.on_close_other_windows)
        self.add_action(close_other_windows_action)

        # Window switching action
        switch_window_action = Gio.SimpleAction.new(
            "switch-window", 
            GLib.VariantType.new("i")
        )
        switch_window_action.connect("activate", self.on_switch_window)
        self.add_action(switch_window_action)

    def create_window_menu(self):
        """Create a fresh window menu"""
        menu = Gio.Menu()
        actions_section = Gio.Menu()
        window_section = Gio.Menu()
        
        # Add "Close Other Windows" option at the top if there's more than one window
        if len(self.windows) > 1:
            actions_section.append("Close Other Windows", "app.close-other-windows")
            menu.append_section("Actions", actions_section)
        
        # Add all windows to the menu
        for i, win in enumerate(self.windows):
            title = self.get_menu_title(win)
            action_string = f"app.switch-window({i})"
            window_section.append(title, action_string)
        
        menu.append_section("Windows", window_section)
        return menu

    def update_window_menu(self):
        """Force update all window menu buttons"""
        fresh_menu = self.create_window_menu()
        
        # Should we show the window menu button?
        show_button = len(self.windows) > 1
        
        # Create a set of windows that still need a button
        windows_needing_buttons = set(self.windows)
        
        # First, update existing buttons
        buttons_to_remove = []
        for window_id, button in self.window_buttons.items():
            # Check if the window still exists
            window_exists = False
            for win in self.windows:
                if id(win) == window_id:
                    window_exists = True
                    windows_needing_buttons.remove(win)
                    break
            
            if window_exists:
                # Update existing button with fresh menu and visibility
                button.set_menu_model(fresh_menu)
                button.set_visible(show_button)
            else:
                # Window no longer exists, mark button for removal
                buttons_to_remove.append(window_id)
        
        # Remove buttons for closed windows
        for window_id in buttons_to_remove:
            del self.window_buttons[window_id]
        
        # Add buttons for new windows
        for win in windows_needing_buttons:
            self.add_window_menu_button(win, fresh_menu)
    
    def add_window_menu_button(self, win, menu_model=None):
        """Add a window menu button to a window or update an existing one"""
        # Look for existing window menu button
        window_button = None
        child = win.headerbar.get_first_child()
        while child:
            if (isinstance(child, Gtk.MenuButton) and 
                child.get_icon_name() == "multi-window-symbolic"):
                window_button = child
                break
            child = child.get_next_sibling()
        
        # Create a new menu model if not provided
        if menu_model is None:
            menu_model = self.create_window_menu()
        
        # Only show the window menu button if there's more than one window
        show_button = len(self.windows) > 1
        
        if window_button:
            # Update existing button's menu and visibility
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
        elif show_button:
            # Only create a new button if we need to show it
            window_button = Gtk.MenuButton()
            window_button.set_icon_name("multi-window-symbolic")
            window_button.set_tooltip_text("Window List")
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
            window_button.add_css_class("flat")
            win.headerbar.pack_end(window_button)
            
            # Store reference to the button
            self.window_buttons[id(win)] = window_button
        
        # Make sure we keep the reference if button exists
        if window_button:
            self.window_buttons[id(win)] = window_button
            
    def on_switch_window(self, action, param):
        """Handle window switching action"""
        index = param.get_int32()
        if 0 <= index < len(self.windows):
            self.windows[index].present()
            
    def on_new_window(self, action, param):
        """Create a new empty window"""
        win = self.create_window()
        win.present()
        # Update all window menus
        self.update_window_menu()

    def on_close_other_windows(self, action, param):
        """Close all windows except the active one with confirmation"""
        if len(self.windows) <= 1:
            return
            
        # Find the active window (the one that was most recently focused)
        active_window = None
        for win in self.windows:
            if win.is_active():
                active_window = win
                break
                
        # If no active window found, use the first one
        if not active_window and self.windows:
            active_window = self.windows[0]
            
        if not active_window:
            return
            
        # The number of windows that will be closed
        windows_to_close_count = len(self.windows) - 1
        
        # Create confirmation dialog using non-deprecated methods
        dialog = Adw.Dialog.new()
        dialog.set_title(f"Close {windows_to_close_count} Other Window{'s' if windows_to_close_count > 1 else ''}?")
        dialog.set_content_width(350)
        
        # Create dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Message label
        message_label = Gtk.Label()
        message_label.set_text(f"Are you sure you want to close {windows_to_close_count} other window{'s' if windows_to_close_count > 1 else ''}?")
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        # Close button (destructive)
        close_button = Gtk.Button(label="Close Windows")
        close_button.add_css_class("destructive-action")
        close_button.connect("clicked", lambda btn: self._on_close_others_response(dialog, active_window))
        button_box.append(close_button)
        
        content_box.append(button_box)
        
        # Set the dialog content and present
        dialog.set_child(content_box)
        dialog.present(active_window)

    def _on_close_others_response(self, dialog, active_window):
        """Handle the close action from the dialog"""
        # Close dialog
        dialog.close()
        
        # Get windows to close (all except active_window)
        windows_to_close = [win for win in self.windows if win != active_window]
        
        # Close each window
        for win in windows_to_close[:]:  # Use a copy of the list since we'll modify it
            win.close()
            
        # Make sure active window is still presented
        if active_window in self.windows:
            active_window.present()
            
        # Update window menu
        self.update_window_menu()

    def remove_window(self, window):
        """Properly remove a window and update menus"""
        if window in self.windows:
            # Remove window from list
            self.windows.remove(window)
            # Clean up button reference
            if id(window) in self.window_buttons:
                del self.window_buttons[id(window)]
            # Update menus in all remaining windows
            self.update_window_menu()
            
            # Focus the next window if available
            if self.windows:
                self.windows[0].present()
    
    # On Quit
    def on_quit(self, action, param):
        """Quit the application with save confirmation if needed"""
        # Check if any window has unsaved changes
        windows_with_changes = [win for win in self.windows if win.modified]
        
        if windows_with_changes:
            # Prioritize the active window if it has unsaved changes
            active_window = None
            for win in self.windows:
                if win.is_active() and win.modified:
                    active_window = win
                    break
                    
            # If no active window with changes, use the first window with changes
            if not active_window and windows_with_changes:
                active_window = windows_with_changes[0]
            
            # Move the active window to the front of the list
            if active_window in windows_with_changes:
                windows_with_changes.remove(active_window)
                windows_with_changes.insert(0, active_window)
            
            # Start handling windows one by one
            self._handle_quit_with_unsaved_changes(windows_with_changes)
        else:
            # No unsaved changes, quit directly
            self.quit()

    def _handle_quit_with_unsaved_changes(self, windows_with_changes):
        """Handle unsaved changes during quit, one window at a time"""
        if not windows_with_changes:
            # All windows handled, check if we should quit
            if not self.windows:
                self.quit()
            return
            
        win = windows_with_changes[0]
        # Make sure the window is presented to the user
        win.present()
        # Show the confirmation dialog
        self.show_save_confirmation_dialog(win, lambda response: self._handle_quit_confirmation(
            response, windows_with_changes, win))

    def _handle_quit_confirmation(self, response, windows_with_changes, win):
        """Handle the response from the save confirmation dialog during quit"""
        if response == "save":
            # Save and then close this window
            if win.current_file:
                # We have a file path, save directly
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_continue_quit(
                        win, webview, result, windows_with_changes),
                    None
                )
            else:
                # No file path, show save dialog
                dialog = Gtk.FileDialog()
                dialog.set_title("Save Before Quitting")
                
                filter = Gtk.FileFilter()
                filter.set_name("HTML files")
                filter.add_pattern("*.html")
                filter.add_pattern("*.htm")
                
                filters = Gio.ListStore.new(Gtk.FileFilter)
                filters.append(filter)
                
                dialog.set_filters(filters)
                dialog.save(win, None, lambda dialog, result: self._on_save_response_during_quit(
                    win, dialog, result, windows_with_changes))
        elif response == "discard":
            # Explicitly mark as unmodified before closing
            win.modified = False
            
            # Close this window without saving and continue with the next
            self.remove_window(win)
            win.close()
            
            # Continue with remaining windows
            remaining_windows = windows_with_changes[1:]
            if remaining_windows:
                GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
            elif not self.windows:
                # If all windows are closed, quit the application
                self.quit()
        elif response == "cancel":
            # Cancel the entire quit operation
            # Continue with other windows that might be open but not modified
            pass

    def _on_save_continue_quit(self, win, webview, result, windows_with_changes):
        """Save the content, close this window, and continue with the quit process"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                               js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                
                # Define a callback for after saving
                def after_save(file, result):
                    try:
                        success, _ = file.replace_contents_finish(result)
                        if success:
                            win.modified = False  # Mark as unmodified
                            self.update_window_title(win)
                        
                        # Close this window
                        self.remove_window(win)
                        win.close()
                        
                        # Continue with remaining windows
                        remaining_windows = windows_with_changes[1:]
                        if remaining_windows:
                            GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
                        elif not self.windows:
                            # If all windows are closed, quit the application
                            self.quit()
                    except Exception as e:
                        print(f"Error saving during quit: {e}")
                        # Close anyway and continue
                        self.remove_window(win)
                        win.close()
                        
                        # Continue with remaining windows
                        remaining_windows = windows_with_changes[1:]
                        if remaining_windows:
                            GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
                        elif not self.windows:
                            # If all windows are closed, quit the application
                            self.quit()
                
                # Save with our callback
                self.save_html_content(win, editor_content, win.current_file, after_save)
        except Exception as e:
            print(f"Error getting HTML content during quit: {e}")
            # Close anyway and continue
            self.remove_window(win)
            win.close()
            
            # Continue with remaining windows
            remaining_windows = windows_with_changes[1:]
            if remaining_windows:
                GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
            elif not self.windows:
                # If all windows are closed, quit the application
                self.quit()

    def _on_save_response_during_quit(self, win, dialog, result, windows_with_changes):
        """Handle save dialog response during quit"""
        try:
            file = dialog.save_finish(result)
            if file:
                win.current_file = file
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_continue_quit(
                        win, webview, result, windows_with_changes),
                    None
                )
            else:
                # User cancelled save dialog, cancel quit for this window
                # but continue with other windows that might need attention
                remaining_windows = windows_with_changes[1:]
                if remaining_windows:
                    GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
        except GLib.Error as error:
            if error.domain != 'gtk-dialog-error-quark' or error.code != 2:  # Ignore cancel
                print(f"Error saving file during quit: {error.message}")
            # Continue with other windows
            remaining_windows = windows_with_changes[1:]
            if remaining_windows:
                GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
    
    def on_about(self, action, param):
        """Show about dialog"""
        parent_window = self.windows[0] if self.windows else None
        about = Adw.AboutWindow(
            transient_for=parent_window,
            application_name="HTML Editor",
            application_icon="text-editor",
            developer_name="Developer",
            version="1.0",
            developers=["Your Name"],
            copyright="© 2025"
        )
        about.present()
    
    def on_preferences(self, action, param):
        """Show preferences dialog"""
        if not self.windows:
            return
                
        # Find the active window instead of just using the first window
        active_win = None
        for win in self.windows:
            if win.is_active():
                active_win = win
                break
        
        # If no active window found, use the first one as fallback
        if not active_win:
            active_win = self.windows[0]
                
        # Create dialog
        dialog = Adw.Dialog.new()
        dialog.set_title("Preferences")
        dialog.set_content_width(450)
        
        # Create content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Add settings UI
        header = Gtk.Label()
        header.set_markup("<b>Editor Settings</b>")
        header.set_halign(Gtk.Align.START)
        header.set_margin_bottom(12)
        content_box.append(header)
        
        # Show/Hide UI elements section
        ui_header = Gtk.Label()
        ui_header.set_markup("<b>User Interface</b>")
        ui_header.set_halign(Gtk.Align.START)
        ui_header.set_margin_bottom(12)
        ui_header.set_margin_top(24)
        content_box.append(ui_header)
        
        # Show Toolbar option
        formatting_toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        formatting_toolbar_box.set_margin_start(12)
        
        formatting_toolbar_label = Gtk.Label(label="Show Toolbar:")
        formatting_toolbar_label.set_halign(Gtk.Align.START)
        formatting_toolbar_label.set_hexpand(True)
        
        formatting_toolbar_switch = Gtk.Switch()
        formatting_toolbar_switch.set_active(active_win.formatting_toolbar_revealer.get_reveal_child())
        formatting_toolbar_switch.set_valign(Gtk.Align.CENTER)
        formatting_toolbar_switch.connect("state-set", lambda sw, state: active_win.formatting_toolbar_revealer.set_reveal_child(state))
        
        formatting_toolbar_box.append(formatting_toolbar_label)
        formatting_toolbar_box.append(formatting_toolbar_switch)
        content_box.append(formatting_toolbar_box)
        
        # Show Statusbar option
        statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        statusbar_box.set_margin_start(12)
        statusbar_box.set_margin_top(12)
        
        statusbar_label = Gtk.Label(label="Show Statusbar:")
        statusbar_label.set_halign(Gtk.Align.START)
        statusbar_label.set_hexpand(True)
        
        statusbar_switch = Gtk.Switch()
        statusbar_switch.set_active(active_win.statusbar_revealer.get_reveal_child())
        statusbar_switch.set_valign(Gtk.Align.CENTER)
        statusbar_switch.connect("state-set", lambda sw, state: active_win.statusbar_revealer.set_reveal_child(state))
        
        statusbar_box.append(statusbar_label)
        statusbar_box.append(statusbar_switch)
        content_box.append(statusbar_box)
        
        # Show Headerbar option
        headerbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        headerbar_box.set_margin_start(12)
        headerbar_box.set_margin_top(12)
        
        headerbar_label = Gtk.Label(label="Show Headerbar:")
        headerbar_label.set_halign(Gtk.Align.START)
        headerbar_label.set_hexpand(True)
        
        headerbar_switch = Gtk.Switch()
        headerbar_switch.set_active(active_win.headerbar_revealer.get_reveal_child())
        headerbar_switch.set_valign(Gtk.Align.CENTER)
        headerbar_switch.connect("state-set", lambda sw, state: active_win.headerbar_revealer.set_reveal_child(state))
        
        headerbar_box.append(headerbar_label)
        headerbar_box.append(headerbar_switch)
        content_box.append(headerbar_box)
        
        # Auto-save toggle
        auto_save_section = Gtk.Label()
        auto_save_section.set_markup("<b>Auto Save</b>")
        auto_save_section.set_halign(Gtk.Align.START)
        auto_save_section.set_margin_bottom(12)
        auto_save_section.set_margin_top(24)
        content_box.append(auto_save_section)
        
        auto_save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        auto_save_box.set_margin_start(12)
        
        auto_save_label = Gtk.Label(label="Auto Save:")
        auto_save_label.set_halign(Gtk.Align.START)
        auto_save_label.set_hexpand(True)
        
        auto_save_switch = Gtk.Switch()
        auto_save_switch.set_active(active_win.auto_save_enabled)
        auto_save_switch.set_valign(Gtk.Align.CENTER)
        
        auto_save_box.append(auto_save_label)
        auto_save_box.append(auto_save_switch)
        content_box.append(auto_save_box)
        
        # Interval settings
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        interval_box.set_margin_start(12)
        interval_box.set_margin_top(12)
        
        interval_label = Gtk.Label(label="Auto-save Interval (seconds):")
        interval_label.set_halign(Gtk.Align.START)
        interval_label.set_hexpand(True)
        
        adjustment = Gtk.Adjustment(
            value=active_win.auto_save_interval,
            lower=10,
            upper=600,
            step_increment=10
        )
        
        spinner = Gtk.SpinButton()
        spinner.set_adjustment(adjustment)
        spinner.set_valign(Gtk.Align.CENTER)
        
        interval_box.append(interval_label)
        interval_box.append(spinner)
        content_box.append(interval_box)
        
        # Dialog buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        ok_button.connect("clicked", lambda btn: self.save_preferences(
            dialog, active_win, auto_save_switch.get_active(), spinner.get_value_as_int()
        ))
        button_box.append(ok_button)
        
        content_box.append(button_box)
        
        # Important: Store a reference to the dialog in the window
        active_win.preferences_dialog = dialog
        
        # Connect to the closed signal to clean up the reference
        dialog.connect("closed", lambda d: self.on_preferences_dialog_closed(active_win))
        
        # Set dialog content and show
        dialog.set_child(content_box)
        dialog.present(active_win)

    def on_preferences_dialog_closed(self, win):
        """Handle preferences dialog closed event"""
        # Remove the reference to allow proper cleanup
        if hasattr(win, 'preferences_dialog'):
            win.preferences_dialog = None

    def save_preferences(self, dialog, win, auto_save_enabled, auto_save_interval):
        """Save preferences settings"""
        previous_auto_save = win.auto_save_enabled
        
        win.auto_save_enabled = auto_save_enabled
        win.auto_save_interval = auto_save_interval
        
        # Update auto-save timer if needed
        if auto_save_enabled != previous_auto_save:
            if auto_save_enabled:
                self.start_auto_save_timer(win)
                win.statusbar.set_text("Auto-save enabled")
            else:
                self.stop_auto_save_timer(win)
                win.statusbar.set_text("Auto-save disabled")
        elif auto_save_enabled:
            # Restart timer with new interval
            self.stop_auto_save_timer(win)
            self.start_auto_save_timer(win)
            win.statusbar.set_text(f"Auto-save interval set to {auto_save_interval} seconds")
        
        dialog.close()

    def save_preferences(self, dialog, win, auto_save_enabled, auto_save_interval):
        """Save preferences settings"""
        previous_auto_save = win.auto_save_enabled
        
        win.auto_save_enabled = auto_save_enabled
        win.auto_save_interval = auto_save_interval
        
        # Update auto-save timer if needed
        if auto_save_enabled != previous_auto_save:
            if auto_save_enabled:
                self.start_auto_save_timer(win)
                win.statusbar.set_text("Auto-save enabled")
            else:
                self.stop_auto_save_timer(win)
                win.statusbar.set_text("Auto-save disabled")
        elif auto_save_enabled:
            # Restart timer with new interval
            self.stop_auto_save_timer(win)
            self.start_auto_save_timer(win)
            win.statusbar.set_text(f"Auto-save interval set to {auto_save_interval} seconds")
        
        dialog.close()

    def start_auto_save_timer(self, win):
        """Start auto-save timer for a window"""
        if win.auto_save_source_id:
            GLib.source_remove(win.auto_save_source_id)
            
        # Set up auto-save timer
        win.auto_save_source_id = GLib.timeout_add_seconds(
            win.auto_save_interval,
            lambda: self.auto_save(win)
        )

    def stop_auto_save_timer(self, win):
        """Stop auto-save timer for a window"""
        if win.auto_save_source_id:
            GLib.source_remove(win.auto_save_source_id)
            win.auto_save_source_id = None

    def auto_save(self, win):
        """Perform auto-save if needed"""
        if win.modified and win.current_file:
            win.statusbar.set_text("Auto-saving...")
            win.webview.evaluate_javascript(
                "document.getElementById('editor').innerHTML;",
                -1, None, None, None,
                lambda webview, result, file: self._on_get_html_content_auto_save(win, webview, result, win.current_file),
                None
            )
        return win.auto_save_enabled  # Continue timer if enabled

    def _on_get_html_content_auto_save(self, win, webview, result, file):
        """Handle auto-save content retrieval"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                                js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                
                self.save_html_content(win, editor_content, file, 
                                      lambda file, result: self._on_auto_save_completed(win, file, result))
        except Exception as e:
            print(f"Error getting HTML content for auto-save: {e}")
            win.statusbar.set_text(f"Auto-save failed: {e}")

    def _on_auto_save_completed(self, win, file, result):
        """Handle auto-save completion"""
        try:
            success, _ = file.replace_contents_finish(result)
            if success:
                win.modified = False  # Reset modified flag after save
                self.update_window_title(win)
                win.statusbar.set_text(f"Auto-saved at {GLib.DateTime.new_now_local().format('%H:%M:%S')}")
            else:
                win.statusbar.set_text("Auto-save failed")
        except GLib.Error as error:
            print(f"Error during auto-save: {error.message}")
            win.statusbar.set_text(f"Auto-save failed: {error.message}")

    def show_error_dialog(self, message):
        """Show error message dialog"""
        if not self.windows:
            print(f"Error: {message}")
            return
            
        # Find the active window
        active_window = None
        for win in self.windows:
            if win.is_active():
                active_window = win
                break
                
        # Fallback to first window if none is active
        if not active_window:
            active_window = self.windows[0]
        
        dialog = Adw.Dialog.new()
        dialog.set_title("Error")
        dialog.set_content_width(350)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
        error_icon.set_pixel_size(48)
        error_icon.set_margin_bottom(12)
        content_box.append(error_icon)
        
        message_label = Gtk.Label(label=message)
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)
        
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        ok_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(ok_button)
        
        content_box.append(button_box)
        
        dialog.set_child(content_box)
        dialog.present(active_window)

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

    def on_print_clicked(self, win, btn):
        """Handle print button click using WebKit's print operation"""
        win.statusbar.set_text("Preparing to print...")
        
        # Create a print operation with WebKit
        print_op = WebKit.PrintOperation.new(win.webview)
        
        # Run the print dialog
        print_op.run_dialog(win)
######################


#### Zoom statusbar
    def on_zoom_changed_statusbar(self, win, scale):
        """Handle zoom scale change with snapping to common values"""
        # Get the current value from the scale
        raw_value = scale.get_value()
        
        # Define common zoom levels to snap to
        common_zoom_levels = [50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400]
        
        # Find the closest common zoom level
        closest_zoom = min(common_zoom_levels, key=lambda x: abs(x - raw_value))
        
        # Check if we're close enough to snap
        snap_threshold = 5  # Snap if within 5% of a common value
        if abs(raw_value - closest_zoom) <= snap_threshold:
            # We're close to a common value, snap to it
            if raw_value != closest_zoom:  # Only set if different to avoid infinite recursion
                scale.set_value(closest_zoom)
            zoom_level = closest_zoom
        else:
            # Not close to a common value, use the rounded value
            zoom_level = int(raw_value)
        
        # Update the label and apply zoom
        win.zoom_label.set_text(f"{zoom_level}%")
        win.zoom_level = zoom_level
        
        # Apply zoom to the editor
        self.apply_zoom(win, zoom_level)
        
    # Add these new methods for zoom control in the statusbar
    def on_zoom_toggle_clicked(self, win, button):
        """Handle zoom toggle button click"""
        is_active = button.get_active()
        win.zoom_revealer.set_reveal_child(is_active)
        
        # Update status text
        if is_active:
            win.statusbar.set_text("Zoom controls shown")
        else:
            # Restore previous status message or show 'Ready'
            win.statusbar.set_text("Ready")

    def on_zoom_in_clicked(self, win):
        """Handle zoom in button click"""
        current_value = win.zoom_scale.get_value()
        new_value = min(current_value + 10, 400)  # Increase by 10%, max 400%
        win.zoom_scale.set_value(new_value)

    def on_zoom_out_clicked(self, win):
        """Handle zoom out button click"""
        current_value = win.zoom_scale.get_value()
        new_value = max(current_value - 10, 50)  # Decrease by 10%, min 50%
        win.zoom_scale.set_value(new_value)

########################### line spacing and column
    def setup_spacing_actions(self, win):
        """Setup actions for paragraph and line spacing"""
        # Line spacing actions
        line_spacing_action = Gio.SimpleAction.new("line-spacing", GLib.VariantType.new("s"))
        line_spacing_action.connect("activate", lambda action, param: self.apply_quick_line_spacing(win, float(param.get_string())))
        win.add_action(line_spacing_action)
        
        line_spacing_dialog_action = Gio.SimpleAction.new("line-spacing-dialog", None)
        line_spacing_dialog_action.connect("activate", lambda action, param: self.on_line_spacing_clicked(win, action, param))
        win.add_action(line_spacing_dialog_action)
        
        # Paragraph spacing actions
        para_spacing_action = Gio.SimpleAction.new("paragraph-spacing", GLib.VariantType.new("s"))
        para_spacing_action.connect("activate", lambda action, param: self.apply_quick_paragraph_spacing(win, int(param.get_string())))
        win.add_action(para_spacing_action)
        
        para_spacing_dialog_action = Gio.SimpleAction.new("paragraph-spacing-dialog", None)
        para_spacing_dialog_action.connect("activate", lambda action, param: self.on_paragraph_spacing_clicked(win, action, param))
        win.add_action(para_spacing_dialog_action)

    def on_paragraph_spacing_clicked(self, win, action, param):
        """Show dialog to adjust paragraph spacing for individual or all paragraphs"""
        dialog = Adw.Dialog()
        dialog.set_title("Paragraph Spacing")
        
        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Create spacing selection
        header = Gtk.Label()
        header.set_markup("<b>Paragraph Spacing Options:</b>")
        header.set_halign(Gtk.Align.START)
        content_box.append(header)
        
        # Radio buttons for scope selection
        scope_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scope_box.set_margin_top(12)
        scope_box.set_margin_bottom(12)
        
        scope_label = Gtk.Label(label="Apply to:")
        scope_label.set_halign(Gtk.Align.START)
        scope_box.append(scope_label)
        
        # Create radio buttons
        current_radio = Gtk.CheckButton(label="Current paragraph only")
        current_radio.set_active(True)
        scope_box.append(current_radio)
        
        all_radio = Gtk.CheckButton(label="All paragraphs")
        all_radio.set_group(current_radio)
        scope_box.append(all_radio)
        
        content_box.append(scope_box)
        
        # Spacing slider
        spacing_label = Gtk.Label(label="Spacing value:")
        spacing_label.set_halign(Gtk.Align.START)
        content_box.append(spacing_label)
        
        adjustment = Gtk.Adjustment.new(10, 0, 50, 1, 5, 0)
        spacing_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        spacing_scale.set_hexpand(True)
        spacing_scale.set_digits(0)
        spacing_scale.set_draw_value(True)
        spacing_scale.add_mark(0, Gtk.PositionType.BOTTOM, "None")
        spacing_scale.add_mark(10, Gtk.PositionType.BOTTOM, "Default")
        spacing_scale.add_mark(30, Gtk.PositionType.BOTTOM, "Wide")
        content_box.append(spacing_scale)
        
        # Preset buttons
        presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        presets_box.set_homogeneous(False)
        presets_box.set_max_children_per_line(100)
        presets_box.set_margin_top(12)
        
        none_button = Gtk.Button(label="None")
        none_button.connect("clicked", lambda btn: spacing_scale.set_value(0))
        presets_box.append(none_button)
        
        small_button = Gtk.Button(label="Small")
        small_button.connect("clicked", lambda btn: spacing_scale.set_value(5))
        presets_box.append(small_button)
        
        medium_button = Gtk.Button(label="Medium") 
        medium_button.connect("clicked", lambda btn: spacing_scale.set_value(15))
        presets_box.append(medium_button)
        
        large_button = Gtk.Button(label="Large")
        large_button.connect("clicked", lambda btn: spacing_scale.set_value(30))
        presets_box.append(large_button)
        
        content_box.append(presets_box)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        # Apply button
        apply_button = Gtk.Button(label="Apply")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", lambda btn: self.apply_paragraph_spacing(
            win, dialog, spacing_scale.get_value(), current_radio.get_active()))
        button_box.append(apply_button)
        
        content_box.append(button_box)
        
        # Set up the dialog content
        dialog.set_child(content_box)
        
        # Present the dialog
        dialog.present(win)

    def apply_paragraph_spacing(self, win, dialog, spacing, current_only):
        """Apply paragraph spacing to the current paragraph or all paragraphs"""
        if current_only:
            # Apply spacing to just the selected paragraphs
            js_code = f"""
            (function() {{
                return setParagraphSpacing({int(spacing)});
            }})();
            """
            self.execute_js(win, js_code)
        else:
            # Apply spacing to all paragraphs
            js_code = f"""
            (function() {{
                // First ensure all direct text content is wrapped
                wrapUnwrappedText(document.getElementById('editor'));
                
                // Target both p tags and div tags as paragraphs
                let paragraphs = document.getElementById('editor').querySelectorAll('p, div');
                
                // Apply to all paragraphs
                for (let i = 0; i < paragraphs.length; i++) {{
                    paragraphs[i].style.marginBottom = '{int(spacing)}px';
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
        
        win.statusbar.set_text(f"Paragraph spacing set to {int(spacing)}px")
        dialog.close()

    def apply_quick_paragraph_spacing(self, win, spacing):
        """Apply spacing to the selected paragraphs through menu action"""
        js_code = f"""
        (function() {{
            return setParagraphSpacing({spacing});
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Paragraph spacing set to {spacing}px")

    def on_line_spacing_clicked(self, win, action, param):
        """Show dialog to adjust line spacing for individual or all paragraphs"""
        dialog = Adw.Dialog()
        dialog.set_title("Line Spacing")
        
        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Create spacing selection
        header = Gtk.Label()
        header.set_markup("<b>Line Spacing Options:</b>")
        header.set_halign(Gtk.Align.START)
        content_box.append(header)
        
        # Radio buttons for scope selection
        scope_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scope_box.set_margin_top(12)
        scope_box.set_margin_bottom(12)
        
        scope_label = Gtk.Label(label="Apply to:")
        scope_label.set_halign(Gtk.Align.START)
        scope_box.append(scope_label)
        
        # Create radio buttons
        current_radio = Gtk.CheckButton(label="Current paragraph only")
        current_radio.set_active(True)
        scope_box.append(current_radio)
        
        all_radio = Gtk.CheckButton(label="All paragraphs")
        all_radio.set_group(current_radio)
        scope_box.append(all_radio)
        
        content_box.append(scope_box)
        
        # Preset buttons
        presets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        presets_label = Gtk.Label(label="Common spacing:")
        presets_label.set_halign(Gtk.Align.START)
        presets_box.append(presets_label)
        
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        buttons_box.set_homogeneous(True)
        
        single_button = Gtk.Button(label="Single (1.0)")
        single_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, 1.0, current_radio.get_active()))
        buttons_box.append(single_button)
        
        one_half_button = Gtk.Button(label="1.5 lines")
        one_half_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, 1.5, current_radio.get_active()))
        buttons_box.append(one_half_button)
        
        double_button = Gtk.Button(label="Double (2.0)")
        double_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, 2.0, current_radio.get_active()))
        buttons_box.append(double_button)
        
        presets_box.append(buttons_box)
        content_box.append(presets_box)
        
        # Custom spacing section
        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        custom_box.set_margin_top(8)
        
        custom_label = Gtk.Label(label="Custom spacing:")
        custom_label.set_halign(Gtk.Align.START)
        custom_box.append(custom_label)
        
        # Add slider for custom spacing
        adjustment = Gtk.Adjustment.new(1.0, 0.8, 3.0, 0.1, 0.2, 0)
        spacing_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        spacing_scale.set_hexpand(True)
        spacing_scale.set_digits(1)
        spacing_scale.set_draw_value(True)
        spacing_scale.add_mark(1.0, Gtk.PositionType.BOTTOM, "1.0")
        spacing_scale.add_mark(1.5, Gtk.PositionType.BOTTOM, "1.5")
        spacing_scale.add_mark(2.0, Gtk.PositionType.BOTTOM, "2.0")
        custom_box.append(spacing_scale)
        
        # Apply custom button
        custom_apply_button = Gtk.Button(label="Apply Custom Value")
        custom_apply_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, spacing_scale.get_value(), current_radio.get_active()))
        custom_apply_button.set_margin_top(8)
        custom_box.append(custom_apply_button)
        
        content_box.append(custom_box)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        content_box.append(button_box)
        
        # Set up the dialog content
        dialog.set_child(content_box)
        
        # Present the dialog
        dialog.present(win)

    def apply_line_spacing(self, win, dialog, spacing, current_only):
        """Apply line spacing to the current paragraph or all paragraphs"""
        if current_only:
            # Apply spacing to just the selected paragraphs
            js_code = f"""
            (function() {{
                return setLineSpacing({spacing});
            }})();
            """
            self.execute_js(win, js_code)
        else:
            # Apply spacing to all paragraphs
            js_code = f"""
            (function() {{
                // First ensure all direct text content is wrapped
                wrapUnwrappedText(document.getElementById('editor'));
                
                // Target both p tags and div tags as paragraphs
                let paragraphs = document.getElementById('editor').querySelectorAll('p, div');
                
                // Apply to all paragraphs
                for (let i = 0; i < paragraphs.length; i++) {{
                    paragraphs[i].style.lineHeight = '{spacing}';
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
        
        win.statusbar.set_text(f"Line spacing set to {spacing}")
        dialog.close()
    def apply_quick_line_spacing(self, win, spacing):
        """Apply line spacing to the selected paragraphs through menu action"""
        js_code = f"""
        (function() {{
            return setLineSpacing({spacing});
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Line spacing set to {spacing}")

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

        {self.save_state_js()}
        {self.perform_undo_js()}
        {self.perform_redo_js()}
        {self.find_last_text_node_js()}
        {self.get_stack_sizes_js()}
        {self.set_content_js()}
        {self.selection_change_js()}
        {self.search_functions_js()}
        {self.paragraph_and_line_spacing_js()}
        {self.init_editor_js()}
        """

    def paragraph_and_line_spacing_js(self):
        """JavaScript for paragraph and line spacing functions"""
        return """
        // Function to set paragraph spacing
        function setParagraphSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Strategy: Get all paragraphs in the selection range
            const range = selection.getRangeAt(0);
            const startNode = findContainerParagraph(range.startContainer);
            const endNode = findContainerParagraph(range.endContainer);
            
            // If we couldn't find containers, try a different approach
            if (!startNode || !endNode) {
                return setSimpleParagraphSpacing(spacing);
            }
            
            // Get all paragraphs in the selection range
            const paragraphs = getAllParagraphsInRange(startNode, endNode);
            
            // Apply spacing to all found paragraphs
            paragraphs.forEach(para => {
                para.style.marginBottom = spacing + 'px';
            });
            
            return true;
        }
        
        // Function to set line spacing
        function setLineSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Strategy: Get all paragraphs in the selection range
            const range = selection.getRangeAt(0);
            const startNode = findContainerParagraph(range.startContainer);
            const endNode = findContainerParagraph(range.endContainer);
            
            // If we couldn't find containers, try a different approach
            if (!startNode || !endNode) {
                return setSimpleLineSpacing(spacing);
            }
            
            // Get all paragraphs in the selection range
            const paragraphs = getAllParagraphsInRange(startNode, endNode);
            
            // Apply spacing to all found paragraphs
            paragraphs.forEach(para => {
                para.style.lineHeight = spacing;
            });
            
            return true;
        }
        
        // Helper function to find the container paragraph of a node
        function findContainerParagraph(node) {
            while (node && node.id !== 'editor') {
                if (node.nodeType === 1 && 
                    (node.nodeName.toLowerCase() === 'p' || 
                     node.nodeName.toLowerCase() === 'div')) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        }
        
        // Get all paragraphs between start and end node (inclusive)
        function getAllParagraphsInRange(startNode, endNode) {
            // If start and end are the same, just return that node
            if (startNode === endNode) {
                return [startNode];
            }
            
            // Get all paragraphs in the editor
            const allParagraphs = Array.from(document.getElementById('editor').querySelectorAll('p, div'));
            
            // Find the indices of our start and end nodes
            const startIndex = allParagraphs.indexOf(startNode);
            const endIndex = allParagraphs.indexOf(endNode);
            
            // Handle case where we can't find one of the nodes
            if (startIndex === -1 || endIndex === -1) {
                // Fall back to just the nodes we have
                return [startNode, endNode].filter(node => node !== null);
            }
            
            // Return all paragraphs between start and end (inclusive)
            return allParagraphs.slice(
                Math.min(startIndex, endIndex), 
                Math.max(startIndex, endIndex) + 1
            );
        }
        
        // Fallback method for paragraph spacing when selection is unusual
        function setSimpleParagraphSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            let node = selection.getRangeAt(0).commonAncestorContainer;
            
            // Navigate up to find the paragraph node
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            
            // Find the containing paragraph or div
            while (node && node.id !== 'editor' && 
                  (node.nodeName.toLowerCase() !== 'p' && 
                   node.nodeName.toLowerCase() !== 'div')) {
                node = node.parentNode;
            }
            
            if (node && node.id !== 'editor') {
                node.style.marginBottom = spacing + 'px';
                return true;
            }
            return false;
        }
        
        // Fallback method for line spacing when selection is unusual
        function setSimpleLineSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            let node = selection.getRangeAt(0).commonAncestorContainer;
            
            // Navigate up to find the paragraph node
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            
            // Find the containing paragraph or div
            while (node && node.id !== 'editor' && 
                  (node.nodeName.toLowerCase() !== 'p' && 
                   node.nodeName.toLowerCase() !== 'div')) {
                node = node.parentNode;
            }
            
            if (node && node.id !== 'editor') {
                node.style.lineHeight = spacing;
                return true;
            }
            return false;
        }
        
        // Function to wrap unwrapped text
        function wrapUnwrappedText(container) {
            let childNodes = Array.from(container.childNodes);
            for (let i = 0; i < childNodes.length; i++) {
                let node = childNodes[i];
                if (node.nodeType === 3 && node.nodeValue.trim() !== '') {
                    // It's a text node with content, wrap it
                    let wrapper = document.createElement('div');
                    node.parentNode.insertBefore(wrapper, node);
                    wrapper.appendChild(node);
                }
            }
        }
        // Function to apply column layout to a container
        function setColumnLayout(container, columns) {
            if (columns <= 1) {
                // Remove column styling
                container.style.columnCount = '';
                container.style.columnGap = '';
                container.style.columnRule = '';
            } else {
                // Apply column styling
                container.style.columnCount = columns;
                container.style.columnGap = '20px';
                container.style.columnRule = '1px solid #ccc';
            }
        }
        """      
        
############ column
    def setup_spacing_actions(self, win):
        """Setup actions for paragraph and line spacing"""
        # Line spacing actions
        line_spacing_action = Gio.SimpleAction.new("line-spacing", GLib.VariantType.new("s"))
        line_spacing_action.connect("activate", lambda action, param: self.apply_quick_line_spacing(win, float(param.get_string())))
        win.add_action(line_spacing_action)
        
        line_spacing_dialog_action = Gio.SimpleAction.new("line-spacing-dialog", None)
        line_spacing_dialog_action.connect("activate", lambda action, param: self.on_line_spacing_clicked(win, action, param))
        win.add_action(line_spacing_dialog_action)
        
        # Paragraph spacing actions
        para_spacing_action = Gio.SimpleAction.new("paragraph-spacing", GLib.VariantType.new("s"))
        para_spacing_action.connect("activate", lambda action, param: self.apply_quick_paragraph_spacing(win, int(param.get_string())))
        win.add_action(para_spacing_action)
        
        para_spacing_dialog_action = Gio.SimpleAction.new("paragraph-spacing-dialog", None)
        para_spacing_dialog_action.connect("activate", lambda action, param: self.on_paragraph_spacing_clicked(win, action, param))
        win.add_action(para_spacing_dialog_action)
        
        # Column layout actions
        column_action = Gio.SimpleAction.new("set-columns", GLib.VariantType.new("s"))
        column_action.connect("activate", lambda action, param: self.apply_column_layout(win, int(param.get_string())))
        win.add_action(column_action)        

    def apply_column_layout(self, win, columns):
        """Apply column layout to the selected content"""
        js_code = f"""
        (function() {{
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Strategy similar to paragraph spacing
            const range = selection.getRangeAt(0);
            
            // First, try to get a structured element like div or p
            let container = null;
            
            // Check if selection is within a paragraph or div
            let node = range.commonAncestorContainer;
            if (node.nodeType === 3) {{ // Text node
                node = node.parentNode;
            }}
            
            // Find a suitable container or create one
            while (node && node.id !== 'editor') {{
                if (node.nodeName.toLowerCase() === 'div' || 
                    node.nodeName.toLowerCase() === 'p') {{
                    container = node;
                    break;
                }}
                node = node.parentNode;
            }}
            
            // If we didn't find a container, we'll need to create a wrapper
            if (!container || container.id === 'editor') {{
                // Create a wrapper around the selection
                document.execCommand('formatBlock', false, 'div');
                
                // Get the newly created div
                const newRange = selection.getRangeAt(0);
                node = newRange.commonAncestorContainer;
                if (node.nodeType === 3) {{
                    node = node.parentNode;
                }}
                
                // Find our new container
                while (node && node.id !== 'editor') {{
                    if (node.nodeName.toLowerCase() === 'div') {{
                        container = node;
                        break;
                    }}
                    node = node.parentNode;
                }}
            }}
            
            if (container) {{
                if ({columns} <= 1) {{
                    // Remove column styling
                    container.style.columnCount = '';
                    container.style.columnGap = '';
                    container.style.columnRule = '';
                    return true;
                }} else {{
                    // Apply column styling
                    container.style.columnCount = {columns};
                    container.style.columnGap = '20px';
                    container.style.columnRule = '1px solid #ccc';
                    return true;
                }}
            }}
            
            return false;
        }})();
        """
        self.execute_js(win, js_code)
        
        status_text = "Column layout removed" if columns <= 1 else f"Applied {columns}-column layout"
        win.statusbar.set_text(status_text)
#####################
    def create_main_layout(fself):
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        toolbar_view = Adw.ToolbarView()
        main_box.append(toolbar_view)
        header = Adw.HeaderBar()
        header.add_css_class("flat-header")
        header.set_centering_policy(Adw.CenteringPolicy.STRICT)
        toolbar_view.add_top_bar(header)

        # Create the FlowBox for toolbar groups
        toolbars_flowbox = Gtk.FlowBox()
        toolbars_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        toolbars_flowbox.set_max_children_per_line(100)  # Allow many groups per line
        toolbars_flowbox.add_css_class("toolbar-container")
        
        # Create and add toolbar groups
        self.create_file_toolbar_group(toolbars_flowbox)
        self.create_formatting_toolbar_group(toolbars_flowbox)
        
        # Content area (editor)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.webview)
        
        # Content box containing toolbar and editor
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(toolbars_flowbox)
        content_box.append(scroll)
        toolbar_view.set_content(content_box)

    def create_window(self):
        """Create a new window with all initialization"""
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
        
        # Create content box (for webview and toolbars)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        # Create webview first so it's available when needed by handlers
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
        except:
            print("Warning: Could not set up JavaScript message handlers")
        
        # Now create toolbar container with FlowBox
        # Modify the FlowBox creation and properties
        win.toolbars_flowbox = Adw.WrapBox()
        win.toolbars_flowbox.set_child_spacing(5)
        win.toolbars_flowbox.set_line_spacing(5)


# Allow wrapping after each child if needed

        #win.toolbars_flowbox.add_css_class("toolbar-container")
        win.toolbars_flowbox.set_margin_start(0)
        win.toolbars_flowbox.set_margin_end(5)
        win.toolbars_flowbox.set_margin_top(5)
        win.toolbars_flowbox.set_margin_bottom(5)
        
        # === FILE/EDIT BUTTONS ===
        # File operations group
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_group.add_css_class("toolbar-group")
        file_group.add_css_class("linked")
        
        for icon, handler in [
            ("document-new-symbolic", self.on_new_clicked), 
            ("document-open-symbolic", self.on_open_clicked),
            ("document-save-symbolic", self.on_save_clicked), 
            ("document-save-as-symbolic", self.on_save_as_clicked),
        ]:
            btn = Gtk.Button(icon_name=icon)
            btn.set_tooltip_text(icon.split("-")[1].capitalize())
            btn.add_css_class("flat")
            btn.set_size_request(40, 36)
            btn.connect("clicked", lambda b, h=handler: h(win, b))
            file_group.append(btn)
        
        # Add file group directly to the FlowBox
        #win.toolbars_flowbox.insert(file_group, -1)
        
        # Edit operations group
        edit_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        edit_group.add_css_class("toolbar-group")
        edit_group.add_css_class("linked")
        
        for icon, handler in [
            ("edit-cut-symbolic", self.on_cut_clicked), 
            ("edit-copy-symbolic", self.on_copy_clicked),
            ("edit-paste-symbolic", self.on_paste_clicked)
        ]:
            btn = Gtk.Button(icon_name=icon)
            btn.set_tooltip_text(icon.split("-")[1].capitalize())
            btn.add_css_class("flat")
            btn.set_size_request(40, 36)
            btn.connect("clicked", lambda b, h=handler: h(win, b))
            #edit_group.append(btn)
            file_group.append(btn)
        
        # Add edit group directly to the FlowBox
        #win.toolbars_flowbox.insert(file_group, -1)
        
        # Undo/Redo group
        history_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        history_group.add_css_class("toolbar-group")
        history_group.add_css_class("linked")
        
        # Undo button
        win.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        win.undo_button.set_tooltip_text("Undo")
        win.undo_button.add_css_class("flat")
        win.undo_button.set_size_request(40, 36)
        win.undo_button.connect("clicked", lambda btn: self.on_undo_clicked(win, btn))
        win.undo_button.set_sensitive(False)
        file_group.append(win.undo_button)
        
        # Redo button
        win.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        win.redo_button.set_tooltip_text("Redo")
        win.redo_button.add_css_class("flat")
        win.redo_button.set_size_request(40, 36)
        win.redo_button.connect("clicked", lambda btn: self.on_redo_clicked(win, btn))
        win.redo_button.set_sensitive(False)
        file_group.append(win.redo_button)
        
        # Add find button
        win.find_button = Gtk.ToggleButton()
        find_icon = Gtk.Image.new_from_icon_name("edit-find-replace-symbolic")
        win.find_button.set_child(find_icon)
        win.find_button.set_tooltip_text("Find and Replace (Ctrl+F)")
        win.find_button.add_css_class("flat")
        win.find_button.set_size_request(40, 36)
        win.find_button_handler_id = win.find_button.connect("toggled", lambda btn: self.on_find_button_toggled(win, btn))
        file_group.append(win.find_button)
        
        # Add history group to FlowBox
        win.toolbars_flowbox.append(file_group)
        
        # === TEXT STYLE GROUP ===
        text_style_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        text_style_group.add_css_class("toolbar-group")
        
        # Paragraph style dropdown
        heading_store = Gtk.StringList()
        for h in ["Normal", "H1", "H2", "H3", "H4", "H5", "H6"]:
            heading_store.append(h)
        win.paragraph_style_dropdown = Gtk.DropDown(model=heading_store)
        win.paragraph_style_handler_id = win.paragraph_style_dropdown.connect("notify::selected", 
            lambda dropdown, param: self.on_paragraph_style_changed(win, dropdown))
        win.paragraph_style_dropdown.add_css_class("flat")
        win.paragraph_style_dropdown.set_size_request(100, 36)
        text_style_group.append(win.paragraph_style_dropdown)
        
        # Font family dropdown
        font_map = PangoCairo.FontMap.get_default()
        families = font_map.list_families()
        font_names = sorted([family.get_name() for family in families])
        font_store = Gtk.StringList(strings=font_names)
        win.font_dropdown = Gtk.DropDown(model=font_store)
        default_font_index = font_names.index("Sans") if "Sans" in font_names else 0
        win.font_dropdown.set_selected(default_font_index)
        win.font_handler_id = win.font_dropdown.connect("notify::selected", 
            lambda dropdown, param: self.on_font_changed(win, dropdown))
        win.font_dropdown.add_css_class("flat")
        win.font_dropdown.set_size_request(150, 36)
        text_style_group.append(win.font_dropdown)
        
        # Font size dropdown
        win.size_range = [str(size) for size in [6, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72, 96]]
        size_store = Gtk.StringList(strings=win.size_range)
        win.font_size_dropdown = Gtk.DropDown(model=size_store)
        win.font_size_dropdown.set_selected(6)  # Default to 12pt
        win.font_size_handler_id = win.font_size_dropdown.connect("notify::selected", 
            lambda dropdown, param: self.on_font_size_changed(win, dropdown))
        win.font_size_dropdown.add_css_class("flat")
        win.font_size_dropdown.set_size_request(60, 36)
        text_style_group.append(win.font_size_dropdown)
        
        # Add text style group to FlowBox
        win.toolbars_flowbox.append(text_style_group)
        
        # === TEXT FORMATTING GROUP ===
        text_format_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        text_format_group.add_css_class("toolbar-group")
        text_format_group.add_css_class("linked")
        
        # Bold, italic, underline, strikethrough buttons
        win.bold_button = Gtk.ToggleButton(icon_name="format-text-bold-symbolic")
        win.bold_button.add_css_class("flat")
        win.bold_button.set_size_request(40, 36)
        win.bold_handler_id = win.bold_button.connect("toggled", lambda btn: self.on_bold_toggled(win, btn))
        text_format_group.append(win.bold_button)
        
        win.italic_button = Gtk.ToggleButton(icon_name="format-text-italic-symbolic")
        win.italic_button.add_css_class("flat")
        win.italic_button.set_size_request(40, 36)
        win.italic_handler_id = win.italic_button.connect("toggled", lambda btn: self.on_italic_toggled(win, btn))
        text_format_group.append(win.italic_button)
        
        win.underline_button = Gtk.ToggleButton(icon_name="format-text-underline-symbolic")
        win.underline_button.add_css_class("flat")
        win.underline_button.set_size_request(40, 36)
        win.underline_handler_id = win.underline_button.connect("toggled", lambda btn: self.on_underline_toggled(win, btn))
        text_format_group.append(win.underline_button)
        
        win.strikeout_button = Gtk.ToggleButton(icon_name="format-text-strikethrough-symbolic")
        win.strikeout_button.add_css_class("flat")
        win.strikeout_button.set_size_request(40, 36)
        win.strikeout_handler_id = win.strikeout_button.connect("toggled", lambda btn: self.on_strikeout_toggled(win, btn))
        text_format_group.append(win.strikeout_button)
        
        # Add subscript and superscript buttons if your handlers exist
        if hasattr(self, 'on_subscript_toggled'):
            win.subscript_button = Gtk.ToggleButton(icon_name="format-text-subscript-symbolic")
            win.subscript_button.set_tooltip_text("Subscript")
            win.subscript_button.add_css_class("flat")
            win.subscript_button.set_size_request(40, 36)
            win.subscript_handler_id = win.subscript_button.connect("toggled", 
                lambda btn: self.on_subscript_toggled(win, btn))
            text_format_group.append(win.subscript_button)
        
        if hasattr(self, 'on_superscript_toggled'):
            win.superscript_button = Gtk.ToggleButton(icon_name="format-text-superscript-symbolic")
            win.superscript_button.set_tooltip_text("Superscript")
            win.superscript_button.add_css_class("flat")
            win.superscript_button.set_size_request(40, 36)
            win.superscript_handler_id = win.superscript_button.connect("toggled", 
                lambda btn: self.on_superscript_toggled(win, btn))
            text_format_group.append(win.superscript_button)
        
        # Add text format group to FlowBox
        win.toolbars_flowbox.append(text_format_group)
        
        # === LIST AND INDENT GROUP ===
        list_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        list_group.add_css_class("toolbar-group")
        list_group.add_css_class("linked")
        
        # Bullet list button
        win.bullet_list_button = Gtk.ToggleButton(icon_name="view-list-bullet-symbolic")
        win.bullet_list_button.set_tooltip_text("Bullet List")
        win.bullet_list_button.add_css_class("flat")
        win.bullet_list_button.set_size_request(40, 36)
        win.bullet_list_button.handler_id = win.bullet_list_button.connect("toggled", 
            lambda btn: self.on_bullet_list_toggled(win, btn))
        list_group.append(win.bullet_list_button)
        
        # Numbered list button
        win.numbered_list_button = Gtk.ToggleButton(icon_name="view-list-ordered-symbolic")
        win.numbered_list_button.set_tooltip_text("Numbered List")
        win.numbered_list_button.add_css_class("flat")
        win.numbered_list_button.set_size_request(40, 36)
        win.numbered_list_button.handler_id = win.numbered_list_button.connect("toggled", 
            lambda btn: self.on_numbered_list_toggled(win, btn))
        list_group.append(win.numbered_list_button)
        
        # Indent buttons
        indent_button = Gtk.Button(icon_name="format-indent-more-symbolic")
        indent_button.set_tooltip_text("Increase Indent")
        indent_button.add_css_class("flat")
        indent_button.set_size_request(40, 36)
        indent_button.connect("clicked", lambda btn: self.on_indent_clicked(win, btn))
        list_group.append(indent_button)
        
        outdent_button = Gtk.Button(icon_name="format-indent-less-symbolic")
        outdent_button.set_tooltip_text("Decrease Indent")
        outdent_button.add_css_class("flat")
        outdent_button.set_size_request(40, 36)
        outdent_button.connect("clicked", lambda btn: self.on_outdent_clicked(win, btn))
        list_group.append(outdent_button)
        
        # Add list group to FlowBox
        win.toolbars_flowbox.append(list_group)
        
        # === ALIGNMENT GROUP ===
        align_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        align_group.add_css_class("toolbar-group")
        align_group.add_css_class("linked")
        
        # Align left button
        align_left_button = Gtk.ToggleButton(icon_name="format-justify-left-symbolic")
        align_left_button.set_tooltip_text("Align Left")
        align_left_button.add_css_class("flat")
        align_left_button.set_size_request(40, 36)
        align_left_button.handler_id = align_left_button.connect("toggled", 
            lambda btn: self.on_align_left_toggled(win, btn))
        align_group.append(align_left_button)
        
        # Align center button
        align_center_button = Gtk.ToggleButton(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Align Center")
        align_center_button.add_css_class("flat")
        align_center_button.set_size_request(40, 36)
        align_center_button.handler_id = align_center_button.connect("toggled", 
            lambda btn: self.on_align_center_toggled(win, btn))
        align_group.append(align_center_button)
        
        # Align right button
        align_right_button = Gtk.ToggleButton(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right")
        align_right_button.add_css_class("flat")
        align_right_button.set_size_request(40, 36)
        align_right_button.handler_id = align_right_button.connect("toggled", 
            lambda btn: self.on_align_right_toggled(win, btn))
        align_group.append(align_right_button)
        
        # Align justify button
        align_justify_button = Gtk.ToggleButton(icon_name="format-justify-fill-symbolic")
        align_justify_button.set_tooltip_text("Justify")
        align_justify_button.add_css_class("flat")
        align_justify_button.set_size_request(40, 36)
        align_justify_button.handler_id = align_justify_button.connect("toggled", 
            lambda btn: self.on_align_justify_toggled(win, btn))
        align_group.append(align_justify_button)
        
        # Store references to alignment buttons for toggling
        win.alignment_buttons = {
            'left': align_left_button,
            'center': align_center_button, 
            'right': align_right_button,
            'justify': align_justify_button
        }
        
        align_left_button.set_active(True)
        
        # Add alignment group to FlowBox
        win.toolbars_flowbox.append(align_group)
        
        # Create a revealer for the toolbar
        win.toolbar_revealer = Gtk.Revealer()  # Single toolbar revealer
        win.toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.toolbar_revealer.set_transition_duration(250)
        win.toolbar_revealer.set_reveal_child(True)  # Visible by default
        win.toolbar_revealer.set_child(win.toolbars_flowbox)
        
        win.headerbar_box.append(win.toolbar_revealer)
        
        # For backward compatibility
        win.formatting_toolbar_revealer = win.toolbar_revealer
        
        # Set the headerbar_box as the child of the headerbar_revealer
        win.headerbar_revealer.set_child(win.headerbar_box)
        win.main_box.append(win.headerbar_revealer)
        
        # Load HTML content
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        # Find bar with revealer
        win.find_bar = self.create_find_bar(win)
        content_box.append(win.find_bar)
        
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
        
        # Add zoom toggle button if needed
        if hasattr(self, 'on_zoom_toggle_clicked'):
            win.zoom_toggle_button = Gtk.ToggleButton()
            win.zoom_toggle_button.set_icon_name("org.gnome.Settings-accessibility-zoom-symbolic")
            win.zoom_toggle_button.set_tooltip_text("Toggle Zoom Controls")
            win.zoom_toggle_button.add_css_class("flat")
            win.zoom_toggle_button.connect("toggled", lambda btn: self.on_zoom_toggle_clicked(win, btn))
            statusbar_box.append(win.zoom_toggle_button)
            
            # Create zoom revealer
            win.zoom_revealer = Gtk.Revealer()
            win.zoom_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
            win.zoom_revealer.set_transition_duration(200)
            win.zoom_revealer.set_reveal_child(False)  # Hidden by default
            
            # Create zoom control elements
            zoom_control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            zoom_control_box.add_css_class("linked")
            zoom_control_box.set_halign(Gtk.Align.END)
            
            # Create zoom level label
            win.zoom_label = Gtk.Label(label="100%")
            win.zoom_label.set_width_chars(4)
            win.zoom_label.set_margin_start(6)
            zoom_control_box.append(win.zoom_label)
            
            # Add zoom out button
            zoom_out_button = Gtk.Button.new_from_icon_name("zoom-out-symbolic")
            zoom_out_button.set_tooltip_text("Zoom Out")
            zoom_out_button.connect("clicked", lambda btn: self.on_zoom_out_clicked(win))
            zoom_control_box.append(zoom_out_button)
            
            # Create the slider for zoom
            adjustment = Gtk.Adjustment(
                value=100,     # Default value
                lower=50,      # Minimum value
                upper=400,     # Maximum value
                step_increment=10,  # Step size
                page_increment=50   # Page step size
            )

            win.zoom_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
            win.zoom_scale.set_draw_value(False)
            win.zoom_scale.set_size_request(200, -1)
            win.zoom_scale.set_round_digits(0)

            # Add marks
            for mark_value in [50, 100, 200, 300]:
                win.zoom_scale.add_mark(mark_value, Gtk.PositionType.BOTTOM, None)

            # Connect to zoom handler
            win.zoom_scale.connect("value-changed", lambda s: self.on_zoom_changed_statusbar(win, s))
            zoom_control_box.append(win.zoom_scale)

            # Add zoom in button
            zoom_in_button = Gtk.Button.new_from_icon_name("zoom-in-symbolic")
            zoom_in_button.set_tooltip_text("Zoom In")
            zoom_in_button.connect("clicked", lambda btn: self.on_zoom_in_clicked(win))
            zoom_control_box.append(zoom_in_button)
            
            # Set the control box as child of the revealer
            win.zoom_revealer.set_child(zoom_control_box)
            statusbar_box.insert_child_after(win.zoom_revealer, win.statusbar)
        
        # Add the statusbar to its revealer
        win.statusbar_revealer.set_child(statusbar_box)
        content_box.append(win.statusbar_revealer)

        win.main_box.append(content_box)
        win.set_content(win.main_box)

        self.setup_keyboard_shortcuts(win)
        
        # Add case change action to the window
        case_change_action = Gio.SimpleAction.new("change-case", GLib.VariantType.new("s"))
        case_change_action.connect("activate", lambda action, param: self.on_change_case(win, param.get_string()))
        win.add_action(case_change_action)
        
        win.connect("close-request", self.on_window_close_request)

        # Add to windows list
        self.windows.append(win)
        
        # Setup spacing actions if the method exists
        if hasattr(self, 'setup_spacing_actions'):
            self.setup_spacing_actions(win)
        
        return win
         
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
