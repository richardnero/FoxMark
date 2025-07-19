def set_editor_mode(self, mode: EditorMode):
        """Set the editor mode and update UI accordingly"""
        self.current_mode = mode
        
        if mode == EditorMode.MARKDOWN:
            # Markdown Mode: Editor editable, Preview read-only
            self.editor.setReadOnly(False)
            self.preview.page().runJavaScript("document.getElementById('content').contentEditable = 'false';")
            
            # Show both panes
            self.editor.show()
            self.preview.show()
            self.editor_splitter.setSizes([700, 700])
            
            # Update preview from current markdown
            content = self.editor.toPlainText()
            self.preview.update_preview(content, preserve_scroll=True)
            
            self.status_bar.showMessage("Markdown Mode - Edit source code, preview updates automatically", 2000)
            
        else:  # WYSIWYG Mode
            # WYSIWYG Mode: Preview editable, Editor read-only (but visible)
            self.editor.setReadOnly(True)
            self.preview.page().runJavaScript("document.getElementById('content').contentEditable = 'true';")
            
            # Show both panes but emphasize preview
            self.editor.show()
            self.preview.show()
            self.editor_splitter.setSizes([300, 1100])  # Emphasize preview
            
            # Convert current markdown to HTML for editing
            content = self.editor.toPlainText()
            self.preview.update_preview(content, preserve_scroll=True)
            
            self.status_bar.showMessage("WYSIWYG Mode - Edit visually, markdown updates when switching modes", 2000)
        
        # Update mode toggle
        self.mode_toggle.set_mode(mode)
        
        # Run linting
        self.run_linting()
    
        def switch_to_markdown_mode(self):
            """Switch to markdown mode, converting from WYSIWYG if needed"""
        if self.current_mode == EditorMode.WYSIWYG:
            # Get current content from preview and update markdown
            self.preview.page().runJavaScript(
                "document.getElementById('content').innerHTML",
                self.on_wysiwyg_to_markdown_conversion
            )
        else:
            self.set_editor_mode(EditorMode.MARKDOWN)
    
        def on_wysiwyg_to_markdown_conversion(self, html_content):
            """Handle conversion from WYSIWYG HTML to Markdown"""
        if html_content:
            # Convert HTML back to markdown
            markdown_content = self.preview.html_to_markdown(html_content)
            
            # Update editor with converted markdown
            self.editor.setPlainText(markdown_content)
            self.is_modified = True
            self.update_title()
        
        # Switch to markdown mode
        self.set_editor_mode(EditorMode.MARKDOWN)
    
    def switch_to_wysiwyg_mode(self):
        """Switch to WYSIWYG mode"""
        self.set_editor_mode(EditorMode.WYSIWYG)
    
    def run_linting(self):
        """Run linting on current document"""
        content = self.editor.toPlainText()
        front_matter_title = getattr(self.document_manager.metadata, 'title', '')
        
        # Run linting in background
        QTimer.singleShot(100, lambda: self.linting_widget.check_document(content, front_matter_title))#!/usr/bin/env python3
