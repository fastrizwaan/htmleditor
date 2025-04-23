import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib, Pango, Gio

class Page(Gtk.Box):
    def __init__(self, page_number):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        
        # Page border
        self.frame = Gtk.Frame()
        self.frame.set_size_request(300, 100)  # Width based on 30 chars, height based on 2 lines
        self.append(self.frame)
        
        # Text buffer for this page
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(10)
        self.text_view.set_right_margin(10)
        self.text_view.set_top_margin(10)
        self.text_view.set_bottom_margin(10)
        
        # Set monospace font to ensure character width consistency
        self.text_view.set_monospace(True)
        
        # In GTK4, we need to use CSS for font customization
        css_provider = Gtk.CssProvider()
        css = """
        textview {
            font-family: monospace;
            font-size: 12pt;
        }
        """
        css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply the CSS to the text view
        style_context = self.text_view.get_style_context()
        Gtk.StyleContext.add_provider(style_context, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Configure the buffer
        self.buffer = self.text_view.get_buffer()
        self.buffer.connect("changed", self.on_buffer_changed)
        
        # Page number label
        self.page_label = Gtk.Label(label=f"Page {page_number}")
        
        # Add the text view to the frame
        self.frame.set_child(self.text_view)
        
        # Add page number below
        self.append(self.page_label)
        
        # Track the page number
        self.page_number = page_number
        
        # Maximum content (2 lines, 30 chars per line)
        self.max_chars_per_line = 30
        self.max_lines = 2
        self.max_content = self.max_chars_per_line * self.max_lines
        
        # Flag to prevent recursive changes
        self.is_updating = False

    def on_buffer_changed(self, buffer):
        # The buffer change callback is handled in PageEditor
        pass
        
    def set_text(self, text):
        if self.is_updating:
            return
            
        self.is_updating = True
        self.buffer.set_text(text)
        self.is_updating = False
        
    def get_text(self):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        return self.buffer.get_text(start, end, True)
        
    def update_page_number(self, number):
        self.page_number = number
        self.page_label.set_text(f"Page {number}")


class PageEditor(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Page Editor")
        self.set_default_size(350, 600)
        
        # Page parameters
        self.chars_per_line = 30
        self.lines_per_page = 2
        self.chars_per_page = self.chars_per_line * self.lines_per_page
        
        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        
        # Header bar with save button
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        
        # Save button
        self.save_button = Gtk.Button(label="Save")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.header.pack_end(self.save_button)
        
        # Scrolled window for pages
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box.append(self.scrolled)
        
        # Pages container
        self.pages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pages_box.set_spacing(20)
        self.scrolled.set_child(self.pages_box)
        
        # Store pages
        self.pages = []
        
        # Add initial page
        self.add_page()
        
        # Full text content
        self.full_text = ""
        
        # Connection flags
        self.updating_pages = False
        
        # Monitor key presses globally to catch text changes
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-released", self.on_key_released)
        self.add_controller(key_controller)

    def add_page(self):
        page_number = len(self.pages) + 1
        page = Page(page_number)
        self.pages.append(page)
        self.pages_box.append(page)
        
        # Connect to text changes using GTK4 approach
        page.buffer.connect("changed", lambda buf: self.on_page_content_changed(page))
        
        return page
        
    def remove_page(self, index):
        if index < len(self.pages):
            page = self.pages.pop(index)
            self.pages_box.remove(page)
            
            # Update page numbers
            for i, p in enumerate(self.pages):
                p.update_page_number(i + 1)
    
    def on_page_content_changed(self, page):
        if self.updating_pages:
            return
            
        # Get the complete text from all pages
        self.collect_text()
        
        # Redistribute text across pages
        self.redistribute_text()
    
    def on_key_released(self, controller, keyval, keycode, state):
        # This ensures we catch all text changes including cut/paste operations
        GLib.idle_add(self.collect_and_redistribute)
    
    def collect_and_redistribute(self):
        self.collect_text()
        self.redistribute_text()
        return False  # To stop the idle callback
    
    def collect_text(self):
        if self.updating_pages:
            return
            
        text = ""
        for page in self.pages:
            text += page.get_text()
        
        self.full_text = text
    
    def redistribute_text(self):
        if self.updating_pages:
            return
        
        self.updating_pages = True
        
        # Calculate how many pages we need
        text_length = len(self.full_text)
        pages_needed = max(1, (text_length + self.chars_per_page - 1) // self.chars_per_page)
        
        # Adjust number of pages
        current_pages = len(self.pages)
        
        if pages_needed > current_pages:
            # Add more pages
            for _ in range(pages_needed - current_pages):
                self.add_page()
        elif pages_needed < current_pages:
            # Remove extra pages
            for _ in range(current_pages - pages_needed):
                self.remove_page(len(self.pages) - 1)
        
        # Distribute text across pages
        for i in range(pages_needed):
            start_idx = i * self.chars_per_page
            end_idx = min((i + 1) * self.chars_per_page, text_length)
            page_text = self.full_text[start_idx:end_idx]
            self.pages[i].set_text(page_text)
        
        self.updating_pages = False
    
    def on_save_clicked(self, button):
        # Create a file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        
        # Add buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.ACCEPT)
        
        # Set default file name and filter for HTML
        dialog.set_current_name("document.html")
        file_filter = Gtk.FileFilter()
        file_filter.set_name("HTML files")
        file_filter.add_pattern("*.html")
        dialog.add_filter(file_filter)
        
        # Show dialog and handle response
        dialog.connect("response", self.on_save_dialog_response)
        dialog.show()
    
    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                file_path = file.get_path()
                self.save_document(file_path)
        dialog.destroy()
    
    def save_document(self, file_path):
        # Generate HTML from the content
        html_content = self.generate_html()
        
        try:
            with open(file_path, 'w') as file:
                file.write(html_content)
                
            # Show success message in GTK4 style
            message = Adw.MessageDialog.new(
                self,
                "Document Saved",
                f"The document has been saved to {file_path}"
            )
            message.add_response("ok", "OK")
            message.connect("response", lambda dialog, response: dialog.destroy())
            message.present()
                
        except Exception as e:
            # Show error message
            message = Adw.MessageDialog.new(
                self,
                "Error Saving Document",
                f"An error occurred while saving: {str(e)}"
            )
            message.add_response("ok", "OK")
            message.connect("response", lambda dialog, response: dialog.destroy())
            message.present()
    
    def generate_html(self):
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Paged Document</title>
    <style>
        body {
            font-family: monospace;
            line-height: 1.5;
        }
        .page {
            width: 300px;
            min-height: 100px;
            border: 1px solid #000;
            margin: 20px auto;
            padding: 10px;
            box-shadow: 0 0 5px rgba(0,0,0,0.2);
            position: relative;
        }
        .page-number {
            text-align: center;
            margin-top: 5px;
            font-weight: bold;
        }
        @media print {
            .page {
                page-break-after: always;
                box-shadow: none;
            }
        }
    </style>
</head>
<body>
"""
        
        for i, page in enumerate(self.pages):
            page_text = page.get_text()
            # Replace newlines with HTML breaks and preserve spacing
            page_text = page_text.replace("\n", "<br>")
            page_text = page_text.replace(" ", "&nbsp;")
            
            html += f"""    <div class="page">
        {page_text}
    </div>
    <div class="page-number">Page {i+1}</div>
"""
        
        html += """</body>
</html>"""
        
        return html


class EditorApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.pageeditor")
        self.connect('activate', self.on_activate)
        
    def on_activate(self, app):
        win = PageEditor(app)
        win.present()


if __name__ == "__main__":
    app = EditorApp()
    app.run(None)
