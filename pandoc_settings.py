#!/usr/bin/env python3
"""
Pandoc Settings Manager
Handles all Pandoc configuration, templates, and export options
"""

import json
import os
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


@dataclass
class PandocSettings:
    """Pandoc configuration settings"""
    # Executable path
    pandoc_path: str = "pandoc"
    
    # General options
    standalone: bool = True
    table_of_contents: bool = False
    number_sections: bool = False
    highlight_style: str = "github"
    
    # Templates and CSS
    html_template: str = ""
    latex_template: str = ""
    css_file: str = ""
    reference_docx: str = ""
    
    # PDF options
    pdf_engine: str = "pdflatex"  # pdflatex, xelatex, lualatex
    geometry: str = "margin=1in"
    fontsize: str = "12pt"
    
    # HTML options
    html_math_method: str = "katex"  # katex, mathjax, mathml
    email_obfuscation: str = "references"
    
    # Citation options
    bibliography: str = ""
    csl_style: str = ""
    citation_abbreviations: str = ""
    
    # Custom filters and extensions
    lua_filters: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    
    # Custom arguments per format
    html_args: List[str] = field(default_factory=list)
    pdf_args: List[str] = field(default_factory=list)
    docx_args: List[str] = field(default_factory=list)
    latex_args: List[str] = field(default_factory=list)
    
    # Output directories
    export_directory: str = ""
    template_directory: str = ""
    
    # Advanced options
    resource_path: List[str] = field(default_factory=list)
    data_dir: str = ""
    custom_variables: Dict[str, str] = field(default_factory=dict)


class PandocManager:
    """Manages Pandoc operations and settings"""
    
    def __init__(self):
        self.settings = PandocSettings()
        self.config_file = Path.home() / ".markdown_editor" / "pandoc_settings.json"
        self.load_settings()
    
    def load_settings(self):
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Update settings with loaded data
                    for key, value in data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
            except Exception as e:
                print(f"Error loading Pandoc settings: {e}")
    
    def save_settings(self):
        """Save settings to config file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.settings), f, indent=2)
        except Exception as e:
            print(f"Error saving Pandoc settings: {e}")
    
    def check_pandoc_installation(self) -> tuple[bool, str]:
        """Check if Pandoc is installed and get version"""
        try:
            result = subprocess.run(
                [self.settings.pandoc_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, version_line
            else:
                return False, "Pandoc not found"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Pandoc not found or not accessible"
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported input and output formats"""
        try:
            # Get input formats
            result_input = subprocess.run(
                [self.settings.pandoc_path, '--list-input-formats'],
                capture_output=True,
                text=True
            )
            input_formats = result_input.stdout.strip().split('\n') if result_input.returncode == 0 else []
            
            # Get output formats
            result_output = subprocess.run(
                [self.settings.pandoc_path, '--list-output-formats'],
                capture_output=True,
                text=True
            )
            output_formats = result_output.stdout.strip().split('\n') if result_output.returncode == 0 else []
            
            return {
                'input': input_formats,
                'output': output_formats
            }
        except Exception:
            return {'input': [], 'output': []}
    
    def build_pandoc_command(self, input_file: str, output_file: str, output_format: str) -> List[str]:
        """Build Pandoc command with current settings"""
        cmd = [self.settings.pandoc_path, input_file, '-o', output_file]
        
        # Add format
        cmd.extend(['--to', output_format])
        
        # General options
        if self.settings.standalone:
            cmd.append('--standalone')
        
        if self.settings.table_of_contents:
            cmd.append('--toc')
        
        if self.settings.number_sections:
            cmd.append('--number-sections')
        
        if self.settings.highlight_style:
            cmd.extend(['--highlight-style', self.settings.highlight_style])
        
        # Templates and styling
        if output_format == 'html':
            if self.settings.html_template:
                cmd.extend(['--template', self.settings.html_template])
            if self.settings.css_file:
                cmd.extend(['--css', self.settings.css_file])
            if self.settings.html_math_method:
                cmd.extend(['--mathjax' if self.settings.html_math_method == 'mathjax' else f'--{self.settings.html_math_method}'])
            cmd.extend(self.settings.html_args)
        
        elif output_format == 'pdf':
            if self.settings.pdf_engine:
                cmd.extend(['--pdf-engine', self.settings.pdf_engine])
            if self.settings.geometry:
                cmd.extend(['-V', f'geometry:{self.settings.geometry}'])
            if self.settings.fontsize:
                cmd.extend(['-V', f'fontsize:{self.settings.fontsize}'])
            if self.settings.latex_template:
                cmd.extend(['--template', self.settings.latex_template])
            cmd.extend(self.settings.pdf_args)
        
        elif output_format == 'docx':
            if self.settings.reference_docx:
                cmd.extend(['--reference-doc', self.settings.reference_docx])
            cmd.extend(self.settings.docx_args)
        
        elif output_format == 'latex':
            if self.settings.latex_template:
                cmd.extend(['--template', self.settings.latex_template])
            cmd.extend(self.settings.latex_args)
        
        # Citations
        if self.settings.bibliography:
            cmd.extend(['--bibliography', self.settings.bibliography])
        
        if self.settings.csl_style:
            cmd.extend(['--csl', self.settings.csl_style])
        
        # Lua filters
        for filter_path in self.settings.lua_filters:
            cmd.extend(['--lua-filter', filter_path])
        
        # Extensions
        if self.settings.extensions:
            extensions_str = '+'.join(self.settings.extensions)
            cmd.extend(['--from', f'markdown+{extensions_str}'])
        
        # Custom variables
        for key, value in self.settings.custom_variables.items():
            cmd.extend(['-V', f'{key}:{value}'])
        
        # Resource path
        if self.settings.resource_path:
            for path in self.settings.resource_path:
                cmd.extend(['--resource-path', path])
        
        return cmd
    
    def export_file(self, input_file: str, output_file: str, output_format: str, 
                   progress_callback=None) -> tuple[bool, str]:
        """Export file using Pandoc"""
        try:
            cmd = self.build_pandoc_command(input_file, output_file, output_format)
            
            if progress_callback:
                progress_callback("Building Pandoc command...")
            
            # Run Pandoc
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(input_file).parent
            )
            
            if result.returncode == 0:
                return True, f"Successfully exported to {output_format.upper()}"
            else:
                return False, f"Pandoc error:\n{result.stderr}"
                
        except Exception as e:
            return False, f"Export failed: {str(e)}"


