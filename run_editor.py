#!/usr/bin/env python3
"""
Run Editor - Main Entry Point
Launch the Advanced Markdown Editor application
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path so we can import our modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    
    # Import our main application
    from main_editor_app import EnhancedMainWindow
    
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("\nPlease install the required dependencies:")
    print("pip install PySide6 markdown PyYAML")
    sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import markdown
    except ImportError:
        missing_deps.append("markdown")
    
    try:
        import yaml
    except ImportError:
        missing_deps.append("PyYAML")
    
    return missing_deps


def main():
    """Main application entry point"""
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them with:")
        print(f"pip install {' '.join(missing_deps)}")
        return 1
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Advanced Markdown Editor")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Markdown Editor Team")
    app.setOrganizationDomain("markdowneditor.local")
    
    # Set application icon if available
    icon_path = current_dir / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Handle high DPI displays (Qt 6+ handles this automatically)
    # These attributes are deprecated in Qt 6
    pass
    
    try:
        # Create and show main window
        window = EnhancedMainWindow()
        window.show()
        
        # Load sample content if no file specified
        if len(sys.argv) > 1:
            # Open file specified in command line
            file_path = sys.argv[1]
            if Path(file_path).exists():
                window.open_file(file_path)
            else:
                print(f"Warning: File '{file_path}' not found")
        else:
            # Load welcome content
            load_welcome_content(window)
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        # Show error dialog
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Application Error")
        error_dialog.setText("An unexpected error occurred:")
        error_dialog.setDetailedText(str(e))
        error_dialog.exec()
        return 1


def load_welcome_content(window):
    """Load welcome content into the editor"""
    welcome_content = """---
title: "Welcome to Advanced Markdown Editor"
author: "Markdown Editor Team"
date: "2025-01-18"
tags: ["markdown", "editor", "welcome"]
categories: ["documentation"]
description: "Welcome guide for the Advanced Markdown Editor"
---

# 🎉 Welcome to Advanced Markdown Editor

A **professional** markdown editor with *perfect* bidirectional synchronization!

## ✨ Key Features

### 🔄 **Perfect Bidirectional Sync**
- Edit in **either** the markdown source or the live preview
- Changes sync instantly without content loss
- No more jumping or broken formatting

### 📁 **File Management**
- **File Explorer** - Browse and open files easily
- **Document Outline** - Navigate through headings with one click
- **Recent Files** - Quick access to your documents

### 🎨 **Beautiful Interface**
- **Dark Theme** - Easy on the eyes for long writing sessions
- **Live Syntax Highlighting** - See your markdown come to life
- **Smooth Animations** - Professional, polished experience

### ⚡ **Quick Actions**
Use the toolbar for instant formatting:

| Button | Action | Shortcut |
|--------|--------|----------|
| **B** | Bold text | Ctrl+B |
| **I** | Italic text | Ctrl+I |
| **`** | Inline code | - |
| **H1-H3** | Headers | - |
| **Table** | Insert table | - |
| **Link** | Insert link | - |
| **Image** | Insert image | - |

### 📝 **Front Matter Support**
- Complete **YAML metadata** management
- Document properties dialog (Ctrl+Alt+P)
- Custom fields for any metadata you need

## 🚀 **Getting Started**

### Try These Features:

1. **Bidirectional Editing**
   - Type in the left pane (markdown source)
   - Or click and edit directly in the right pane (preview)
   - Watch how both stay perfectly synchronized!

2. **File Explorer**
   - Click the "Files" tab in the sidebar
   - Navigate to any directory
   - Double-click to open markdown files

3. **Document Outline**
   - Click the "Outline" tab in the sidebar
   - See all your headings in a tree structure
   - Click any heading to jump to that section

4. **Quick Formatting**
   - Select text and click toolbar buttons
   - Use keyboard shortcuts for speed
   - Try bold (**Ctrl+B**) and italic (*Ctrl+I*)

### 📖 **Sample Content**

Here's some **markdown** to play with:

#### Code Blocks
```python
def hello_world():
    print("Hello from the markdown editor!")
    return "Perfect sync achieved! 🎉"

# Try editing this code in the preview pane!
```

#### Lists Work Great
- ✅ Unordered lists
- ✅ Perfect sync between panes
- ✅ Add items by pressing Enter
  - Nested items work too
  - Edit directly in preview!

1. ✅ Ordered lists
2. ✅ Auto-numbering
3. ✅ Easy editing

#### Blockquotes
> "This editor provides the smooth, professional experience you wanted!"
> 
> Try editing this quote in the preview pane and watch the markdown update automatically.

#### Links and Images
Check out the [Markdown Guide](https://www.markdownguide.org) for more syntax.

![Sample Image](https://via.placeholder.com/400x200/4fc3f7/ffffff?text=Advanced+Markdown+Editor)

---

## 🔧 **Keyboard Shortcuts**

| Shortcut | Action |
|----------|--------|
| **Ctrl+N** | New file |
| **Ctrl+O** | Open file |
| **Ctrl+S** | Save file |
| **Ctrl+Shift+S** | Save as |
| **Ctrl+Alt+P** | Document properties |
| **Ctrl+\\** | Toggle sidebar |
| **Ctrl+P** | Toggle preview |
| **F11** | Focus mode |

## 🎯 **What Makes This Special?**

Unlike other markdown editors, this one provides:
- **True bidirectional editing** - Edit in preview without breaking markdown
- **Perfect synchronization** - No content loss or formatting issues
- **Professional polish** - Smooth animations and responsive interface
- **Complete feature set** - Everything you need in one application

**Start writing and experience the difference!** ✨

---

*Tip: Press **F11** for distraction-free writing mode*
"""
    
    window.editor.setPlainText(welcome_content)


if __name__ == "__main__":
    sys.exit(main())