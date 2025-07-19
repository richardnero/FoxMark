#!/usr/bin/env python3
"""
UI Components
Quick actions toolbar and other UI utilities
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class QuickActionsToolbar(QToolBar):
    """Toolbar for quick markdown actions"""
    
    def __init__(self, parent=None):
        super().__init__("Quick Actions", parent)
        self.setup_actions()
    
    def setup_actions(self):
        """Setup toolbar actions"""
        # Bold
        bold_action = QAction("B", self)
        bold_action.setToolTip("Bold (Ctrl+B)")
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self.parent().insert_markdown("**", "**"))
        self.addAction(bold_action)
        
        # Italic
        italic_action = QAction("I", self)
        italic_action.setToolTip("Italic (Ctrl+I)")
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self.parent().insert_markdown("*", "*"))
        self.addAction(italic_action)
        
        # Code
        code_action = QAction("`", self)
        code_action.setToolTip("Inline Code")
        code_action.triggered.connect(lambda: self.parent().insert_markdown("`", "`"))
        self.addAction(code_action)
        
        self.addSeparator()
        
        # Headers (including H4, H5, H6)
        h1_action = QAction("H1", self)
        h1_action.setToolTip("Header 1")
        h1_action.triggered.connect(lambda: self.parent().insert_header(1))
        self.addAction(h1_action)
        
        h2_action = QAction("H2", self)
        h2_action.setToolTip("Header 2")
        h2_action.triggered.connect(lambda: self.parent().insert_header(2))
        self.addAction(h2_action)
        
        h3_action = QAction("H3", self)
        h3_action.setToolTip("Header 3")
        h3_action.triggered.connect(lambda: self.parent().insert_header(3))
        self.addAction(h3_action)
        
        h4_action = QAction("H4", self)
        h4_action.setToolTip("Header 4")
        h4_action.triggered.connect(lambda: self.parent().insert_header(4))
        self.addAction(h4_action)
        
        h5_action = QAction("H5", self)
        h5_action.setToolTip("Header 5")
        h5_action.triggered.connect(lambda: self.parent().insert_header(5))
        self.addAction(h5_action)
        
        h6_action = QAction("H6", self)
        h6_action.setToolTip("Header 6")
        h6_action.triggered.connect(lambda: self.parent().insert_header(6))
        self.addAction(h6_action)
        
        self.addSeparator()
        
        # Table
        table_action = QAction("Table", self)
        table_action.setToolTip("Insert Table")
        table_action.triggered.connect(lambda: self.parent().insert_table())
        self.addAction(table_action)
        
        # Link
        link_action = QAction("Link", self)
        link_action.setToolTip("Insert Link")
        link_action.triggered.connect(lambda: self.parent().insert_link())
        self.addAction(link_action)
        
        # Image
        image_action = QAction("Image", self)
        image_action.setToolTip("Insert Image")
        image_action.triggered.connect(lambda: self.parent().insert_image())
        self.addAction(image_action)
        
        self.addSeparator()
        
        # Quote
        quote_action = QAction("Quote", self)
        quote_action.setToolTip("Insert Blockquote")
        quote_action.triggered.connect(self.insert_quote)
        self.addAction(quote_action)
        
        # List
        list_action = QAction("List", self)
        list_action.setToolTip("Insert List")
        list_action.triggered.connect(self.insert_list)
        self.addAction(list_action)
        
        # Ordered List
        ordered_list_action = QAction("1.", self)
        ordered_list_action.setToolTip("Insert Ordered List")
        ordered_list_action.triggered.connect(self.insert_ordered_list)
        self.addAction(ordered_list_action)
    
    def insert_quote(self):
        """Insert blockquote"""
        if hasattr(self.parent(), 'editor'):
            editor = self.parent().editor
            cursor = editor.textCursor()
            
            # Get current line
            cursor.movePosition(QTextCursor.StartOfLine)
            current_line = cursor.block().text()
            
            # Add quote marker if not already present
            if not current_line.startswith('> '):
                cursor.insertText('> ')
    
    def insert_list(self):
        """Insert unordered list item"""
        if hasattr(self.parent(), 'editor'):
            editor = self.parent().editor
            cursor = editor.textCursor()
            
            # Get current line
            cursor.movePosition(QTextCursor.StartOfLine)
            current_line = cursor.block().text()
            
            # Add list marker if not already present
            if not current_line.strip().startswith('- '):
                cursor.insertText('- ')
    
    def insert_ordered_list(self):
        """Insert ordered list item"""
        if hasattr(self.parent(), 'editor'):
            editor = self.parent().editor
            cursor = editor.textCursor()
            
            # Get current line
            cursor.movePosition(QTextCursor.StartOfLine)
            current_line = cursor.block().text()
            
            # Add ordered list marker if not already present
            import re
            if not re.match(r'^\s*\d+\.\s', current_line):
                cursor.insertText('1. ')


class StatusBarWidget(QWidget):
    """Custom status bar widget with advanced information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Document stats
        self.stats_label = QLabel("Words: 0 | Chars: 0 | Lines: 0")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        # Sync status
        self.sync_indicator = QLabel("●")
        self.sync_indicator.setStyleSheet("color: #4caf50; font-size: 16px;")
        self.sync_indicator.setToolTip("Editor and preview are synchronized")
        layout.addWidget(QLabel("Sync:"))
        layout.addWidget(self.sync_indicator)
        
        # Cursor position
        self.cursor_label = QLabel("Line: 1, Col: 1")
        layout.addWidget(self.cursor_label)
        
        # Encoding
        self.encoding_label = QLabel("UTF-8")
        layout.addWidget(self.encoding_label)
    
    def update_stats(self, words: int, chars: int, lines: int):
        """Update document statistics"""
        self.stats_label.setText(f"Words: {words} | Chars: {chars} | Lines: {lines}")
    
    def update_cursor_position(self, line: int, column: int):
        """Update cursor position"""
        self.cursor_label.setText(f"Line: {line}, Col: {column}")
    
    def set_sync_status(self, synced: bool):
        """Update sync status indicator"""
        if synced:
            self.sync_indicator.setStyleSheet("color: #4caf50; font-size: 16px;")
            self.sync_indicator.setToolTip("Editor and preview are synchronized")
        else:
            self.sync_indicator.setStyleSheet("color: #f44336; font-size: 16px;")
            self.sync_indicator.setToolTip("Synchronization in progress...")