"""
Main Editor Application
Core window and application setup
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# Import our custom components
from editor_components import MarkdownEditor, MarkdownPreview
from sidebar_components import SidebarWidget
from dialog_components import FrontMatterDialog, SettingsDialog
from document_manager import DocumentManager
from ui_components import QuickActionsToolbar
from editor_modes import EditorMode, ModeToggleWidget, LintingWidget


class EnhancedMainWindow(QMainWindow):
    """Main application window with all features"""
    
    def __init__(self):
        super().__init__(parent=None)
        self.current_file = None
        self.is_modified = False
        self.document_manager = DocumentManager()
        self._syncing_scroll = False
        self._syncing_content = False
        
        # Editor mode management
        self.current_mode = EditorMode.MARKDOWN
        self.mode_switching = False
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_connections()
        self.apply_dark_theme()
        
        # Set window properties
        self.setWindowTitle("Advanced Markdown Editor")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        self.center_window()
    
    def setup_ui(self):
        """Setup the main user interface with mode support"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Mode toggle widget
        self.mode_toggle = ModeToggleWidget()
        self.mode_toggle.mode_changed.connect(self.on_mode_changed)
        main_layout.addWidget(self.mode_toggle)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(1)
        
        # Sidebar with linting tab
        self.sidebar = SidebarWidget()
        self.sidebar.setMaximumWidth(300)
        
        # Add linting widget to sidebar
        self.linting_widget = LintingWidget()
        self.sidebar.tab_widget.addTab(self.linting_widget, "Issues")
        
        content_layout.addWidget(self.sidebar)
        
        # Editor and preview container
        self.editor_container = QWidget()
        editor_layout = QHBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(1)
        
        # Editor and preview splitter
        self.editor_splitter = QSplitter(Qt.Horizontal)
        self.editor_splitter.setHandleWidth(1)
        
        # Editor (always present)
        self.editor = MarkdownEditor()
        
        # Preview (always present)
        self.preview = MarkdownPreview()
        
        # Add to splitter
        self.editor_splitter.addWidget(self.editor)
        self.editor_splitter.addWidget(self.preview)
        self.editor_splitter.setSizes([700, 700])
        
        editor_layout.addWidget(self.editor_splitter)
        content_layout.addWidget(self.editor_container)
        
        main_layout.addLayout(content_layout)
        
        # Set initial mode (Markdown mode)
        self.set_editor_mode(EditorMode.MARKDOWN)
    
    def setup_menu(self):
        """Setup application menu bar"""
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
        save_as_action.triggered.connect(self.save_file_as)
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
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        settings_action = QAction('Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Mode switching
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
        
        toggle_preview_action = QAction('Toggle Preview', self)
        toggle_preview_action.setShortcut('Ctrl+P')
        toggle_preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(toggle_preview_action)
        
        focus_mode_action = QAction('Focus Mode', self)
        focus_mode_action.setShortcut('F11')
        focus_mode_action.triggered.connect(self.toggle_focus_mode)
        view_menu.addAction(focus_mode_action)
    
    def setup_toolbar(self):
        """Setup quick actions toolbar"""
        self.toolbar = QuickActionsToolbar(self)
        self.addToolBar(self.toolbar)
    
    def setup_statusbar(self):
        """Setup status bar with information"""
        self.status_bar = self.statusBar()
        
        # Word count
        self.word_count_label = QLabel("Words: 0")
        self.status_bar.addPermanentWidget(self.word_count_label)
        
        # Cursor position
        self.cursor_position_label = QLabel("Line: 1, Col: 1")
        self.status_bar.addPermanentWidget(self.cursor_position_label)
        
        # Sync status
        self.sync_label = QLabel("Sync: ✓")
        self.sync_label.setStyleSheet("color: #4caf50;")
        self.status_bar.addPermanentWidget(self.sync_label)
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # Editor connections
        self.editor.content_changed.connect(self.on_editor_content_changed)
        self.editor.cursor_position_changed.connect(self.on_editor_cursor_changed)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.editor.scroll_changed.connect(self.on_editor_scroll_changed)
        
        # Preview connections
        self.preview.scroll_sync_requested.connect(self.sync_editor_scroll)
        self.preview.content_edited.connect(self.on_preview_content_edited)
        self.preview.cursor_sync_requested.connect(self.sync_editor_cursor)
        
        # Sidebar connections
        self.sidebar.file_explorer.file_selected.connect(self.open_file_from_explorer)
        self.sidebar.document_outline.heading_selected.connect(self.goto_heading)
    
    def apply_dark_theme(self):
        """Apply dark theme styling"""
        dark_stylesheet = """
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
        
        QTreeWidget {
            background-color: #161b22;
            border: none;
            color: #e1e4e8;
        }
        
        QTreeWidget::item {
            padding: 4px;
            border-bottom: 1px solid #21262d;
        }
        
        QTreeWidget::item:selected {
            background-color: #264f78;
        }
        
        QTreeWidget::item:hover {
            background-color: #30363d;
        }
        
        QLabel {
            color: #e1e4e8;
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
        
        QTextEdit {
            background-color: #0d1117;
            color: #e1e4e8;
            border: none;
            selection-background-color: #264f78;
        }
        
        QSplitter::handle {
            background-color: #21262d;
            width: 1px;
        }
        
        QSplitter::handle:hover {
            background-color: #30363d;
        }
        
        QStatusBar {
            background-color: #161b22;
            color: #8b949e;
            border-top: 1px solid #30363d;
        }
        
        QScrollBar:vertical {
            background-color: #0d1117;
            width: 14px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background-color: #21262d;
            border-radius: 7px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #30363d;
        }
        """
        
        self.setStyleSheet(dark_stylesheet)
    
    # Mode-aware event handlers
    def on_editor_content_changed(self):
        """Handle editor content changes (only in Markdown mode)"""
        if self.current_mode != EditorMode.MARKDOWN or self._syncing_content:
            return
        
        self.is_modified = True
        self.update_title()
        self.update_word_count()
        
        # Get content
        content = self.editor.toPlainText()
        
        # Cancel previous timers
        if hasattr(self, '_content_timer'):
            self._content_timer.stop()
        if hasattr(self, '_outline_timer'):
            self._outline_timer.stop()
        if hasattr(self, '_lint_timer'):
            self._lint_timer.stop()
        
        # Update preview (only in markdown mode)
        self._content_timer = QTimer()
        self._content_timer.setSingleShot(True)
        self._content_timer.timeout.connect(lambda: self._update_preview_smooth(content))
        self._content_timer.start(200)
        
        # Update outline
        self._outline_timer = QTimer()
        self._outline_timer.setSingleShot(True)
        self._outline_timer.timeout.connect(lambda: self.sidebar.document_outline.update_outline(content))
        self._outline_timer.start(100)
        
        # Run linting
        self._lint_timer = QTimer()
        self._lint_timer.setSingleShot(True)
        self._lint_timer.timeout.connect(self.run_linting)
        self._lint_timer.start(500)  # Longer delay for linting
    
    def on_preview_content_edited(self, markdown_content: str):
        """Handle preview content edits (only in WYSIWYG mode)"""
        if self.current_mode != EditorMode.WYSIWYG or self._syncing_content:
            return
        
        # In WYSIWYG mode, we don't automatically update the markdown
        # The markdown will be updated when switching back to markdown mode
        self.is_modified = True
        self.update_title()
        
        # Note: We don't update the editor here to maintain clean separation
        # The conversion happens when switching modes
    
    def _update_preview_smooth(self, content: str):
        """Smooth preview update with better performance"""
        # Set sync flag to prevent cascading updates
        self._syncing_content = True
        try:
            self.preview.update_preview(content, preserve_scroll=True)
        finally:
            # Reset sync flag after minimal delay
            QTimer.singleShot(50, lambda: setattr(self, '_syncing_content', False))
    
    def on_editor_cursor_changed(self, line_number: int):
        """Handle editor cursor changes with smoother sync"""
        if not self._syncing_content:
            # Very fast cursor sync for immediate response
            QTimer.singleShot(10, lambda: self.preview.scroll_to_line(line_number))
    
    def on_editor_scroll_changed(self, ratio: float):
        """Handle editor scroll changes with smoother sync"""
        if not self._syncing_scroll:
            self._syncing_scroll = True
            # Immediate scroll sync for fluid feel
            self.preview.sync_scroll_position(ratio)
            QTimer.singleShot(25, lambda: setattr(self, '_syncing_scroll', False))
    
    def sync_editor_scroll(self, ratio: float):
        """Sync editor scroll from preview with smoother timing"""
        if not self._syncing_scroll:
            self._syncing_scroll = True
            # Immediate sync
            self.editor.sync_scroll_position(ratio)
            QTimer.singleShot(25, lambda: setattr(self, '_syncing_scroll', False))
    
    def on_preview_content_edited(self, markdown_content: str):
        """Handle preview content edits with improved responsiveness"""
        if self._syncing_content:
            return
        
        self._syncing_content = True
        try:
            # Immediate editor update for responsive feel
            self.editor.set_content_silently(markdown_content)
            self.is_modified = True
            self.update_title()
            self.update_word_count()
            
            # Quick outline update
            QTimer.singleShot(25, lambda: self.sidebar.document_outline.update_outline(markdown_content))
        except Exception as e:
            print(f"Error updating content: {e}")
            
    def _update_preview_smooth(self, content: str):
        """Smooth preview update with better performance"""
        if self.current_mode == EditorMode.MARKDOWN:
            # Only update preview in markdown mode
            self._syncing_content = True
            try:
                self.preview.update_preview(content, preserve_scroll=True)
            finally:
                QTimer.singleShot(50, lambda: setattr(self, '_syncing_content', False))
    
    def sync_editor_cursor(self, line_number: int):
        """Sync editor cursor from preview"""
        if not self._syncing_content:
            self.editor.goto_line(line_number)
    
    def goto_heading(self, line_number: int):
        """Navigate to heading from outline - FIXED"""
        # Go to line in editor
        self.editor.goto_line(line_number)
        
        # Also scroll preview to the same line with slight delay
        QTimer.singleShot(100, lambda: self.preview.scroll_to_line(line_number))
        
        # Give focus to editor so user can see the cursor
        self.editor.setFocus()
    
    def open_file_from_explorer(self, file_path: str):
        self.open_file(file_path)
    
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
                    self, 
                    "Open Markdown File",
                    "",
                    "Markdown files (*.md *.markdown *.txt);;All files (*)"
                )
            
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        
                        # Parse front matter
                        metadata, markdown_content = self.document_manager.parse_front_matter(content)
                        self.document_manager.metadata = metadata
                        
                        self.editor.setPlainText(content)
                        self.current_file = file_path
                        self.is_modified = False
                        self.update_title()
                        
                        # Update sidebar directory
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
            self,
            "Save Markdown File",
            "",
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
                self.status_bar.showMessage("File saved successfully", 2000)
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
        {self.preview.get_preview_css()}
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
            
            self.status_bar.showMessage("Exported to HTML successfully", 3000)
            
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
    
    def toggle_preview(self):
        self.preview.setVisible(not self.preview.isVisible())
    
    def toggle_focus_mode(self):
        """Toggle focus mode with proper F11 handling"""
        if self.isFullScreen():
            # Exit focus mode
            self.showNormal()
            self.sidebar.show()
            self.preview.show()
            self.toolbar.show()
            self.menuBar().show()
            self.statusBar().show()
            self.status_bar.showMessage("Exited focus mode", 1000)
        else:
            # Enter focus mode
            self.showFullScreen()
            self.sidebar.hide()
            self.preview.hide()
            self.toolbar.hide()
            self.menuBar().hide()
            self.statusBar().hide()
            self.status_bar.showMessage("Focus mode - Press F11 to exit", 2000)
    
    def keyPressEvent(self, event):
        """Handle key press events including mode switching"""
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
        title = "Advanced Markdown Editor"
        if self.current_file:
            filename = Path(self.current_file).name
            title = f"{filename} - {title}"
        if self.is_modified:
            title = f"* {title}"
        self.setWindowTitle(title)
    
    def update_word_count(self):
        text = self.editor.toPlainText()
        
        # Remove front matter for counting
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
                self,
                "Unsaved Changes",
                "Do you want to save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
                return not self.is_modified
            elif reply == QMessageBox.Cancel:
                return False
        
        return True
    
    # Quick action methods for toolbar
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
    
    # Set application properties
    app.setApplicationName("Advanced Markdown Editor")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Your Company")
    
    # Create and show main window
    window = EnhancedMainWindow()
    window.show()
    
    # Load sample content
    sample_content = """---
title: "Advanced Markdown Editor"
author: "Your Name"
date: "2025-01-18"
tags: ["markdown", "editor"]
---

# Advanced Markdown Editor

A professional markdown editor with **perfect bidirectional sync**.

## Features

- ✅ **File Explorer** - Browse files
- ✅ **Document Outline** - Navigate headings  
- ✅ **Perfect Sync** - Edit in either pane
- ✅ **Export** - HTML and more formats

Try editing in either the editor or preview pane!
"""
    
    window.editor.setPlainText(sample_content)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()