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
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Paginated Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            overflow-x: hidden;
            background-color: #f5f5f5;
        }
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 30px;
            padding: 30px;
        }
        .page {
            width: 500px;
            min-height: 200px;
            max-height: 300px;
            border: 1px solid #ccc;
            padding: 15px;
            line-height: 1.5;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            background-color: white;
            user-select: text;
            cursor: text;
            margin: 10px 0;
            position: relative;
        }
        .page:focus {
            outline: 2px solid #007bff;
            outline-offset: 2px;
        }
        ::selection {
            background-color: rgba(0, 123, 255, 0.3);
        }
        .page[contenteditable=true] {
            caret-color: black;
        }
        .page-number {
            position: absolute;
            bottom: 5px;
            right: 5px;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div id="editor-container" contenteditable="true" spellcheck="false"></div>

    <script>
        let text = '';
        const container = document.getElementById('editor-container');
        
        container.addEventListener('input', (e) => {
            text = '';
            document.querySelectorAll('.page').forEach(page => {
                text += page.textContent + '\\n';
            });
            updatePages();
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        });

        function updatePages() {
            if (window.getSelection().type === 'Range') return;
            
            const selection = window.getSelection();
            const range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
            let selectionPageIndex = -1;
            let selectionOffset = 0;
            
            if (range && range.startContainer) {
                const node = range.startContainer;
                const pageElement = node.nodeType === 3 ? 
                    node.parentElement.closest('.page') : 
                    node.closest('.page');
                
                if (pageElement) {
                    selectionPageIndex = parseInt(pageElement.dataset.pageIndex);
                    selectionOffset = range.startOffset;
                    
                    for (let i = 0; i < selectionPageIndex; i++) {
                        const prevPage = document.querySelector(`.page[data-page-index="${i}"]`);
                        if (prevPage) {
                            selectionOffset += prevPage.textContent.length + 1;
                        }
                    }
                }
            }
            
            const pages = document.querySelectorAll('.page');
            pages.forEach(page => page.removeEventListener('input', pageInputHandler));
            container.removeEventListener('input', containerInputHandler);
            
            const activeElement = document.activeElement;
            const isFocused = activeElement && activeElement.classList && activeElement.classList.contains('page');
            
            container.innerHTML = '';
            
            if (text.length === 0) {
                const page = createPage(0, '');
                container.appendChild(page);
            } else {
                const testDiv = document.createElement('div');
                testDiv.className = 'page';
                testDiv.style.visibility = 'hidden';
                testDiv.style.position = 'absolute';
                document.body.appendChild(testDiv);
                
                let pageIndex = 0;
                let remainingText = text;
                
                while (remainingText.length > 0) {
                    let start = 0;
                    let end = remainingText.length;
                    let lastGoodFit = 0;
                    
                    testDiv.textContent = remainingText;
                    if (testDiv.scrollHeight <= testDiv.clientHeight && 
                        testDiv.scrollWidth <= testDiv.clientWidth) {
                        lastGoodFit = remainingText.length;
                    } else {
                        while (start < end) {
                            const mid = Math.floor((start + end) / 2);
                            testDiv.textContent = remainingText.substring(0, mid);
                            
                            if (testDiv.scrollHeight <= testDiv.clientHeight && 
                                testDiv.scrollWidth <= testDiv.clientWidth) {
                                lastGoodFit = mid;
                                start = mid + 1;
                            } else {
                                end = mid;
                            }
                        }
                        if (lastGoodFit === 0 && remainingText.length > 0) {
                            lastGoodFit = 1;
                        }
                    }
                    
                    const pageText = remainingText.substring(0, lastGoodFit);
                    const page = createPage(pageIndex++, pageText);
                    container.appendChild(page);
                    remainingText = remainingText.substring(lastGoodFit);
                }
                
                document.body.removeChild(testDiv);
            }
            
            if (selectionPageIndex !== -1 && selectionOffset >= 0) {
                try {
                    let remainingOffset = selectionOffset;
                    let newPageIndex = 0;
                    const allPages = document.querySelectorAll('.page');
                    while (newPageIndex < allPages.length) {
                        const pageLength = allPages[newPageIndex].textContent.length;
                        if (remainingOffset <= pageLength) break;
                        remainingOffset -= pageLength;
                        newPageIndex++;
                    }
                    
                    if (newPageIndex < allPages.length) {
                        const page = allPages[newPageIndex];
                        const textNode = page.firstChild;
                        const newRange = document.createRange();
                        
                        if (textNode) {
                            const actualOffset = Math.min(remainingOffset, textNode.textContent.length);
                            newRange.setStart(textNode, actualOffset);
                        } else {
                            newRange.setStart(page, 0);
                        }
                        
                        setTimeout(() => {
                            selection.removeAllRanges();
                            selection.addRange(newRange);
                            page.focus();
                        }, 0);
                    }
                } catch (e) {
                    console.error('Error restoring selection:', e);
                }
            } else if (isFocused) {
                setTimeout(() => {
                    const firstPage = document.querySelector('.page');
                    if (firstPage) firstPage.focus();
                }, 0);
            }
            
            container.addEventListener('input', containerInputHandler);
        }
        
        function createPage(index, content) {
            const page = document.createElement('div');
            page.className = 'page';
            page.textContent = content;
            page.dataset.pageIndex = index;
            page.setAttribute('contenteditable', 'true');
            
            const pageNumber = document.createElement('div');
            pageNumber.className = 'page-number';
            pageNumber.textContent = `Page ${index + 1}`;
            page.appendChild(pageNumber);
            
            page.addEventListener('input', pageInputHandler);
            page.addEventListener('mouseup', handleSelectionChange);
            page.addEventListener('keyup', handleSelectionChange);
            page.addEventListener('keydown', handleKeyDown);
            
            return page;
        }
        
        let isSelecting = false;
        let selectionTimer = null;
        
        function handleSelectionChange(e) {
            if (selectionTimer) clearTimeout(selectionTimer);
            const selection = window.getSelection();
            if (selection.type === 'Range') {
                isSelecting = true;
                selectionTimer = setTimeout(() => isSelecting = false, 100);
            }
        }
        
        function handleKeyDown(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const page = e.target;
                const selection = window.getSelection();
                const range = selection.getRangeAt(0);
                const offset = range.startOffset;
                
                const beforeText = page.textContent.substring(0, offset);
                const afterText = page.textContent.substring(offset);
                
                page.textContent = beforeText + '\n' + afterText;
                
                text = '';
                document.querySelectorAll('.page').forEach(p => text += p.textContent + '\n');
                
                updatePages();
                
                const newRange = document.createRange();
                newRange.setStart(page.firstChild, offset + 1);
                selection.removeAllRanges();
                selection.addRange(newRange);
                
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }
        }
        
        function pageInputHandler(e) {
            if (isSelecting) return;
            e.stopPropagation();
            
            let fullText = '';
            document.querySelectorAll('.page').forEach(p => fullText += p.textContent + '\n');
            text = fullText;
            
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => {
                updatePages();
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }, 100);
        }
        
        function containerInputHandler(e) {
            if (isSelecting) return;
            text = '';
            document.querySelectorAll('.page').forEach(page => text += page.textContent + '\n');
            
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => {
                updatePages();
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }, 100);
        }
        
        let updateTimer = null;
        container.addEventListener('input', containerInputHandler);
        document.addEventListener('selectionchange', handleSelectionChange);
        
        updatePages();
        
        function getContentAsHtml() {
            const pages = document.querySelectorAll('.page');
            let html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Saved Document</title>';
            html += '<style>body{margin:20px;font-family:sans-serif;}.page{width:500px;min-height:200px;border:1px solid #ccc;';
            html += 'padding:15px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word;margin-bottom:30px;';
            html += 'page-break-after:always;}</style></head><body>';
            
            html += '<div class="container">';
            pages.forEach(page => {
                html += `<div class="page">${page.textContent}</div>`;
            });
            html += '</div></body></html>';
            return html;
        }
        
        function getContentAsText() {
            return text;
        }
        
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                window.webkit.messageHandlers.saveRequested.postMessage('save');
                return;
            }
            
            const activeElement = document.activeElement;
            if (!activeElement || !activeElement.classList.contains('page')) return;
            
            const currentPage = activeElement;
            const currentIndex = parseInt(currentPage.dataset.pageIndex);
            const pages = document.querySelectorAll('.page');
            
            if (e.key === 'ArrowDown') {
                const nextIndex = currentIndex + 1;
                if (nextIndex < pages.length) {
                    e.preventDefault();
                    pages[nextIndex].focus();
                    const selection = window.getSelection();
                    const range = document.createRange();
                    range.setStart(pages[nextIndex].firstChild || pages[nextIndex], 0);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            } else if (e.key === 'ArrowUp') {
                const prevIndex = currentIndex - 1;
                if (prevIndex >= 0) {
                    e.preventDefault();
                    pages[prevIndex].focus();
                    const selection = window.getSelection();
                    const range = document.createRange();
                    const textNode = pages[prevIndex].firstChild;
                    if (textNode) {
                        range.setStart(textNode, textNode.textContent.length);
                    } else {
                        range.setStart(pages[prevIndex], 0);
                    }
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }
        });
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            user_content_manager = self.webview.get_user_content_manager()
            content_changed_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "contentChanged")
            if content_changed_handler:
                user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            save_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "saveRequested")
            if save_handler:
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
            file_path = dialog.get_file().get_path()
            self.webview.evaluate_javascript("getContentAsHtml();", -1, None, None, None, None, self.save_html_callback, file_path)
        dialog.destroy()
    
    def save_html_callback(self, result, user_data):
        file_path = user_data
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
        toast.set_timeout(3)
        print(message)
    
    def do_shutdown(self):
        if os.path.exists(self.tempdir):
            for file in os.listdir(self.tempdir):
                os.unlink(os.path.join(self.tempdir, file))
            os.rmdir(self.tempdir)
        Adw.Application.do_shutdown(self)

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
