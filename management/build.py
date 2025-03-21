#!/usr/bin/env python3
"""
Build script for the Repository Category Manager GUI.
This script creates an executable version of the category manager and improves its appearance.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import PyQt6
        print("✅ PyQt6 is installed")
    except ImportError:
        print("❌ PyQt6 is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
        print("✅ PyQt6 installed successfully")
    
    # Check for PyInstaller (needed for creating executable)
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
    except ImportError:
        print("❌ PyInstaller is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])
        print("✅ PyInstaller installed successfully")

def create_executable():
    """Create an executable version of the category manager."""
    print("Creating executable...")
    
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Create a spec file for PyInstaller
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{current_dir}/category_manager_qt.py'],
    pathex=['{current_dir}'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='category_manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
    """
    
    # Write the spec file
    spec_file = current_dir / "category_manager.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller
    subprocess.check_call([sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"])
    
    # Move the executable to the management directory
    dist_dir = current_dir / "dist"
    if os.path.exists(dist_dir / "category_manager"):
        shutil.copy(dist_dir / "category_manager", current_dir)
        print(f"✅ Executable created at {current_dir}/category_manager")
    else:
        print("❌ Failed to create executable")

def enhance_appearance():
    """Enhance the appearance of the category manager by updating the UI code."""
    print("Enhancing appearance...")
    
    # Path to the category manager file
    manager_file = Path(__file__).parent / "category_manager_qt.py"
    
    # Read the current content
    with open(manager_file, "r") as f:
        content = f.read()
    
    # Define the style sheet for improved appearance
    style_sheet = """
        app.setStyleSheet('''
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                selection-background-color: #0078D4;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QScrollArea {
                border: none;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        ''')
    """
    
    # Insert the style sheet into the main function
    if "def main():" in content:
        # Find the position to insert the style sheet
        main_pos = content.find("def main():")
        app_pos = content.find("app = QApplication(sys.argv)", main_pos)
        style_pos = content.find("app.setStyle(QStyleFactory.create(\"Fusion\"))", app_pos)
        
        if style_pos > 0:
            # Insert after the setStyle line
            insert_pos = content.find("\n", style_pos) + 1
            modified_content = content[:insert_pos] + style_sheet + content[insert_pos:]
            
            # Write the modified content back
            with open(manager_file, "w") as f:
                f.write(modified_content)
            
            print("✅ Enhanced appearance with custom style sheet")
        else:
            print("❌ Could not find position to insert style sheet")
    else:
        print("❌ Could not find main function")

def create_desktop_entry():
    """Create a desktop entry for easy launching."""
    print("Creating desktop entry...")
    
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    
    # Create desktop entry content
    desktop_entry = f"""[Desktop Entry]
Name=Repository Category Manager
Comment=Manage GitHub repository categories
Exec={current_dir}/category_manager
Terminal=false
Type=Application
Categories=Development;
"""
    
    # Write the desktop entry file
    desktop_file = Path.home() / ".local" / "share" / "applications" / "repo-category-manager.desktop"
    
    # Create directory if it doesn't exist
    desktop_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(desktop_file, "w") as f:
        f.write(desktop_entry)
    
    # Make the desktop entry executable
    os.chmod(desktop_file, 0o755)
    
    print(f"✅ Desktop entry created at {desktop_file}")

def create_launcher_script():
    """Create a simple launcher script."""
    print("Creating launcher script...")
    
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    
    # Create launcher script content
    launcher_script = f"""#!/bin/bash
# Launcher script for Repository Category Manager

# Change to the script directory
cd "{current_dir}"

# Run the executable
./category_manager

# If executable fails, try running the Python script directly
if [ $? -ne 0 ]; then
    echo "Executable failed, trying Python script..."
    python3 category_manager_qt.py
fi
"""
    
    # Write the launcher script
    launcher_file = current_dir / "launch_manager.sh"
    
    with open(launcher_file, "w") as f:
        f.write(launcher_script)
    
    # Make the launcher script executable
    os.chmod(launcher_file, 0o755)
    
    print(f"✅ Launcher script created at {launcher_file}")

def main():
    """Main function to build the category manager."""
    print("Building Repository Category Manager...")
    
    # Check dependencies
    check_dependencies()
    
    # Enhance appearance
    enhance_appearance()
    
    # Create executable
    create_executable()
    
    # Create launcher script
    create_launcher_script()
    
    # Create desktop entry
    create_desktop_entry()
    
    print("\n✅ Build completed successfully!")
    print("You can now run the category manager using:")
    print("  1. The executable: ./category_manager")
    print("  2. The launcher script: ./launch_manager.sh")
    print("  3. From the application menu (if desktop entry was created successfully)")

if __name__ == "__main__":
    main()
