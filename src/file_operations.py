#!/usr/bin/env python3
# file_operations.py - Enhanced with LibreOffice conversion support
import os
import re
import subprocess
import tempfile
import time
import shutil
from datetime import datetime
from gi.repository import Gtk, GLib, Gio, WebKit, Pango, Adw, GObject

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

# LibreOffice document formats
LIBREOFFICE_INPUT_FORMATS = {
    "Writer Documents": [
        {"extension": ".odt", "name": "OpenDocument Text", "mime": "application/vnd.oasis.opendocument.text"},
        {"extension": ".doc", "name": "Microsoft Word 97-2003", "mime": "application/msword"},
        {"extension": ".docx", "name": "Microsoft Word", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        {"extension": ".rtf", "name": "Rich Text Format", "mime": "application/rtf"},
    ],
    "Office Documents": [
        # PDF removed from here for import
        {"extension": ".wpd", "name": "WordPerfect", "mime": "application/vnd.wordperfect"},
    ],
    "Web Documents": [
        {"extension": ".html", "name": "HTML Document", "mime": "text/html"},
        {"extension": ".htm", "name": "HTML Document", "mime": "text/html"},
        {"extension": ".mht", "name": "MHTML Document", "mime": "message/rfc822"},
        {"extension": ".mhtml", "name": "MHTML Document", "mime": "message/rfc822"},
    ],
    "Plain Text": [
        {"extension": ".txt", "name": "Plain Text", "mime": "text/plain"},
        {"extension": ".md", "name": "Markdown", "mime": "text/markdown"},
        {"extension": ".markdown", "name": "Markdown", "mime": "text/markdown"},
    ]
}


# Output formats supported by the editor
OUTPUT_FORMATS = [
    {"extension": ".odt", "name": "OpenDocument Text", "mime": "application/vnd.oasis.opendocument.text"},
    {"extension": ".html", "name": "HTML Document", "mime": "text/html"},
    {"extension": ".mht", "name": "MHTML Document", "mime": "message/rfc822"},
    {"extension": ".md", "name": "Markdown Document", "mime": "text/markdown"},
    {"extension": ".txt", "name": "Plain Text", "mime": "text/plain"},
    {"extension": ".pdf", "name": "PDF Document", "mime": "application/pdf"},
    {"extension": ".docx", "name": "Microsoft Word", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
]

# Check if LibreOffice is available
def is_libreoffice_available():
    """Check if LibreOffice is installed and available"""
    try:
        result = subprocess.run(['which', 'libreoffice'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        return result.returncode == 0
    except Exception:
        return False

# Cache the result to avoid repeated checks
LIBREOFFICE_AVAILABLE = is_libreoffice_available()

def show_loading_dialog(self, win, message="Loading document..."):
    """Show a loading dialog with a progress spinner"""
    dialog = Adw.Dialog.new()
    dialog.set_content_width(300)
    
    # Create main box
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content_box.set_margin_top(24)
    content_box.set_margin_bottom(24)
    content_box.set_margin_start(24)
    content_box.set_margin_end(24)
    
    # Add loading label
    loading_label = Gtk.Label(label=message)
    loading_label.set_wrap(True)
    loading_label.set_max_width_chars(40)
    content_box.append(loading_label)
    
    # Add spinner
    spinner = Gtk.Spinner()
    spinner.set_size_request(32, 32)
    spinner.start()
    spinner.set_margin_top(12)
    content_box.append(spinner)
    
    dialog.set_child(content_box)
    dialog.present(win)
    
    return dialog


def get_all_supported_extensions():
    """Get a list of all supported file extensions"""
    extensions = []
    for category in LIBREOFFICE_INPUT_FORMATS:
        for format_info in LIBREOFFICE_INPUT_FORMATS[category]:
            extensions.append(format_info["extension"])
    return extensions

def is_libreoffice_format(file_path):
    """Check if a file is in a format that requires LibreOffice conversion"""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Web and plain text formats don't need LibreOffice
    direct_formats = ['.html', '.htm', '.mht', '.mhtml', '.txt', '.md', '.markdown']
    if ext in direct_formats:
        return False
        
    # Check if it's a LibreOffice-convertible format
    return ext in get_all_supported_extensions()

def convert_with_libreoffice(self, input_file, output_format="html"):
    """
    Convert a document using LibreOffice in headless mode with improved image handling
    
    Args:
        input_file: Path to the input file
        output_format: Format to convert to (default: html)
        
    Returns:
        Tuple of (path to the converted file, directory containing image files) or (None, None) if conversion failed
    """
    if not LIBREOFFICE_AVAILABLE:
        print("LibreOffice not available for document conversion")
        return None, None
        
    try:
        # Early return for PDF files when importing (not for exporting to PDF)
        file_ext = os.path.splitext(input_file)[1].lower()
        if file_ext == '.pdf' and output_format != "pdf":
            print("PDF import is disabled")
            return None, None
            
        # Create a temporary directory for the output
        temp_dir = tempfile.mkdtemp()
        
        # Get the absolute path of the input file
        input_abs_path = os.path.abspath(input_file)
        
        # Prepare the command - specify the actual output filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Use the correct command format for LibreOffice
        # The format should be: output_format:output_filter
        if output_format == "html":
            conversion_format = "html:HTML (StarWriter)"
        elif output_format == "pdf":
            conversion_format = "pdf:writer_pdf_Export"
        else:
            conversion_format = output_format
        
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', conversion_format,
            '--outdir', temp_dir,
            input_abs_path
        ]
    
        print(f"Running conversion command: {' '.join(cmd)}")
        
        # Run the conversion process
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Debug output
        print(f"LibreOffice stdout: {process.stdout}")
        print(f"LibreOffice stderr: {process.stderr}")
        
        if process.returncode != 0:
            print(f"LibreOffice conversion failed with return code {process.returncode}: {process.stderr}")
            return None, None
            
        # Find the converted file - it could be named differently than we expect
        converted_files = [f for f in os.listdir(temp_dir) if f.endswith(f".{output_format}")]
        
        if not converted_files:
            print(f"No {output_format} files found in {temp_dir}. Directory contents: {os.listdir(temp_dir)}")
            return None, None
            
        # Use the first matching file found
        output_file = os.path.join(temp_dir, converted_files[0])
        
        print(f"Found converted file: {output_file}")
        
        # Check if the file actually exists and has content
        if not os.path.exists(output_file):
            print(f"LibreOffice did not create output file: {output_file}")
            return None, None
            
        if os.path.getsize(output_file) == 0:
            print(f"LibreOffice created an empty output file: {output_file}")
            return None, None
            
        return output_file, temp_dir
        
    except subprocess.TimeoutExpired:
        print("LibreOffice conversion timed out")
        return None, None
    except Exception as e:
        print(f"Error during LibreOffice conversion: {e}")
        return None, None

# Open operations
def on_open_clicked(self, win, button):
    """Show open file dialog and decide whether to open in current or new window"""
    dialog = Gtk.FileDialog()
    dialog.set_title("Open Document")
    
    # Create file filters for all supported formats
    filter_list = Gio.ListStore.new(Gtk.FileFilter)
    
    # Add filters for each category of document formats
    for category, formats in LIBREOFFICE_INPUT_FORMATS.items():
        # Create a filter for this category
        category_filter = Gtk.FileFilter()
        category_filter.set_name(f"{category}")
        
        # Add patterns for each format in this category
        for format_info in formats:
            extension = format_info["extension"]
            category_filter.add_pattern(f"*{extension}")
        
        filter_list.append(category_filter)
    
    # Add individual filters for common formats
    filter_writer = Gtk.FileFilter()
    filter_writer.set_name("Writer Documents (.odt, .doc, .docx, .rtf)")
    filter_writer.add_pattern("*.odt")
    filter_writer.add_pattern("*.doc")
    filter_writer.add_pattern("*.docx")
    filter_writer.add_pattern("*.rtf")
    filter_list.append(filter_writer)
    
    filter_html = Gtk.FileFilter()
    filter_html.set_name("HTML files (.html, .htm)")
    filter_html.add_pattern("*.html")
    filter_html.add_pattern("*.htm")
    filter_list.append(filter_html)
    
    filter_md = Gtk.FileFilter()
    filter_md.set_name("Markdown files (.md, .markdown)")
    filter_md.add_pattern("*.md")
    filter_md.add_pattern("*.markdown")
    filter_list.append(filter_md)
    
    filter_txt = Gtk.FileFilter()
    filter_txt.set_name("Text files (.txt)")
    filter_txt.add_pattern("*.txt")
    filter_list.append(filter_txt)
    
    # Add an "All Supported Files" filter at the top
    filter_all_supported = Gtk.FileFilter()
    filter_all_supported.set_name("All Supported Files")
    for category, formats in LIBREOFFICE_INPUT_FORMATS.items():
        for format_info in formats:
            extension = format_info["extension"]
            filter_all_supported.add_pattern(f"*{extension}")
    filter_list.insert(0, filter_all_supported)
    
    # Also add "All Files" filter at the end
    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")
    filter_list.append(filter_all)
    
    dialog.set_filters(filter_list)
    
    # Set the default filter to "All Supported Files"
    # Set the "All Supported Files" filter as initial filter
    # In GTK4, we can't directly set the initial filter, but we can ensure it's first in the list
    # The FileDialog will use the first filter as the default
    
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
    """Handle save button click with protection for LibreOffice formats"""
    if win.current_file:
        # Get the file path
        file_path = win.current_file.get_path()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if this is a LibreOffice format that we shouldn't overwrite
        if is_libreoffice_format(file_path) and file_ext not in ['.html', '.htm', '.txt', '.md', '.markdown', '.mht', '.mhtml', '.pdf']:
            # Don't overwrite LibreOffice files - force a Save As
            win.statusbar.set_text(f"Cannot overwrite {file_ext} files. Please use Save As instead.")
            self.show_save_as_warning_dialog(win)
            return
            
        # Handle normal save for supported formats
        if file_ext in ['.mht', '.mhtml']:
            self.save_as_mhtml(win, win.current_file)
        elif file_ext in ['.html', '.htm']:
            self.save_as_html(win, win.current_file)
        elif file_ext in ['.md', '.markdown']:
            self.save_as_markdown(win, win.current_file)
        elif file_ext in ['.txt']:
            self.save_as_text(win, win.current_file)
        elif file_ext == '.pdf':
            self.save_as_pdf(win, win.current_file)
        else:
            # For unknown extensions, save as MHTML by default
            self.save_as_mhtml(win, win.current_file)
    else:
        # Show custom save dialog for new file
        self.show_custom_save_dialog(win)

def show_save_as_warning_dialog(self, win):
    """Show a warning dialog when trying to save directly to a LibreOffice format"""
    dialog = Gtk.MessageDialog(
        transient_for=win,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="Cannot Overwrite Original File"
    )
    
    # Get the file extension
    file_ext = os.path.splitext(win.current_file.get_path())[1].lower()
    
    # Set secondary text
    dialog.format_secondary_text(
        f"This editor cannot save directly back to the original {file_ext} format.\n\n"
        f"Please use 'Save As' to save your changes to a supported format "
        f"like HTML, MHTML, PDF, or Text."
    )
    
    # Add buttons
    dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
    save_as_button = dialog.add_button("_Save As...", Gtk.ResponseType.OK)
    save_as_button.add_css_class("suggested-action")
    
    # Connect response
    dialog.connect("response", self._on_save_warning_response, win)
    
    # Show the dialog
    dialog.present()

def _on_save_warning_response(self, dialog, response, win):
    """Handle response from the save warning dialog"""
    dialog.destroy()
    
    if response == Gtk.ResponseType.OK:
        # Show the Save As dialog
        self.on_save_as_clicked(win, None)

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
        {"extension": ".txt", "name": "Plain Text", "mime": "text/plain"},
        {"extension": ".pdf", "name": "PDF Document", "mime": "application/pdf"},

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
            elif file_ext == '.pdf':
                self.save_as_pdf(win, file)
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
def load_file(self, win, filepath):
    """Load file content into editor with enhanced format support and image handling"""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            self.show_error_dialog("File not found")
            return
            
        # Store the original file path format for reference
        win.original_format = os.path.splitext(filepath)[1].lower()
        win.original_filepath = filepath
        
        # Show loading dialog for potentially slow conversions
        loading_dialog = None
        if is_libreoffice_format(filepath) and win.original_format not in ['.html', '.htm', '.txt', '.md', '.markdown']:
            loading_dialog = self.show_loading_dialog(win)
        
        # Process the file based on its format
        file_ext = os.path.splitext(filepath)[1].lower()
        
        # Function to continue loading after potential conversion
        def continue_loading(html_content=None, converted_path=None, image_dir=None):
            try:
                # Close loading dialog if it was shown
                if loading_dialog:
                    try:
                        loading_dialog.close()
                    except Exception as e:
                        print(f"Warning: Could not close loading dialog: {e}")
                
                # Initialize content variable
                content = ""
                
                # If we already have HTML content from conversion, use it
                if html_content:
                    content = html_content
                else:
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
                
                # Process content based on file type
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
                            content = self._simple_markdown_to_html(content)
                    else:
                        # Use simplified markdown conversion
                        content = self._simple_markdown_to_html(content)
                elif file_ext == '.txt':
                    # Convert plain text to HTML
                    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    content = f"<div>{content.replace(chr(10), '<br>')}</div>"
                
                # Process image references for converted LibreOffice documents
                if converted_path and image_dir and os.path.exists(image_dir):
                    # Look for an 'images' subfolder that LibreOffice might have created
                    images_folder = os.path.join(image_dir, 'images')
                    if os.path.exists(images_folder) and os.path.isdir(images_folder):
                        print(f"Found images folder: {images_folder}")
                        # Store the image directory for reference
                        win.image_dir = images_folder
                        
                        # Process the image references in the content
                        content = self._process_image_references(content, images_folder)
                    else:
                        # Check for any image files in the main output directory
                        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                        if image_files:
                            print(f"Found {len(image_files)} image files in output directory")
                            win.image_dir = image_dir
                            content = self._process_image_references(content, image_dir)
                        else:
                            print(f"No images folder or image files found in {image_dir}")
                
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
                
                # Update file information - CHANGED BEHAVIOR HERE
                if converted_path and is_libreoffice_format(filepath) and win.original_format not in ['.html', '.htm', '.txt', '.md', '.markdown']:
                    # For LibreOffice files that were converted, use the HTML file as the current file
                    win.current_file = Gio.File.new_for_path(converted_path)
                    win.statusbar.set_text(f"Opened {os.path.basename(filepath)} (converted to HTML)")
                    # Add information for the user about the conversion
                    GLib.timeout_add(1000, lambda: self.show_conversion_notification(win, filepath, converted_path))
                else:
                    # For directly supported formats, use the original file
                    win.current_file = Gio.File.new_for_path(filepath)
                    win.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
                
                win.modified = False
                self.update_window_title(win)
                        
            except Exception as e:
                # Close loading dialog if it was shown
                if loading_dialog:
                    try:
                        loading_dialog.close()
                    except:
                        pass
                print(f"Error processing file content: {str(e)}")
                win.statusbar.set_text(f"Error processing file: {str(e)}")
                self.show_error_dialog(f"Error processing file: {e}")
        
        # Check if file needs LibreOffice conversion
        if is_libreoffice_format(filepath) and file_ext not in ['.html', '.htm', '.txt', '.md', '.markdown']:
            # Start the conversion in a separate thread to keep UI responsive
            def convert_thread():
                try:
                    # Convert the file to HTML using LibreOffice
                    converted_file, image_dir = self.convert_with_libreoffice(filepath, "html")
                    
                    if converted_file:
                        # Read the converted HTML file
                        try:
                            with open(converted_file, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                                
                            # Extract body content
                            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                            if body_match:
                                html_content = body_match.group(1).strip()
                            
                            # Schedule continuing in the main thread with the HTML content
                            GLib.idle_add(lambda: continue_loading(html_content, converted_file, image_dir))
                        except Exception as e:
                            print(f"Error reading converted file: {e}")
                            GLib.idle_add(lambda: self.show_error_dialog(f"Error reading converted file: {e}"))
                            GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                    else:
                        # Conversion failed
                        GLib.idle_add(lambda: self.show_error_dialog("Failed to convert document with LibreOffice. Please check if LibreOffice is installed correctly."))
                        GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                except Exception as e:
                    print(f"Error in conversion thread: {e}")
                    GLib.idle_add(lambda: self.show_error_dialog(f"Conversion error: {e}"))
                    GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                
                return False  # Don't repeat
            
            # Start the conversion thread
            GLib.idle_add(lambda: GLib.Thread.new(None, convert_thread) and False)
        else:
            # Continue with normal loading for directly supported formats
            continue_loading()
            
    except Exception as e:
        if loading_dialog:
            try:
                loading_dialog.close()
            except:
                pass
        print(f"Error loading file: {str(e)}")
        win.statusbar.set_text(f"Error loading file: {str(e)}")
        self.show_error_dialog(f"Error loading file: {e}")

def show_conversion_notification(self, win, original_path, html_path):
    """Show a notification that the file was converted"""
    original_ext = os.path.splitext(os.path.basename(original_path))[1].upper()
    
    dialog = Gtk.MessageDialog(
        transient_for=win,
        modal=True,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=f"Document Converted from {original_ext}"
    )
    
    dialog.format_secondary_text(
        f"The {original_ext} document has been converted to HTML for editing. "
        f"When you save, it will save as an HTML file.\n\n"
        f"Use 'Save As' if you want to save in a different format like PDF."
    )
    
    dialog.connect("response", lambda d, r: d.destroy())
    dialog.present()
    
    return False  # Don't repeat this timeout

def update_window_title(self, win):
    """Update window title to show current file and format"""
    app_name = "HTML Editor"
    
    if win.current_file:
        file_path = win.current_file.get_path()
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # If this is a converted document, indicate it in the title
        if hasattr(win, 'original_filepath') and win.original_filepath != file_path:
            original_ext = os.path.splitext(win.original_filepath)[1].upper()
            current_ext = file_ext.upper()
            title = f"{file_name} [{original_ext} → {current_ext}] - {app_name}"
        else:
            title = f"{file_name} - {app_name}"
            
        if win.modified:
            title = f"*{title}"
    else:
        title = f"Untitled - {app_name}"
        if win.modified:
            title = f"*{title}"
    
    win.set_title(title)

           
def _process_image_references(self, html_content, image_dir):
    """Process image references in HTML content converted from LibreOffice documents"""
    try:
        import urllib.parse  # Add this import for URL decoding
        print(f"Processing image references from directory: {image_dir}")
        
        # Find all image tags in the HTML
        image_tags = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', html_content)
        print(f"Found {len(image_tags)} image references in HTML")
        
        # List all files in the image directory
        image_files = os.listdir(image_dir)
        print(f"Found {len(image_files)} files in image directory: {image_files}")
        
        # Function to process an image tag
        def process_image_ref(match):
            img_tag = match.group(0)
            src = match.group(1)
            
            print(f"Processing image reference: {src}")
            
            # Skip already processed or external images
            if src.startswith(('http://', 'https://', 'data:')):
                print(f"Skipping external image: {src}")
                return img_tag
            
            # URL decode the source - this is key to handling LibreOffice's encoding
            decoded_src = urllib.parse.unquote(src)
            print(f"Decoded source: {decoded_src}")
                
            # If the src is relative, try to find the image in the image directory
            img_path = os.path.join(image_dir, decoded_src)
            if not os.path.exists(img_path):
                # Try removing any directory prefix
                img_path = os.path.join(image_dir, os.path.basename(decoded_src))
                
            print(f"Looking for image at: {img_path}")
            
            if os.path.exists(img_path):
                print(f"Found image at: {img_path}")
                
                # Convert the image to a data URL to embed it directly
                try:
                    with open(img_path, 'rb') as img_file:
                        import base64
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        mime_type = self._get_mime_type(img_path)
                        data_url = f"data:{mime_type};base64,{img_data}"
                        
                        # Replace the src attribute with the data URL
                        new_tag = img_tag.replace(f'src="{src}"', f'src="{data_url}"')
                        print(f"Converted image to data URL")
                        return new_tag
                except Exception as e:
                    print(f"Error creating data URL for image {img_path}: {e}")
            else:
                # Search for any image file with a similar name pattern
                base_name = os.path.splitext(os.path.basename(decoded_src))[0].lower()
                print(f"Image not found, searching for similar names with base: {base_name}")
                
                for file in image_files:
                    if base_name in file.lower():
                        img_path = os.path.join(image_dir, file)
                        print(f"Found potential match: {img_path}")
                        
                        try:
                            with open(img_path, 'rb') as img_file:
                                import base64
                                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                                mime_type = self._get_mime_type(img_path)
                                data_url = f"data:{mime_type};base64,{img_data}"
                                
                                # Replace the src attribute with the data URL
                                new_tag = img_tag.replace(f'src="{src}"', f'src="{data_url}"')
                                print(f"Used similar image as data URL")
                                return new_tag
                        except Exception as e:
                            print(f"Error creating data URL for similar image {img_path}: {e}")
                            break
                
                print(f"No matching image found for {src}")
                    
            # If we couldn't process the image, return the original tag
            return img_tag
        
        # Find and process all image tags
        processed_html = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', process_image_ref, html_content)
        
        return processed_html
    except Exception as e:
        print(f"Error processing image references: {e}")
        return html_content

def _get_mime_type(self, file_path):
    """Get MIME type for a file"""
    # Simple extension-based MIME type detection
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }
    return mime_map.get(ext, 'application/octet-stream')

def cleanup_temp_files(self, win):
    """Clean up temporary files when closing a window"""
    # Clean up image directory if it exists
    if hasattr(win, 'image_dir') and win.image_dir and os.path.exists(win.image_dir):
        try:
            shutil.rmtree(win.image_dir)
        except Exception as e:
            print(f"Error cleaning up image directory: {e}")


def convert_with_libreoffice(self, input_file, output_format="html"):
    """
    Convert a document using LibreOffice in headless mode with improved image handling
    
    Args:
        input_file: Path to the input file
        output_format: Format to convert to (default: html)
        
    Returns:
        Tuple of (path to the converted file, directory containing image files) or (None, None) if conversion failed
    """
    if not LIBREOFFICE_AVAILABLE:
        print("LibreOffice not available for document conversion")
        return None, None
        
    try:
        # Create a temporary directory for the output
        temp_dir = tempfile.mkdtemp()
        
        # Get the absolute path of the input file
        input_abs_path = os.path.abspath(input_file)
        file_ext = os.path.splitext(input_file)[1].lower()
        
        # Prepare the command - specify the actual output filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Special handling for PDF files - they need a different filter
        if file_ext == '.pdf':
            conversion_format = "html:HTML"
        else:
            # Use the correct command format for LibreOffice
            # The format should be: output_format:output_filter
            if output_format == "html":
                conversion_format = "html:HTML (StarWriter)"
            else:
                conversion_format = output_format
            
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', conversion_format,
            '--outdir', temp_dir,
            input_abs_path
        ]
        
        print(f"Running conversion command: {' '.join(cmd)}")
        
        # Run the conversion process
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60  # Increased timeout to 60 seconds
        )
        
        # Debug output
        print(f"LibreOffice stdout: {process.stdout}")
        print(f"LibreOffice stderr: {process.stderr}")
        
        if process.returncode != 0:
            print(f"LibreOffice conversion failed with return code {process.returncode}: {process.stderr}")
            
            # For PDFs, try alternative conversion approach if first method failed
            if file_ext == '.pdf' and 'Error Area:Io' in process.stderr:
                print("Trying alternative PDF conversion method...")
                alt_cmd = [
                    'libreoffice',
                    '--headless',
                    '--infilter="pdf:writer_pdf_import"', 
                    '--convert-to', "html",
                    '--outdir', temp_dir,
                    input_abs_path
                ]
                
                print(f"Running alternative command: {' '.join(alt_cmd)}")
                
                alt_process = subprocess.run(
                    alt_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )
                
                print(f"Alternative stdout: {alt_process.stdout}")
                print(f"Alternative stderr: {alt_process.stderr}")
                
                if alt_process.returncode != 0:
                    print(f"Alternative PDF conversion also failed")
                    return None, None
            else:
                return None, None
            
        # Find the converted file - it could be named differently than we expect
        converted_files = [f for f in os.listdir(temp_dir) if f.endswith(f".{output_format}")]
        
        if not converted_files:
            print(f"No {output_format} files found in {temp_dir}. Directory contents: {os.listdir(temp_dir)}")
            return None, None
            
        # Use the first matching file found
        output_file = os.path.join(temp_dir, converted_files[0])
        
        print(f"Found converted file: {output_file}")
        
        # Check if the file actually exists and has content
        if not os.path.exists(output_file):
            print(f"LibreOffice did not create output file: {output_file}")
            return None, None
            
        if os.path.getsize(output_file) == 0:
            print(f"LibreOffice created an empty output file: {output_file}")
            return None, None
            
        return output_file, temp_dir
        
    except subprocess.TimeoutExpired:
        print("LibreOffice conversion timed out")
        return None, None
    except Exception as e:
        print(f"Error during LibreOffice conversion: {e}")
        return None, None
# Save as PDF
def save_as_pdf(self, win, file):
    """Save document as PDF using LibreOffice for conversion"""
    # First save as HTML to a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_html_path = os.path.join(temp_dir, "temp_export.html")
    temp_html_file = Gio.File.new_for_path(temp_html_path)
    
    win.statusbar.set_text(f"Preparing to save as PDF: {file.get_path()}")
    
    # Show a loading dialog since PDF conversion can take time
    loading_dialog = self.show_loading_dialog(win, "Converting document to PDF...")
    
    # Get the editor content
    win.webview.evaluate_javascript(
        "document.documentElement.outerHTML",
        -1, None, None, None,
        lambda webview, result, data: self._save_pdf_step1(win, webview, result, file, temp_html_file, temp_dir, loading_dialog),
        None
    )

def _save_pdf_step1(self, win, webview, result, target_file, temp_html_file, temp_dir, loading_dialog):
    """Step 1 of PDF saving - get HTML content and save to temporary file"""
    try:
        js_result = webview.evaluate_javascript_finish(result)
        if js_result:
            # Get the HTML content
            if hasattr(js_result, 'get_js_value'):
                html_content = js_result.get_js_value().to_string()
            else:
                html_content = js_result.to_string()
            
            # Save the complete HTML to a temporary file
            try:
                html_bytes = html_content.encode('utf-8')
                success, etag = temp_html_file.replace_contents(
                    html_bytes,
                    None,  # etag
                    False,  # make_backup
                    Gio.FileCreateFlags.REPLACE_DESTINATION,
                    None   # cancellable
                )
                
                if success:
                    # Now use LibreOffice to convert the temp HTML to PDF
                    GLib.idle_add(lambda: self._save_pdf_step2(win, temp_html_file.get_path(), target_file, temp_dir, loading_dialog))
                else:
                    self._pdf_save_cleanup(win, "Failed to create temporary HTML file", temp_dir, loading_dialog)
            except GLib.Error as e:
                self._pdf_save_cleanup(win, f"Error creating temporary file: {str(e)}", temp_dir, loading_dialog)
        else:
            self._pdf_save_cleanup(win, "Failed to get document content", temp_dir, loading_dialog)
    except Exception as e:
        self._pdf_save_cleanup(win, f"Error preparing PDF conversion: {str(e)}", temp_dir, loading_dialog)

def _save_pdf_step2(self, win, temp_html_path, target_file, temp_dir, loading_dialog):
    """Step 2 of PDF saving - convert temporary HTML to PDF using LibreOffice"""
    try:
        # Run the conversion in a separate thread to keep UI responsive
        def convert_thread():
            try:
                # Convert HTML to PDF using LibreOffice
                pdf_file, _ = self.convert_with_libreoffice(temp_html_path, "pdf")
                
                if pdf_file and os.path.exists(pdf_file):
                    # Copy the PDF to the target location
                    try:
                        # Read the PDF file
                        with open(pdf_file, 'rb') as f:
                            pdf_content = f.read()
                        
                        # Write to the target file
                        target_path = target_file.get_path()
                        with open(target_path, 'wb') as f:
                            f.write(pdf_content)
                        
                        # Update the UI in the main thread
                        GLib.idle_add(lambda: self._pdf_save_success(win, target_file, temp_dir, loading_dialog))
                    except Exception as e:
                        GLib.idle_add(lambda: self._pdf_save_cleanup(
                            win, f"Error saving PDF to target location: {str(e)}", temp_dir, loading_dialog))
                else:
                    GLib.idle_add(lambda: self._pdf_save_cleanup(
                        win, "PDF conversion failed. Please check if LibreOffice is installed correctly.", 
                        temp_dir, loading_dialog))
            except Exception as e:
                GLib.idle_add(lambda: self._pdf_save_cleanup(
                    win, f"Error during PDF conversion: {str(e)}", temp_dir, loading_dialog))
            
            return False  # Don't repeat
        
        # Start the conversion thread
        GLib.Thread.new(None, convert_thread)
        return False  # Don't repeat this idle callback
    except Exception as e:
        self._pdf_save_cleanup(win, f"Error starting PDF conversion thread: {str(e)}", temp_dir, loading_dialog)
        return False  # Don't repeat this idle callback

def _pdf_save_success(self, win, file, temp_dir, loading_dialog):
    """Handle successful PDF save"""
    try:
        # Close the loading dialog
        if loading_dialog:
            loading_dialog.close()
        
        # Update the UI
        win.current_file = file
        win.modified = False
        self.update_window_title(win)
        win.statusbar.set_text(f"Saved PDF: {file.get_path()}")
        
        # Clean up temporary directory
        self._cleanup_temp_dir(temp_dir)
    except Exception as e:
        print(f"Error in PDF save success handler: {e}")
        win.statusbar.set_text(f"PDF saved, but encountered an error: {str(e)}")

def _pdf_save_cleanup(self, win, error_message, temp_dir, loading_dialog):
    """Clean up after PDF save error"""
    try:
        # Close the loading dialog
        if loading_dialog:
            loading_dialog.close()
        
        # Show error
        print(f"PDF save error: {error_message}")
        win.statusbar.set_text(f"Error saving PDF: {error_message}")
        self.show_error_dialog(win, f"Error saving PDF: {error_message}")
        
        # Clean up temporary directory
        self._cleanup_temp_dir(temp_dir)
    except Exception as e:
        print(f"Error in PDF save cleanup: {e}")

def _cleanup_temp_dir(self, temp_dir):
    """Helper to clean up temporary directory"""
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error cleaning up temporary directory: {e}")   

################# 
def load_file(self, win, filepath):
    """Load file content into editor with enhanced format support and image handling"""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            self.show_error_dialog("File not found")
            return
            
        # Store the original file path format for reference
        win.original_format = os.path.splitext(filepath)[1].lower()
        win.original_filepath = filepath
        
        # Show loading dialog for potentially slow conversions
        loading_dialog = None
        if is_libreoffice_format(filepath) and win.original_format not in ['.html', '.htm', '.txt', '.md', '.markdown']:
            loading_dialog = self.show_loading_dialog(win)
        
        # Process the file based on its format
        file_ext = os.path.splitext(filepath)[1].lower()
        
        # Function to continue loading after potential conversion
        def continue_loading(html_content=None, converted_path=None, image_dir=None):
            try:
                # Close loading dialog if it was shown
                if loading_dialog:
                    try:
                        loading_dialog.close()
                    except Exception as e:
                        print(f"Warning: Could not close loading dialog: {e}")
                
                # Initialize content variable
                content = ""
                
                # If we already have HTML content from conversion, use it
                if html_content:
                    content = html_content
                else:
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
                
                # Process content based on file type
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
                            content = self._simple_markdown_to_html(content)
                    else:
                        # Use simplified markdown conversion
                        content = self._simple_markdown_to_html(content)
                elif file_ext == '.txt':
                    # Convert plain text to HTML
                    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    content = f"<div>{content.replace(chr(10), '<br>')}</div>"
                
                # Process image references for converted LibreOffice documents
                if converted_path and image_dir and os.path.exists(image_dir):
                    # Look for an 'images' subfolder that LibreOffice might have created
                    images_folder = os.path.join(image_dir, 'images')
                    if os.path.exists(images_folder) and os.path.isdir(images_folder):
                        print(f"Found images folder: {images_folder}")
                        # Store the image directory for reference
                        win.image_dir = images_folder
                        
                        # Process the image references in the content
                        content = self._process_image_references(content, images_folder)
                    else:
                        # Check for any image files in the main output directory
                        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                        if image_files:
                            print(f"Found {len(image_files)} image files in output directory")
                            win.image_dir = image_dir
                            content = self._process_image_references(content, image_dir)
                        else:
                            print(f"No images folder or image files found in {image_dir}")
                
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
                
                # Mark as converted document if LibreOffice conversion was used
                if converted_path and is_libreoffice_format(filepath) and win.original_format not in ['.html', '.htm', '.txt', '.md', '.markdown']:
                    # Mark as a converted document
                    win.is_converted_document = True
                else:
                    win.is_converted_document = False
                
                win.modified = False
                self.update_window_title(win)
                win.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
                        
            except Exception as e:
                # Close loading dialog if it was shown
                if loading_dialog:
                    try:
                        loading_dialog.close()
                    except:
                        pass
                print(f"Error processing file content: {str(e)}")
                win.statusbar.set_text(f"Error processing file: {str(e)}")
                self.show_error_dialog(f"Error processing file: {e}")
        
        # Check if file needs LibreOffice conversion
        if is_libreoffice_format(filepath) and file_ext not in ['.html', '.htm', '.txt', '.md', '.markdown']:
            # Start the conversion in a separate thread to keep UI responsive
            def convert_thread():
                try:
                    # Convert the file to HTML using LibreOffice
                    converted_file, image_dir = self.convert_with_libreoffice(filepath, "html")
                    
                    if converted_file:
                        # Read the converted HTML file
                        try:
                            with open(converted_file, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                                
                            # Extract body content
                            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                            if body_match:
                                html_content = body_match.group(1).strip()
                            
                            # Schedule continuing in the main thread with the HTML content
                            GLib.idle_add(lambda: continue_loading(html_content, converted_file, image_dir))
                        except Exception as e:
                            print(f"Error reading converted file: {e}")
                            GLib.idle_add(lambda: self.show_error_dialog(f"Error reading converted file: {e}"))
                            GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                    else:
                        # Conversion failed
                        GLib.idle_add(lambda: self.show_error_dialog("Failed to convert document with LibreOffice. Please check if LibreOffice is installed correctly."))
                        GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                except Exception as e:
                    print(f"Error in conversion thread: {e}")
                    GLib.idle_add(lambda: self.show_error_dialog(f"Conversion error: {e}"))
                    GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                
                return False  # Don't repeat
            
            # Start the conversion thread
            GLib.idle_add(lambda: GLib.Thread.new(None, convert_thread) and False)
        else:
            # Continue with normal loading for directly supported formats
            continue_loading()
            
    except Exception as e:
        if loading_dialog:
            try:
                loading_dialog.close()
            except:
                pass
        print(f"Error loading file: {str(e)}")
        win.statusbar.set_text(f"Error loading file: {str(e)}")
        self.show_error_dialog(f"Error loading file: {e}")

def on_save_clicked(self, win, button):
    """Handle save button click by redirecting to Save As for converted documents"""
    # Check if this is a converted document
    if hasattr(win, 'is_converted_document') and win.is_converted_document:
        # For converted documents, redirect to Save As - no dialog needed
        self.on_save_as_clicked(win, button)
        return
        
    # Normal save operation for non-converted documents
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
        elif file_ext == '.pdf':
            self.save_as_pdf(win, win.current_file)
        else:
            # For unknown extensions, save as MHTML by default
            self.save_as_mhtml(win, win.current_file)
    else:
        # Show custom save dialog for new file
        self.show_custom_save_dialog(win)
