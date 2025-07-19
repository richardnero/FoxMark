#!/usr/bin/env python3
"""
Dialog Components
Settings and front matter dialogs
"""

from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from document_manager import DocumentMetadata


class FrontMatterDialog(QDialog):
    """Dialog for editing document front matter"""
    
    def __init__(self, metadata: DocumentMetadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.setup_ui()
        self.load_metadata()
    
    def setup_ui(self):
        self.setWindowTitle("Document Properties")
        self.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Form layout for metadata fields
        form_layout = QFormLayout()
        
        # Basic fields
        self.title_edit = QLineEdit()
        form_layout.addRow("Title:", self.title_edit)
        
        self.author_edit = QLineEdit()
        form_layout.addRow("Author:", self.author_edit)
        
        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("YYYY-MM-DD")
        form_layout.addRow("Date:", self.date_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_edit)
        
        # Tags (comma-separated)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Categories
        self.categories_edit = QLineEdit()
        self.categories_edit.setPlaceholderText("category1, category2")
        form_layout.addRow("Categories:", self.categories_edit)
        
        # Keywords
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("keyword1, keyword2")
        form_layout.addRow("Keywords:", self.keywords_edit)
        
        # Layout
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["default", "post", "page", "article"])
        self.layout_combo.setEditable(True)
        form_layout.addRow("Layout:", self.layout_combo)
        
        # Draft checkbox
        self.draft_checkbox = QCheckBox("Draft")
        form_layout.addRow("Status:", self.draft_checkbox)
        
        layout.addLayout(form_layout)
        
        # Custom fields section
        custom_group = QGroupBox("Custom Fields")
        custom_layout = QVBoxLayout(custom_group)
        
        self.custom_table = QTableWidget(0, 2)
        self.custom_table.setHorizontalHeaderLabels(["Key", "Value"])
        self.custom_table.horizontalHeader().setStretchLastSection(True)
        custom_layout.addWidget(self.custom_table)
        
        custom_buttons = QHBoxLayout()
        add_field_btn = QPushButton("Add Field")
        add_field_btn.clicked.connect(self.add_custom_field)
        remove_field_btn = QPushButton("Remove Field")
        remove_field_btn.clicked.connect(self.remove_custom_field)
        custom_buttons.addWidget(add_field_btn)
        custom_buttons.addWidget(remove_field_btn)
        custom_buttons.addStretch()
        custom_layout.addLayout(custom_buttons)
        
        layout.addWidget(custom_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_metadata(self):
        """Load metadata into form fields"""
        self.title_edit.setText(self.metadata.title)
        self.author_edit.setText(self.metadata.author)
        self.date_edit.setText(self.metadata.date)
        self.description_edit.setPlainText(self.metadata.description)
        self.tags_edit.setText(", ".join(self.metadata.tags))
        self.categories_edit.setText(", ".join(self.metadata.categories))
        self.keywords_edit.setText(", ".join(self.metadata.keywords))
        self.layout_combo.setCurrentText(self.metadata.layout)
        self.draft_checkbox.setChecked(self.metadata.draft)
        
        # Load custom fields
        for key, value in self.metadata.custom_fields.items():
            self.add_custom_field(key, str(value))
    
    def add_custom_field(self, key="", value=""):
        """Add a custom field row"""
        row = self.custom_table.rowCount()
        self.custom_table.insertRow(row)
        self.custom_table.setItem(row, 0, QTableWidgetItem(key))
        self.custom_table.setItem(row, 1, QTableWidgetItem(value))
    
    def remove_custom_field(self):
        """Remove selected custom field"""
        current_row = self.custom_table.currentRow()
        if current_row >= 0:
            self.custom_table.removeRow(current_row)
    
    def get_metadata(self) -> DocumentMetadata:
        """Get metadata from form fields"""
        # Parse lists from comma-separated strings
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        categories = [cat.strip() for cat in self.categories_edit.text().split(",") if cat.strip()]
        keywords = [kw.strip() for kw in self.keywords_edit.text().split(",") if kw.strip()]
        
        # Get custom fields
        custom_fields = {}
        for row in range(self.custom_table.rowCount()):
            key_item = self.custom_table.item(row, 0)
            value_item = self.custom_table.item(row, 1)
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key:
                    custom_fields[key] = value
        
        return DocumentMetadata(
            title=self.title_edit.text(),
            author=self.author_edit.text(),
            date=self.date_edit.text(),
            description=self.description_edit.toPlainText(),
            tags=tags,
            categories=categories,
            keywords=keywords,
            layout=self.layout_combo.currentText(),
            draft=self.draft_checkbox.isChecked(),
            custom_fields=custom_fields
        )


class SettingsDialog(QDialog):
    """Settings dialog for editor configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different settings categories
        tab_widget = QTabWidget()
        
        # Editor settings
        editor_tab = self.create_editor_settings()
        tab_widget.addTab(editor_tab, "Editor")
        
        # Export settings
        export_tab = self.create_export_settings()
        tab_widget.addTab(export_tab, "Export")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_editor_settings(self):
        """Create editor settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Font settings
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Cascadia Code"))
        layout.addRow("Editor Font:", self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(14)
        layout.addRow("Font Size:", self.font_size_spin)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "High Contrast"])
        layout.addRow("Theme:", self.theme_combo)
        
        # Editor behavior
        self.word_wrap_check = QCheckBox("Word Wrap")
        self.word_wrap_check.setChecked(True)
        layout.addRow("", self.word_wrap_check)
        
        self.line_numbers_check = QCheckBox("Show Line Numbers")
        layout.addRow("", self.line_numbers_check)
        
        self.auto_save_check = QCheckBox("Auto Save")
        layout.addRow("", self.auto_save_check)
        
        # Sync settings
        sync_group = QGroupBox("Synchronization")
        sync_layout = QFormLayout(sync_group)
        
        self.bidirectional_edit_check = QCheckBox("Enable bidirectional editing")
        self.bidirectional_edit_check.setChecked(True)
        sync_layout.addRow("", self.bidirectional_edit_check)
        
        self.scroll_sync_check = QCheckBox("Synchronize scrolling")
        self.scroll_sync_check.setChecked(True)
        sync_layout.addRow("", self.scroll_sync_check)
        
        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(50, 500)
        self.debounce_spin.setValue(150)
        self.debounce_spin.setSuffix(" ms")
        sync_layout.addRow("Update delay:", self.debounce_spin)
        
        layout.addRow(sync_group)
        
        return widget
    
    def create_export_settings(self):
        """Create export settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export formats
        formats_group = QGroupBox("Supported Formats")
        formats_layout = QGridLayout(formats_group)
        
        formats = [
            "HTML", "PDF", "DOCX", "ODT", "RTF", "EPUB",
            "LaTeX", "Beamer", "RevealJS", "S5", "Slidy", "DZSlides"
        ]
        
        self.format_checks = {}
        for i, fmt in enumerate(formats):
            check = QCheckBox(fmt)
            check.setChecked(True)
            self.format_checks[fmt] = check
            formats_layout.addWidget(check, i // 3, i % 3)
        
        layout.addWidget(formats_group)
        
        # Default export directory
        export_dir_layout = QHBoxLayout()
        self.export_dir_edit = QLineEdit()
        self.export_dir_edit.setText(str(Path.home() / "Documents"))
        export_dir_layout.addWidget(self.export_dir_edit)
        
        export_dir_browse = QPushButton("Browse...")
        export_dir_browse.clicked.connect(self.browse_export_dir)
        export_dir_layout.addWidget(export_dir_browse)
        
        layout.addWidget(QLabel("Default Export Directory:"))
        layout.addLayout(export_dir_layout)
        
        # Pandoc settings
        pandoc_group = QGroupBox("Pandoc Integration")
        pandoc_layout = QFormLayout(pandoc_group)
        
        self.pandoc_path_edit = QLineEdit()
        self.pandoc_path_edit.setText("pandoc")
        pandoc_layout.addRow("Pandoc executable:", self.pandoc_path_edit)
        
        self.pandoc_enabled_check = QCheckBox("Enable Pandoc export")
        pandoc_layout.addRow("", self.pandoc_enabled_check)
        
        layout.addWidget(pandoc_group)
        
        return widget
    
    def browse_export_dir(self):
        """Browse for export directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if dir_path:
            self.export_dir_edit.setText(dir_path)