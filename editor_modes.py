#!/usr/bin/env python3
"""
Editor Modes
Manages switching between Markdown and WYSIWYG modes
"""

import re
from enum import Enum
from typing import List
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class EditorMode(Enum):
    """Editor mode enumeration"""
    MARKDOWN = "markdown"
    WYSIWYG = "wysiwyg"


class ModeToggleWidget(QWidget):
    """Widget for toggling between editor modes"""
    mode_changed = Signal(EditorMode)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = EditorMode.MARKDOWN
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Mode label
        self.mode_label = QLabel("Mode:")
        layout.addWidget(self.mode_label)
        
        # Mode toggle buttons (like tabs)
        self.button_group = QButtonGroup(self)
        
        # Markdown mode button
        self.markdown_btn = QPushButton("📝 Markdown")
        self.markdown_btn.setCheckable(True)
        self.markdown_btn.setChecked(True)
        self.markdown_btn.setToolTip("Edit markdown source code")
        self.markdown_btn.clicked.connect(lambda: self.set_mode(EditorMode.MARKDOWN))
        layout.addWidget(self.markdown_btn)
        
        # WYSIWYG mode button
        self.wysiwyg_btn = QPushButton("🎨 WYSIWYG")
        self.wysiwyg_btn.setCheckable(True)
        self.wysiwyg_btn.setToolTip("Edit with visual formatting")
        self.wysiwyg_btn.clicked.connect(lambda: self.set_mode(EditorMode.WYSIWYG))
        layout.addWidget(self.wysiwyg_btn)
        
        # Add buttons to group for exclusive selection
        self.button_group.addButton(self.markdown_btn)
        self.button_group.addButton(self.wysiwyg_btn)
        
        layout.addStretch()
        
        # Mode indicator
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet("color: #4fc3f7; font-size: 16px;")
        self.indicator.setToolTip("Current editor mode")
        layout.addWidget(self.indicator)
        
        # Apply styling
        self.apply_styling()
    
    def apply_styling(self):
        """Apply custom styling to mode toggle"""
        style = """
        QPushButton {
            border: 2px solid #30363d;
            border-radius: 6px;
            padding: 8px 16px;
            background-color: #21262d;
            color: #8b949e;
            font-weight: bold;
            min-width: 100px;
        }
        
        QPushButton:checked {
            background-color: #0969da;
            color: #ffffff;
            border-color: #0969da;
        }
        
        QPushButton:hover:!checked {
            background-color: #30363d;
            color: #e1e4e8;
        }
        
        QLabel {
            color: #e1e4e8;
            font-weight: bold;
        }
        """
        self.setStyleSheet(style)
    
    def set_mode(self, mode: EditorMode):
        """Set the current editor mode"""
        if mode != self.current_mode:
            self.current_mode = mode
            
            # Update button states
            self.markdown_btn.setChecked(mode == EditorMode.MARKDOWN)
            self.wysiwyg_btn.setChecked(mode == EditorMode.WYSIWYG)
            
            # Update indicator
            if mode == EditorMode.MARKDOWN:
                self.indicator.setStyleSheet("color: #4fc3f7; font-size: 16px;")
                self.indicator.setToolTip("Markdown Mode - Source editing")
            else:
                self.indicator.setStyleSheet("color: #fb8500; font-size: 16px;")
                self.indicator.setToolTip("WYSIWYG Mode - Visual editing")
            
            # Emit signal
            self.mode_changed.emit(mode)
    
    def get_mode(self) -> EditorMode:
        """Get current editor mode"""
        return self.current_mode


