#!/usr/bin/env python3

import os
import re
import importlib.util
from datetime import datetime
from gi.repository import Gtk, GLib, Gio, WebKit, Pango

# Check if markdown package is available
MARKDOWN_AVAILABLE = False
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    pass

# Check if html2text package is available (for HTML to Markdown conversion)
HTML2TEXT_AVAILABLE = False
try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    pass

# Open operations
def on_open_clicked(self, win, button):
    """Show open file dialog and decide whether to open in current or new window"""
    dialog = Gtk.FileDialog()
    dialog.set_title("Open Document")
    
    # Create file filters for all supported formats
    filter_html = Gtk.FileFilter()
    filter_html.set_name("HTML files")
    filter_html.add_pattern("*.html")
    filter_html.add_pattern("*.htm")
    filter_html.add_pattern("*.mht")
    filter_html.add_pattern("*.mhtml")
    
    filter_md = Gtk.FileFilter()
    filter_md.set_name("Markdown files")
    filter_md.add_pattern("*.md")
    filter_md.add_pattern("*.markdown")
    
    filter_txt = Gtk.FileFilter()
    filter_txt.set_name("Text files")
    filter_txt.add_pattern("*.txt")
    
    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")
    
    filter_list = Gio.ListStore.new(Gtk.FileFilter)
    filter_list.append(filter_html)
    filter_list.append(filter_md)
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
    """Load file content into editor with support for various formats"""
    try:
        # Store the original file path format for reference
        win.original_format = os.path.splitext(filepath)[1].lower()
        
        # Try to detect file encoding
        encoding = 'utf-8'  # Default encoding
        try:
            import chardet
            with open(filepath, 'rb') as raw_file:
                raw_content = raw_file.read()
                detected = chardet.detect(raw_content)
                if detected['confidence'] > 0.7:
                    encoding = detected['encoding']
        except ImportError:
            pass  # Fallback to utf-8 if chardet not available
            
        # Now read the file with the detected encoding
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # If there's a decode error, try a fallback encoding
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Determine file type and process accordingly
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext in ['.mht', '.mhtml']:
            # Handle MHTML files - extract the HTML content
            try:
                import email
                message = email.message_from_string(content)
                for part in message.walk():
                    if part.get_content_type() == 'text/html':
                        content = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                        break
            except ImportError:
                # Fallback to regex extraction if email module not ideal
                body_match = re.search(r'Content-Type: text/html.*?charset=["\']?([\w-]+)["\']?.*?(?:\r?\n){2}(.*?)(?:\r?\n){1,2}--', 
                                       content, re.DOTALL | re.IGNORECASE)
                if body_match:
                    charset, html_content = body_match.groups()
                    content = html_content
                    
            # Extract body content from the HTML
            body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1).strip()
                    
        elif file_ext in ['.html', '.htm']:
            # Handle HTML content
            body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1).strip()
                
        elif file_ext in ['.md', '.markdown']:
            # Convert markdown to HTML
            if MARKDOWN_AVAILABLE:
                try:
                    # Get available extensions
                    available_extensions = []
                    for ext in ['tables', 'fenced_code', 'codehilite', 'nl2br', 'sane_lists', 'smarty', 'attr_list']:
                        try:
                            # Test if extension can be loaded
                            markdown.markdown("test", extensions=[ext])
                            available_extensions.append(ext)
                        except (ImportError, ValueError):
                            pass
                    
                    # Convert markdown to HTML
                    content = markdown.markdown(content, extensions=available_extensions)
                except Exception as e:
                    print(f"Error converting markdown: {e}")
                    # Fallback to simple conversion
                    content = _simple_markdown_to_html(content)
            else:
                # Use simplified markdown conversion
                content = _simple_markdown_to_html(content)
        else:  # .txt or other plain text
            # Convert plain text to HTML
            content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            content = f"<div>{content.replace(chr(10), '<br>')}</div>"
        
        # Ensure content is properly wrapped in a div if not already
        if not (content.strip().startswith('<div') or content.strip().startswith('<p') or 
                content.strip().startswith('<h')):
            content = f"<div>{content}</div>"
        
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

