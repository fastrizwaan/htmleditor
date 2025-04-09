#!/usr/bin/env python3

import os
import re
from gi.repository import Gtk, GLib, Gio, WebKit

# Open operations
def on_open_clicked(self, win, button):
    """Show open file dialog and decide whether to open in current or new window"""
    dialog = Gtk.FileDialog()
    dialog.set_title("Open Document")
    
    filter_html = Gtk.FileFilter()
    filter_html.set_name("HTML files")
    filter_html.add_pattern("*.html")
    filter_html.add_pattern("*.htm")
    
    filter_txt = Gtk.FileFilter()
    filter_txt.set_name("Text files")
    filter_txt.add_pattern("*.txt")
    
    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")
    
    filter_list = Gio.ListStore.new(Gtk.FileFilter)
    filter_list.append(filter_html)
    filter_list.append(filter_txt)
    filter_list.append(filter_all)
    
    dialog.set_filters(filter_list)
    
    # If no changes made and no file is open, open in current window, otherwise open in new window
    if win.modified or win.current_file:
        dialog.open(win, None, lambda dialog, result: self.on_open_new_window_response(win, dialog, result))
    else:
        dialog.open(win, None, lambda dialog, result: self.on_open_current_window_response(win, dialog, result))

def on_open_new_window_response(self, win, dialog, result):
    """Handle open file dialog response to open in a new window"""
    try:
        file = dialog.open_finish(result)
        if file:
            filepath = file.get_path()
            # Create a new window for the file
            new_win = self.create_window()
            self.load_file(new_win, filepath)
            new_win.present()
            self.update_window_menu()
    except GLib.Error as e:
        if e.domain != 'gtk-dialog-error-quark' or e.code != 2:  # Ignore cancel
            self.show_error_dialog(f"Error opening file: {e}")

def on_open_current_window_response(self, win, dialog, result):
    """Handle open file dialog response to open in current window"""
    try:
        file = dialog.open_finish(result)
        if file:
            filepath = file.get_path()
            self.load_file(win, filepath)
            win.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
    except GLib.Error as e:
        if e.domain != 'gtk-dialog-error-quark' or e.code != 2:  # Ignore cancel
            self.show_error_dialog(f"Error opening file: {e}")

def load_file(self, win, filepath):
    """Load file content into editor"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        is_html = content.strip().startswith("<") and (
            "<html" in content.lower() or 
            "<body" in content.lower() or 
            "<div" in content.lower()
        )
        if is_html:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1).strip()
        else:
            content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            content = content.replace("\n", "<br>")
        
        # Escape for JavaScript
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        js_code = f'setContent("{content}");'
        
        # Check WebView load status and execute JS accordingly
        def execute_when_ready():
            # Get the current load status
            load_status = win.webview.get_estimated_load_progress()
            
            if load_status == 1.0:  # Fully loaded
                # Execute directly
                self.execute_js(win, js_code)
                return False  # Stop the timeout
            else:
                # Set up a handler for when loading finishes
                def on_load_changed(webview, event):
                    if event == WebKit.LoadEvent.FINISHED:
                        self.execute_js(win, js_code)
                        webview.disconnect_by_func(on_load_changed)
                
                win.webview.connect("load-changed", on_load_changed)
                return False  # Stop the timeout
        
        # Use GLib timeout to ensure we're not in the middle of another operation
        GLib.timeout_add(50, execute_when_ready)
        
        # Update file information
        win.current_file = Gio.File.new_for_path(filepath)
        win.modified = False
        self.update_window_title(win)
        win.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        win.statusbar.set_text(f"Error loading file: {str(e)}")
        # Call show_error_dialog if it exists
        self.show_error_dialog(f"Error loading file: {e}")

# Save operations
def on_save_clicked(self, win, button):
    """Handle save button click"""
    if win.current_file:
        # Save to existing file
        win.webview.evaluate_javascript(
            "document.getElementById('editor').innerHTML;",
            -1, None, None, None,
            lambda webview, result, file: self._on_get_html_content(win, webview, result, win.current_file), 
            None
        )
    else:
        # Show save dialog for new file
        dialog = Gtk.FileDialog()
        dialog.set_title("Save HTML File")
        
        filter = Gtk.FileFilter()
        filter.set_name("HTML files")
        filter.add_pattern("*.html")
        filter.add_pattern("*.htm")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter)
        
        dialog.set_filters(filters)
        dialog.save(win, None, lambda dialog, result: self._on_save_response(win, dialog, result))

def _on_save_response(self, win, dialog, result):
    """Handle save dialog response"""
    try:
        file = dialog.save_finish(result)
        if file:
            win.current_file = file  # Already a Gio.File
            win.webview.evaluate_javascript(
                "document.getElementById('editor').innerHTML;",
                -1, None, None, None,
                lambda webview, result, file: self._on_get_html_content(win, webview, result, file), 
                file
            )
    except GLib.Error as error:
        print(f"Error saving file: {error.message}")
        
def save_html_content(self, win, editor_content, file, callback):
    """Save HTML content to file"""
    try:
        if editor_content.strip() == "" or editor_content == "<br>":
            editor_content = "<div><br></div>"
        elif not (editor_content.startswith('<div') and editor_content.endswith('</div>')):
            editor_content = f"<div>{editor_content.strip()}</div>"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HTML Document</title>
    <meta charset="utf-8">
</head>
<body>
{editor_content}
</body>
</html>
"""
        file_bytes = html_content.encode('utf-8')
        file.replace_contents_async(file_bytes, None, False, Gio.FileCreateFlags.NONE, None, callback)
    except Exception as e:
        print(f"Error saving content: {e}")

