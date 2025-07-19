#!/usr/bin/env python3
"""
Editor Components
Markdown editor and preview with perfect bidirectional sync
"""

import os
import re
from typing import List
import os
import re
from typing import List
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
import markdown
from markdown.extensions import codehilite, tables, toc, fenced_code, meta


class MarkdownSyntaxHighlighter(QSyntaxHighlighter):
    """Enhanced syntax highlighter with fixed regex patterns"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Define colors for dark theme
        self.colors = {
            'header': QColor('#4fc3f7'),
            'bold': QColor('#ffcc80'),
            'italic': QColor('#c8e6c9'),
            'code': QColor('#f8bbd9'),
            'link': QColor('#81c784'),
            'quote': QColor('#bcaaa4'),
            'list': QColor('#ffab91'),
            'frontmatter': QColor('#ce93d8'),
        }
        
        # Front matter (YAML between ---)
        frontmatter_format = QTextCharFormat()
        frontmatter_format.setForeground(self.colors['frontmatter'])
        frontmatter_format.setBackground(QColor('#2d1b69'))
        self.highlighting_rules.append((QRegularExpression(r'^---.*'), frontmatter_format))
        
        # Enhanced syntax highlighting with H4-H6 support
        self.highlighting_rules.append((QRegularExpression(r'^#{1,6}\s.*'), header_format))
        
        # Bold text (**text**)
        bold_format = QTextCharFormat()
        bold_format.setForeground(self.colors['bold'])
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\*\*[^*]+\*\*'), bold_format))
        
        # Italic text (*text*)
        italic_format = QTextCharFormat()
        italic_format.setForeground(self.colors['italic'])
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r'\*[^*]+\*'), italic_format))
        
        # Inline code (`code`)
        code_format = QTextCharFormat()
        code_format.setForeground(self.colors['code'])
        code_format.setFontFamilies(['Cascadia Code', 'Consolas', 'monospace'])
        self.highlighting_rules.append((QRegularExpression(r'`[^`]+`'), code_format))
        
        # Links [text](url) - FIXED REGEX
        link_format = QTextCharFormat()
        link_format.setForeground(self.colors['link'])
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((QRegularExpression(r'\[[^\]]+\]\([^)]+\)'), link_format))
        
        # Blockquotes (>)
        quote_format = QTextCharFormat()
        quote_format.setForeground(self.colors['quote'])
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r'^>\s.*'), quote_format))
        
        # Lists (- * +)
        list_format = QTextCharFormat()
        list_format.setForeground(self.colors['list'])
        self.highlighting_rules.append((QRegularExpression(r'^\s*[-*+]\s.*'), list_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern
            if expression.isValid():  # Check if regex is valid
                iterator = expression.globalMatch(text)
                while iterator.hasNext():
                    match = iterator.next()
                    self.setFormat(match.capturedStart(), match.capturedLength(), format)


class MarkdownEditor(QTextEdit):
    """Enhanced text editor with improved cursor handling"""
    content_changed = Signal()
    cursor_position_changed = Signal(int)  # line number
    scroll_changed = Signal(float)  # scroll ratio
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.is_syncing = False  # Prevent recursive sync
        self.last_cursor_position = 0
        
    def setup_editor(self):
        # Improved font handling to reduce warnings
        available_fonts = QFontDatabase.families()
        
        # Preferred fonts in order
        preferred_fonts = [
            "Cascadia Code",
            "Fira Code", 
            "Consolas",
            "Courier New",
            "DejaVu Sans Mono",
            "Liberation Mono",
            "monospace"
        ]
        
        selected_font = None
        for font_name in preferred_fonts:
            if font_name in available_fonts or font_name == "monospace":
                selected_font = QFont(font_name, 14)
                selected_font.setStyleHint(QFont.Monospace)
                selected_font.setFixedPitch(True)
                break
        
        # Fallback
        if selected_font is None:
            selected_font = QFont()
            selected_font.setFamily("monospace")
            selected_font.setPointSize(14)
            selected_font.setStyleHint(QFont.Monospace)
            selected_font.setFixedPitch(True)
        
        self.setFont(selected_font)
        
        # Apply syntax highlighting
        self.highlighter = MarkdownSyntaxHighlighter(self.document())
        
        # Enable line wrap
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Set tab stop width (4 spaces)
        fm = QFontMetrics(selected_font)
        self.setTabStopDistance(fm.horizontalAdvance(' ') * 4)
        
        # Connect signals with improved timing
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        
        # Connect scroll events with throttling
        scrollbar = self.verticalScrollBar()
        scrollbar.valueChanged.connect(self.on_scroll_changed_throttled)
        
        # Setup scroll throttling
        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self.emit_scroll_change)
        self._last_scroll_ratio = 0.0
    
    def on_scroll_changed_throttled(self):
        """Throttled scroll change handler for smoother performance"""
        if not self.is_syncing:
            # Cancel previous timer
            self._scroll_timer.stop()
            
            # Store current ratio
            self._last_scroll_ratio = self.get_scroll_ratio()
            
            # Start timer with very short delay for fluid scrolling
            self._scroll_timer.start(16)  # ~60fps timing
    
    def emit_scroll_change(self):
        """Emit scroll change after throttling"""
        if not self.is_syncing:
            self.scroll_changed.emit(self._last_scroll_ratio)
    
    def on_text_changed(self):
        if not self.is_syncing:
            self.content_changed.emit()
    
    def on_cursor_position_changed(self):
        if not self.is_syncing:
            cursor = self.textCursor()
            line_number = cursor.blockNumber()
            self.cursor_position_changed.emit(line_number)
    
    def on_scroll_changed(self):
        # This method is now handled by throttled version
        pass
    
    def goto_line(self, line_number: int):
        """Jump to specific line number - FIXED"""
        self.is_syncing = True
        try:
            # Get the document
            doc = self.document()
            if line_number < doc.blockCount():
                # Get the block at the line number
                block = doc.findBlockByLineNumber(line_number)
                if block.isValid():
                    # Create cursor and move to block
                    cursor = QTextCursor(block)
                    self.setTextCursor(cursor)
                    # Scroll to make line visible
                    self.ensureCursorVisible()
        finally:
            self.is_syncing = False
    
    def sync_scroll_position(self, ratio: float):
        """Sync scroll position based on ratio (0.0 to 1.0)"""
        if self.is_syncing:
            return
        
        self.is_syncing = True
        try:
            scrollbar = self.verticalScrollBar()
            max_value = scrollbar.maximum()
            new_value = int(ratio * max_value)
            scrollbar.setValue(new_value)
        finally:
            self.is_syncing = False
    
    def get_scroll_ratio(self) -> float:
        """Get current scroll position as ratio"""
        scrollbar = self.verticalScrollBar()
        if scrollbar.maximum() == 0:
            return 0.0
        return scrollbar.value() / scrollbar.maximum()
    
    def set_content_silently(self, content: str):
        """Set content without triggering change signals"""
        self.is_syncing = True
        try:
            # Save cursor position
            cursor = self.textCursor()
            position = cursor.position()
            
            # Set content
            self.setPlainText(content)
            
            # Restore cursor position if possible
            new_cursor = self.textCursor()
            if position <= len(content):
                new_cursor.setPosition(position)
                self.setTextCursor(new_cursor)
        finally:
            self.is_syncing = False
    
    def insert_markdown(self, prefix: str, suffix: str = ""):
        """Insert markdown formatting around selected text"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            cursor.insertText(f"{prefix}text{suffix}")
            # Select "text" for replacement
            for _ in range(len(suffix) + 4):
                cursor.movePosition(QTextCursor.Left)
            for _ in range(4):
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
    
    def insert_header(self, level: int):
        """Insert header at current line"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        current_line = cursor.block().text()
        
        # Remove existing header markers
        clean_line = re.sub(r'^#+\s*', '', current_line)
        
        # Insert new header
        header_text = f"{'#' * level} {clean_line}" if clean_line else f"{'#' * level} Header {level}"
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.insertText(header_text)
    
    def insert_table(self):
        """Insert a table template"""
        table_template = """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