def _simple_markdown_to_html(content):
    """Static method for simple markdown to HTML conversion as fallback"""
    html = content
    
    # Basic markdown conversions
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
    
    # Convert paragraphs
    paragraphs = re.split(r'\n\s*\n', html)
    processed_paragraphs = []
    for p in paragraphs:
        if p.strip() and not p.strip().startswith('<'):
            processed_paragraphs.append(f'<p>{p}</p>')
        else:
            processed_paragraphs.append(p)
    
    html = '\n'.join(processed_paragraphs)
    return html

# Save operations
def on_save_clicked(self, win, button):
    """Handle save button click"""
    if win.current_file:
        # Get the file path
        file_path = win.current_file.get_path()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Save based on file extension
        if file_ext in ['.mht', '.mhtml']:
            self.save_as_mhtml(win, win.current_file)
        elif file_ext in ['.html', '.htm']:
            self.save_as_html(win, win.current_file)
        elif file_ext in ['.md', '.markdown']:
            self.save_as_markdown(win, win.current_file)
        elif file_ext in ['.txt']:
            self.save_as_text(win, win.current_file)
        else:
            # For unknown extensions, save as MHTML by default
            self.save_as_mhtml(win, win.current_file)
    else:
        # Show custom save dialog for new file
        self.show_custom_save_dialog(win)

def on_save_as_clicked(self, win, button):
    """Show custom save as dialog to save current document with a new filename"""
    self.show_custom_save_dialog(win)

def show_custom_save_dialog(self, win):
    """Show custom save dialog with filename entry and extension dropdown using GTK4 patterns"""
    # Generate initial filename if needed
    initial_name = ""
    if win.current_file:
        initial_name = os.path.basename(win.current_file.get_path())
    else:
        current_date = datetime.now().strftime("%Y-%m-%d")
        initial_name = f"Untitled-{current_date}"
    
    # Get current format if available
    current_format = win.original_format if hasattr(win, 'original_format') else None
    
    # Create the dialog
    dialog = self._create_custom_save_dialog(win, initial_name, current_format)
    dialog_data = dialog.dialog_data
    
    # Connect the response signal - GTK4 style
    dialog.connect("response", self._on_dialog_response, dialog_data, win)
    
    # Present the dialog (GTK4 way to show dialog)
    dialog.present()

