#!/usr/bin/env python3
import gi
import tempfile
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit, Gio

class PaginatedEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.PaginatedEditor")
        self.connect('activate', self.on_activate)
        self.tempdir = tempfile.mkdtemp()
        self.editor_html_path = os.path.join(self.tempdir, "editor.html")
        self.content_changed = False

    def on_activate(self, app):
        self.win = Adw.ApplicationWindow(application=app, default_width=600, default_height=800)
        self.win.set_title("Paginated Editor")
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_content(main_box)
        
        header = Adw.HeaderBar()
        main_box.append(header)
        
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        header.pack_end(save_button)
        
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        self.webview.connect("load-changed", self.on_load_changed)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.webview)
        main_box.append(scrolled)
        
        self.create_editor_html()
        self.webview.load_uri(f"file://{self.editor_html_path}")
        self.win.present()

    # ADD MISSING LOAD HANDLER
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            user_content_manager = self.webview.get_user_content_manager()
            user_content_manager.register_script_message_handler("contentChanged")
            user_content_manager.register_script_message_handler("saveRequested")
            user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            user_content_manager.connect("script-message-received::saveRequested", self.on_save_requested)

    def on_content_changed(self, manager, message):
        self.content_changed = True

    def on_save_requested(self, manager, message):
        self.on_save_clicked(None)

    def on_save_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self.win,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.ACCEPT
        )
        dialog.set_current_name("document.html")
        
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        dialog.add_filter(filter_html)
        
        dialog.connect("response", self.on_save_dialog_response)
        dialog.present()

    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            file_path = file.get_path()
            
            self.webview.evaluate_javascript(
                "getContentAsHtml();", 
                -1, 
                None, 
                None, 
                None, 
                None, 
                self.save_html_callback, 
                file_path
            )
        dialog.destroy()

    def save_html_callback(self, result, file_path):
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                html_content = js_result.get_js_value().to_string()
                with open(file_path, 'w') as f:
                    f.write(html_content)
                self.show_notification("Document saved successfully")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")

    def show_notification(self, message):
        toast = Adw.Toast.new(message)
        toast_overlay = Adw.ToastOverlay.new()
        toast_overlay.add_toast(toast)
        self.win.set_content(toast_overlay)

    def create_editor_html(self):
        html_content = """<!-- Your HTML content from previous answer -->"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)

    def do_shutdown(self):
        if os.path.exists(self.tempdir):
            for file in os.listdir(self.tempdir):
                os.unlink(os.path.join(self.tempdir, file))
            os.rmdir(self.tempdir)
        super().do_shutdown()

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