class TableInsertDialog(QDialog):
    """Dialog for inserting tables with custom dimensions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Table")
        self.setFixedSize(300, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Rows
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 20)
        self.rows_spin.setValue(3)
        form_layout.addRow("Rows:", self.rows_spin)
        
        # Columns
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 10)
        self.cols_spin.setValue(3)
        form_layout.addRow("Columns:", self.cols_spin)
        
        # Include header
        self.header_check = QCheckBox("Include header row")
        self.header_check.setChecked(True)
        form_layout.addRow("", self.header_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Insert")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def get_table_config(self):
        """Get table configuration"""
        return {
            'rows': self.rows_spin.value(),
            'cols': self.cols_spin.value(),
            'header': self.header_check.isChecked()
        }


class LinkInsertDialog(QDialog):
    """Dialog for inserting links with URL and text"""
    
    def __init__(self, selected_text="", parent=None):
        super().__init__(parent)
        self.selected_text = selected_text
        self.setWindowTitle("Insert Link")
        self.setFixedSize(400, 120)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Link text
        self.text_edit = QLineEdit()
        self.text_edit.setText(self.selected_text)
        self.text_edit.setPlaceholderText("Link text")
        form_layout.addRow("Text:", self.text_edit)
        
        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        form_layout.addRow("URL:", self.url_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Insert")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # Focus on URL if text is provided
        if self.selected_text:
            self.url_edit.setFocus()
        else:
            self.text_edit.setFocus()
    
    def get_link_data(self):
        """Get link data"""
        return {
            'text': self.text_edit.text().strip(),
            'url': self.url_edit.text().strip()
        }


class ImageInsertDialog(QDialog):
    """Dialog for inserting images with alt text and path"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Image")
        self.setFixedSize(500, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Alt text
        self.alt_edit = QLineEdit()
        self.alt_edit.setPlaceholderText("Image description")
        form_layout.addRow("Alt text:", self.alt_edit)
        
        # Image path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Image path or URL")
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_image)
        path_layout.addWidget(browse_btn)
        
        form_layout.addRow("Path:", path_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Insert")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def browse_image(self):
        """Browse for image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp);;All files (*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
            
            # Auto-generate alt text from filename if empty
            if not self.alt_edit.text():
                from pathlib import Path
                filename = Path(file_path).stem
                # Convert filename to readable alt text
                alt_text = filename.replace('_', ' ').replace('-', ' ').title()
                self.alt_edit.setText(alt_text)
    
    def get_image_data(self):
        """Get image data"""
        return {
            'alt': self.alt_edit.text().strip(),
            'path': self.path_edit.text().strip()
        }


class FindReplaceDialog(QDialog):
    """Find and replace dialog"""
    
    find_requested = Signal(str, bool, bool)  # text, case_sensitive, whole_word
    replace_requested = Signal(str, str, bool, bool)  # find_text, replace_text, case_sensitive, whole_word
    replace_all_requested = Signal(str, str, bool, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find and Replace")
        self.setFixedSize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Find text
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Text to find")
        form_layout.addRow("Find:", self.find_edit)
        
        # Replace text
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replace with")
        form_layout.addRow("Replace:", self.replace_edit)
        
        layout.addLayout(form_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.case_sensitive_check = QCheckBox("Case sensitive")
        options_layout.addWidget(self.case_sensitive_check)
        
        self.whole_word_check = QCheckBox("Whole word")
        options_layout.addWidget(self.whole_word_check)
        
        layout.addLayout(options_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self.find_next)
        button_layout.addWidget(find_btn)
        
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace_current)
        button_layout.addWidget(replace_btn)
        
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        button_layout.addWidget(replace_all_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Connect Enter key to find
        self.find_edit.returnPressed.connect(self.find_next)
        self.replace_edit.returnPressed.connect(self.find_next)
    
    def find_next(self):
        """Find next occurrence"""
        text = self.find_edit.text()
        if text:
            self.find_requested.emit(
                text,
                self.case_sensitive_check.isChecked(),
                self.whole_word_check.isChecked()
            )
    
    def replace_current(self):
        """Replace current occurrence"""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        
        if find_text:
            self.replace_requested.emit(
                find_text,
                replace_text,
                self.case_sensitive_check.isChecked(),
                self.whole_word_check.isChecked()
            )
    
    def replace_all(self):
        """Replace all occurrences"""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        
        if find_text:
            self.replace_all_requested.emit(
                find_text,
                replace_text,
                self.case_sensitive_check.isChecked(),
                self.whole_word_check.isChecked()
            )
    
    def set_find_text(self, text: str):
        """Set find text from external source"""
        self.find_edit.setText(text)
        self.find_edit.selectAll()


class ThemeManager:
    """Manages application themes"""
    
    @staticmethod
    def get_dark_theme() -> str:
        """Get dark theme stylesheet"""
        return """
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
            padding: 4px;
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
        
        QLineEdit {
            background-color: #21262d;
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 6px;
        }
        
        QLineEdit:focus {
            border-color: #58a6ff;
        }
        
        QPushButton {
            background-color: #21262d;
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 6px 12px;
        }
        
        QPushButton:hover {
            background-color: #30363d;
        }
        
        QPushButton:pressed {
            background-color: #264f78;
        }
        
        QComboBox {
            background-color: #21262d;
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 6px;
        }
        
        QComboBox:drop-down {
            border: none;
        }
        
        QComboBox::drop-down {
            background-color: #30363d;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }
        
        QCheckBox {
            color: #e1e4e8;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #30363d;
            border-radius: 3px;
            background-color: #21262d;
        }
        
        QCheckBox::indicator:checked {
            background-color: #58a6ff;
            border-color: #58a6ff;
        }
        
        QSpinBox {
            background-color: #21262d;
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 6px;
        }
        
        QGroupBox {
            color: #e1e4e8;
            border: 1px solid #30363d;
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 4px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
        }
        """
    
    @staticmethod
    def get_light_theme() -> str:
        """Get light theme stylesheet"""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #24292f;
        }
        
        QWidget {
            background-color: #ffffff;
            color: #24292f;
        }
        
        QTabWidget::pane {
            border: 1px solid #d0d7de;
            background-color: #f6f8fa;
        }
        
        QTabBar::tab {
            background-color: #f6f8fa;
            color: #24292f;
            padding: 8px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid #d0d7de;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }
        
        QTextEdit {
            background-color: #ffffff;
            color: #24292f;
            border: 1px solid #d0d7de;
            selection-background-color: #0969da;
        }
        """