def _create_custom_save_dialog(self, win, initial_name="", current_format=None):
    """Create a custom save dialog with filename entry and extension dropdown"""
    
    dialog = Gtk.Dialog(
        title="Save As",
        transient_for=win,
        modal=True,
        destroy_with_parent=True
    )
        
    dialog.set_default_size(500, 250)
    
    # Set up the available file formats
    formats = [
        {"extension": ".mht", "name": "MHTML Document", "mime": "message/rfc822"},
        {"extension": ".html", "name": "HTML Document", "mime": "text/html"},
        {"extension": ".txt", "name": "Plain Text", "mime": "text/plain"}
    ]
    
    # Add markdown if html2text is available
    if HTML2TEXT_AVAILABLE:
        formats.append(
            {"extension": ".md", "name": "Markdown Document", "mime": "text/markdown"}
        )
    
    # Parse initial name
    basename = initial_name
    if "." in basename:
        name_parts = basename.rsplit(".", 1)
        basename = name_parts[0]
        ext = "." + name_parts[1].lower()
    else:
        ext = current_format if current_format else ".mht"
    
    # Create UI
    content_area = dialog.get_content_area()
    content_area.set_margin_top(10)
    content_area.set_margin_bottom(10)
    content_area.set_margin_start(10)
    content_area.set_margin_end(10)
    content_area.set_spacing(10)
    
    # Create a grid layout
    grid = Gtk.Grid()
    grid.set_row_spacing(10)
    grid.set_column_spacing(10)
    
    # Filename label and entry
    filename_label = Gtk.Label(label="Filename:")
    filename_label.set_halign(Gtk.Align.START)
    grid.attach(filename_label, 0, 0, 1, 1)
    
    filename_entry = Gtk.Entry()
    filename_entry.set_text(basename)
    filename_entry.set_hexpand(True)
    grid.attach(filename_entry, 1, 0, 1, 1)
    
    # File type label and dropdown
    filetype_label = Gtk.Label(label="Save as type:")
    filetype_label.set_halign(Gtk.Align.START)
    grid.attach(filetype_label, 0, 1, 1, 1)
    
    # Create a dropdown for file types
    format_dropdown = Gtk.DropDown()
    
    # Create a string list model for the dropdown
    string_list = Gtk.StringList()
    selected_index = 0
    
    for i, fmt in enumerate(formats):
        string_list.append(f"{fmt['name']} ({fmt['extension']})")
        if fmt['extension'] == ext:
            selected_index = i
    
    format_dropdown.set_model(string_list)
    format_dropdown.set_selected(selected_index)
    format_dropdown.set_hexpand(True)
    grid.attach(format_dropdown, 1, 1, 1, 1)
    
    # Location label and button
    location_label = Gtk.Label(label="Location:")
    location_label.set_halign(Gtk.Align.START)
    grid.attach(location_label, 0, 2, 1, 1)
    
    # Get user documents directory as default
    current_folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    if not current_folder:
        current_folder = GLib.get_home_dir()
    
    # If there's a current file, use its directory
    if win.current_file:
        parent_dir = win.current_file.get_parent()
        if parent_dir and parent_dir.get_path():
            current_folder = parent_dir.get_path()
    
    # Store all dialog data in a dictionary for easy access
    dialog_data = {
        "formats": formats,
        "filename_entry": filename_entry,
        "format_dropdown": format_dropdown,
        "current_folder": current_folder,
        "dialog": dialog  # Store reference to the dialog itself
    }
    
    # Store the dialog data in the dialog object for later retrieval
    dialog.dialog_data = dialog_data
    
    location_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    location_box.set_hexpand(True)
    
    location_display = Gtk.Label(label=self._get_shortened_path(current_folder))
    location_display.set_ellipsize(Pango.EllipsizeMode.START)
    location_display.set_hexpand(True)
    location_display.set_halign(Gtk.Align.START)
    location_box.append(location_display)
    
    # Store the location label in dialog data
    dialog_data["location_label"] = location_display
    
    browse_button = Gtk.Button(label="Browse...")
    browse_button.connect("clicked", self._on_browse_clicked, dialog_data)
    location_box.append(browse_button)
    
    grid.attach(location_box, 1, 2, 1, 1)
    
    # Add the grid to the content area
    content_area.append(grid)
    
    # Add action buttons - using the GTK4 approach for dialog buttons
    cancel_button = dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
    save_button = dialog.add_button("_Save", Gtk.ResponseType.ACCEPT)
    save_button.add_css_class("suggested-action")
    
    # Make the dialog resizable
    dialog.set_resizable(True)
    
    # Return the dialog
    return dialog

def _get_shortened_path(self, path, max_length=40):
    """Shortens a path for display"""
    if len(path) <= max_length:
        return path
    
    # Try to preserve the last part of the path
    parts = path.split('/')
    if len(parts) > 2:
        return f".../{parts[-1]}"
    return path

def _on_browse_clicked(self, button, dialog_data):
    """Handle browse button click to select folder"""
    file_dialog = Gtk.FileDialog.new()
    file_dialog.set_title("Select Folder")
    
    initial_folder = Gio.File.new_for_path(dialog_data["current_folder"])
    file_dialog.set_initial_folder(initial_folder)
    
    # Open the dialog to select a folder
    file_dialog.select_folder(dialog_data["dialog"], None, 
                         lambda fd, result: self._on_folder_selected(fd, result, dialog_data))

def _on_dialog_response(self, dialog, response_id, dialog_data, win):
    """Handle dialog response callback"""
    if response_id == Gtk.ResponseType.ACCEPT:
        filepath = self._get_file_path_from_dialog(dialog_data)
        if filepath:
            file = Gio.File.new_for_path(filepath)
            
            # Determine file type and call appropriate save method
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext in ['.mht', '.mhtml']:
                self.save_as_mhtml(win, file)
            elif file_ext in ['.html', '.htm']:
                self.save_as_html(win, file)
            elif file_ext in ['.md', '.markdown']:
                self.save_as_markdown(win, file)
            elif file_ext in ['.txt']:
                self.save_as_text(win, file)
            else:
                # For unknown extensions, save as MHTML by default
                self.save_as_mhtml(win, file)
    
    # Destroy the dialog when done
    dialog.destroy()
    
