#!/usr/bin/env python3
"""
Sidebar Components
File explorer and document outline widgets
"""

import re
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class DocumentOutlineItem:
    """Represents a heading in the document outline"""
    def __init__(self, text: str, level: int, line_number: int):
        self.text = text
        self.level = level
        self.line_number = line_number
        self.children = []


class FileExplorer(QWidget):
    """File explorer sidebar"""
    file_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_directory = Path.home()
        self.load_directory(self.current_directory)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("File Explorer")
        header.setStyleSheet("font-weight: bold; padding: 8px; background-color: #21262d;")
        layout.addWidget(header)
        
        # Directory navigation
        nav_layout = QHBoxLayout()
        self.path_label = QLabel(str(Path.home()))
        self.path_label.setStyleSheet("padding: 4px; font-size: 11px; color: #8b949e;")
        nav_layout.addWidget(self.path_label)
        
        self.up_button = QPushButton("↑")
        self.up_button.setMaximumWidth(30)
        self.up_button.clicked.connect(self.go_up)
        nav_layout.addWidget(self.up_button)
        
        layout.addLayout(nav_layout)
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_tree)
    
    def load_directory(self, directory: Path):
        """Load files and directories"""
        self.current_directory = directory
        self.path_label.setText(str(directory))
        self.file_tree.clear()
        
        try:
            # Add directories first
            for item in sorted(directory.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    tree_item = QTreeWidgetItem([f"📁 {item.name}"])
                    tree_item.setData(0, Qt.UserRole, str(item))
                    self.file_tree.addTopLevelItem(tree_item)
            
            # Add markdown files
            for item in sorted(directory.iterdir()):
                if item.is_file() and item.suffix.lower() in ['.md', '.markdown', '.txt']:
                    tree_item = QTreeWidgetItem([f"📄 {item.name}"])
                    tree_item.setData(0, Qt.UserRole, str(item))
                    self.file_tree.addTopLevelItem(tree_item)
        except PermissionError:
            pass
    
    def go_up(self):
        """Navigate to parent directory"""
        parent = self.current_directory.parent
        if parent != self.current_directory:
            self.load_directory(parent)
    
    def on_item_double_clicked(self, item):
        """Handle double-click on file or directory"""
        path = Path(item.data(0, Qt.UserRole))
        if path.is_dir():
            self.load_directory(path)
        else:
            self.file_selected.emit(str(path))


class DocumentOutline(QWidget):
    """Document structure outline"""
    heading_selected = Signal(int)  # line number
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.outline_items = []
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Document Outline")
        header.setStyleSheet("font-weight: bold; padding: 8px; background-color: #21262d;")
        layout.addWidget(header)
        
        # Outline tree
        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.outline_tree)
    
    def update_outline(self, text: str):
        """Update outline from markdown text"""
        self.outline_tree.clear()
        self.outline_items = []
        
        lines = text.split('\n')
        stack = []  # Stack to maintain hierarchy
        
        for line_num, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s+(.+)', line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                
                # Create outline item
                outline_item = DocumentOutlineItem(title, level, line_num)
                self.outline_items.append(outline_item)
                
                # Create tree widget item
                tree_item = QTreeWidgetItem([title])
                tree_item.setData(0, Qt.UserRole, line_num)
                
                # Style based on heading level
                if level == 1:
                    font = tree_item.font(0)
                    font.setBold(True)
                    tree_item.setFont(0, font)
                    tree_item.setForeground(0, QColor("#4fc3f7"))
                elif level == 2:
                    tree_item.setForeground(0, QColor("#81c784"))
                else:
                    tree_item.setForeground(0, QColor("#ffcc80"))
                
                # Maintain hierarchy
                while stack and stack[-1]['level'] >= level:
                    stack.pop()
                
                if stack:
                    stack[-1]['item'].addChild(tree_item)
                else:
                    self.outline_tree.addTopLevelItem(tree_item)
                
                stack.append({'level': level, 'item': tree_item})
        
        self.outline_tree.expandAll()
    
    def on_item_clicked(self, item):
        """Handle click on outline item"""
        line_number = item.data(0, Qt.UserRole)
        if line_number is not None:
            self.heading_selected.emit(line_number)


class SidebarWidget(QWidget):
    """Combined sidebar with file explorer and document outline"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for switching between panels
        self.tab_widget = QTabWidget()
        
        # File explorer
        self.file_explorer = FileExplorer()
        self.tab_widget.addTab(self.file_explorer, "Files")
        
        # Document outline
        self.document_outline = DocumentOutline()
        self.tab_widget.addTab(self.document_outline, "Outline")
        
        layout.addWidget(self.tab_widget)