class MarkdownLinter:
    """Markdown linting and validation"""
    
    def __init__(self):
        self.rules = {
            'front_matter_title': self.check_front_matter_title,
            'heading_hierarchy': self.check_heading_hierarchy,
            'line_length': self.check_line_length,
            'trailing_whitespace': self.check_trailing_whitespace,
            'empty_links': self.check_empty_links,
            'duplicate_headings': self.check_duplicate_headings,
            'list_marker_consistency': self.check_list_markers,
        }
    
    def lint_document(self, content: str, front_matter_title: str = "") -> List[dict]:
        """Lint markdown document and return issues"""
        issues = []
        
        for rule_name, rule_func in self.rules.items():
            try:
                rule_issues = rule_func(content, front_matter_title)
                issues.extend(rule_issues)
            except Exception as e:
                print(f"Linting rule {rule_name} failed: {e}")
        
        return issues
    
    def check_front_matter_title(self, content: str, front_matter_title: str) -> List[dict]:
        """Check if document has proper title structure"""
        issues = []
        lines = content.split('\n')
        
        # Skip front matter
        start_line = 0
        if content.startswith('---'):
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    start_line = i + 1
                    break
        
        # Look for first heading
        first_heading_level = None
        for i, line in enumerate(lines[start_line:], start_line):
            if line.strip().startswith('#'):
                heading_match = re.match(r'^(#{1,6})\s+(.+)', line.strip())
                if heading_match:
                    first_heading_level = len(heading_match.group(1))
                    break
        
        # Check if we have front matter title but first heading is H1
        if front_matter_title and first_heading_level == 1:
            issues.append({
                'type': 'warning',
                'message': 'Document has front matter title and H1 heading. Consider starting sections with H2.',
                'line': start_line,
                'rule': 'front_matter_title'
            })
        
        return issues
    
    def check_heading_hierarchy(self, content: str, front_matter_title: str) -> List[dict]:
        """Check heading hierarchy (no skipping levels)"""
        issues = []
        lines = content.split('\n')
        
        previous_level = 0
        if front_matter_title:
            previous_level = 1  # Front matter title counts as H1
        
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                heading_match = re.match(r'^(#{1,6})\s+(.+)', line.strip())
                if heading_match:
                    current_level = len(heading_match.group(1))
                    
                    # Check for skipped levels
                    if current_level > previous_level + 1:
                        issues.append({
                            'type': 'warning',
                            'message': f'Heading level jumps from H{previous_level} to H{current_level}. Consider using H{previous_level + 1}.',
                            'line': line_num,
                            'rule': 'heading_hierarchy'
                        })
                    
                    previous_level = current_level
        
        return issues
    
    def check_line_length(self, content: str, front_matter_title: str) -> List[dict]:
        """Check for overly long lines"""
        issues = []
        lines = content.split('\n')
        max_length = 120
        
        for line_num, line in enumerate(lines, 1):
            # Skip code blocks and tables
            if line.strip().startswith('```') or line.strip().startswith('|'):
                continue
            
            if len(line) > max_length:
                issues.append({
                    'type': 'info',
                    'message': f'Line is {len(line)} characters long. Consider breaking at {max_length} characters.',
                    'line': line_num,
                    'rule': 'line_length'
                })
        
        return issues
    
    def check_trailing_whitespace(self, content: str, front_matter_title: str) -> List[dict]:
        """Check for trailing whitespace"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if line.endswith(' ') or line.endswith('\t'):
                issues.append({
                    'type': 'warning',
                    'message': 'Line has trailing whitespace.',
                    'line': line_num,
                    'rule': 'trailing_whitespace'
                })
        
        return issues
    
    def check_empty_links(self, content: str, front_matter_title: str) -> List[dict]:
        """Check for empty or placeholder links"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Find markdown links
            link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
            links = re.finditer(link_pattern, line)
            
            for link in links:
                text, url = link.groups()
                if not url.strip() or url.strip() in ['url', 'URL', '#', 'javascript:void(0)']:
                    issues.append({
                        'type': 'error',
                        'message': f'Empty or placeholder link: [{text}]({url})',
                        'line': line_num,
                        'rule': 'empty_links'
                    })
        
        return issues
    
    def check_duplicate_headings(self, content: str, front_matter_title: str) -> List[dict]:
        """Check for duplicate heading texts"""
        issues = []
        lines = content.split('\n')
        headings = {}
        
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                heading_match = re.match(r'^#{1,6}\s+(.+)', line.strip())
                if heading_match:
                    heading_text = heading_match.group(1).lower().strip()
                    
                    if heading_text in headings:
                        issues.append({
                            'type': 'warning',
                            'message': f'Duplicate heading "{heading_text}" (first seen on line {headings[heading_text]})',
                            'line': line_num,
                            'rule': 'duplicate_headings'
                        })
                    else:
                        headings[heading_text] = line_num
        
        return issues
    
    def check_list_markers(self, content: str, front_matter_title: str) -> List[dict]:
        """Check for consistent list markers"""
        issues = []
        lines = content.split('\n')
        
        in_list = False
        list_marker = None
        list_start_line = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check if this is a list item
            list_match = re.match(r'^(\s*)([-*+])\s+', line)
            if list_match:
                indent, marker = list_match.groups()
                
                if not in_list:
                    # Starting a new list
                    in_list = True
                    list_marker = marker
                    list_start_line = line_num
                elif marker != list_marker:
                    # Inconsistent marker
                    issues.append({
                        'type': 'warning',
                        'message': f'Inconsistent list marker "{marker}" (list started with "{list_marker}" on line {list_start_line})',
                        'line': line_num,
                        'rule': 'list_marker_consistency'
                    })
            else:
                # Not a list item
                if in_list and stripped == '':
                    # Empty line in list is okay
                    continue
                elif in_list:
                    # End of list
                    in_list = False
                    list_marker = None
                    list_start_line = None
        
        return issues