def _on_folder_selected(self, file_dialog, result, dialog_data):
    """Handle folder selection result"""
    try:
        folder = file_dialog.select_folder_finish(result)
        if folder:
            dialog_data["current_folder"] = folder.get_path()
            dialog_data["location_label"].set_text(self._get_shortened_path(dialog_data["current_folder"]))
    except GLib.Error as e:
        # Ignore cancellation
        if e.domain != 'gtk-dialog-error-quark' or e.code != 2:
            print(f"Error selecting folder: {e}")

def _get_file_path_from_dialog(self, dialog_data):
    """Get the complete file path from dialog inputs"""
    filename = dialog_data["filename_entry"].get_text().strip()
    if not filename:
        return None
    
    # Get the selected extension
    format_idx = dialog_data["format_dropdown"].get_selected()
    extension = dialog_data["formats"][format_idx]["extension"]
    
    # Remove existing extension if present and add the selected one
    if "." in filename:
        base = filename.rsplit(".", 1)[0]
        filename = base
    
    # Build full path
    return os.path.join(dialog_data["current_folder"], filename + extension)


def save_as_mhtml(self, win, file):
    """Save document as MHTML using WebKit's save method"""
    try:
        # Get the file URI
        file_uri = file.get_uri()
        
        # Check which WebKit version and methods are available
        if hasattr(win.webview, 'save_to_file'):
            # WebKit 6.0+ method
            win.webview.save_to_file(file, WebKit.SaveMode.MHTML, None, 
                                  lambda webview, result: self.save_webkit_callback(win, file, result))
        elif hasattr(win.webview, 'save'):
            # Older WebKit method
            win.webview.save(WebKit.SaveMode.MHTML, None,  # No cancellable
                          lambda webview, result: self.save_webkit_callback(win, file, result))
        else:
            # Fallback for even older WebKit versions
            print("WebKit save methods not available, falling back to HTML")
            self.save_as_html(win, file)
            return
            
        win.statusbar.set_text(f"Saving MHTML file: {file.get_path()}")
    except Exception as e:
        print(f"Error saving as MHTML: {e}")
        win.statusbar.set_text(f"Error saving MHTML: {e}")
        # Fallback to manual saving
        self.save_as_html(win, file)

def save_webkit_callback(self, win, file, result):
    """Handle WebKit save result"""
    try:
        # Check if this is a WebKit 6.0+ result with get_web_error
        if hasattr(result, 'get_web_error'):
            error = result.get_web_error()
            if error is None:
                # Successful WebKit save
                win.current_file = file
                win.modified = False
                self.update_window_title(win)
                win.statusbar.set_text(f"Saved: {file.get_path()}")
            else:
                # WebKit save failed
                print(f"WebKit save error: {error.get_message()}")
                win.statusbar.set_text(f"Error: {error.get_message()}")
                # Fallback to manual saving
                self.save_as_html(win, file)
        else:
            # For older WebKit versions without detailed error info
            # Just assume success and update the UI
            win.current_file = file
            win.modified = False
            self.update_window_title(win)
            win.statusbar.set_text(f"Saved: {file.get_path()}")
    except Exception as e:
        print(f"Error in WebKit save callback: {e}")
        # Fallback to manual saving
        self.save_as_html(win, file)

def save_as_html(self, win, file):
    """Save document as HTML by extracting just the editor content"""
    # We only want to get the editor content, not the entire HTML document
    win.webview.evaluate_javascript(
        "document.getElementById('editor').innerHTML",
        -1, None, None, None,
        lambda webview, result, data: self.save_html_callback(win, webview, result, file),
        None
    )
    win.statusbar.set_text(f"Saving HTML file: {file.get_path()}")

