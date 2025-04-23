import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, Adw, WebKit, GLib

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 20px;
            font-family: monospace;
        }
        .page-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .page {
            width: 10ch;
            height: 2em;
            border: 1px solid #ccc;
            padding: 10px;
            overflow: hidden;
            line-height: 1em;
            white-space: pre;
        }
        #editor {
            display: none;
        }
    </style>
</head>
<body>
    <div class="page-container" id="pages"></div>
    <div id="editor" contenteditable="true"></div>
    <script>
        const editor = document.getElementById('editor');
        const pagesContainer = document.getElementById('pages');
        let currentText = '';

        function updatePages() {
            currentText = editor.textContent;
            pagesContainer.innerHTML = '';
            
            let pageContent = '';
            let lineCount = 0;
            
            for(let char of currentText) {
                pageContent += char;
                if(pageContent.replace(/\n$/, '').split('\n').pop().length >= 10) {
                    pageContent += '\n';
                    lineCount++;
                }
                if(lineCount >= 2) {
                    addPage(pageContent);
                    pageContent = '';
                    lineCount = 0;
                }
            }
            
            if(pageContent.length > 0 || currentText.length === 0) {
                addPage(pageContent);
            }
        }

        function addPage(content) {
            const page = document.createElement('div');
            page.className = 'page';
            page.textContent = content.padEnd(20, ' ');
            pagesContainer.appendChild(page);
        }

        editor.addEventListener('input', () => {
            updatePages();
            // Keep editor focused
            editor.focus();
        });

        document.addEventListener('click', (e) => {
            if(e.target.classList.contains('page')) {
                editor.focus();
            }
        });

        updatePages();
    </script>
</body>
</html>
"""

class PageEditorWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(600, 400)
        self.set_title("Page Editor")

        # Main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        # Header bar
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)

        # Save button
        self.save_button = Gtk.Button(label="Save")
        self.save_button.add_css_class("suggested-action")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.header.pack_end(self.save_button)

        # WebView
        self.webview = WebKit.WebView()
        self.webview.load_html(HTML_CONTENT, "null")
        self.main_box.append(self.webview)

    def on_save_clicked(self, button):
        self.webview.run_javascript(
            "document.documentElement.outerHTML;",
            None,
            self.on_javascript_finished,
            None
        )

    def on_javascript_finished(self, webview, result, user_data):
        try:
            js_result = webview.run_javascript_finish(result)
            if js_result and js_result.get_js_value():
                full_html = js_result.get_js_value().to_string()
                
                # Create save dialog
                chooser = Gtk.FileChooserNative.new(
                    "Save HTML",
                    self,
                    Gtk.FileChooserAction.SAVE,
                    "_Save",
                    "_Cancel"
                )
                chooser.connect("response", self.on_save_response, full_html)
                chooser.show()
        except Exception as e:
            print("Error:", e)

    def on_save_response(self, dialog, response, html_content):
        if response == Gtk.ResponseType.ACCEPT:
            try:
                file = dialog.get_file()
                file.replace_contents(
                    html_content.encode('utf-8'),
                    None,
                    False,
                    Gio.FileCreateFlags.REPLACE_DESTINATION,
                    None,
                    None
                )
            except Exception as e:
                print("Save error:", e)

class PageEditorApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.example.PageEditor')
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = PageEditorWindow(application=self)
        self.window.present()

if __name__ == "__main__":
    app = PageEditorApp()
    app.run(None)
