#!/usr/bin/env python3
import sys
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GtkSource', '5')
gi.require_version('Pango', '1.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Adw, GtkSource, Pango, Gdk, GLib, Gio

class RichTextEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.RichTextEditor",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        self.connect('activate', self.on_activate)
        self.current_file = None
        self.modified = False
        
    def on_activate(self, app):
        # Set up the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(800, 600)
        self.win.set_title("Rich Text Editor")
        
        # Create Adw header bar with controls
        self.header = Adw.HeaderBar()
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")
        
        # Create menu model
        menu = Gio.Menu()
        menu.append("New", "app.new")
        menu.append("Open", "app.open")
        menu.append("Save", "app.save")
        menu.append("Save As", "app.save_as")
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")
        
        # Set up menu actions
        self.create_action("new", self.on_new_clicked)
        self.create_action("open", self.on_open_clicked)
        self.create_action("save", self.on_save_clicked)
        self.create_action("save_as", self.on_save_as_clicked)
        self.create_action("about", self.on_about_clicked)
        self.create_action("quit", self.on_quit)
        
        self.menu_button.set_menu_model(menu)
        self.header.pack_end(self.menu_button)
        
        # Add formatting toolbar buttons
        self.format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.format_box.add_css_class("toolbar")
        
        # Bold button
        self.bold_button = Gtk.ToggleButton()
        self.bold_button.set_icon_name("format-text-bold-symbolic")
        self.bold_button.set_tooltip_text("Bold")
        self.bold_button.connect("toggled", self.on_bold_toggled)
        self.format_box.append(self.bold_button)
        
        # Italic button
        self.italic_button = Gtk.ToggleButton()
        self.italic_button.set_icon_name("format-text-italic-symbolic")
        self.italic_button.set_tooltip_text("Italic")
        self.italic_button.connect("toggled", self.on_italic_toggled)
        self.format_box.append(self.italic_button)
        
        # Underline button
        self.underline_button = Gtk.ToggleButton()
        self.underline_button.set_icon_name("format-text-underline-symbolic")
        self.underline_button.set_tooltip_text("Underline")
        self.underline_button.connect("toggled", self.on_underline_toggled)
        self.format_box.append(self.underline_button)
        
        # Add separator
        self.format_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Font size buttons
        self.font_smaller_button = Gtk.Button()
        self.font_smaller_button.set_icon_name("format-text-smaller-symbolic")
        self.font_smaller_button.set_tooltip_text("Decrease Font Size")
        self.font_smaller_button.connect("clicked", self.on_font_size_change, -1)
        self.format_box.append(self.font_smaller_button)
        
        self.font_larger_button = Gtk.Button()
        self.font_larger_button.set_icon_name("format-text-larger-symbolic")
        self.font_larger_button.set_tooltip_text("Increase Font Size")
        self.font_larger_button.connect("clicked", self.on_font_size_change, 1)
        self.format_box.append(self.font_larger_button)
        
        # Add separator
        self.format_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Alignment buttons
        self.align_left_button = Gtk.ToggleButton()
        self.align_left_button.set_icon_name("format-justify-left-symbolic")
        self.align_left_button.set_tooltip_text("Align Left")
        self.align_left_button.connect("toggled", self.on_align_toggled, "left")
        self.format_box.append(self.align_left_button)
        
        self.align_center_button = Gtk.ToggleButton()
        self.align_center_button.set_icon_name("format-justify-center-symbolic")
        self.align_center_button.set_tooltip_text("Align Center")
        self.align_center_button.connect("toggled", self.on_align_toggled, "center")
        self.format_box.append(self.align_center_button)
        
        self.align_right_button = Gtk.ToggleButton()
        self.align_right_button.set_icon_name("format-justify-right-symbolic")
        self.align_right_button.set_tooltip_text("Align Right")
        self.align_right_button.connect("toggled", self.on_align_toggled, "right")
        self.format_box.append(self.align_right_button)
        
        # Add separator
        self.format_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Font color button
        self.color_button = Gtk.ColorButton()
        self.color_button.set_tooltip_text("Text Color")
        self.color_button.connect("color-set", self.on_color_set)
        self.format_box.append(self.color_button)
        
        # Create ScrolledWindow for TextView
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        
        # Create TextView with buffer
        self.textbuffer = Gtk.TextBuffer()
        self.textview = Gtk.TextView.new_with_buffer(self.textbuffer)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_top_margin(10)
        self.textview.set_bottom_margin(10)
        self.textview.set_left_margin(10)
        self.textview.set_right_margin(10)
        
        # Connect buffer signals
        self.textbuffer.connect("changed", self.on_buffer_changed)
        
        # Add TextView to ScrolledWindow
        self.scrolled_window.set_child(self.textview)
        
        # Create status bar
        self.statusbar = Gtk.Label()
        self.statusbar.set_xalign(0)
        self.statusbar.set_margin_start(10)
        self.statusbar.set_margin_end(10)
        self.statusbar.set_margin_top(5)
        self.statusbar.set_margin_bottom(5)
        self.update_statusbar()
        
        # Set up the layout
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox.append(self.header)
        self.vbox.append(self.format_box)
        self.vbox.append(self.scrolled_window)
        self.vbox.append(self.statusbar)
        
        self.win.set_content(self.vbox)
        self.win.present()
        
        # Set up tags for text styling
        self.setup_text_tags()
        
        # Connect selection change signal
        self.textbuffer.connect("notify::cursor-position", self.on_cursor_position_changed)
        
    def setup_text_tags(self):
        """Initialize the text tags for the buffer"""
        self.textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.textbuffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        
        # Create tags for font sizes (8pt to 36pt)
        for size in range(8, 37, 2):
            self.textbuffer.create_tag(f"size-{size}", size_points=size)
        
        # Create alignment tags
        self.textbuffer.create_tag("left", justification=Gtk.Justification.LEFT)
        self.textbuffer.create_tag("center", justification=Gtk.Justification.CENTER)
        self.textbuffer.create_tag("right", justification=Gtk.Justification.RIGHT)
    
    def create_action(self, name, callback):
        """Add an app action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
    
    def on_buffer_changed(self, buffer):
        """Handle text buffer changes"""
        self.modified = True
        self.update_statusbar()
    
    def update_statusbar(self):
        """Update the status bar with current file and modified status"""
        status = ""
        if self.current_file:
            status = f"Editing: {os.path.basename(self.current_file)}"
        else:
            status = "New Document"
            
        if self.modified:
            status += " (modified)"
            
        self.statusbar.set_text(status)
    
    def on_cursor_position_changed(self, buffer, param):
        """Update formatting buttons when cursor position changes"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                self.update_format_buttons(start, end)
        else:
            cursor = self.textbuffer.get_insert()
            pos = self.textbuffer.get_iter_at_mark(cursor)
            self.update_format_buttons_at_iter(pos)
    
    def update_format_buttons(self, start, end):
        """Update format buttons based on selected text"""
        # Check if entire selection has bold
        has_bold = True
        has_italic = True
        has_underline = True
        
        pos = start.copy()
        while pos.compare(end) < 0:
            if not pos.has_tag(self.textbuffer.get_tag_table().lookup("bold")):
                has_bold = False
            if not pos.has_tag(self.textbuffer.get_tag_table().lookup("italic")):
                has_italic = False
            if not pos.has_tag(self.textbuffer.get_tag_table().lookup("underline")):
                has_underline = False
            
            if not (has_bold or has_italic or has_underline):
                break
            
            pos.forward_char()
        
        # Update toggle button states without triggering signals
        self.bold_button.handler_block_by_func(self.on_bold_toggled)
        self.bold_button.set_active(has_bold)
        self.bold_button.handler_unblock_by_func(self.on_bold_toggled)
        
        self.italic_button.handler_block_by_func(self.on_italic_toggled)
        self.italic_button.set_active(has_italic)
        self.italic_button.handler_unblock_by_func(self.on_italic_toggled)
        
        self.underline_button.handler_block_by_func(self.on_underline_toggled)
        self.underline_button.set_active(has_underline)
        self.underline_button.handler_unblock_by_func(self.on_underline_toggled)
    
    def update_format_buttons_at_iter(self, iter):
        """Update format buttons based on text at cursor position"""
        has_bold = iter.has_tag(self.textbuffer.get_tag_table().lookup("bold"))
        has_italic = iter.has_tag(self.textbuffer.get_tag_table().lookup("italic"))
        has_underline = iter.has_tag(self.textbuffer.get_tag_table().lookup("underline"))
        
        # Update toggle button states without triggering signals
        self.bold_button.handler_block_by_func(self.on_bold_toggled)
        self.bold_button.set_active(has_bold)
        self.bold_button.handler_unblock_by_func(self.on_bold_toggled)
        
        self.italic_button.handler_block_by_func(self.on_italic_toggled)
        self.italic_button.set_active(has_italic)
        self.italic_button.handler_unblock_by_func(self.on_italic_toggled)
        
        self.underline_button.handler_block_by_func(self.on_underline_toggled)
        self.underline_button.set_active(has_underline)
        self.underline_button.handler_unblock_by_func(self.on_underline_toggled)
        
        # Update alignment buttons
        has_left = iter.has_tag(self.textbuffer.get_tag_table().lookup("left"))
        has_center = iter.has_tag(self.textbuffer.get_tag_table().lookup("center"))
        has_right = iter.has_tag(self.textbuffer.get_tag_table().lookup("right"))
        
        self.align_left_button.handler_block_by_func(self.on_align_toggled)
        self.align_left_button.set_active(has_left)
        self.align_left_button.handler_unblock_by_func(self.on_align_toggled)
        
        self.align_center_button.handler_block_by_func(self.on_align_toggled)
        self.align_center_button.set_active(has_center)
        self.align_center_button.handler_unblock_by_func(self.on_align_toggled)
        
        self.align_right_button.handler_block_by_func(self.on_align_toggled)
        self.align_right_button.set_active(has_right)
        self.align_right_button.handler_unblock_by_func(self.on_align_toggled)
    
    def on_bold_toggled(self, button):
        """Toggle bold formatting"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                if button.get_active():
                    self.textbuffer.apply_tag_by_name("bold", start, end)
                else:
                    self.textbuffer.remove_tag_by_name("bold", start, end)
        else:
            # If no text is selected, set tag for insertion
            cursor_mark = self.textbuffer.get_insert()
            cursor_iter = self.textbuffer.get_iter_at_mark(cursor_mark)
            # We would ideally set an "input mode" here, but we'll just mark the current position
    
    def on_italic_toggled(self, button):
        """Toggle italic formatting"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                if button.get_active():
                    self.textbuffer.apply_tag_by_name("italic", start, end)
                else:
                    self.textbuffer.remove_tag_by_name("italic", start, end)
    
    def on_underline_toggled(self, button):
        """Toggle underline formatting"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                if button.get_active():
                    self.textbuffer.apply_tag_by_name("underline", start, end)
                else:
                    self.textbuffer.remove_tag_by_name("underline", start, end)
    
    def on_align_toggled(self, button, align_type):
        """Toggle text alignment"""
        # Uncheck other alignment buttons
        if button.get_active():
            for btn, align in [(self.align_left_button, "left"), 
                               (self.align_center_button, "center"), 
                               (self.align_right_button, "right")]:
                if btn != button:
                    btn.handler_block_by_func(self.on_align_toggled)
                    btn.set_active(False)
                    btn.handler_unblock_by_func(self.on_align_toggled)
            
            if self.textbuffer.get_has_selection():
                bounds = self.textbuffer.get_selection_bounds()
                if bounds:
                    start, end = bounds
                    for tag in ["left", "center", "right"]:
                        self.textbuffer.remove_tag_by_name(tag, start, end)
                    self.textbuffer.apply_tag_by_name(align_type, start, end)
            else:
                # If no selection, apply to current paragraph
                cursor_mark = self.textbuffer.get_insert()
                cursor_iter = self.textbuffer.get_iter_at_mark(cursor_mark)
                
                # Find paragraph start and end
                para_start = cursor_iter.copy()
                para_start.set_line_offset(0)
                
                para_end = cursor_iter.copy()
                if not para_end.ends_line():
                    para_end.forward_to_line_end()
                
                for tag in ["left", "center", "right"]:
                    self.textbuffer.remove_tag_by_name(tag, para_start, para_end)
                self.textbuffer.apply_tag_by_name(align_type, para_start, para_end)
    
    def on_font_size_change(self, button, change):
        """Change font size"""
        current_size = 12  # Default size
        
        # Try to get current size from selected text
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                # Get all size tags applied to the selection
                for size in range(8, 37, 2):
                    if start.has_tag(self.textbuffer.get_tag_table().lookup(f"size-{size}")):
                        current_size = size
                        break
                
                # Calculate new size
                new_size = max(8, min(36, current_size + (change * 2)))
                
                # Remove all size tags
                for size in range(8, 37, 2):
                    self.textbuffer.remove_tag_by_name(f"size-{size}", start, end)
                
                # Apply new size tag
                self.textbuffer.apply_tag_by_name(f"size-{new_size}", start, end)
    
    def on_color_set(self, button):
        """Set text color"""
        color = button.get_rgba()
        color_str = f"#{int(color.red*255):02x}{int(color.green*255):02x}{int(color.blue*255):02x}"
        
        # Create or get color tag
        tag_name = f"color-{color_str}"
        tag = self.textbuffer.get_tag_table().lookup(tag_name)
        
        if not tag:
            tag = self.textbuffer.create_tag(tag_name, foreground=color_str)
        
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                
                # Remove any existing color tags
                tags = self.textbuffer.get_tag_table()
                iter = tags.get_first()
                while iter:
                    name = iter.get_property("name")
                    if name and name.startswith("color-"):
                        self.textbuffer.remove_tag(iter, start, end)
                    iter = tags.get_next(iter)
                
                # Apply new color tag
                self.textbuffer.apply_tag(tag, start, end)
    
    def on_new_clicked(self, action, parameter):
        """Handle New button click"""
        if self.modified:
            dialog = Adw.MessageDialog.new(self.win, "Save changes?", 
                                          "Do you want to save changes to the current document?")
            dialog.add_response("discard", "Discard")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("save", "Save")
            dialog.set_default_response("save")
            dialog.set_close_response("cancel")
            
            dialog.connect("response", self.on_new_dialog_response)
            dialog.present()
        else:
            self.clear_document()
    
    def on_new_dialog_response(self, dialog, response):
        """Handle response from new document dialog"""
        if response == "save":
            self.on_save_clicked(None, None)
            self.clear_document()
        elif response == "discard":
            self.clear_document()
    
    def clear_document(self):
        """Clear the document for new file"""
        self.textbuffer.set_text("")
        self.current_file = None
        self.modified = False
        self.update_statusbar()
    
    def on_open_clicked(self, action, parameter):
        """Handle Open button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open File")
        
        # Create file filter for HTML files
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        filter_html.add_pattern("*.html")
        filter_html.add_pattern("*.htm")
        
        # Create file filter for all files
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_html)
        filters.append(filter_all)
        dialog.set_filters(filters)
        
        dialog.open(self.win, None, self.on_open_dialog_response)
    
    def on_open_dialog_response(self, dialog, result):
        """Handle response from open file dialog"""
        try:
            file = dialog.open_finish(result)
            if file:
                self.open_file(file.get_path())
        except GLib.Error as error:
            print(f"Error opening file: {error.message}")
    
    def open_file(self, filepath):
        """Open a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Clear existing content
            self.textbuffer.set_text("")
            
            if filepath.lower().endswith(('.html', '.htm')):
                self.load_html(content)
            else:
                # Just load as plain text
                self.textbuffer.set_text(content)
            
            self.current_file = filepath
            self.modified = False
            self.update_statusbar()
            
        except Exception as e:
            dialog = Adw.MessageDialog.new(self.win, "Error", f"Failed to open file: {str(e)}")
            dialog.add_response("ok", "OK")
            dialog.present()
    
    def load_html(self, html_content):
        """Parse HTML content and load it into the buffer with formatting"""
        try:
            # Simple HTML parser (for a full implementation you'd use a proper HTML parser)
            # This is a very basic implementation and won't handle all HTML properly
            
            # Strip HTML tags and convert some basic formatting
            in_tag = False
            in_style = False
            tag_name = ""
            style_text = ""
            plain_text = ""
            format_stack = []
            
            i = 0
            while i < len(html_content):
                if html_content[i] == '<':
                    in_tag = True
                    tag_name = ""
                    i += 1
                    # Check if closing tag
                    is_closing = False
                    if i < len(html_content) and html_content[i] == '/':
                        is_closing = True
                        i += 1
                    
                    # Get tag name
                    while i < len(html_content) and html_content[i] != '>' and html_content[i] != ' ':
                        tag_name += html_content[i]
                        i += 1
                    
                    # Handle style attribute
                    if i < len(html_content) and html_content[i] == ' ':
                        while i < len(html_content) and html_content[i] != '>':
                            if html_content[i:i+7] == ' style="':
                                in_style = True
                                i += 8  # Skip past style="
                                while i < len(html_content) and html_content[i] != '"':
                                    style_text += html_content[i]
                                    i += 1
                                in_style = False
                            else:
                                i += 1
                    
                    # Skip to end of tag
                    while i < len(html_content) and html_content[i] != '>':
                        i += 1
                    
                    # Process tag
                    if is_closing:
                        if format_stack and format_stack[-1][0] == tag_name.lower():
                            # Apply formatting for the tag we're closing
                            tag_type, start_pos = format_stack.pop()
                            end_iter = self.textbuffer.get_end_iter()
                            
                            if tag_type == 'b' or tag_type == 'strong':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("bold", start_iter, end_iter)
                            elif tag_type == 'i' or tag_type == 'em':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("italic", start_iter, end_iter)
                            elif tag_type == 'u':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("underline", start_iter, end_iter)
                    else:
                        if tag_name.lower() in ['b', 'strong', 'i', 'em', 'u']:
                            # Push formatting tag to stack
                            format_stack.append((tag_name.lower(), len(plain_text)))
                        elif tag_name.lower() == 'br':
                            plain_text += '\n'
                        elif tag_name.lower() == 'p':
                            if plain_text and not plain_text.endswith('\n\n'):
                                plain_text += '\n\n'
                    
                    in_tag = False
                else:
                    if not in_tag:
                        plain_text += html_content[i]
                    i += 1
            
            # Set the plain text to buffer
            self.textbuffer.set_text(plain_text)
            
        except Exception as e:
            print(f"Error parsing HTML: {str(e)}")
            # Fallback: just set the raw HTML
            self.textbuffer.set_text(html_content)
    
    def on_save_clicked(self, action, parameter):
        """Handle Save button click"""
        if self.current_file:
            self.save_file(self.current_file)
        else:
            self.on_save_as_clicked(action, parameter)
    
    def on_save_as_clicked(self, action, parameter):
        """Handle Save As button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Save File")
        
        # Create file filter for HTML files
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        filter_html.add_pattern("*.html")
        
        # Create file filter for all files
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_html)
        filters.append(filter_all)
        dialog.set_filters(filters)
        
        dialog.save(self.win, None, self.on_save_dialog_response)
    
    def on_save_dialog_response(self, dialog, result):
        """Handle response from save file dialog"""
        try:
            file = dialog.save_finish(result)
            if file:
                filepath = file.get_path()
                # Add .html extension if none is specified
                if not filepath.lower().endswith(('.html', '.htm')):
                    filepath += '.html'
                self.save_file(filepath)
        except GLib.Error as error:
            print(f"Error saving file: {error.message}")
    
    def save_file(self, filepath):
        """Save file to given path"""
        try:
            html_content = self.generate_html()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.current_file = filepath
            self.modified = False
            self.update_statusbar()
            
        except Exception as e:
            dialog = Adw.MessageDialog.new(self.win, "Error", f"Failed to save file: {str(e)}")
            dialog.add_response("ok", "OK")
            dialog.present()
    
    def generate_html(self):
        """Generate HTML from the current buffer content with formatting"""
        html = ['<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Rich Text Editor Document</title>\n</head>\n<body>\n']
        
        # Get all text
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        text = self.textbuffer.get_text(start, end, include_hidden_chars=True)
        
        # Process text with tags
        offset = 0
        html_parts = []
        last_offset = 0
        self.open_tags = []
        self.in_paragraph = False
        self.paragraph_align = None
        
        while offset < len(text):
            # Get all tags at current position
            iter = self.textbuffer.get_iter_at_offset(offset)
            tags = iter.get_tags()
            
            # Check for tag changes
            if tags or offset == 0:
                # Append any text since last tag change
                if offset > last_offset:
                    html_parts.append(text[last_offset:offset])
                
                # Close any open format tags if we're at a tag boundary
                if offset > 0 and offset > last_offset:
                    # Close tags in reverse order they were opened
                    for tag in reversed(self.open_tags):
                        html_parts.append(f"</{tag}>")
                    self.open_tags = []
                
                # Open new tags
                self.open_tags = []
                alignment = None
                
                for tag in tags:
                    tag_name = tag.get_property("name")
                    
                    if tag_name == "bold":
                        html_parts.append("<b>")
                        self.open_tags.append("b")
                    elif tag_name == "italic":
                        html_parts.append("<i>")
                        self.open_tags.append("i")
                    elif tag_name == "underline":
                        html_parts.append("<u>")
                        self.open_tags.append("u")
                    elif tag_name.startswith("size-"):
                        size = tag_name.split("-")[1]
                        html_parts.append(f'<span style="font-size: {size}pt;">')
                        self.open_tags.append("span")
                    elif tag_name.startswith("color-"):
                        color = tag_name.split("-")[1]
                        html_parts.append(f'<span style="color: {color};">')
                        self.open_tags.append("span")
                    elif tag_name in ["left", "center", "right"]:
                        alignment = tag_name
                
                # Handle paragraph alignment
                if alignment and not self.in_paragraph:
                    html_parts.append(f'<p style="text-align: {alignment};">')
                    self.in_paragraph = True
                    self.paragraph_align = alignment
                
                last_offset = offset
            
            # Check for line breaks
            if offset < len(text) and text[offset] == '\n':
                # Close tags before line break
                for tag in reversed(self.open_tags):
                    html_parts.append(f"</{tag}>")
                
                # Close paragraph if open
                if self.in_paragraph:
                    html_parts.append("</p>")
                    self.in_paragraph = False
                
                # Add line break
                html_parts.append("<br>\n")
                
                # Reopen tags after line break
                for tag in self.open_tags:
                    if tag == "b":
                        html_parts.append("<b>")
                    elif tag == "i":
                        html_parts.append("<i>")
                    elif tag == "u":
                        html_parts.append("<u>")
                    # Note: size and color tags are included in self.open_tags
                
                # Reopen paragraph with alignment if needed
                if self.paragraph_align:
                    html_parts.append(f'<p style="text-align: {self.paragraph_align};">')
                    self.in_paragraph = True
                
                last_offset = offset + 1
            
            offset += 1
        
        # Append any remaining text
        if last_offset < len(text):
            html_parts.append(text[last_offset:])
        
        # Close any open tags
        for tag in reversed(self.open_tags):
            html_parts.append(f"</{tag}>")
        
        # Close paragraph if open
        if self.in_paragraph:
            html_parts.append("</p>")
        
        # Join all parts
        html.append(''.join(html_parts))
        html.append('\n</body>\n</html>')
        
        return ''.join(html)
    
    def on_about_clicked(self, action, parameter):
        """Show about dialog"""
        about = Adw.AboutWindow.new()
        about.set_application_name("Rich Text Editor")
        about.set_version("1.0")
        about.set_developer_name("PyGObject Developer")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_comments("A rich text editor with HTML support.")
        about.set_website("https://github.com/example/rich-text-editor")
        about.set_transient_for(self.win)
        about.present()
    
    def on_quit(self, action, parameter):
        """Quit the application"""
        if self.modified:
            dialog = Adw.MessageDialog.new(self.win, "Save changes?", 
                                          "Do you want to save changes to the current document?")
            dialog.add_response("discard", "Discard")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("save", "Save")
            dialog.set_default_response("save")
            dialog.set_close_response("cancel")
            
            dialog.connect("response", self.on_quit_dialog_response)
            dialog.present()
        else:
            self.quit()
    
    def on_quit_dialog_response(self, dialog, response):
        """Handle response from quit dialog"""
        if response == "save":
            self.on_save_clicked(None, None)
            self.quit()
        elif response == "discard":
            self.quit()

def main(args):
    app = RichTextEditor()
    return app.run(args)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
