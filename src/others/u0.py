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
<script type="text/javascript" src="http://code.jquery.com/jquery.min.js"></script>
<style>
    body{ background-color: ivory; }
    .page{border:1px solid red;}
</style>
<script>
$(function(){

    var canvas=document.createElement("canvas");
    var ctx=canvas.getContext("2d");
    ctx.font="14px verdana";

    var pageWidth=250;
    var pageHeight=150;
    var pagePaddingLeft=10;
    var pagePaddingRight=10;
    var approxWordsPerPage=500;        
    var lineHeight=18;
    var maxLinesPerPage=parseInt(pageHeight/lineHeight)-1;
    var x=pagePaddingLeft;
    var y=lineHeight;
    var maxWidth=pageWidth-pagePaddingLeft-pagePaddingRight;
    var text="Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.";

    // # words that have been displayed 
    //(used when ordering a new page of words)
    var wordCount=0;

    // size the div to the desired page size
    $pages=$(".page");
    $pages.width(pageWidth)
    $pages.height(pageHeight);


    // Test: Page#1

    // get a reference to the page div
    var $page=$("#page");
    // use html canvas to word-wrap this page
    var lines=textToLines(getNextWords(wordCount),maxWidth,maxLinesPerPage,x,y);
    // create svg elements for each line of text on the page
    drawSvg(lines,x);

    // Test: Page#2 (just testing...normally there's only 1 full-screen page)
    var $page=$("#page2");
    var lines=textToLines(getNextWords(wordCount),maxWidth,maxLinesPerPage,x,y);
    drawSvg(lines,x);

    // Test: Page#3 (just testing...normally there's only 1 full-screen page)
    var $page=$("#page3");
    var lines=textToLines(getNextWords(wordCount),maxWidth,maxLinesPerPage,x,y);
    drawSvg(lines,x);


    // fetch the next page of words from the server database
    // (since we've specified the starting point in the entire text
    //  we only have to download 1 page of text as needed
    function getNextWords(nextWordIndex){
        // Eg: select top 500 word from romeoAndJuliet 
        //     where wordIndex>=nextwordIndex
        //     order by wordIndex
        //
        // But here for testing, we just hardcode the entire text 
        var testingText="Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.";
        var testingWords=testingText.split(" ");
        var words=testingWords.splice(nextWordIndex,approxWordsPerPage);

        // 
        return(words);    
    }


    function textToLines(words,maxWidth,maxLines,x,y){

        var lines=[];

        while(words.length>0 && lines.length<=maxLines){
            var line=getLineOfText(words,maxWidth);
            words=words.splice(line.index+1);
            lines.push(line);
            wordCount+=line.index+1;
        }

        return(lines);
    }

    function getLineOfText(words,maxWidth){
        var line="";
        var space="";
        for(var i=0;i<words.length;i++){
            var testWidth=ctx.measureText(line+" "+words[i]).width;
            if(testWidth>maxWidth){return({index:i-1,text:line});}
            line+=space+words[i];
            space=" ";
        }
        return({index:words.length-1,text:line});
    }

    function drawSvg(lines,x){
        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        var sText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        sText.setAttributeNS(null, 'font-family', 'verdana');
        sText.setAttributeNS(null, 'font-size', "14px");
        sText.setAttributeNS(null, 'fill', '#000000');
        for(var i=0;i<lines.length;i++){
            var sTSpan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            sTSpan.setAttributeNS(null, 'x', x);
            sTSpan.setAttributeNS(null, 'dy', lineHeight+"px");
            sTSpan.appendChild(document.createTextNode(lines[i].text));
            sText.appendChild(sTSpan);
        }
        svg.appendChild(sText);
        $page.append(svg);
    }

}); // end $(function(){});
</script>
</head>
<body>
    <h4>Text split into "pages"<br>(Selectable & Searchable)</h4>
    <div id="page" class="page"></div>
    <h4>Page 2</h4>
    <div id="page2" class="page"></div>
    <h4>Page 3</h4>
    <div id="page3" class="page"></div>
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
        dialog.set_current_name("document.html")
        
        # Set up filters
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
            self.webview.evaluate_javascript("getContentAsHtml();", -1, None, None, None, None, self.save_html_callback, file_path)
        
        dialog.destroy()
    
    def save_html_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                html_content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    f.write(html_content)
                
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