class SpellChecker:
    """Basic spell checking functionality"""
    
    def __init__(self):
        self.custom_words = set()
        self.load_custom_dictionary()
    
    def load_custom_dictionary(self):
        """Load custom words (markdown/programming terms)"""
        # Common programming and markdown terms
        tech_terms = {
            'markdown', 'html', 'css', 'javascript', 'python', 'json', 'yaml',
            'frontend', 'backend', 'api', 'url', 'uri', 'http', 'https',
            'github', 'gitlab', 'repo', 'git', 'commit', 'merge', 'branch',
            'readme', 'changelog', 'documentation', 'docs', 'config',
            'async', 'await', 'npm', 'pip', 'cli', 'gui', 'ui', 'ux'
        }
        self.custom_words.update(tech_terms)
    
    def add_word(self, word: str):
        """Add word to custom dictionary"""
        self.custom_words.add(word.lower())
    
    def is_word_correct(self, word: str) -> bool:
        """Check if word is spelled correctly (basic implementation)"""
        # Remove punctuation and convert to lowercase
        clean_word = re.sub(r'[^\w]', '', word.lower())
        
        # Skip very short words, numbers, and custom words
        if len(clean_word) <= 2 or clean_word.isdigit() or clean_word in self.custom_words:
            return True
        
        # This is a basic implementation - in a real app you'd use a proper spell checker
        # like pyspellchecker, enchant, or integrate with system spell checker
        return True  # For now, assume all words are correct
    
    def check_text(self, text: str) -> List[dict]:
        """Check text for spelling errors"""
        errors = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip code blocks and inline code
            if '```' in line or line.strip().startswith('    '):
                continue
            
            # Remove inline code
            line = re.sub(r'`[^`]*`', '', line)
            
            # Find words
            words = re.finditer(r'\b[a-zA-Z]+\b', line)
            
            for word_match in words:
                word = word_match.group()
                if not self.is_word_correct(word):
                    errors.append({
                        'type': 'spelling',
                        'message': f'Possible spelling error: "{word}"',
                        'line': line_num,
                        'column': word_match.start(),
                        'word': word,
                        'suggestions': []  # Would contain suggestions in real implementation
                    })
        
        return errors


class LintingWidget(QWidget):
    """Widget to display linting results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.linter = MarkdownLinter()
        self.spell_checker = SpellChecker()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Document Issues")
        header.setStyleSheet("font-weight: bold; padding: 8px; background-color: #21262d;")
        layout.addWidget(header)
        
        # Issues list
        self.issues_list = QListWidget()
        self.issues_list.setAlternatingRowColors(True)
        layout.addWidget(self.issues_list)
        
        # Summary
        self.summary_label = QLabel("No issues found")
        self.summary_label.setStyleSheet("padding: 8px; color: #4caf50;")
        layout.addWidget(self.summary_label)
    
    def check_document(self, content: str, front_matter_title: str = ""):
        """Check document for issues"""
        self.issues_list.clear()
        
        # Get linting issues
        lint_issues = self.linter.lint_document(content, front_matter_title)
        
        # Get spelling issues
        spell_issues = self.spell_checker.check_text(content)
        
        # Combine all issues
        all_issues = lint_issues + spell_issues
        
        # Sort by line number
        all_issues.sort(key=lambda x: x.get('line', 0))
        
        # Display issues
        error_count = 0
        warning_count = 0
        info_count = 0
        
        for issue in all_issues:
            issue_type = issue.get('type', 'info')
            line = issue.get('line', 0)
            message = issue.get('message', '')
            
            # Create list item
            item_text = f"Line {line}: {message}"
            item = QListWidgetItem(item_text)
            
            # Set icon and color based on type
            if issue_type == 'error':
                item.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
                item.setForeground(QColor('#f44336'))
                error_count += 1
            elif issue_type == 'warning':
                item.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
                item.setForeground(QColor('#ff9800'))
                warning_count += 1
            elif issue_type == 'spelling':
                item.setIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
                item.setForeground(QColor('#9c27b0'))
                warning_count += 1
            else:  # info
                item.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
                item.setForeground(QColor('#2196f3'))
                info_count += 1
            
            self.issues_list.addItem(item)
        
        # Update summary
        if all_issues:
            summary_parts = []
            if error_count > 0:
                summary_parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
            if warning_count > 0:
                summary_parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")
            if info_count > 0:
                summary_parts.append(f"{info_count} suggestion{'s' if info_count != 1 else ''}")
            
            summary_text = ", ".join(summary_parts)
            self.summary_label.setText(summary_text)
            self.summary_label.setStyleSheet("padding: 8px; color: #ff9800;")
        else:
            self.summary_label.setText("✓ No issues found")
            self.summary_label.setStyleSheet("padding: 8px; color: #4caf50;")