#!/usr/bin/env python3
"""
Main Editor Application - Ultra-Smooth Version
Core window and application setup with perfect sync and no flashing
"""

import sys
import os
import re
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
import markdown

# Import our custom components
from sidebar_components import SidebarWidget
from dialog_components import FrontMatterDialog, SettingsDialog
from document_manager import DocumentManager
from ui_components import QuickActionsToolbar
from editor_modes import EditorMode, LintingWidget


class SmoothMarkdownEditor(QTextEdit):
    """Ultra-smooth markdown editor with optimized font handling"""
    content_changed = Signal()
    cursor_position_changed = Signal(int)
    scroll_changed = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.is_syncing = False
        
    def setup_editor(self):
        # Fix font issues by using system fonts only
        try:
            font = QFont()
            font.setStyleHint(QFont.Monospace)
            font.setFamily("Consolas")
            font.setPointSize(12)
            font.setFixedPitch(True)
            
            if not QFontDatabase().families().__contains__("Consolas"):
                font.setFamily("Courier New")
            
            self.setFont(font)
        except Exception:
            font = QFont("monospace", 12)
            self.setFont(font)
        
        # Apply syntax highlighting
        self.highlighter = SmoothSyntaxHighlighter(self.document())
        
        # Enable line wrap
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Connect signals
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_changed)
        
        # Smooth scrolling
        scrollbar = self.verticalScrollBar()
        scrollbar.valueChanged.connect(self.on_scroll_changed)
    
    def on_text_changed(self):
        if not self.is_syncing:
            self.content_changed.emit()
    
    def on_cursor_changed(self):
        if not self.is_syncing:
            cursor = self.textCursor()
            line_number = cursor.blockNumber()
            self.cursor_position_changed.emit(line_number)
    
    def on_scroll_changed(self):
        if not self.is_syncing:
            scrollbar = self.verticalScrollBar()
            if scrollbar.maximum() > 0:
                ratio = scrollbar.value() / scrollbar.maximum()
                self.scroll_changed.emit(ratio)
    
    def goto_line(self, line_number: int):
        """Jump to specific line"""
        self.is_syncing = True
        try:
            doc = self.document()
            if line_number < doc.blockCount():
                block = doc.findBlockByLineNumber(line_number)
                if block.isValid():
                    cursor = QTextCursor(block)
                    self.setTextCursor(cursor)
                    self.ensureCursorVisible()
        finally:
            self.is_syncing = False
    
    def sync_scroll_position(self, ratio: float):
        """Sync scroll position"""
        if self.is_syncing:
            return
        
        self.is_syncing = True
        try:
            scrollbar = self.verticalScrollBar()
            new_value = int(ratio * scrollbar.maximum())
            scrollbar.setValue(new_value)
        finally:
            self.is_syncing = False
    
    def set_content_silently(self, content: str):
        """Set content without triggering signals"""
        self.is_syncing = True
        try:
            cursor = self.textCursor()
            position = cursor.position()
            
            self.setPlainText(content)
            
            new_cursor = self.textCursor()
            if position <= len(content):
                new_cursor.setPosition(position)
                self.setTextCursor(new_cursor)
        finally:
            self.is_syncing = False
    
    # Markdown formatting methods
    def insert_markdown(self, prefix: str, suffix: str = ""):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:  # WYSIWYG
            # Show WYSIWYG view
            self.content_stack.setCurrentIndex(1)
            
            # Update WYSIWYG with current editor content and make editable
            content = self.editor.toPlainText()
            self.wysiwyg_preview.update_content_smooth(content, editable=True)
            
            self.statusBar().showMessage("WYSIWYG Mode - Visual editing", 1500)
        
        self.mode_toggle.set_mode(mode)
        self.run_linting()
    
    def switch_to_markdown_mode(self):
        """Switch to markdown mode with content sync"""
        if self.current_mode == EditorMode.WYSIWYG:
            # Get content from WYSIWYG and update editor
            self.wysiwyg_preview.get_content_as_markdown(self.sync_wysiwyg_to_editor)
        else:
            self.set_editor_mode(EditorMode.MARKDOWN)
    
    def sync_wysiwyg_to_editor(self, markdown_content):
        """Sync WYSIWYG content back to editor - THE KEY FIX!"""
        if markdown_content and not self._syncing:
            self._syncing = True
            try:
                self.editor.set_content_silently(markdown_content)
                self.is_modified = True
                self.update_title()
            finally:
                self._syncing = False
        
        self.set_editor_mode(EditorMode.MARKDOWN)
    
    def switch_to_wysiwyg_mode(self):
        """Switch to WYSIWYG mode"""
        self.set_editor_mode(EditorMode.WYSIWYG)
    
    def on_editor_content_changed(self):
        """Handle editor content changes"""
        if self._syncing or self.current_mode != EditorMode.MARKDOWN:
            return
        
        self.is_modified = True
        self.update_title()
        self.update_word_count()
        
        # Update preview smoothly
        content = self.editor.toPlainText()
        self.preview.update_content_smooth(content, editable=False)
        
        # Update outline and linting with delays
        QTimer.singleShot(100, lambda: self.sidebar.document_outline.update_outline(content))
        QTimer.singleShot(300, self.run_linting)
    
    def on_preview_content_edited(self, markdown_content: str):
        """Handle markdown preview editing"""
        if self._syncing or self.current_mode != EditorMode.MARKDOWN:
            return
        
        self._syncing = True
        try:
            self.editor.set_content_silently(markdown_content)
            self.is_modified = True
            self.update_title()
        finally:
            QTimer.singleShot(50, lambda: setattr(self, '_syncing', False))
    
    def on_wysiwyg_content_edited(self, markdown_content: str):
        """Handle WYSIWYG content editing - CRITICAL FIX!"""
        if self._syncing or self.current_mode != EditorMode.WYSIWYG:
            return
        
        self._syncing = True
        try:
            # Update the underlying editor content
            self.editor.set_content_silently(markdown_content)
            self.is_modified = True
            self.update_title()
            self.update_word_count()
        finally:
            QTimer.singleShot(50, lambda: setattr(self, '_syncing', False))
    
    def on_editor_cursor_changed(self, line_number: int):
        """Handle cursor changes"""
        if not self._syncing and self.current_mode == EditorMode.MARKDOWN:
            self.preview.scroll_to_line(line_number)
    
    def on_editor_scroll_changed(self, ratio: float):
        """Handle scroll changes"""
        if not self._syncing and self.current_mode == EditorMode.MARKDOWN:
            self.preview.sync_scroll_position(ratio)
    
    def sync_editor_scroll(self, ratio: float):
        """Sync editor scroll from preview"""
        if not self._syncing and self.current_mode == EditorMode.MARKDOWN:
            self.editor.sync_scroll_position(ratio)
    
    def goto_line_from_issue(self, line_number: int):
        """Go to line from linting issue"""
        if self.current_mode == EditorMode.WYSIWYG:
            self.switch_to_markdown_mode()
            QTimer.singleShot(200, lambda: self._goto_line_actual(line_number))
        else:
            self._goto_line_actual(line_number)
    
    def _goto_line_actual(self, line_number: int):
        """Actually navigate to line"""
        self.editor.goto_line(line_number - 1)
        self.editor.setFocus()
        QTimer.singleShot(100, lambda: self.preview.scroll_to_line(line_number - 1))
    
    def goto_heading(self, line_number: int):
        """Navigate to heading"""
        self.editor.goto_line(line_number)
        QTimer.singleShot(100, lambda: self.preview.scroll_to_line(line_number))
        self.editor.setFocus()
    
    def open_file_from_explorer(self, file_path: str):
        self.open_file(file_path)
    
    def run_linting(self):
        """Run document linting"""
        content = self.editor.toPlainText()
        front_matter_title = getattr(self.document_manager.metadata, 'title', '')
        QTimer.singleShot(50, lambda: self.linting_widget.check_document(content, front_matter_title))
    
    # Menu and toolbar setup
    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Document properties
        properties_action = QAction('Document Properties...', self)
        properties_action.setShortcut('Ctrl+Alt+P')
        properties_action.triggered.connect(self.edit_document_properties)
        file_menu.addAction(properties_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu('Export')
        
        formats = ['HTML', 'PDF', 'DOCX', 'ODT', 'EPUB', 'LaTeX']
        for fmt in formats:
            action = QAction(f'Export as {fmt}...', self)
            action.triggered.connect(lambda checked, f=fmt: self.export_file(f))
            export_menu.addAction(action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        markdown_mode_action = QAction('Markdown Mode', self)
        markdown_mode_action.setShortcut('Ctrl+1')
        markdown_mode_action.triggered.connect(self.switch_to_markdown_mode)
        view_menu.addAction(markdown_mode_action)
        
        wysiwyg_mode_action = QAction('WYSIWYG Mode', self)
        wysiwyg_mode_action.setShortcut('Ctrl+2')
        wysiwyg_mode_action.triggered.connect(self.switch_to_wysiwyg_mode)
        view_menu.addAction(wysiwyg_mode_action)
        
        view_menu.addSeparator()
        
        toggle_sidebar_action = QAction('Toggle Sidebar', self)
        toggle_sidebar_action.setShortcut('Ctrl+\\')
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)
        
        focus_mode_action = QAction('Focus Mode', self)
        focus_mode_action.setShortcut('F11')
        focus_mode_action.triggered.connect(self.toggle_focus_mode)
        view_menu.addAction(focus_mode_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        settings_action = QAction('Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
    
    def setup_toolbar(self):
        self.toolbar = QuickActionsToolbar(self)
        self.addToolBar(self.toolbar)
    
    def setup_statusbar(self):
        status_bar = self.statusBar()
        
        self.word_count_label = QLabel("Words: 0")
        status_bar.addPermanentWidget(self.word_count_label)
        
        self.cursor_position_label = QLabel("Line: 1, Col: 1")
        status_bar.addPermanentWidget(self.cursor_position_label)
        
        # Connect cursor position updates
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
        QMainWindow {
            background-color: #0d1117;
            color: #e1e4e8;
        }
        
        QWidget {
            background-color: #0d1117;
            color: #e1e4e8;
        }
        
        QTabWidget::pane {
            border: 1px solid #30363d;
            background-color: #161b22;
        }
        
        QTabBar::tab {
            background-color: #21262d;
            color: #e1e4e8;
            padding: 8px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #161b22;
        }
        
        QTreeWidget, QListWidget {
            background-color: #161b22;
            border: none;
            color: #e1e4e8;
        }
        
        QTreeWidget::item, QListWidget::item {
            padding: 6px;
            border-bottom: 1px solid #21262d;
        }
        
        QTreeWidget::item:selected, QListWidget::item:selected {
            background-color: #264f78;
        }
        
        QTreeWidget::item:hover, QListWidget::item:hover {
            background-color: #30363d;
        }
        
        QTextEdit {
            background-color: #0d1117;
            color: #e1e4e8;
            border: none;
            selection-background-color: #264f78;
        }
        
        QSplitter::handle {
            background-color: #21262d;
            width: 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #30363d;
        }
        
        QStatusBar {
            background-color: #161b22;
            color: #8b949e;
            border-top: 1px solid #30363d;
        }
        
        QStackedWidget {
            background-color: #0d1117;
        }
        
        QToolBar {
            background-color: #161b22;
            border-bottom: 1px solid #30363d;
            spacing: 4px;
        }
        
        QToolBar QToolButton {
            background-color: #21262d;
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        
        QToolBar QToolButton:hover {
            background-color: #30363d;
        }
        
        QToolBar QToolButton:pressed {
            background-color: #264f78;
        }
        
        QMenuBar {
            background-color: #161b22;
            color: #e1e4e8;
            border-bottom: 1px solid #30363d;
            padding: 4px;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: #21262d;
        }
        
        QMenu {
            background-color: #161b22;
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 6px;
        }
        
        QMenu::item {
            padding: 8px 20px;
        }
        
        QMenu::item:selected {
            background-color: #21262d;
        }
        """)
    
    # File operations
    def new_file(self):
        if self.check_save_changes():
            self.editor.clear()
            self.current_file = None
            self.is_modified = False
            self.document_manager.metadata = self.document_manager.create_empty_metadata()
            self.update_title()
    
    def open_file(self, file_path: str = None):
        if self.check_save_changes():
            if not file_path:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Open Markdown File", "",
                    "Markdown files (*.md *.markdown *.txt);;All files (*)"
                )
            
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        
                        metadata, markdown_content = self.document_manager.parse_front_matter(content)
                        self.document_manager.metadata = metadata
                        
                        self.editor.setPlainText(content)
                        self.current_file = file_path
                        self.is_modified = False
                        self.update_title()
                        
                        file_dir = Path(file_path).parent
                        self.sidebar.file_explorer.load_directory(file_dir)
                        
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open file:\n{str(e)}")
    
    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown File", "",
            "Markdown files (*.md);;All files (*)"
        )
        
        if file_path:
            self.save_to_file(file_path)
            self.current_file = file_path
            self.update_title()
    
    def save_to_file(self, file_path: str):
        try:
            content = self.editor.toPlainText()
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
                self.is_modified = False
                self.update_title()
                self.statusBar().showMessage("File saved successfully", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file:\n{str(e)}")
    
    def export_file(self, format_type: str):
        """Export file using basic conversion"""
        if not self.current_file:
            QMessageBox.warning(self, "Export Error", "Please save the file first.")
            return
        
        # Get export file path
        extensions = {
            'HTML': 'html',
            'PDF': 'pdf', 
            'DOCX': 'docx',
            'ODT': 'odt',
            'EPUB': 'epub',
            'LaTeX': 'tex'
        }
        
        ext = extensions.get(format_type, 'html')
        default_name = Path(self.current_file).stem + f'.{ext}'
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            f"Export as {format_type}", 
            default_name,
            f"{format_type} files (*.{ext});;All files (*)"
        )
        
        if file_path:
            if format_type == 'HTML':
                self.export_to_html(file_path)
            else:
                QMessageBox.information(
                    self, "Export", 
                    f"{format_type} export requires Pandoc installation.\n"
                    "Please install Pandoc for advanced export features."
                )
    
    def export_to_html(self, file_path: str):
        """Export to HTML using built-in markdown processor"""
        try:
            content = self.editor.toPlainText()
            
            # Remove front matter for export
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].lstrip('\n')
            
            # Convert to HTML
            html_content = self.preview.markdown_processor.convert(content)
            
            # Create full HTML document
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.document_manager.metadata.title or 'Exported Document'}</title>
    <style>
        {self.preview.get_css()}
    </style>
</head>
<body>
    <div class="markdown-body">
        {html_content}
    </div>
</body>
</html>"""
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(full_html)
            
            self.statusBar().showMessage("Exported to HTML successfully", 3000)
            
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Could not export file:\n{str(e)}")
    
    # Dialog methods
    def edit_document_properties(self):
        dialog = FrontMatterDialog(self.document_manager.metadata, self)
        if dialog.exec() == QDialog.Accepted:
            self.document_manager.metadata = dialog.get_metadata()
            self.update_document_with_front_matter()
    
    def update_document_with_front_matter(self):
        content = self.editor.toPlainText()
        
        # Remove existing front matter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].lstrip('\n')
        
        # Add new front matter
        front_matter = self.document_manager.generate_front_matter(self.document_manager.metadata)
        new_content = front_matter + content
        
        self.editor.setPlainText(new_content)
        self.is_modified = True
        self.update_title()
    
    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
    
    # View methods
    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())
    
    def toggle_focus_mode(self):
        if self.isFullScreen():
            self.showNormal()
            self.sidebar.show()
            self.toolbar.show()
            self.menuBar().show()
            self.statusBar().show()
        else:
            self.showFullScreen()
            self.sidebar.hide()
            self.toolbar.hide()
            self.menuBar().hide()
            self.statusBar().hide()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_focus_mode()
            event.accept()
        elif event.key() == Qt.Key_1 and event.modifiers() == Qt.ControlModifier:
            self.switch_to_markdown_mode()
            event.accept()
        elif event.key() == Qt.Key_2 and event.modifiers() == Qt.ControlModifier:
            self.switch_to_wysiwyg_mode()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    # Utility methods
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def update_title(self):
        title = "FoxMark - Advanced Markdown Editor"
        if self.current_file:
            filename = Path(self.current_file).name
            title = f"{filename} - FoxMark"
        if self.is_modified:
            title = f"● {title}"
        self.setWindowTitle(title)
    
    def update_word_count(self):
        text = self.editor.toPlainText()
        
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                text = parts[2]
        
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        paragraphs = len([p for p in text.split('\n\n') if p.strip()]) if text.strip() else 0
        
        self.word_count_label.setText(f"Words: {words} | Chars: {chars} | ¶: {paragraphs}")
    
    def update_cursor_position(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_position_label.setText(f"Line: {line}, Col: {col}")
    
    def check_save_changes(self) -> bool:
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Do you want to save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
                return not self.is_modified
            elif reply == QMessageBox.Cancel:
                return False
        
        return True
    
    # Quick actions for toolbar
    def insert_markdown(self, prefix: str, suffix: str = ""):
        self.editor.insert_markdown(prefix, suffix)
    
    def insert_header(self, level: int):
        self.editor.insert_header(level)
    
    def insert_table(self):
        self.editor.insert_table()
    
    def insert_link(self):
        self.editor.insert_link()
    
    def insert_image(self):
        self.editor.insert_image()
    
    def closeEvent(self, event):
        if self.check_save_changes():
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("FoxMark - Advanced Markdown Editor")
    app.setApplicationVersion("2.2.0")
    app.setOrganizationName("FoxMark Team")
    
    window = EnhancedMainWindow()
    window.show()
    
    # Load optimized sample content
    sample_content = """---
title: "FoxMark Ultra-Smooth Edition"
author: "FoxMark Team"
date: "2025-01-18"
tags: ["markdown", "wysiwyg", "smooth"]
---

# 🦊 FoxMark Ultra-Smooth Edition

**Perfect bidirectional sync** with **zero flashing**!

## ✅ Issues Fixed

### 🔄 **WYSIWYG ↔ Markdown Sync**
- **WYSIWYG edits now update markdown** ✅
- **Perfect content preservation** during mode switches
- **Real-time bidirectional sync** working flawlessly

### 🚀 **Zero Flashing**
- **JavaScript content updates** instead of page reloads
- **Smooth transitions** with optimized rendering
- **No more flickering** or visual disruptions

### 🖋️ **Fixed Font Issues**
- **System font fallbacks** prevent font warnings
- **Optimized font handling** for better performance
- **Clean console output** with no font errors

## 🎯 **Test These Features**

1. **Switch to WYSIWYG mode** (Ctrl+2)
2. **Edit content visually** → watch markdown update!
3. **Switch back to Markdown** (Ctrl+1) → content preserved!
4. **Click issues in sidebar** → jumps to exact line
5. **Notice smooth updates** → no flashing!

## 💡 **Pro Tips**

- **F11**: Focus mode for distraction-free writing
- **Ctrl+\\**: Toggle sidebar
- **Real-time sync**: Edit in either mode seamlessly

---

**Your optimized markdown editing experience awaits!** 🎉
"""
    
    window.editor.setPlainText(sample_content)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
            cursor.insertText(f"{prefix}text{suffix}")
            for _ in range(len(suffix) + 4):
                cursor.movePosition(QTextCursor.Left)
            for _ in range(4):
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
    
    def insert_header(self, level: int):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        current_line = cursor.block().text()
        clean_line = re.sub(r'^#+\s*', '', current_line)
        header_text = f"{'#' * level} {clean_line}" if clean_line else f"{'#' * level} Header {level}"
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.insertText(header_text)
    
    def insert_table(self):
        table_template = """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
"""
        cursor = self.textCursor()
        cursor.insertText(table_template)
    
    def insert_link(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"[{selected_text}](url)")
        else:
            cursor.insertText("[link text](url)")
    
    def insert_image(self):
        cursor = self.textCursor()
        cursor.insertText("![alt text](image_url)")


class SmoothSyntaxHighlighter(QSyntaxHighlighter):
    """Optimized syntax highlighter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        colors = {
            'header': QColor('#58a6ff'),
            'bold': QColor('#ffa657'),
            'italic': QColor('#a5d6ff'),
            'code': QColor('#f47067'),
            'link': QColor('#7ee787'),
        }
        
        # Headers
        header_format = QTextCharFormat()
        header_format.setForeground(colors['header'])
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'^#{1,6}\s.*'), header_format))
        
        # Bold
        bold_format = QTextCharFormat()
        bold_format.setForeground(colors['bold'])
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\*\*[^*]+\*\*'), bold_format))
        
        # Italic
        italic_format = QTextCharFormat()
        italic_format.setForeground(colors['italic'])
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r'\*[^*]+\*'), italic_format))
        
        # Code
        code_format = QTextCharFormat()
        code_format.setForeground(colors['code'])
        self.highlighting_rules.append((QRegularExpression(r'`[^`]+`'), code_format))
        
        # Links
        link_format = QTextCharFormat()
        link_format.setForeground(colors['link'])
        self.highlighting_rules.append((QRegularExpression(r'\[[^\]]+\]\([^)]+\)'), link_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            if pattern.isValid():
                iterator = pattern.globalMatch(text)
                while iterator.hasNext():
                    match = iterator.next()
                    self.setFormat(match.capturedStart(), match.capturedLength(), format)


class UltraSmoothPreview(QWebEngineView):
    """Ultra-smooth preview with NO flashing"""
    scroll_sync_requested = Signal(float)
    content_edited = Signal(str)
    cursor_sync_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.markdown_processor = markdown.Markdown(
            extensions=['codehilite', 'tables', 'toc', 'fenced_code'],
            extension_configs={'codehilite': {'css_class': 'highlight'}}
        )
        
        # Bridge for communication
        self.channel = QWebChannel()
        self.page().setWebChannel(self.channel)
        self.bridge = PreviewBridge()
        self.channel.registerObject("bridge", self.bridge)
        
        # Connect signals
        self.bridge.scroll_changed.connect(self.scroll_sync_requested.emit)
        self.bridge.content_changed.connect(self.on_content_edited)
        
        # Prevent flashing variables
        self._current_content = ""
        self._is_updating = False
        self._content_hash = ""
        
        # Initialize with empty content
        self.set_initial_content()
    
    def set_initial_content(self):
        """Set initial HTML structure"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>{self.get_css()}</style>
        </head>
        <body>
            <div id="content" class="markdown-body"></div>
            <script>{self.get_javascript()}</script>
        </body>
        </html>
        """
        self.setHtml(html)
    
    def update_content_smooth(self, markdown_text: str, editable: bool = False):
        """Update content without flashing - key optimization!"""
        # Skip if content hasn't changed
        content_hash = hash(markdown_text)
        if content_hash == self._content_hash and not self._is_updating:
            return
        
        if self._is_updating:
            return
        
        self._is_updating = True
        self._content_hash = content_hash
        
        try:
            # Convert markdown to HTML
            html_content = self.markdown_processor.convert(markdown_text)
            
            # Properly escape content for JavaScript
            escaped_content = (html_content
                             .replace('\\', '\\\\')
                             .replace('"', '\\"')
                             .replace('\n', '\\n')
                             .replace('\r', '\\r'))
            
            # Use JavaScript to update content smoothly
            js_code = f"""
            var content = document.getElementById('content');
            if (content) {{
                var scrollTop = window.pageYOffset;
                content.innerHTML = "{escaped_content}";
                content.contentEditable = '{str(editable).lower()}';
                window.scrollTo(0, scrollTop);
                if ({str(editable).lower()}) {{
                    setupEditingHandlers();
                }}
            }}
            """
            
            self.page().runJavaScript(js_code)
            
        except Exception as e:
            print(f"Preview update error: {e}")
        finally:
            # Reset flag after short delay
            QTimer.singleShot(50, lambda: setattr(self, '_is_updating', False))
    
    def on_content_edited(self, html_content: str):
        """Handle content editing in WYSIWYG mode"""
        if self._is_updating:
            return
        
        # Convert HTML back to markdown
        markdown_content = self.html_to_markdown(html_content)
        self.content_edited.emit(markdown_content)
    
    def html_to_markdown(self, html: str) -> str:
        """Enhanced HTML to Markdown conversion"""
        import re
        
        text = html.strip()
        
        # Headers
        for i in range(6, 0, -1):
            text = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', f'{"#" * i} \\1', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Formatting
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Links
        text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Images
        text = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', text, flags=re.IGNORECASE)
        
        # Paragraphs and line breaks
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<br[^>]*/?>', r'\n', text, flags=re.IGNORECASE)
        
        # Lists
        text = re.sub(r'<ul[^>]*>(.*?)</ul>', lambda m: self.convert_list(m.group(1), False), text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<ol[^>]*>(.*?)</ol>', lambda m: self.convert_list(m.group(1), True), text, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def convert_list(self, list_content: str, ordered: bool) -> str:
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
    
    def set_editable(self, editable: bool):
        """Set content editable state"""
        js_code = f"""
        var content = document.getElementById('content');
        if (content) {{
            content.contentEditable = '{str(editable).lower()}';
            if ({str(editable).lower()}) {{
                content.style.cursor = 'text';
                setupEditingHandlers();
            }} else {{
                content.style.cursor = 'default';
            }}
        }}
        """
        self.page().runJavaScript(js_code)
    
    def get_content_as_markdown(self, callback):
        """Get current content as markdown"""
        def handle_html(html_content):
            if html_content:
                markdown_content = self.html_to_markdown(html_content)
                callback(markdown_content)
            else:
                callback("")
        
        self.page().runJavaScript("document.getElementById('content').innerHTML", handle_html)
    
    def scroll_to_line(self, line_number: int):
        """Scroll to specific line"""
        js_code = f"""
        var elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, pre, blockquote');
        if (elements.length > {line_number} && elements[{line_number}]) {{
            elements[{line_number}].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
        """
        self.page().runJavaScript(js_code)
    
    def sync_scroll_position(self, ratio: float):
        """Sync scroll position"""
        js_code = f"""
        var maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        window.scrollTo(0, {ratio} * maxScroll);
        """
        self.page().runJavaScript(js_code)
    
    def get_css(self):
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #e1e4e8;
            background-color: #0d1117;
            margin: 0;
            padding: 20px;
            transition: none !important;
        }
        
        .markdown-body {
            max-width: none;
            transition: none !important;
        }
        
        .markdown-body * {
            transition: none !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #58a6ff;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }
        
        h1 { font-size: 2em; }
        h2 { font-size: 1.5em; }
        h3 { font-size: 1.25em; }
        
        p { margin-bottom: 16px; }
        
        code {
            padding: 2px 4px;
            font-size: 85%;
            background-color: #161b22;
            border-radius: 3px;
            color: #f47067;
        }
        
        pre {
            padding: 16px;
            background-color: #161b22;
            border-radius: 6px;
            overflow-x: auto;
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
        }
        
        table th {
            background-color: #161b22;
            font-weight: 600;
        }
        
        ul, ol {
            padding-left: 30px;
            margin-bottom: 16px;
        }
        
        li { margin-bottom: 4px; }
        
        a {
            color: #7ee787;
            text-decoration: none;
        }
        
        a:hover { text-decoration: underline; }
        
        strong { color: #ffa657; }
        em { color: #a5d6ff; }
        
        [contenteditable="true"]:focus {
            outline: 2px solid #58a6ff;
            outline-offset: 2px;
            border-radius: 4px;
        }
        """
    
    def get_javascript(self):
        return """
        var bridge;
        var isEditing = false;
        
        new QWebChannel(qt.webChannelTransport, function(channel) {
            bridge = channel.objects.bridge;
            setupEditingHandlers();
        });
        
        function setupEditingHandlers() {
            var content = document.getElementById('content');
            if (!content || isEditing) return;
            
            isEditing = true;
            
            // Content editing
            content.addEventListener('input', function() {
                if (bridge && bridge.on_content_changed) {
                    bridge.on_content_changed(content.innerHTML);
                }
            });
            
            // Paste handling
            content.addEventListener('paste', function(e) {
                e.preventDefault();
                var text = (e.originalEvent || e).clipboardData.getData('text/plain');
                document.execCommand('insertText', false, text);
            });
            
            // Scroll sync
            var scrollTimeout;
            window.addEventListener('scroll', function() {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(function() {
                    var scrollTop = window.pageYOffset;
                    var scrollHeight = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
                    var ratio = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
                    
                    if (bridge && bridge.on_scroll_changed) {
                        bridge.on_scroll_changed(ratio);
                    }
                }, 10);
            });
        }
        """


class PreviewBridge(QObject):
    """Bridge for web communication"""
    scroll_changed = Signal(float)
    content_changed = Signal(str)
    
    @Slot(float)
    def on_scroll_changed(self, ratio):
        self.scroll_changed.emit(ratio)
    
    @Slot(str)
    def on_content_changed(self, content):
        self.content_changed.emit(content)


class OptimizedModeToggle(QWidget):
    """Clean mode toggle"""
    mode_changed = Signal(EditorMode)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = EditorMode.MARKDOWN
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.mode_label = QLabel("📝 Markdown Mode")
        self.mode_label.setStyleSheet("""
            QLabel {
                background-color: #0969da;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.mode_label)
        
        self.switch_button = QPushButton("Switch to WYSIWYG")
        self.switch_button.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                color: #e1e4e8;
                border: 1px solid #30363d;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #30363d; }
        """)
        self.switch_button.clicked.connect(self.toggle_mode)
        layout.addWidget(self.switch_button)
        
        layout.addStretch()
        
        help_text = QLabel("Ctrl+1: Markdown | Ctrl+2: WYSIWYG")
        help_text.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(help_text)
    
    def toggle_mode(self):
        new_mode = EditorMode.WYSIWYG if self.current_mode == EditorMode.MARKDOWN else EditorMode.MARKDOWN
        self.set_mode(new_mode)
        self.mode_changed.emit(new_mode)
    
    def set_mode(self, mode: EditorMode):
        self.current_mode = mode
        
        if mode == EditorMode.MARKDOWN:
            self.mode_label.setText("📝 Markdown Mode")
            self.switch_button.setText("Switch to WYSIWYG")
            self.mode_label.setStyleSheet("""
                QLabel {
                    background-color: #0969da;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self.mode_label.setText("🎨 WYSIWYG Mode")
            self.switch_button.setText("Switch to Markdown")
            self.mode_label.setStyleSheet("""
                QLabel {
                    background-color: #fb8500;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)


class EnhancedLintingWidget(LintingWidget):
    """Enhanced linting with click-to-goto"""
    issue_clicked = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.issues_list.itemClicked.connect(self.on_issue_clicked)
    
    def on_issue_clicked(self, item):
        text = item.text()
        if text.startswith("Line "):
            try:
                line_part = text.split(":")[0]
                line_number = int(line_part.split(" ")[1])
                self.issue_clicked.emit(line_number)
            except (ValueError, IndexError):
                pass


class EnhancedMainWindow(QMainWindow):
    """Ultra-smooth main window with perfect sync"""
    
    def __init__(self):
        super().__init__(parent=None)
        self.current_file = None
        self.is_modified = False
        self.document_manager = DocumentManager()
        self.current_mode = EditorMode.MARKDOWN
        self._syncing = False
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_connections()
        self.apply_theme()
        
        self.setWindowTitle("FoxMark - Advanced Markdown Editor")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        self.center_window()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Mode toggle
        self.mode_toggle = OptimizedModeToggle()
        self.mode_toggle.mode_changed.connect(self.on_mode_changed)
        main_layout.addWidget(self.mode_toggle)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.setMaximumWidth(300)
        
        self.linting_widget = EnhancedLintingWidget()
        self.linting_widget.issue_clicked.connect(self.goto_line_from_issue)
        self.sidebar.tab_widget.addTab(self.linting_widget, "Issues")
        
        content_layout.addWidget(self.sidebar)
        
        # Main content stack
        self.content_stack = QStackedWidget()
        
        # Markdown mode widget
        self.markdown_widget = QWidget()
        markdown_layout = QHBoxLayout(self.markdown_widget)
        markdown_layout.setContentsMargins(0, 0, 0, 0)
        
        self.editor_splitter = QSplitter(Qt.Horizontal)
        self.editor = SmoothMarkdownEditor()
        self.preview = UltraSmoothPreview()
        
        self.editor_splitter.addWidget(self.editor)
        self.editor_splitter.addWidget(self.preview)
        self.editor_splitter.setSizes([700, 700])
        
        markdown_layout.addWidget(self.editor_splitter)
        
        # WYSIWYG mode widget
        self.wysiwyg_widget = QWidget()
        wysiwyg_layout = QHBoxLayout(self.wysiwyg_widget)
        wysiwyg_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wysiwyg_preview = UltraSmoothPreview()
        wysiwyg_layout.addWidget(self.wysiwyg_preview)
        
        # Add to stack
        self.content_stack.addWidget(self.markdown_widget)
        self.content_stack.addWidget(self.wysiwyg_widget)
        
        content_layout.addWidget(self.content_stack)
        main_layout.addLayout(content_layout)
        
        # Start in markdown mode
        self.set_editor_mode(EditorMode.MARKDOWN)
    
    def setup_connections(self):
        # Editor connections
        self.editor.content_changed.connect(self.on_editor_content_changed)
        self.editor.cursor_position_changed.connect(self.on_editor_cursor_changed)
        self.editor.scroll_changed.connect(self.on_editor_scroll_changed)
        
        # Preview connections
        self.preview.scroll_sync_requested.connect(self.sync_editor_scroll)
        self.preview.content_edited.connect(self.on_preview_content_edited)
        
        # WYSIWYG connections - THIS IS THE KEY FIX!
        self.wysiwyg_preview.content_edited.connect(self.on_wysiwyg_content_edited)
        
        # Sidebar connections
        self.sidebar.file_explorer.file_selected.connect(self.open_file_from_explorer)
        self.sidebar.document_outline.heading_selected.connect(self.goto_heading)
    
    def on_mode_changed(self, mode: EditorMode):
        """Handle mode change with perfect sync"""
        self.set_editor_mode(mode)
    
    def set_editor_mode(self, mode: EditorMode):
        """Set editor mode with ultra-smooth transitions"""
        if self.current_mode == mode:
            return
        
        self.current_mode = mode
        
        if mode == EditorMode.MARKDOWN:
            # Show markdown view
            self.content_stack.setCurrentIndex(0)
            
            # Update preview with current editor content
            content = self.editor.toPlainText()
            self.preview.update_content_smooth(content, editable=False)
            
            self.statusBar().showMessage("Markdown Mode - Source editing", 1500)
            
        else: