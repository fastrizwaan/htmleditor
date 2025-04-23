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

    def create_editor_html(self):
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>Paginated Editor</title>
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; overflow-x: hidden; }
        #editor-container { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 20px; }
        .page {
            width: 10ch; height: 2em; border: 1px solid #000; padding: 10px; line-height: 1em;
            overflow: hidden; white-space: pre-wrap; word-wrap: break-word;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2); background-color: white;
            user-select: text; cursor: text; display: block !important;
        }
        .page:focus { outline: none; }
        ::selection { background-color: rgba(200,200,200,0.3); }
    </style>
</head>
<body>
    <div id=\"editor-container\" contenteditable=\"true\" spellcheck=\"false\"></div>
    <script>
        let text = '';
        const container = document.getElementById('editor-container');
        let updateTimer = null;

        function updatePages() {
            if (window.getSelection().type === 'Range') return;
            const sel = window.getSelection();
            const range = sel.rangeCount ? sel.getRangeAt(0) : null;
            let selOffset = 0;
            if (range) {
                let node = range.startContainer;
                const pageEl = (node.nodeType === 3 ? node.parentElement : node).closest('.page');
                if (pageEl) {
                    const pageIndex = +pageEl.dataset.pageIndex;
                    for (let i = 0; i < pageIndex; i++) {
                        selOffset += document.querySelector(`.page[data-page-index=\"${i}\"]`).textContent.length;
                    }
                    selOffset += range.startOffset;
                }
            }

            document.querySelectorAll('.page').forEach(p => {
                p.removeEventListener('input', pageInputHandler);
                p.removeEventListener('keydown', keyDownHandler);
            });
            container.innerHTML = '';

            const testDiv = document.createElement('div');
            testDiv.className = 'page'; testDiv.style.visibility = 'hidden'; testDiv.style.position = 'absolute';
            document.body.appendChild(testDiv);

            let idx = 0, rem = text;
            while (rem.length || idx === 0) {
                let fit = 0;
                testDiv.textContent = rem;
                if (testDiv.scrollHeight <= testDiv.clientHeight && testDiv.scrollWidth <= testDiv.clientWidth) {
                    fit = rem.length;
                } else {
                    let lo = 0, hi = rem.length;
                    while (lo < hi) {
                        const mid = (lo + hi) >> 1;
                        testDiv.textContent = rem.slice(0, mid);
                        if (testDiv.scrollHeight <= testDiv.clientHeight && testDiv.scrollWidth <= testDiv.clientWidth) {
                            fit = mid; lo = mid + 1;
                        } else hi = mid;
                    }
                    if (!fit) fit = 1;
                }
                const p = document.createElement('div');
                p.className = 'page'; p.textContent = rem.slice(0, fit);
                p.dataset.pageIndex = idx; p.contentEditable = true;
                p.addEventListener('input', pageInputHandler);
                p.addEventListener('keydown', keyDownHandler);
                container.appendChild(p);
                rem = rem.slice(fit); idx++;
            }
            document.body.removeChild(testDiv);

            if (range) {
                let off = selOffset, newIndex = 0;
                const pages = document.querySelectorAll('.page');
                while (newIndex < pages.length && off > pages[newIndex].textContent.length) {
                    off -= pages[newIndex].textContent.length; newIndex++;
                }
                if (pages[newIndex]) {
                    const p = pages[newIndex];
                    const r = document.createRange();
                    const tn = p.firstChild || p;
                    r.setStart(tn, Math.min(off, tn.textContent.length)); r.collapse(true);
                    sel.removeAllRanges(); sel.addRange(r);
                    p.focus();
                }
            }
            window.webkit.messageHandlers.contentChanged.postMessage(text);
        }

        function pageInputHandler() {
            text = Array.from(document.querySelectorAll('.page')).map(p => p.textContent).join('');
            clearTimeout(updateTimer); updateTimer = setTimeout(updatePages, 100);
        }

        function keyDownHandler(e) {
            if (e.ctrlKey && e.key.toLowerCase() === 'a') {
                e.preventDefault(); const sel = window.getSelection(); const range = document.createRange();
                range.selectNodeContents(container); sel.removeAllRanges(); sel.addRange(range); return false;
            }
            if (e.key === 'Enter') {
                e.preventDefault(); document.execCommand('insertLineBreak'); const p = e.target;
                setTimeout(() => {
                    const sel = window.getSelection(); const tn = p.lastChild || p;
                    const offset = tn.nodeType === Node.TEXT_NODE ? tn.textContent.length : p.childNodes.length;
                    const r = document.createRange(); r.setStart(tn, offset); r.collapse(true);
                    sel.removeAllRanges(); sel.addRange(r); p.focus();
                }, 0);
                pageInputHandler(); return false;
            }
        }

        function initEditor() {
            const p = document.createElement('div'); p.className = 'page'; p.dataset.pageIndex = 0; p.contentEditable = true;
            p.addEventListener('input', pageInputHandler); p.addEventListener('keydown', keyDownHandler);
            container.appendChild(p); p.focus();
        }
        initEditor();

        window.getContentAsHtml = () => {
            const pages = document.querySelectorAll('.page');
            let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Saved</title>' +
                       '<style>.page{width:10ch;height:2em;border:1px solid #000;padding:10px;white-space:pre-wrap;word-wrap:break-word;margin-bottom:20px;page-break-after:always;}</style></head><body>';
            pages.forEach(p => html += `<div class=\"page\">${p.textContent}</div>`);
            return html + '</body></html>';
        };
    </script>
</body>
</html>"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)

    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            ucm = self.webview.get_user_content_manager()
            ucm.register_script_message_handler("contentChanged")
            ucm.connect("script-message-received::contentChanged", self.on_content_changed)
            ucm.register_script_message_handler("saveRequested")
            ucm.connect("script-message-received::saveRequested", self.on_save_requested)

    def on_content_changed(self, manager, message):
        self.content_changed = True

    def on_save_requested(self, manager, message):
        self.on_save_clicked(None)

    def on_save_clicked(self, button):
        dialog = Gtk.FileChooserDialog(title="Save Document", parent=self.win, action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.ACCEPT)
        dialog.set_current_name("document.html")
        filt = Gtk.FileFilter(); filt.set_name("HTML files"); filt.add_mime_type("text/html"); dialog.add_filter(filt)
        filt2 = Gtk
if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
