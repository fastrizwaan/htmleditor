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
        body {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            overflow-x: hidden;
        }
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            padding: 20px;
        }
        .page {
            width: 10ch;
            height: 2em;
            border: 1px solid #000;
            padding: 10px;
            line-height: 1em;
            overflow: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            position: relative;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            background-color: white;
            user-select: text;
            cursor: text;
        }
        
        .page:focus {
            outline: none;
        }
        
        ::selection {
            background-color: rgba(200, 200, 200, 0.3);
        }
        
        .page[contenteditable=true] {
            caret-color: black;
        }
    </style>
</head>
<body>
    <div id="editor-container" contenteditable="true" spellcheck="false"></div>

    <script>
        let text = '';
        const container = document.getElementById('editor-container');
        
        container.addEventListener('input', (e) => {
            text = Array.from(document.querySelectorAll('.page')).map(p => p.textContent).join('');
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
                        if (prevPage) selectionOffset += prevPage.textContent.length;
                    }
                }
            }
            
            const pages = document.querySelectorAll('.page');
            pages.forEach(page => page.removeEventListener('input', pageInputHandler));
            container.removeEventListener('input', containerInputHandler);
            
            const activeElement = document.activeElement;
            const isFocused = activeElement && activeElement.classList.contains('page');
            
            container.innerHTML = '';
            
            if (text.length === 0) {
                const page = createPage(0);
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
                    let mid = end;
                    let lastGoodFit = 0;
                    
                    testDiv.textContent = remainingText;
                    
                    if (testDiv.scrollHeight <= testDiv.clientHeight && 
                        testDiv.scrollWidth <= testDiv.clientWidth) {
                        lastGoodFit = remainingText.length;
                    } else {
                        while (start < end) {
                            mid = Math.floor((start + end) / 2);
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
                    
                    const page = createPage(pageIndex++);
                    page.textContent = remainingText.substring(0, lastGoodFit);
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

        function createPage(index) {
            const page = document.createElement('div');
            page.className = 'page';
            page.dataset.pageIndex = index;
            page.setAttribute('contenteditable', 'true');
            page.addEventListener('input', pageInputHandler);
            page.addEventListener('mouseup', handleSelectionChange);
            page.addEventListener('keyup', handleSelectionChange);
            return page;
        }

        let isSelecting = false;
        let selectionTimer = null;
        
        function handleSelectionChange(e) {
            if (selectionTimer) clearTimeout(selectionTimer);
            const selection = window.getSelection();
            if (selection.type === 'Range') {
                isSelecting = true;
                selectionTimer = setTimeout(() => {
                    isSelecting = false;
                }, 100);
            }
        }

        function pageInputHandler(e) {
            if (isSelecting) return;
            e.stopPropagation();
            text = Array.from(document.querySelectorAll('.page')).map(p => p.textContent).join('');
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => {
                updatePages();
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }, 100);
        }

        function containerInputHandler(e) {
            if (isSelecting) return;
            text = Array.from(document.querySelectorAll('.page')).map(p => p.textContent).join('');
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => {
                updatePages();
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }, 100);
        }

        let updateTimer = null;

        document.addEventListener('keydown', (e) => {
            // Handle Ctrl+S
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                window.webkit.messageHandlers.saveRequested.postMessage('save');
                return;
            }

            const activeElement = document.activeElement;
            if (!activeElement?.classList?.contains('page')) return;

            const currentIndex = parseInt(activeElement.dataset.pageIndex);
            const pages = document.querySelectorAll('.page');

            // Handle Enter key
            if (e.key === 'Enter') {
                e.preventDefault();
                const selection = window.getSelection();
                if (!selection.rangeCount) return;

                const range = selection.getRangeAt(0);
                const newNode = document.createTextNode('\n');
                range.deleteContents();
                range.insertNode(newNode);

                const newRange = document.createRange();
                newRange.setStart(newNode, 1);
                newRange.collapse(true);
                selection.removeAllRanges();
                selection.addRange(newRange);

                const inputEvent = new Event('input', { bubbles: true });
                container.dispatchEvent(inputEvent);
            }
            // Handle arrow navigation
            else if (e.key === 'ArrowDown') {
                e.preventDefault();
                const nextPage = pages[currentIndex + 1];
                if (nextPage) focusPage(nextPage, 0);
            } 
            else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const prevPage = pages[currentIndex - 1];
                if (prevPage) focusPage(prevPage, prevPage.textContent.length);
            }
        });

        function focusPage(page, offset) {
            page.focus();
            const selection = window.getSelection();
            const range = document.createRange();
            const textNode = page.firstChild || page;
            
            if (textNode.nodeType === 3) {
                range.setStart(textNode, Math.min(offset, textNode.length));
            } else {
                range.setStart(page, 0);
            }
            
            selection.removeAllRanges();
            selection.addRange(range);
        }

        updatePages();
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
    
    # [Rest of the Python code remains identical...]

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
