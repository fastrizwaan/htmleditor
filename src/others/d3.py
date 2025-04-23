import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gio, WebKit

class SimplePageEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.pageeditor",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        # Create the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(900, 800)
        self.win.set_title("Page Layout Editor")

        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Create header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Add close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda btn: app.quit())
        header.pack_end(close_button)

        # Add page size selector
        page_sizes = Gtk.StringList.new(["A4", "US Letter"])
        self.page_size_dropdown = Gtk.DropDown(model=page_sizes)
        self.page_size_dropdown.set_selected(0)  # Default to A4
        self.page_size_dropdown.connect("notify::selected", self.on_page_size_changed)
        header.pack_start(self.page_size_dropdown)

        # Create scrolled window for WebKit
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)

        # Create WebKit view
        self.web_view = WebKit.WebView()
        self.web_view.set_editable(True)
        scrolled_window.set_child(self.web_view)

        main_box.append(scrolled_window)

        # Set window content
        self.win.set_content(main_box)

        # Load editor HTML
        self.load_editor("a4")

        # Show window
        self.win.present()

    def load_editor(self, page_size):
        css = """
            body {
                margin: 0;
                padding: 20px;
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
                font-size: 12pt;
                line-height: 1.5;
            }
            #editor-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 30px;
            }
            .page {
                width: %s;
                height: %s;
                background-color: white;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
            }
            .page-content {
                width: calc(100%% - 50.8mm);
                height: calc(100%% - 50.8mm);
                margin: 25.4mm;
                overflow: hidden;
                outline: none;
                overflow-wrap: break-word;
            }
            .page:not(:last-child) {
                page-break-after: always;
            }
        """ % ("210mm" if page_size == "a4" else "8.5in",
               "297mm" if page_size == "a4" else "11in")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{css}</style>
        </head>
        <body>
            <div id="editor-container">
                <div class="page">
                    <div class="page-content" contenteditable="true">
                        Type your text here...
                    </div>
                </div>
            </div>
            <script>
                let pageSize = '{page_size}';
                let pageCount = 1;

                document.addEventListener('DOMContentLoaded', () => {
                    const firstPage = document.querySelector('.page-content');
                    firstPage.addEventListener('input', handleInput);
                });

                function handleInput(event) {
                    const content = event.target;
                    if (isOverflowing(content)) {
                        addPage(content);
                    }
                }

                function isOverflowing(element) {
                    return element.scrollHeight > element.clientHeight;
                }

                function addPage(currentContent) {
                    const container = document.getElementById('editor-container');
                    const newPage = document.createElement('div');
                    newPage.className = 'page';
                    const newContent = document.createElement('div');
                    newContent.className = 'page-content';
                    newContent.contentEditable = true;
                    newContent.addEventListener('input', handleInput);
                    newPage.appendChild(newContent);
                    container.appendChild(newPage);
                    pageCount++;

                    // Split content if needed
                    const overflowText = extractOverflow(currentContent);
                    if (overflowText) {
                        newContent.innerHTML = overflowText;
                    }

                    // Focus new page
                    newContent.focus();
                }

                function extractOverflow(content) {
                    const maxHeight = content.clientHeight;
                    const tempDiv = document.createElement('div');
                    tempDiv.style.position = 'absolute';
                    tempDiv.style.visibility = 'hidden';
                    tempDiv.style.width = content.clientWidth + 'px';
                    tempDiv.innerHTML = content.innerHTML;
                    document.body.appendChild(tempDiv);

                    let low = 0;
                    let high = content.innerHTML.length;
                    let splitPos = 0;

                    while (low <= high) {
                        const mid = Math.floor((low + high) / 2);
                        tempDiv.innerHTML = content.innerHTML.substring(0, mid);
                        if (tempDiv.scrollHeight <= maxHeight) {
                            splitPos = mid;
                            low = mid + 1;
                        } else {
                            high = mid - 1;
                        }
                    }

                    const beforeSplit = content.innerHTML.substring(0, splitPos);
                    const afterSplit = content.innerHTML.substring(splitPos);
                    content.innerHTML = beforeSplit;
                    document.body.removeChild(tempDiv);
                    return afterSplit;
                }

                function setPageSize(size) {
                    pageSize = size;
                    const pages = document.querySelectorAll('.page');
                    pages.forEach(page => {
                        page.style.width = size === 'a4' ? '210mm' : '8.5in';
                        page.style.height = size === 'a4' ? '297mm' : '11in';
                    });
                }
            </script>
        </body>
        </html>
        """
        self.web_view.load_html(html, "file:///")

    def on_page_size_changed(self, dropdown, _pspec):
        selected = dropdown.get_selected()
        page_size = "a4" if selected == 0 else "us-letter"
        self.web_view.evaluate_javascript(f"setPageSize('{page_size}')", -1, None, None, None, None)

if __name__ == "__main__":
    Adw.init()
    app = SimplePageEditor()
    app.run()
