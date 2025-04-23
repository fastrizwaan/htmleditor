import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib, Pango, Gio

class PageEditor(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Page Editor")
        self.set_default_size(350, 600)
        
        # Page parameters - explicitly set to small values
        self.chars_per_line = 30
        self.lines_per_page = 2
        self.chars_per_page = self.chars_per_line * self.lines_per_page  # Should be 60
        
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
        
        # Create main text buffer and view
        self.buffer = Gtk.TextBuffer()
        self.buffer.connect("changed", self.on_text_changed)
        
        # Main text view (hidden, used for editing)
        self.main_text_view = Gtk.TextView()
        self.main_text_view.set_buffer(self.buffer)
        self.main_text_view.set_visible(False)
        
        # Scrolled window for pages
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box.append(self.scrolled)
        
        # Pages container
        self.pages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pages_box.set_spacing(20)
        self.scrolled.set_child(self.pages_box)
        
        # Initialize page views
        self.page_views = []
        self.create_initial_page()
        
        # Flag to prevent recursive updates
        self.updating = False
    
    def create_initial_page(self):
        # Create the first page
        self.add_page()
    
    def add_page(self):
        # Create page container
        page_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page_container.set_margin_top(10)
        page_container.set_margin_bottom(10)
        page_container.set_margin_start(10)
        page_container.set_margin_end(10)
        
        # Page number
        page_number = len(self.page_views) + 1
        
        # Create page frame
        frame = Gtk.Frame()
        frame.set_size_request(300, 100)  # Width for 30 chars, height for 2 lines
        
        # Create text view for this page
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.set_left_margin(10)
        text_view.set_right_margin(10)
        text_view.set_top_margin(10)
        text_view.set_bottom_margin(10)
        text_view.set_monospace(True)
        text_view.set_editable(True)
        text_view.set_cursor_visible(True)
        
        # Set CSS for font
        css_provider = Gtk.CssProvider()
        css = """
        textview {
            font-family: monospace;
            font-size: 12pt;
        }
        """
        css_provider.load_from_data(css.encode('utf-8'))
        style_context = text_view.get_style_context()
        Gtk.StyleContext.add_provider(style_context, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Connect key events to sync with main buffer
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_page_key_pressed, page_number-1)
        key_controller.connect("key-released", self.on_page_key_released, page_number-1)
        text_view.add_controller(key_controller)
        
        # Create page-specific buffer
        buffer = Gtk.TextBuffer()
        text_view.set_buffer(buffer)
        
        # Add text view to frame
        frame.set_child(text_view)
        
        # Add frame to page container
        page_container.append(frame)
        
        # Add page number label
        page_label = Gtk.Label(label=f"Page {page_number}")
        page_container.append(page_label)
        
        # Add page to the pages box
        self.pages_box.append(page_container)
        
        # Store page components
        self.page_views.append({
            'container': page_container,
            'frame': frame, 
            'text_view': text_view,
            'buffer': buffer,
            'label': page_label,
            'number': page_number
        })
        
        return len(self.page_views) - 1  # Return index of the new page
    
    def remove_page(self, index):
        if index < len(self.page_views):
            # Get page container
            page = self.page_views[index]
            # Remove from box
            self.pages_box.remove(page['container'])
            # Remove from list
            self.page_views.pop(index)
            
            # Update page numbers
            for i, page in enumerate(self.page_views):
                page_number = i + 1
                page['number'] = page_number
                page['label'].set_text(f"Page {page_number}")
    
    def on_page_key_pressed(self, controller, keyval, keycode, state, page_index):
        # Transfer focus to the appropriate location in the main buffer
        return False  # Continue event propagation
    
    def on_page_key_released(self, controller, keyval, keycode, state, page_index):
        # After a key is released, sync the page content with the main buffer
        self.sync_pages_to_main_buffer()
        # Explicitly force a redistribution after key events
        GLib.idle_add(self.sync_main_buffer_to_pages)
        return False
    
    def sync_pages_to_main_buffer(self):
        if self.updating:
            return
        
        self.updating = True
        
        # Collect all text from individual page buffers
        full_text = ""
        for page in self.page_views:
            buffer = page['buffer']
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            page_text = buffer.get_text(start_iter, end_iter, False)
            full_text += page_text
        
        # Update the main buffer
        self.buffer.set_text(full_text, -1)
        
        self.updating = False
    
    def sync_main_buffer_to_pages(self):
        if self.updating:
            return
        
        self.updating = True
        
        try:
            # Get text from main buffer
            start_iter = self.buffer.get_start_iter()
            end_iter = self.buffer.get_end_iter()
            full_text = self.buffer.get_text(start_iter, end_iter, False)
            
            # Debug
            print(f"Full text length: {len(full_text)}, chars per page: {self.chars_per_page}")
            
            # Calculate how many pages we need - use ceil to ensure we have enough pages
            text_length = len(full_text)
            pages_needed = max(1, (text_length + self.chars_per_page - 1) // self.chars_per_page)
            
            # Alternative calculation with Math.ceil for debugging
            import math
            pages_needed_alt = max(1, math.ceil(text_length / self.chars_per_page))
            
            print(f"Pages needed: {pages_needed} (alternative calculation: {pages_needed_alt})")
            
            # Use the more reliable calculation
            pages_needed = pages_needed_alt
            
            # Adjust number of pages
            current_pages = len(self.page_views)
            print(f"Current pages: {current_pages}, adjusting to {pages_needed}")
            
            if pages_needed > current_pages:
                # Add more pages
                for _ in range(pages_needed - current_pages):
                    self.add_page()
                    print(f"Added page, now have {len(self.page_views)}")
            elif pages_needed < current_pages:
                # Remove extra pages
                for _ in range(current_pages - pages_needed):
                    self.remove_page(len(self.page_views) - 1)
                    print(f"Removed page, now have {len(self.page_views)}")
            
            # Update each page with its portion of text
            for i in range(pages_needed):
                start_idx = i * self.chars_per_page
                end_idx = min((i + 1) * self.chars_per_page, text_length)
                page_text = full_text[start_idx:end_idx]
                
                print(f"Page {i+1}: text from {start_idx} to {end_idx}: '{page_text}' ({len(page_text)} chars)")
                
                # Update the page buffer only if we have this page
                if i < len(self.page_views):
                    page_buffer = self.page_views[i]['buffer']
                    page_buffer.set_text(page_text, -1)
                else:
                    print(f"ERROR: Trying to update page {i+1} but only have {len(self.page_views)} pages")
        
        except Exception as e:
            print(f"Error in sync_main_buffer_to_pages: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.updating = False
    
    def on_text_changed(self, buffer):
        # When main buffer changes, update pages
        if not self.updating:
            GLib.idle_add(self.sync_main_buffer_to_pages)
    
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
                
            # Show success message
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
            padding: 20px;
        }
        .page {
            width: 300px;
            min-height: 100px;
            border: 1px solid #000;
            margin: 20px auto;
            padding: 10px;
            box-shadow: 0 0 5px rgba(0,0,0,0.2);
            position: relative;
            white-space: pre-wrap;
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
        
        for i, page in enumerate(self.page_views):
            buffer = page['buffer']
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            page_text = buffer.get_text(start_iter, end_iter, False)
            
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