class AdvancedPandocDialog(QDialog):
    """Advanced Pandoc settings dialog"""
    
    def __init__(self, pandoc_manager: PandocManager, parent=None):
        super().__init__(parent)
        self.pandoc_manager = pandoc_manager
        self.settings = pandoc_manager.settings
        
        self.setWindowTitle("Advanced Pandoc Settings")
        self.setMinimumSize(800, 700)
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        self.tab_widget = QTabWidget()
        
        # General settings tab
        self.tab_widget.addTab(self.create_general_tab(), "General")
        
        # Templates tab
        self.tab_widget.addTab(self.create_templates_tab(), "Templates")
        
        # Export formats tab
        self.tab_widget.addTab(self.create_formats_tab(), "Export Formats")
        
        # Citations tab
        self.tab_widget.addTab(self.create_citations_tab(), "Citations")
        
        # Advanced tab
        self.tab_widget.addTab(self.create_advanced_tab(), "Advanced")
        
        layout.addWidget(self.tab_widget)
        
        # Pandoc info
        info_widget = self.create_info_widget()
        layout.addWidget(info_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Pandoc")
        test_btn.clicked.connect(self.test_pandoc)
        button_layout.addWidget(test_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def create_general_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Pandoc executable
        pandoc_layout = QHBoxLayout()
        self.pandoc_path_edit = QLineEdit()
        pandoc_layout.addWidget(self.pandoc_path_edit)
        
        browse_pandoc_btn = QPushButton("Browse...")
        browse_pandoc_btn.clicked.connect(self.browse_pandoc_executable)
        pandoc_layout.addWidget(browse_pandoc_btn)
        
        layout.addRow("Pandoc Executable:", pandoc_layout)
        
        # General options
        self.standalone_check = QCheckBox("Standalone document")
        layout.addRow("", self.standalone_check)
        
        self.toc_check = QCheckBox("Table of Contents")
        layout.addRow("", self.toc_check)
        
        self.number_sections_check = QCheckBox("Number Sections")
        layout.addRow("", self.number_sections_check)
        
        # Syntax highlighting
        self.highlight_combo = QComboBox()
        self.highlight_combo.addItems([
            "github", "pygments", "kate", "monochrome", "breezedark", 
            "espresso", "zenburn", "haddock", "tango"
        ])
        self.highlight_combo.setEditable(True)
        layout.addRow("Highlight Style:", self.highlight_combo)
        
        # Export directory
        export_layout = QHBoxLayout()
        self.export_dir_edit = QLineEdit()
        export_layout.addWidget(self.export_dir_edit)
        
        browse_export_btn = QPushButton("Browse...")
        browse_export_btn.clicked.connect(self.browse_export_directory)
        export_layout.addWidget(browse_export_btn)
        
        layout.addRow("Default Export Directory:", export_layout)
        
        return widget
    
    def create_templates_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # HTML template
        html_template_layout = QHBoxLayout()
        self.html_template_edit = QLineEdit()
        html_template_layout.addWidget(self.html_template_edit)
        
        browse_html_btn = QPushButton("Browse...")
        browse_html_btn.clicked.connect(lambda: self.browse_file(self.html_template_edit, "HTML template"))
        html_template_layout.addWidget(browse_html_btn)
        
        layout.addRow("HTML Template:", html_template_layout)
        
        # LaTeX template
        latex_template_layout = QHBoxLayout()
        self.latex_template_edit = QLineEdit()
        latex_template_layout.addWidget(self.latex_template_edit)
        
        browse_latex_btn = QPushButton("Browse...")
        browse_latex_btn.clicked.connect(lambda: self.browse_file(self.latex_template_edit, "LaTeX template"))
        latex_template_layout.addWidget(browse_latex_btn)
        
        layout.addRow("LaTeX Template:", latex_template_layout)
        
        # CSS file
        css_layout = QHBoxLayout()
        self.css_edit = QLineEdit()
        css_layout.addWidget(self.css_edit)
        
        browse_css_btn = QPushButton("Browse...")
        browse_css_btn.clicked.connect(lambda: self.browse_file(self.css_edit, "CSS file", "CSS files (*.css)"))
        css_layout.addWidget(browse_css_btn)
        
        layout.addRow("CSS File:", css_layout)
        
        # Reference DOCX
        docx_layout = QHBoxLayout()
        self.reference_docx_edit = QLineEdit()
        docx_layout.addWidget(self.reference_docx_edit)
        
        browse_docx_btn = QPushButton("Browse...")
        browse_docx_btn.clicked.connect(lambda: self.browse_file(self.reference_docx_edit, "Reference DOCX", "Word files (*.docx)"))
        docx_layout.addWidget(browse_docx_btn)
        
        layout.addRow("Reference DOCX:", docx_layout)
        
        return widget
    
    def create_formats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # PDF settings
        pdf_group = QGroupBox("PDF Export")
        pdf_layout = QFormLayout(pdf_group)
        
        self.pdf_engine_combo = QComboBox()
        self.pdf_engine_combo.addItems(["pdflatex", "xelatex", "lualatex", "wkhtmltopdf", "weasyprint"])
        pdf_layout.addRow("PDF Engine:", self.pdf_engine_combo)
        
        self.geometry_edit = QLineEdit()
        self.geometry_edit.setPlaceholderText("e.g., margin=1in")
        pdf_layout.addRow("Page Geometry:", self.geometry_edit)
        
        self.fontsize_edit = QLineEdit()
        self.fontsize_edit.setPlaceholderText("e.g., 12pt")
        pdf_layout.addRow("Font Size:", self.fontsize_edit)
        
        layout.addWidget(pdf_group)
        
        # HTML settings
        html_group = QGroupBox("HTML Export")
        html_layout = QFormLayout(html_group)
        
        self.math_method_combo = QComboBox()
        self.math_method_combo.addItems(["katex", "mathjax", "mathml", "webtex"])
        html_layout.addRow("Math Rendering:", self.math_method_combo)
        
        self.email_obfuscation_combo = QComboBox()
        self.email_obfuscation_combo.addItems(["references", "javascript", "none"])
        html_layout.addRow("Email Obfuscation:", self.email_obfuscation_combo)
        
        layout.addWidget(html_group)
        
        # Custom arguments
        args_group = QGroupBox("Custom Arguments")
        args_layout = QFormLayout(args_group)
        
        self.html_args_edit = QLineEdit()
        self.html_args_edit.setPlaceholderText("--self-contained --embed-resources")
        args_layout.addRow("HTML Arguments:", self.html_args_edit)
        
        self.pdf_args_edit = QLineEdit()
        self.pdf_args_edit.setPlaceholderText("--include-in-header header.tex")
        args_layout.addRow("PDF Arguments:", self.pdf_args_edit)
        
        self.docx_args_edit = QLineEdit()
        args_layout.addRow("DOCX Arguments:", self.docx_args_edit)
        
        layout.addWidget(args_group)
        
        return widget
    
    def create_citations_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Bibliography
        bib_layout = QHBoxLayout()
        self.bibliography_edit = QLineEdit()
        bib_layout.addWidget(self.bibliography_edit)
        
        browse_bib_btn = QPushButton("Browse...")
        browse_bib_btn.clicked.connect(lambda: self.browse_file(
            self.bibliography_edit, "Bibliography", 
            "Bibliography files (*.bib *.json *.yaml *.xml)"
        ))
        bib_layout.addWidget(browse_bib_btn)
        
        layout.addRow("Bibliography:", bib_layout)
        
        # CSL style
        csl_layout = QHBoxLayout()
        self.csl_edit = QLineEdit()
        csl_layout.addWidget(self.csl_edit)
        
        browse_csl_btn = QPushButton("Browse...")
        browse_csl_btn.clicked.connect(lambda: self.browse_file(self.csl_edit, "CSL Style", "CSL files (*.csl)"))
        csl_layout.addWidget(browse_csl_btn)
        
        layout.addRow("CSL Style:", csl_layout)
        
        # Citation abbreviations
        abbrev_layout = QHBoxLayout()
        self.citation_abbrev_edit = QLineEdit()
        abbrev_layout.addWidget(self.citation_abbrev_edit)
        
        browse_abbrev_btn = QPushButton("Browse...")
        browse_abbrev_btn.clicked.connect(lambda: self.browse_file(
            self.citation_abbrev_edit, "Citation Abbreviations", 
            "JSON files (*.json)"
        ))
        abbrev_layout.addWidget(browse_abbrev_btn)
        
        layout.addRow("Citation Abbreviations:", abbrev_layout)
        
        return widget
    
    def create_advanced_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lua filters
        filters_group = QGroupBox("Lua Filters")
        filters_layout = QVBoxLayout(filters_group)
        
        self.filters_list = QListWidget()
        filters_layout.addWidget(self.filters_list)
        
        filters_buttons = QHBoxLayout()
        add_filter_btn = QPushButton("Add Filter...")
        add_filter_btn.clicked.connect(self.add_lua_filter)
        filters_buttons.addWidget(add_filter_btn)
        
        remove_filter_btn = QPushButton("Remove Filter")
        remove_filter_btn.clicked.connect(self.remove_lua_filter)
        filters_buttons.addWidget(remove_filter_btn)
        
        filters_buttons.addStretch()
        filters_layout.addLayout(filters_buttons)
        
        layout.addWidget(filters_group)
        
        # Extensions
        ext_group = QGroupBox("Markdown Extensions")
        ext_layout = QVBoxLayout(ext_group)
        
        # Common extensions with checkboxes
        ext_grid = QGridLayout()
        self.extension_checks = {}
        
        common_extensions = [
            "pipe_tables", "simple_tables", "multiline_tables", "grid_tables",
            "fenced_code_blocks", "backtick_code_blocks", "inline_code_attributes",
            "markdown_in_html_blocks", "blank_before_header", "header_attributes",
            "auto_identifiers", "implicit_header_references", "definition_lists",
            "compact_definition_lists", "example_lists", "task_lists",
            "abbreviations", "footnotes", "inline_notes", "citations",
            "tex_math_dollars", "tex_math_single_backslash", "tex_math_double_backslash",
            "raw_html", "raw_tex", "native_divs", "native_spans"
        ]
        
        for i, ext in enumerate(common_extensions):
            check = QCheckBox(ext.replace('_', ' ').title())
            check.setObjectName(ext)
            self.extension_checks[ext] = check
            ext_grid.addWidget(check, i // 4, i % 4)
        
        ext_layout.addLayout(ext_grid)
        layout.addWidget(ext_group)
        
        # Custom variables
        vars_group = QGroupBox("Custom Variables")
        vars_layout = QVBoxLayout(vars_group)
        
        self.variables_table = QTableWidget(0, 2)
        self.variables_table.setHorizontalHeaderLabels(["Variable", "Value"])
        self.variables_table.horizontalHeader().setStretchLastSection(True)
        vars_layout.addWidget(self.variables_table)
        
        vars_buttons = QHBoxLayout()
        add_var_btn = QPushButton("Add Variable")
        add_var_btn.clicked.connect(self.add_custom_variable)
        vars_buttons.addWidget(add_var_btn)
        
        remove_var_btn = QPushButton("Remove Variable")
        remove_var_btn.clicked.connect(self.remove_custom_variable)
        vars_buttons.addWidget(remove_var_btn)
        
        vars_buttons.addStretch()
        vars_layout.addLayout(vars_buttons)
        
        layout.addWidget(vars_group)
        
        return widget
    
    def create_info_widget(self):
        """Create Pandoc information widget"""
        group = QGroupBox("Pandoc Information")
        layout = QVBoxLayout(group)
        
        self.pandoc_info_label = QLabel("Checking Pandoc installation...")
        self.pandoc_info_label.setWordWrap(True)
        layout.addWidget(self.pandoc_info_label)
        
        # Update info
        self.update_pandoc_info()
        
        return group
    
    def load_current_settings(self):
        """Load current settings into UI"""
        # General settings
        self.pandoc_path_edit.setText(self.settings.pandoc_path)
        self.standalone_check.setChecked(self.settings.standalone)
        self.toc_check.setChecked(self.settings.table_of_contents)
        self.number_sections_check.setChecked(self.settings.number_sections)
        self.highlight_combo.setCurrentText(self.settings.highlight_style)
        self.export_dir_edit.setText(self.settings.export_directory)
        
        # Templates
        self.html_template_edit.setText(self.settings.html_template)
        self.latex_template_edit.setText(self.settings.latex_template)
        self.css_edit.setText(self.settings.css_file)
        self.reference_docx_edit.setText(self.settings.reference_docx)
        
        # Formats
        self.pdf_engine_combo.setCurrentText(self.settings.pdf_engine)
        self.geometry_edit.setText(self.settings.geometry)
        self.fontsize_edit.setText(self.settings.fontsize)
        self.math_method_combo.setCurrentText(self.settings.html_math_method)
        self.email_obfuscation_combo.setCurrentText(self.settings.email_obfuscation)
        
        # Custom arguments
        self.html_args_edit.setText(' '.join(self.settings.html_args))
        self.pdf_args_edit.setText(' '.join(self.settings.pdf_args))
        self.docx_args_edit.setText(' '.join(self.settings.docx_args))
        
        # Citations
        self.bibliography_edit.setText(self.settings.bibliography)
        self.csl_edit.setText(self.settings.csl_style)
        self.citation_abbrev_edit.setText(self.settings.citation_abbreviations)
        
        # Advanced - Lua filters
        for filter_path in self.settings.lua_filters:
            self.filters_list.addItem(filter_path)
        
        # Extensions
        for ext in self.settings.extensions:
            if ext in self.extension_checks:
                self.extension_checks[ext].setChecked(True)
        
        # Custom variables
        for key, value in self.settings.custom_variables.items():
            self.add_custom_variable(key, value)
    
    def save_settings(self):
        """Save UI settings back to settings object"""
        # General
        self.settings.pandoc_path = self.pandoc_path_edit.text()
        self.settings.standalone = self.standalone_check.isChecked()
        self.settings.table_of_contents = self.toc_check.isChecked()
        self.settings.number_sections = self.number_sections_check.isChecked()
        self.settings.highlight_style = self.highlight_combo.currentText()
        self.settings.export_directory = self.export_dir_edit.text()
        
        # Templates
        self.settings.html_template = self.html_template_edit.text()
        self.settings.latex_template = self.latex_template_edit.text()
        self.settings.css_file = self.css_edit.text()
        self.settings.reference_docx = self.reference_docx_edit.text()
        
        # Formats
        self.settings.pdf_engine = self.pdf_engine_combo.currentText()
        self.settings.geometry = self.geometry_edit.text()
        self.settings.fontsize = self.fontsize_edit.text()
        self.settings.html_math_method = self.math_method_combo.currentText()
        self.settings.email_obfuscation = self.email_obfuscation_combo.currentText()
        
        # Custom arguments
        self.settings.html_args = self.html_args_edit.text().split() if self.html_args_edit.text() else []
        self.settings.pdf_args = self.pdf_args_edit.text().split() if self.pdf_args_edit.text() else []
        self.settings.docx_args = self.docx_args_edit.text().split() if self.docx_args_edit.text() else []
        
        # Citations
        self.settings.bibliography = self.bibliography_edit.text()
        self.settings.csl_style = self.csl_edit.text()
        self.settings.citation_abbreviations = self.citation_abbrev_edit.text()
        
        # Lua filters
        self.settings.lua_filters = []
        for i in range(self.filters_list.count()):
            self.settings.lua_filters.append(self.filters_list.item(i).text())
        
        # Extensions
        self.settings.extensions = []
        for ext, check in self.extension_checks.items():
            if check.isChecked():
                self.settings.extensions.append(ext)
        
        # Custom variables
        self.settings.custom_variables = {}
        for row in range(self.variables_table.rowCount()):
            key_item = self.variables_table.item(row, 0)
            value_item = self.variables_table.item(row, 1)
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key:
                    self.settings.custom_variables[key] = value
    
    def browse_pandoc_executable(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Pandoc Executable", "",
            "Executable files (*.exe);;All files (*)"
        )
        if file_path:
            self.pandoc_path_edit.setText(file_path)
            self.update_pandoc_info()
    
    def browse_export_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if dir_path:
            self.export_dir_edit.setText(dir_path)
    
    def browse_file(self, line_edit: QLineEdit, title: str, file_filter: str = "All files (*)"):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select {title}", "", file_filter)
        if file_path:
            line_edit.setText(file_path)
    
    def add_lua_filter(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Lua Filter", "", "Lua files (*.lua);;All files (*)"
        )
        if file_path:
            self.filters_list.addItem(file_path)
    
    def remove_lua_filter(self):
        current_row = self.filters_list.currentRow()
        if current_row >= 0:
            self.filters_list.takeItem(current_row)
    
    def add_custom_variable(self, key: str = "", value: str = ""):
        row = self.variables_table.rowCount()
        self.variables_table.insertRow(row)
        self.variables_table.setItem(row, 0, QTableWidgetItem(key))
        self.variables_table.setItem(row, 1, QTableWidgetItem(value))
    
    def remove_custom_variable(self):
        current_row = self.variables_table.currentRow()
        if current_row >= 0:
            self.variables_table.removeRow(current_row)
    
    def update_pandoc_info(self):
        """Update Pandoc installation information"""
        # Create temporary manager with current path
        temp_settings = PandocSettings()
        temp_settings.pandoc_path = self.pandoc_path_edit.text() or "pandoc"
        temp_manager = PandocManager()
        temp_manager.settings = temp_settings
        
        installed, info = temp_manager.check_pandoc_installation()
        
        if installed:
            formats = temp_manager.get_supported_formats()
            input_count = len(formats['input'])
            output_count = len(formats['output'])
            
            info_text = f"""
            ✅ {info}
            📥 Input formats: {input_count}
            📤 Output formats: {output_count}
            📁 Executable: {temp_settings.pandoc_path}
            """
            self.pandoc_info_label.setStyleSheet("color: #4caf50;")
        else:
            info_text = f"❌ {info}\n\nPlease install Pandoc or specify the correct path."
            self.pandoc_info_label.setStyleSheet("color: #f44336;")
        
        self.pandoc_info_label.setText(info_text.strip())
    
    def test_pandoc(self):
        """Test Pandoc installation with current settings"""
        self.update_pandoc_info()
        
        # Test with a simple conversion
        temp_settings = PandocSettings()
        temp_settings.pandoc_path = self.pandoc_path_edit.text() or "pandoc"
        temp_manager = PandocManager()
        temp_manager.settings = temp_settings
        
        try:
            # Create a temporary markdown file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write("# Test\n\nThis is a test document.")
                temp_md = f.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                temp_html = f.name
            
            # Try conversion
            success, message = temp_manager.export_file(temp_md, temp_html, 'html')
            
            # Clean up
            os.unlink(temp_md)
            if os.path.exists(temp_html):
                os.unlink(temp_html)
            
            if success:
                QMessageBox.information(self, "Test Successful", "Pandoc is working correctly!")
            else:
                QMessageBox.warning(self, "Test Failed", f"Pandoc test failed:\n{message}")
                
        except Exception as e:
            QMessageBox.warning(self, "Test Error", f"Could not test Pandoc:\n{str(e)}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings = PandocSettings()
            self.load_current_settings()
            self.update_pandoc_info()
    
    def accept(self):
        """Save settings and close dialog"""
        self.save_settings()
        self.pandoc_manager.save_settings()
        super().accept()


class ExportDialog(QDialog):
    """Dialog for exporting files with format-specific options"""
    
    def __init__(self, pandoc_manager: PandocManager, current_file: str, parent=None):
        super().__init__(parent)
        self.pandoc_manager = pandoc_manager
        self.current_file = current_file
        
        self.setWindowTitle("Export Document")
        self.setMinimumSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Export format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        
        # Get supported formats from Pandoc
        formats = self.pandoc_manager.get_supported_formats()
        common_formats = [
            ("HTML", "html"), ("PDF", "pdf"), ("Word Document", "docx"),
            ("OpenDocument", "odt"), ("EPUB", "epub"), ("LaTeX", "latex"),
            ("Beamer Slides", "beamer"), ("PowerPoint", "pptx"),
            ("Rich Text", "rtf"), ("Plain Text", "plain")
        ]
        
        for name, format_code in common_formats:
            if format_code in formats.get('output', []):
                self.format_combo.addItem(name, format_code)
        
        format_layout.addWidget(self.format_combo)
        layout.addWidget(format_group)
        
        # Output file selection
        output_group = QGroupBox("Output File")
        output_layout = QVBoxLayout(output_group)
        
        file_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        file_layout.addWidget(self.output_file_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_file)
        file_layout.addWidget(browse_btn)
        
        output_layout.addLayout(file_layout)
        layout.addWidget(output_group)
        
        # Options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)
        
        self.standalone_check = QCheckBox("Standalone document")
        self.standalone_check.setChecked(self.pandoc_manager.settings.standalone)
        options_layout.addRow("", self.standalone_check)
        
        self.toc_check = QCheckBox("Include table of contents")
        self.toc_check.setChecked(self.pandoc_manager.settings.table_of_contents)
        options_layout.addRow("", self.toc_check)
        
        self.number_sections_check = QCheckBox("Number sections")
        self.number_sections_check.setChecked(self.pandoc_manager.settings.number_sections)
        options_layout.addRow("", self.number_sections_check)
        
        layout.addWidget(options_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        settings_btn = QPushButton("Advanced Settings...")
        settings_btn.clicked.connect(self.show_advanced_settings)
        button_layout.addWidget(settings_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_file)
        export_btn.setDefault(True)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
        # Connect format change to update output file
        self.format_combo.currentTextChanged.connect(self.update_output_file)
        self.update_output_file()
    
    def update_output_file(self):
        """Update output filename based on selected format"""
        if not self.current_file:
            return
        
        format_code = self.format_combo.currentData()
        base_name = Path(self.current_file).stem
        
        extensions = {
            'html': '.html',
            'pdf': '.pdf',
            'docx': '.docx',
            'odt': '.odt',
            'epub': '.epub',
            'latex': '.tex',
            'beamer': '.tex',
            'pptx': '.pptx',
            'rtf': '.rtf',
            'plain': '.txt'
        }
        
        ext = extensions.get(format_code, '.html')
        
        # Use export directory if set
        if self.pandoc_manager.settings.export_directory:
            output_dir = Path(self.pandoc_manager.settings.export_directory)
        else:
            output_dir = Path(self.current_file).parent
        
        output_file = output_dir / f"{base_name}{ext}"
        self.output_file_edit.setText(str(output_file))
    
    def browse_output_file(self):
        """Browse for output file location"""
        format_code = self.format_combo.currentData()
        format_name = self.format_combo.currentText()
        
        extensions = {
            'html': 'HTML files (*.html)',
            'pdf': 'PDF files (*.pdf)',
            'docx': 'Word files (*.docx)',
            'odt': 'ODT files (*.odt)',
            'epub': 'EPUB files (*.epub)',
            'latex': 'LaTeX files (*.tex)',
            'beamer': 'LaTeX files (*.tex)',
            'pptx': 'PowerPoint files (*.pptx)',
            'rtf': 'RTF files (*.rtf)',
            'plain': 'Text files (*.txt)'
        }
        
        file_filter = extensions.get(format_code, 'All files (*)')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {format_name}", 
            self.output_file_edit.text(),
            f"{file_filter};;All files (*)"
        )
        
        if file_path:
            self.output_file_edit.setText(file_path)
    
    def show_advanced_settings(self):
        """Show advanced Pandoc settings dialog"""
        dialog = AdvancedPandocDialog(self.pandoc_manager, self)
        dialog.exec()
    
    def export_file(self):
        """Perform the export"""
        output_file = self.output_file_edit.text()
        if not output_file:
            QMessageBox.warning(self, "Export Error", "Please specify an output file.")
            return
        
        format_code = self.format_combo.currentData()
        
        # Update temporary settings with dialog options
        original_standalone = self.pandoc_manager.settings.standalone
        original_toc = self.pandoc_manager.settings.table_of_contents
        original_number = self.pandoc_manager.settings.number_sections
        
        self.pandoc_manager.settings.standalone = self.standalone_check.isChecked()
        self.pandoc_manager.settings.table_of_contents = self.toc_check.isChecked()
        self.pandoc_manager.settings.number_sections = self.number_sections_check.isChecked()
        
        try:
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # Disable buttons
            for btn in self.findChildren(QPushButton):
                btn.setEnabled(False)
            
            # Export
            QApplication.processEvents()
            success, message = self.pandoc_manager.export_file(
                self.current_file, output_file, format_code
            )
            
            if success:
                QMessageBox.information(self, "Export Successful", message)
                self.accept()
            else:
                QMessageBox.warning(self, "Export Failed", message)
        
        finally:
            # Restore original settings
            self.pandoc_manager.settings.standalone = original_standalone
            self.pandoc_manager.settings.table_of_contents = original_toc
            self.pandoc_manager.settings.number_sections = original_number
            
            # Hide progress and re-enable buttons
            self.progress_bar.setVisible(False)
            for btn in self.findChildren(QPushButton):
                btn.setEnabled(True)


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # Test the Pandoc manager
    manager = PandocManager()
    
    # Show settings dialog
    dialog = AdvancedPandocDialog(manager)
    if dialog.exec() == QDialog.Accepted:
        print("Settings saved!")
        print(f"Pandoc path: {manager.settings.pandoc_path}")
        print(f"Export directory: {manager.settings.export_directory}")
    
    # Test export dialog (would need a real file)
    # export_dialog = ExportDialog(manager, "/path/to/test.md")
    # export_dialog.exec()
    
    sys.exit(app.exec())