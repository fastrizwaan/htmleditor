#!/usr/bin/env python3
import gi
import tempfile
import os
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, GLib, WebKit, Gio

class PaginatedEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.PaginatedEditor")
        self.connect('activate', self.on_activate)
        self.tempdir = tempfile.mkdtemp()
        self.editor_html_path = os.path.join(self.tempdir, "editor.html")
        self.content_changed = False
        
    def on_activate(self, app):
        # Create the application window
        self.win = Adw.ApplicationWindow(application=app, default_width=600, default_height=800)
        self.win.set_title("Paginated Editor")
        
        # Main box layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_content(main_box)
        
        # Create the header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Add save button
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        header.pack_end(save_button)
        
        # Create WebView
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Connect to signals
        self.webview.connect("load-changed", self.on_load_changed)
        
        # Create scrolled window for the webview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.webview)
        main_box.append(scrolled)
        
        # Create editor HTML file
        self.create_editor_html()
        
        # Load the editor
        self.webview.load_uri(f"file://{self.editor_html_path}")
        
        # Show the window
        self.win.present()
    
    def create_editor_html(self):
        html_content = """<!doctype html>
<html>
<head>
<link rel="stylesheet" type="text/css" media="all" href="css/reset.css" /> <!-- reset css -->
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<style>
    body { 
        background-color: ivory; 
        font-family: verdana, sans-serif;
        margin: 0;
        padding: 20px;
    }
    .page {
        border: 1px solid #ccc;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        position: relative;
    }
    .page-content {
        outline: none;
        min-height: 100%;
        width: 100%;
        box-sizing: border-box;
        padding: 10px;
        font-size: 14px;
        line-height: 1.5;
    }
    h4 {
        margin: 10px 0;
        color: #333;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
    }
    .toolbar {
        background: #f5f5f5;
        padding: 5px;
        border-bottom: 1px solid #ddd;
        display: flex;
        flex-wrap: wrap;
    }
    .toolbar button {
        margin: 2px;
        padding: 5px 10px;
        background: #fff;
        border: 1px solid #ccc;
        border-radius: 3px;
        cursor: pointer;
    }
    .toolbar button:hover {
        background: #f0f0f0;
    }
    .toolbar select {
        margin: 2px;
        padding: 5px;
        border: 1px solid #ccc;
        border-radius: 3px;
    }
</style>
<script>
$(function(){
    // Current text state
    let pageContents = {};
    const pageWidth = 550;
    const pageHeight = 300;
    const pageCount = 3;
    
    // Initialize pages
    function initializePages() {
        // Size the pages
        $('.page').width(pageWidth).height(pageHeight);
        
        // Make all page content divs editable
        $('.page-content').attr('contenteditable', 'true');
        
        // Add input event listeners to track changes
        $('.page-content').on('input', function() {
            // Send message to GTK app that content has changed
            window.webkit.messageHandlers.contentChanged.postMessage("Content changed");
        });
        
        // Load default text for demo
        const loremText = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.";
        
        // Distribute text across pages for demo
        const words = loremText.split(" ");
        const wordsPerPage = Math.ceil(words.length / pageCount);
        
        for (let i = 1; i <= pageCount; i++) {
            const startIndex = (i - 1) * wordsPerPage;
            const endIndex = Math.min(startIndex + wordsPerPage, words.length);
            const pageWords = words.slice(startIndex, endIndex);
            $(`#page${i}-content`).text(pageWords.join(" "));
        }
    }
    
    // Format text
    function formatText(command, value = null) {
        document.execCommand(command, false, value);
    }
    
    // Set up toolbar buttons
    $('#bold-btn').click(() => formatText('bold'));
    $('#italic-btn').click(() => formatText('italic'));
    $('#underline-btn').click(() => formatText('underline'));
    
    $('#font-size').change(function() {
        formatText('fontSize', $(this).val());
    });
    
    // Initialize
    initializePages();
    
    // Function to get content for saving
    window.getContentAsHtml = function() {
        let content = {
            pages: []
        };
        
        // Collect content from all pages
        for (let i = 1; i <= pageCount; i++) {
            content.pages.push({
                id: `page${i}`,
                content: $(`#page${i}-content`).html()
            });
        }
        
        return JSON.stringify(content);
    };
});
</script>
</head>
<body>
    <div class="container">
        <h4>Paginated Editor</h4>
        
        <div class="toolbar">
            <button id="bold-btn" title="Bold"><b>B</b></button>
            <button id="italic-btn" title="Italic"><i>I</i></button>
            <button id="underline-btn" title="Underline"><u>U</u></button>
            <select id="font-size">
                <option value="1">Small</option>
                <option value="3" selected>Normal</option>
                <option value="5">Large</option>
                <option value="7">Larger</option>
            </select>
        </div>
        
        <h4>Page 1</h4>
        <div id="page1" class="page">
            <div id="page1-content" class="page-content"></div>
        </div>
        
        <h4>Page 2</h4>
        <div id="page2" class="page">
            <div id="page2-content" class="page-content"></div>
        </div>
        
        <h4>Page 3</h4>
        <div id="page3" class="page">
            <div id="page3-content" class="page-content"></div>
        </div>
    </div>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Register message handlers for communication between JS and Python
            user_content_manager = self.webview.get_user_content_manager()
            
            # Handler for content changes
            content_changed_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "contentChanged")
            if content_changed_handler:
                user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            
            # Handler for save requests
            save_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "saveRequested")
            if save_handler:
                user_content_manager.connect("script-message-received::saveRequested", self.on_save_requested)
    
    def on_content_changed(self, manager, message):
        self.content_changed = True
    
    def on_save_requested(self, manager, message):
        self.on_save_clicked(None)
    
    def on_save_clicked(self, button):
        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self.win,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.ACCEPT
        )
        dialog.set_current_name("document.json")
        
        # Set up filters
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)
        
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        dialog.add_filter(filter_html)
        
        dialog.connect("response", self.on_save_dialog_response)
        dialog.present()
    
    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            
            # Get content from WebView
            self.webview.evaluate_javascript("getContentAsHtml();", -1, None, None, None, None, self.save_content_callback, file_path)
        
        dialog.destroy()
    
    def save_content_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    if file_path.endswith('.html'):
                        # Create HTML with the content
                        content_obj = json.loads(content)
                        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Paginated Document</title>
    <style>
        body { font-family: Verdana, sans-serif; margin: 20px; }
        .page { border: 1px solid #ccc; margin-bottom: 20px; padding: 20px; }
        h2 { color: #333; }
    </style>
</head>
<body>
"""
                        for i, page in enumerate(content_obj["pages"]):
                            html_content += f'<h2>Page {i+1}</h2>\n<div class="page">\n{page["content"]}\n</div>\n\n'
                        
                        html_content += "</body>\n</html>"
                        f.write(html_content)
                    else:
                        # Save as JSON
                        f.write(content)
                
                self.show_notification("Document saved successfully")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")
    
    def show_notification(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        # In GTK4/libadwaita, we need a ToastOverlay to show toasts
        # For simplicity in this example, we'll just print the message
        print(message)
    
    def do_shutdown(self):
        # Clean up temporary files
        if os.path.exists(self.tempdir):
            for file in os.listdir(self.tempdir):
                os.unlink(os.path.join(self.tempdir, file))
            os.rmdir(self.tempdir)
        
        Adw.Application.do_shutdown(self)

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