def save_html_callback(self, win, webview, result, file):
    """Process HTML content from webview and save to file"""
    try:
        js_result = webview.evaluate_javascript_finish(result)
        if js_result:
            # Get the content based on the available API
            if hasattr(js_result, 'get_js_value'):
                editor_content = js_result.get_js_value().to_string()
            else:
                editor_content = js_result.to_string()
            
            # Wrap the content in a proper HTML document
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>HTML Document</title>
    <meta charset="utf-8">
</head>
<body>
{editor_content}
</body>
</html>"""

            # Convert the string to bytes
            content_bytes = html_content.encode('utf-8')
            
            # Use the synchronous replace_contents method
            try:
                success, etag = file.replace_contents(
                    content_bytes,
                    None,  # etag
                    False,  # make_backup
                    Gio.FileCreateFlags.REPLACE_DESTINATION,
                    None   # cancellable
                )
                
                if success:
                    win.current_file = file
                    win.modified = False
                    self.update_window_title(win)
                    win.statusbar.set_text(f"Saved: {file.get_path()}")
                else:
                    win.statusbar.set_text("File save was not successful")
                    
            except GLib.Error as e:
                print(f"Error writing file: {e.message if hasattr(e, 'message') else str(e)}")
                win.statusbar.set_text(f"Error writing file: {str(e)}")
                
    except Exception as e:
        print(f"Error processing HTML for save: {e}")
        win.statusbar.set_text(f"Error saving HTML: {e}")
        
def save_as_html_fallback(self, win, file):
    """Fallback method to save HTML when JavaScript evaluation fails"""
    try:
        # Create basic HTML content with the current content
        win.webview.evaluate_javascript(
            "document.body.innerHTML",
            -1, None, None, None,
            lambda webview, result, data: self.save_html_body_callback(win, webview, result, file),
            None
        )
    except Exception as e:
        print(f"Error in HTML fallback save: {e}")
        win.statusbar.set_text(f"Error saving HTML: {e}")
        self.show_error_dialog(win, f"Could not save file: {e}")

def save_html_body_callback(self, win, webview, result, file):
    """Process HTML body content and save to file"""
    try:
        js_result = webview.evaluate_javascript_finish(result)
        if js_result:
            # Get the body HTML content
            if hasattr(js_result, 'get_js_value'):
                body_content = js_result.get_js_value().to_string()
            else:
                body_content = js_result.to_string()
            
            # Create a complete HTML document
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>HTML Document</title>
    <meta charset="utf-8">
</head>
<body>
{body_content}
</body>
</html>"""

            # Convert the string to bytes
            content_bytes = html_content.encode('utf-8')
            
            # Use the simpler replace_contents method
            try:
                success, etag = file.replace_contents(
                    content_bytes,
                    None,  # etag
                    False,  # make_backup
                    Gio.FileCreateFlags.REPLACE_DESTINATION,
                    None   # cancellable
                )
                
                if success:
                    win.current_file = file
                    win.modified = False
                    self.update_window_title(win)
                    win.statusbar.set_text(f"Saved: {file.get_path()}")
                else:
                    win.statusbar.set_text("File save was not successful")
                    
            except GLib.Error as e:
                print(f"Error writing file: {e.message}")
                win.statusbar.set_text(f"Error writing file: {e.message}")
                
        else:
            print("Failed to get HTML content from webview")
            win.statusbar.set_text("Failed to get HTML content for saving")
    except Exception as e:
        print(f"Error processing HTML body for save: {e}")
        win.statusbar.set_text(f"Error saving HTML: {e}")

def save_as_text(self, win, file):
    """Save document as plain text by extracting text content from the webview"""
    win.webview.evaluate_javascript(
        "document.body.innerText || document.body.textContent",
        -1, None, None, None,
        lambda webview, result, data: self.save_text_callback(win, webview, result, file),
        None
    )
    win.statusbar.set_text(f"Saving text file: {file.get_path()}")