def _on_get_html_content(self, win, webview, result, file):
    """Get HTML content from webview and save it"""
    try:
        js_result = webview.evaluate_javascript_finish(result)
        if js_result:
            editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                            js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
            self.save_html_content(win, editor_content, file, 
                                  lambda file, result: self._on_file_saved(win, file, result))
        else:
            print("Failed to get HTML content from webview")
    except Exception as e:
        print(f"Error getting HTML content: {e}")

def _on_file_saved(self, win, file, result):
    """Handle file saved callback"""
    try:
        success, _ = file.replace_contents_finish(result)
        if success:
            win.current_file = file  # Ensure consistency by updating win.current_file
            win.statusbar.set_text(f"Saved: {file.get_path()}")
            win.modified = False  # Reset modified flag after save
            self.update_window_title(win)
        else:
            win.statusbar.set_text("File save was not successful")
    except GLib.Error as error:
        print(f"Error writing file: {error.message}")
        win.statusbar.set_text(f"Error writing file: {error.message}")

# Save As operations
def on_save_as_clicked(self, win, button):
    """Show save as dialog to save current document with a new filename"""
    dialog = Gtk.FileDialog()
    dialog.set_title("Save As")
    
    filter = Gtk.FileFilter()
    filter.set_name("HTML files")
    filter.add_pattern("*.html")
    filter.add_pattern("*.htm")
    
    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(filter)
    
    dialog.set_filters(filters)
    
    # If there's a current file, use its parent directory as the initial folder
    if win.current_file:
        parent_dir = win.current_file.get_parent()
        if parent_dir:
            dialog.set_initial_folder(parent_dir)
    
    dialog.save(win, None, lambda dialog, result: self._on_save_as_response(win, dialog, result))

def _on_save_as_response(self, win, dialog, result):
    """Handle save as dialog response"""
    try:
        file = dialog.save_finish(result)
        if file:
            # Store the new file path
            win.current_file = file
            
            # Get content and save it
            win.webview.evaluate_javascript(
                "document.getElementById('editor').innerHTML;",
                -1, None, None, None,
                lambda webview, result, file: self._on_get_html_content(win, webview, result, file),
                file
            )
    except GLib.Error as error:
        if error.domain != 'gtk-dialog-error-quark' or error.code != 2:  # Ignore cancel
            print(f"Error saving file: {error.message}")
            self.show_error_dialog(f"Error saving file: {error.message}")
