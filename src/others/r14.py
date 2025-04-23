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
    <meta charset="UTF-8">
    <title>Paginated Editor</title>
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; overflow-x: hidden; }
        #editor-container { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 20px; }
        .page {
            width: 10ch; height: 2em; border: 1px solid #000; padding: 10px; line-height: 1em;
            overflow: hidden; white-space: pre-wrap; word-wrap: break-word; position: relative;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2); background-color: white;
            user-select: text; cursor: text; display: block !important;
        }
        .page:focus { outline: none; }
        ::selection { background-color: rgba(200,200,200,0.3); }
        .page[contenteditable=true] { caret-color: black; }
    </style>
</head>
<body>
    <div id="editor-container" contenteditable="false" spellcheck="false"></div>
    <script>
        let text = '';
        const container = document.getElementById('editor-container');
        let updateTimer = null;

        function updatePages() {
            if (window.getSelection().type === 'Range') return;

            const sel = window.getSelection();
            const range = sel.rangeCount ? sel.getRangeAt(0) : null;
            let selOffset = 0, selPage = 0;
            if (range) {
                let node = range.startContainer;
                const pageEl = (node.nodeType === 3 ? node.parentElement : node).closest('.page');
                if (pageEl) {
                    selPage = +pageEl.dataset.pageIndex;
                    for (let i = 0; i < selPage; i++) {
                        selOffset += document.querySelector(`.page[data-page-index="${i}"]`).textContent.length;
                    }
                    if (node.nodeType === 3) selOffset += range.startOffset;
                    else {
                        const walker = document.createTreeWalker(pageEl, NodeFilter.SHOW_TEXT, null, false);
                        let tn, off = 0;
                        while ((tn = walker.nextNode())) {
                            if (tn === node) { off += range.startOffset; break; }
                            off += tn.length;
                        }
                        selOffset += off;
                    }
                }
            }

            document.querySelectorAll('.page').forEach(p => {
                p.removeEventListener('input', pageInputHandler);
                p.removeEventListener('keydown', keyDownHandler);
            });
            const focused = document.activeElement.classList.contains('page');
            container.innerHTML = '';

            if (!text) text = '';
            const testDiv = document.createElement('div');
            testDiv.className = 'page';
            testDiv.style.visibility = 'hidden'; testDiv.style.position = 'absolute';
            document.body.appendChild(testDiv);

            let idx = 0, rem = text;
            while (rem.length || idx === 0) {
                if (!rem.length) {
                    const p = document.createElement('div');
                    p.className = 'page'; p.textContent = '';
                    p.dataset.pageIndex = idx; p.contentEditable = true;
                    p.addEventListener('input', pageInputHandler);
                    p.addEventListener('keydown', keyDownHandler);
                    container.appendChild(p);
                    break;
                }
                let lo = 0, hi = rem.length, fit = 0;
                testDiv.textContent = rem;
                if (testDiv.scrollHeight <= testDiv.clientHeight && testDiv.scrollWidth <= testDiv.clientWidth) {
                    fit = rem.length;
                } else {
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

            // restore selection
            if (sel) {
                let off = selOffset, newIdx = 0;
                const pages = [...document.querySelectorAll('.page')];
                while (newIdx < pages.length && off > pages[newIdx].textContent.length) {
                    off -= pages[newIdx].textContent.length; newIdx++;
                }
                if (pages[newIdx]) {
                    const p = pages[newIdx];
                    const r = document.createRange();
                    const tn = p.firstChild || p;
                    r.setStart(tn, Math.min(off, tn.textContent.length));
                    r.collapse(true);
                    sel.removeAllRanges(); sel.addRange(r);
                    p.focus();
                }
            } else if (focused) {
                setTimeout(() => container.querySelector('.page').focus(), 0);
            }

            window.webkit.messageHandlers.contentChanged.postMessage(text);
        }

        function pageInputHandler() {
            text = [...document.querySelectorAll('.page')].map(p => p.textContent).join('');
            clearTimeout(updateTimer);
            updateTimer = setTimeout(updatePages, 100);
        }

        function keyDownHandler(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.execCommand('insertLineBreak');
                pageInputHandler();
                return false;
            }
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                const cur = e.target; const i = +cur.dataset.pageIndex;
                const pages = document.querySelectorAll('.page');
                const ni = e.key === 'ArrowDown' ? i+1 : i-1;
                if (pages[ni]) {
                    pages[ni].focus();
                    const sel = window.getSelection();
                    const r = document.createRange();
                    const tn = pages[ni].firstChild || pages[ni];
                    const pos = e.key === 'ArrowDown' ? 0 : tn.textContent.length;
                    r.setStart(tn, pos); r.collapse(true);
                    sel.removeAllRanges(); sel.addRange(r);
                }
            }
        }

        function initEditor() {
            const p = document.createElement('div');
            p.className = 'page'; p.dataset.pageIndex = 0; p.contentEditable = true;
            p.addEventListener('input', pageInputHandler);
            p.addEventListener('keydown', keyDownHandler);
            container.appendChild(p); p.focus();
        }

        initEditor();

        window.getContentAsHtml = () => {
            const pages = [...document.querySelectorAll('.page')];
            let h = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Saved</title>'+
                    '<style>body{margin:20px;font-family:sans-serif;}.page{width:10ch;height:2em;'+
                    'border:1px solid #000;padding:10px;line-height:1em;overflow:hidden;'+
                    'white-space:pre-wrap;word-wrap:break-word;margin-bottom:20px;page-break-after:always;}'+
                    '</style></head><body>';
            pages.forEach(p => { h += `<div class="page">${p.textContent}</div>`; });
            return h + '</body></html>';
        };

        window.webkit = window.webkit || { messageHandlers: {} };
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
        dialog = Gtk.FileChooserDialog(
            title="Save Document", parent=self.win, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.ACCEPT)
        dialog.set_current_name("document.html")
        filt = Gtk.FileFilter(); filt.set_name("HTML files"); filt.add_mime_type("text/html"); dialog.add_filter(filt)
        filt2 = Gtk.FileFilter(); filt2.set_name("Text files"); filt2.add_mime_type("text/plain"); dialog.add_filter(filt2)
        filt3 = Gtk.FileFilter(); filt3.set_name("All files"); filt3.add_pattern("*"); dialog.add_filter(filt3)
        dialog.connect("response", self.on_save_dialog_response)
        dialog.present()

    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            path = dialog.get_file().get_path()
            self.webview.run_javascript("window.getContentAsHtml()", None, self.save_html_callback, path)
        dialog.destroy()

    def save_html_callback(self, webview, result, user_data):
        path = user_data
        try:
            js_result = webview.run_javascript_finish(result)
            content = js_result.get_js_value().to_string()
            with open(path, 'w') as f:
                f.write(content)
            print("Document saved successfully")
            self.content_changed = False
        except Exception as e:
            print(f"Error saving document: {e}")

    def do_shutdown(self):
        if os.path.isdir(self.tempdir):
            for fn in os.listdir(self.tempdir): os.unlink(os.path.join(self.tempdir, fn))
            os.rmdir(self.tempdir)
        super().do_shutdown()

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)