"""
        cursor = self.textCursor()
        cursor.insertText(table_template)
    
    def insert_link(self):
        """Insert link template"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"[{selected_text}](url)")
        else:
            cursor.insertText("[link text](url)")
    
    def insert_image(self):
        """Insert image template or open file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", 
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp *.svg);;All files (*)"
        )
        
        if file_path:
            # Convert to relative path if possible
            try:
                rel_path = os.path.relpath(file_path)
                cursor = self.textCursor()
                cursor.insertText(f"![Image]({rel_path})")
            except ValueError:
                cursor = self.textCursor()
                cursor.insertText(f"![Image]({file_path})")
        else:
            cursor = self.textCursor()
            cursor.insertText("![alt text](image_url)")


class PreviewBridge(QObject):
    """Improved bridge for seamless communication"""
    scroll_changed = Signal(float)
    content_changed = Signal(str)
    cursor_position_changed = Signal(int)
    
    @Slot(float)
    def on_scroll_changed(self, ratio):
        self.scroll_changed.emit(ratio)
    
    @Slot(str)
    def on_content_changed(self, content):
        self.content_changed.emit(content)
    
    @Slot(int)
    def on_cursor_changed(self, line):
        self.cursor_position_changed.emit(line)


class MarkdownPreview(QWebEngineView):
    """Improved preview with better bidirectional editing"""
    scroll_sync_requested = Signal(float)
    content_edited = Signal(str)
    cursor_sync_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.markdown_processor = markdown.Markdown(
            extensions=['codehilite', 'tables', 'toc', 'fenced_code', 'nl2br', 'meta'],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                }
            }
        )
        
        # Web channel for bidirectional communication
        self.channel = QWebChannel()
        self.page().setWebChannel(self.channel)
        
        # JavaScript bridge
        self.bridge = PreviewBridge()
        self.channel.registerObject("bridge", self.bridge)
        
        # Connect bridge signals
        self.bridge.scroll_changed.connect(self.scroll_sync_requested.emit)
        self.bridge.content_changed.connect(self.on_content_edited)
        self.bridge.cursor_position_changed.connect(self.cursor_sync_requested.emit)
        
        # Track content to prevent unnecessary updates
        self.last_markdown_content = ""
        self.is_updating = False
        
        # Set initial content
        self.update_preview("")
    
    def on_content_edited(self, html_content: str):
        """Handle content edited in preview - convert back to markdown"""
        if self.is_updating:
            return
        
        # Simple HTML to Markdown conversion
        markdown_content = self.html_to_markdown(html_content)
        
        # Only emit if content actually changed
        if markdown_content != self.last_markdown_content:
            self.last_markdown_content = markdown_content
            self.content_edited.emit(markdown_content)
    
    def html_to_markdown(self, html: str) -> str:
        """Convert HTML back to Markdown - improved conversion"""
        import re
        
        # Clean up HTML
        text = html.strip()
        
        # Convert headers
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert formatting
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert links
        text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert images
        text = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', text, flags=re.IGNORECASE)
        text = re.sub(r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![\1](\2)', text, flags=re.IGNORECASE)
        
        # Convert paragraphs
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert line breaks
        text = re.sub(r'<br[^>]*/?>', r'\n', text, flags=re.IGNORECASE)
        
        # Convert lists
        text = re.sub(r'<ul[^>]*>(.*?)</ul>', lambda m: self.convert_list(m.group(1), False), text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<ol[^>]*>(.*?)</ol>', lambda m: self.convert_list(m.group(1), True), text, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert blockquotes
        text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '\n'.join(f'> {line}' for line in m.group(1).strip().split('\n')), text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def convert_list(self, list_content: str, ordered: bool) -> str:
        """Convert HTML list to Markdown"""
        import re
        items = re.findall(r'<li[^>]*>(.*?)</li>', list_content, re.IGNORECASE | re.DOTALL)
        result = []
        
        for i, item in enumerate(items):
            item = item.strip()
            if ordered:
                result.append(f"{i+1}. {item}")
            else:
                result.append(f"- {item}")
        
        return '\n' + '\n'.join(result) + '\n\n'
    
    def update_preview(self, markdown_text: str, preserve_scroll: bool = True):
        """Update preview with anti-flashing optimization"""
        # Skip update if content hasn't actually changed
        if self.is_updating or markdown_text == self.last_markdown_content:
            return
        
        # Check if content is meaningfully different (ignore whitespace-only changes)
        if self.last_markdown_content and markdown_text.strip() == self.last_markdown_content.strip():
            return
        
        self.is_updating = True
        self.last_markdown_content = markdown_text
        
        try:
            # Store scroll position more reliably
            scroll_position = 0
            if preserve_scroll:
                # Use synchronous method to get scroll position
                self.page().runJavaScript(
                    "window.pageYOffset || document.documentElement.scrollTop || 0",
                    lambda result: setattr(self, '_stored_scroll', result or 0)
                )
                # Give it a moment to execute
                QTimer.singleShot(10, lambda: self._do_html_update(markdown_text))
                return
            else:
                self._do_html_update(markdown_text)
        
        finally:
            # Longer delay before allowing next update to prevent flashing
            QTimer.singleShot(300, lambda: setattr(self, 'is_updating', False))
    
    def _do_html_update(self, markdown_text: str):
        """Perform the actual HTML update"""
        try:
            # Convert markdown to HTML
            html_content = self.markdown_processor.convert(markdown_text)
            
            # Create optimized HTML
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                <style>
                    {self.get_preview_css()}
                </style>
            </head>
            <body>
                <div class="markdown-body" contenteditable="true" id="content">
                    {html_content}
                </div>
                <script>
                    {self.get_optimized_preview_js()}
                </script>
            </body>
            </html>
            """
            
            # Set HTML content
            self.setHtml(full_html)
            
            # Restore scroll position with longer delay for stability
            if hasattr(self, '_stored_scroll'):
                stored_scroll = getattr(self, '_stored_scroll', 0)
                QTimer.singleShot(150, lambda: self.page().runJavaScript(f"window.scrollTo(0, {stored_scroll})"))
        
        except Exception as e:
            print(f"Preview update error: {e}")
            # Reset updating flag on error
            self.is_updating = False
    
    def escape_for_data_attr(self, text: str) -> str:
        """Escape text for use in HTML data attribute"""
        return text.replace('"', '&quot;').replace('\n', '\\n')
    
    def sync_scroll_position(self, ratio: float):
        """Sync scroll position without triggering events"""
        js_code = f"""
        if (!window.isScrollSyncing) {{
            window.isScrollSyncing = true;
            var maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
            window.scrollTo(0, {ratio} * maxScroll);
            setTimeout(() => {{ window.isScrollSyncing = false; }}, 100);
        }}
        """
        self.page().runJavaScript(js_code)
    
    def scroll_to_line(self, line_number: int):
        """Scroll to specific line with improved targeting"""
        js_code = f"""
        // Find all block elements that could represent lines
        var elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, pre, blockquote');
        
        // Try to find the element at the specified line
        if (elements.length > {line_number} && elements[{line_number}]) {{
            elements[{line_number}].scrollIntoView({{ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            }});
            
            // Highlight the target element briefly
            var target = elements[{line_number}];
            target.style.backgroundColor = 'rgba(88, 166, 255, 0.2)';
            target.style.transition = 'background-color 0.3s ease';
            setTimeout(function() {{
                target.style.backgroundColor = '';
            }}, 1000);
        }} else if (elements.length > 0) {{
            // Fallback: scroll to the closest element
            var targetIndex = Math.min({line_number}, elements.length - 1);
            elements[targetIndex].scrollIntoView({{ 
                behavior: 'smooth', 
                block: 'center' 
            }});
        }}
        """
        self.page().runJavaScript(js_code)
    
    def get_preview_css(self):
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #e1e4e8;
            background-color: #0d1117;
            max-width: none;
            margin: 0;
            padding: 20px;
            overflow-x: hidden;
        }
        
        .markdown-body {
            box-sizing: border-box;
            min-width: 200px;
            max-width: none;
            margin: 0 auto;
            outline: none !important;
        }
        
        .markdown-body:focus {
            outline: none !important;
        }
        
        .markdown-body * {
            transition: all 0.1s ease;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #f0f6fc;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            border-bottom: 1px solid #21262d;
            padding-bottom: 8px;
        }
        
        h1 { font-size: 2em; color: #4fc3f7; }
        h2 { font-size: 1.5em; color: #81c784; }
        h3 { font-size: 1.25em; color: #ffcc80; }
        
        p {
            margin-bottom: 16px;
            min-height: 1.6em;
        }
        
        p:empty:before {
            content: '\\00a0';
            color: #484f58;
        }
        
        code {
            padding: 2px 4px;
            margin: 0;
            font-size: 85%;
            background-color: #161b22;
            border-radius: 3px;
            font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
        }
        
        pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #161b22;
            border-radius: 6px;
            margin-bottom: 16px;
        }
        
        pre code {
            background: transparent;
            padding: 0;
        }
        
        blockquote {
            padding: 0 16px;
            color: #8b949e;
            border-left: 4px solid #30363d;
            margin: 0 0 16px 0;
        }
        
        table {
            border-collapse: collapse;
            margin-bottom: 16px;
            width: 100%;
        }
        
        table th, table td {
            padding: 6px 13px;
            border: 1px solid #30363d;
            min-width: 50px;
        }
        
        table th {
            background-color: #161b22;
            font-weight: 600;
        }
        
        ul, ol {
            padding-left: 30px;
            margin-bottom: 16px;
        }
        
        li {
            margin-bottom: 4px;
            min-height: 1.4em;
        }
        
        li:empty:before {
            content: '\\00a0';
            color: #484f58;
        }
        
        a {
            color: #58a6ff;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        hr {
            height: 2px;
            background-color: #30363d;
            border: 0;
            margin: 24px 0;
        }
        
        .highlight {
            background: #161b22;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 16px;
            overflow-x: auto;
        }
        
        ::selection {
            background-color: #264f78;
        }
        """
    
    def get_optimized_preview_js(self):
        return """
        var bridge;
        var isContentChanging = false;
        var isScrollSyncing = false;
        var scrollDebounceTimeout;
        var contentDebounceTimeout;
        
        new QWebChannel(qt.webChannelTransport, function(channel) {
            bridge = channel.objects.bridge;
            
            var content = document.getElementById('content');
            if (!content) return;
            
            // Optimized scroll synchronization with 60fps throttling
            var lastScrollTime = 0;
            window.addEventListener('scroll', function() {
                if (isScrollSyncing) return;
                
                var now = performance.now();
                if (now - lastScrollTime < 16) return; // 60fps throttling
                lastScrollTime = now;
                
                clearTimeout(scrollDebounceTimeout);
                scrollDebounceTimeout = setTimeout(function() {
                    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    var scrollHeight = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
                    var ratio = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
                    
                    if (bridge && bridge.on_scroll_changed) {
                        bridge.on_scroll_changed(ratio);
                    }
                }, 8); // Very fast response
            });
            
            // Optimized content editing with reduced debounce
            var lastInputTime = 0;
            content.addEventListener('input', function(e) {
                if (isContentChanging) return;
                
                var now = performance.now();
                lastInputTime = now;
                
                clearTimeout(contentDebounceTimeout);
                contentDebounceTimeout = setTimeout(function() {
                    // Only process if this is the latest input
                    if (performance.now() - lastInputTime < 100) {
                        var htmlContent = content.innerHTML;
                        
                        if (bridge && bridge.on_content_changed) {
                            bridge.on_content_changed(htmlContent);
                        }
                    }
                }, 150); // Reduced from 300ms
            });
            
            // Improved paste handling
            content.addEventListener('paste', function(e) {
                e.preventDefault();
                var text = (e.originalEvent || e).clipboardData.getData('text/plain');
                
                // Insert as plain text
                var selection = window.getSelection();
                if (selection.rangeCount) {
                    var range = selection.getRangeAt(0);
                    range.deleteContents();
                    
                    // Split by lines and insert properly
                    var lines = text.split('\\n');
                    for (var i = 0; i < lines.length; i++) {
                        if (i > 0) {
                            range.insertNode(document.createElement('br'));
                        }
                        range.insertNode(document.createTextNode(lines[i]));
                        range.collapse(false);
                    }
                    
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
                
                // Immediate content change notification
                setTimeout(function() {
                    content.dispatchEvent(new Event('input'));
                }, 50);
            });
            
            // Fast cursor position tracking
            var cursorDebounceTimeout;
            document.addEventListener('selectionchange', function() {
                clearTimeout(cursorDebounceTimeout);
                cursorDebounceTimeout = setTimeout(function() {
                    var selection = window.getSelection();
                    if (selection.rangeCount > 0) {
                        var range = selection.getRangeAt(0);
                        var element = range.startContainer.nodeType === Node.TEXT_NODE 
                            ? range.startContainer.parentNode 
                            : range.startContainer;
                        
                        var allElements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li'));
                        var lineNumber = allElements.indexOf(element);
                        
                        if (lineNumber >= 0 && bridge && bridge.on_cursor_changed) {
                            bridge.on_cursor_changed(lineNumber);
                        }
                    }
                }, 25); // Faster cursor tracking
            });
            
            // Prevent drag and drop
            ['dragover', 'drop'].forEach(function(eventName) {
                content.addEventListener(eventName, function(e) {
                    e.preventDefault();
                });
            });
            
            // Enhanced table editing
            function makeTablesEditable() {
                var cells = document.querySelectorAll('table td, table th');
                cells.forEach(function(cell) {
                    cell.setAttribute('contenteditable', 'true');
                    cell.style.outline = 'none';
                });
            }
            
            // Initial setup and re-setup after content changes
            makeTablesEditable();
            var observer = new MutationObserver(function() {
                setTimeout(makeTablesEditable, 10);
            });
            observer.observe(content, { childList: true, subtree: true });
        });
        
        // Global sync state management
        function setSyncState(syncing) {
            isContentChanging = syncing;
            isScrollSyncing = syncing;
        }
        
        window.setSyncState = setSyncState;
        
        // Performance optimization
        window.requestIdleCallback = window.requestIdleCallback || function(cb) {
            return setTimeout(cb, 1);
        };
        """