def save_text_callback(self, win, webview, result, file):
    """Process text content from webview and save to file"""
    try:
        js_result = webview.evaluate_javascript_finish(result)
        if js_result:
            text_content = js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else js_result.to_string()
            
            # Replace the file with the new content
            file.replace_contents_async(
                text_content.encode('utf-8'),
                None,
                False,
                Gio.FileCreateFlags.REPLACE_DESTINATION,
                None,
                lambda file, result: self.save_completion_callback(win, file, result)
            )
    except Exception as e:
        print(f"Error processing text for save: {e}")
        win.statusbar.set_text(f"Error saving text: {e}")

def save_as_markdown(self, win, file):
    """Save document as Markdown using html2text if available"""
    if not HTML2TEXT_AVAILABLE:
        win.statusbar.set_text("html2text library not available for Markdown conversion")
        # Fallback to HTML
        self.save_as_html(win, file)
        return
        
    win.webview.evaluate_javascript(
        "document.documentElement.outerHTML",
        -1, None, None, None,
        lambda webview, result, data: self.save_markdown_callback(win, webview, result, file),
        None
    )
    win.statusbar.set_text(f"Saving Markdown file: {file.get_path()}")

def save_markdown_callback(self, win, webview, result, file):
    """Convert HTML to Markdown and save to file"""
    try:
        js_result = webview.evaluate_javascript_finish(result)
        if js_result and HTML2TEXT_AVAILABLE:
            html_content = js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else js_result.to_string()
            
            # Convert HTML to Markdown
            h2t = html2text.HTML2Text()
            h2t.unicode_snob = True        # Use Unicode
            h2t.body_width = 0             # Don't wrap lines
            h2t.ignore_links = False       # Preserve links
            h2t.ignore_images = False      # Preserve images
            h2t.ignore_tables = False      # Try to handle tables
            
            markdown_content = h2t.handle(html_content)
            
            # Replace the file with the new content
            file.replace_contents_async(
                markdown_content.encode('utf-8'),
                None,
                False,
                Gio.FileCreateFlags.REPLACE_DESTINATION,
                None,
                lambda file, result: self.save_completion_callback(win, file, result)
            )
    except Exception as e:
        print(f"Error converting to Markdown for save: {e}")
        win.statusbar.set_text(f"Error saving Markdown: {e}")
        # Fallback to HTML
        self.save_as_html(win, file)

def save_completion_callback(self, win, file, result):
    """Handle save completion"""
    try:
        # For WebKit save operations, the result might be None or not a valid GIO task
        if result is None:
            # WebKit's direct save doesn't provide a result to finish
            success = True
        else:
            try:
                # Check if this is a WebKit result (which is different from a GIO result)
                if hasattr(result, 'get_web_error'):
                    # WebKit result handling
                    error = result.get_web_error()
                    success = (error is None)
                    if not success:
                        print(f"WebKit save error: {error.get_message()}")
                elif hasattr(file, 'replace_contents_finish'):
                    # Standard GIO result
                    success, _ = file.replace_contents_finish(result)
                else:
                    # Fallback - assume success unless we have evidence otherwise
                    success = True
            except GLib.Error as e:
                print(f"Error finishing file operation: {e}")
                success = False
            except Exception as e:
                print(f"Unexpected error in save completion: {e}")
                success = False
                
        if success:
            win.current_file = file
            win.modified = False
            self.update_window_title(win)
            win.statusbar.set_text(f"Saved: {file.get_path()}")
        else:
            win.statusbar.set_text("File save was not successful")
    except Exception as e:
        print(f"Error completing save: {e}")
        win.statusbar.set_text(f"Error completing save: {e}")

# Legacy aliases for backward compatibility
def _on_save_response(self, win, dialog, result):
    """Backward compatibility method"""
    return self.save_dialog_callback(win, dialog, result)
    
def _on_save_as_response(self, win, dialog, result):
    """Backward compatibility method"""
    return self.save_dialog_callback(win, dialog, result)
    
def _on_get_html_content(self, win, webview, result, file):
    """Backward compatibility method - redirects to HTML save"""
    return self.save_html_callback(win, webview, result, file)
    
def _on_file_saved(self, win, file, result):
    """Backward compatibility method"""
    return self.save_completion_callback(win, file, result)



####################




   




