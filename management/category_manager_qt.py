#!/usr/bin/env python3
import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                           QPushButton, QTableWidget, QTableWidgetItem, 
                           QCheckBox, QScrollArea, QFrame, QStatusBar,
                           QStyle, QStyleFactory, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

class CategoryManagerQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Repository Category Manager")
        self.setMinimumSize(1200, 700)
        
        # Get base path
        self.base_path = Path(__file__).parent.parent
        
        # Initialize data
        self.repos = self.load_repos()
        self.categories = self.load_categories()
        self.category_assignments = self.load_current_assignments()
        
        # Setup UI
        self.setup_ui()
        self.setup_shortcuts()
        self.populate_repos()
        
        # Show status message
        self.statusBar().showMessage("Ready")
        
    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)
        
        # Create search bar
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_label = QLabel("Search:")
        search_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search repositories...")
        self.search_input.textChanged.connect(self.filter_repos)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # Create repository table
        self.repo_table = QTableWidget()
        self.repo_table.setColumnCount(1)
        self.repo_table.setHorizontalHeaderLabels(["Repository"])
        self.repo_table.horizontalHeader().setStretchLastSection(True)
        self.repo_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.repo_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.repo_table.itemSelectionChanged.connect(self.on_repo_select)
        
        # Create categories section
        categories_frame = QFrame()
        categories_layout = QVBoxLayout(categories_frame)
        
        # Categories header
        cat_header = QFrame()
        cat_header_layout = QHBoxLayout(cat_header)
        cat_label = QLabel("Categories")
        cat_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.cat_search = QLineEdit()
        self.cat_search.setPlaceholderText("Filter categories...")
        self.cat_search.textChanged.connect(self.filter_categories)
        new_cat_btn = QPushButton("New Category")
        new_cat_btn.clicked.connect(self.show_new_category_dialog)
        cat_header_layout.addWidget(cat_label)
        cat_header_layout.addWidget(self.cat_search)
        cat_header_layout.addWidget(new_cat_btn)
        
        # Categories scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Categories content
        self.cat_widget = QWidget()
        self.cat_layout = QVBoxLayout(self.cat_widget)
        self.category_checkboxes = {}
        
        # Create checkboxes for categories
        for category in sorted(self.categories):
            checkbox = QCheckBox(category)
            checkbox.stateChanged.connect(self.on_category_toggle)
            self.category_checkboxes[category] = checkbox
            self.cat_layout.addWidget(checkbox)
        
        # Add stretch to push checkboxes to the top
        self.cat_layout.addStretch()
        
        # Setup scroll area
        scroll.setWidget(self.cat_widget)
        
        # Add categories components to layout
        categories_layout.addWidget(cat_header)
        categories_layout.addWidget(scroll)
        
        # Create save button
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        save_btn.clicked.connect(self.save_changes)
        
        # Add all components to main layout
        main_layout.addWidget(search_frame, 0, 0, 1, 2)
        main_layout.addWidget(self.repo_table, 1, 0)
        main_layout.addWidget(categories_frame, 1, 1)
        main_layout.addWidget(save_btn, 2, 0, 1, 2)
        
        # Create status bar
        self.statusBar().setFont(QFont("Segoe UI", 9))
        
        # Set layout spacing and margins
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
    def setup_shortcuts(self):
        # Add keyboard shortcuts hint to status bar
        self.statusBar().showMessage("Shortcuts: Ctrl+S (Save), Ctrl+F (Search), Ctrl+N (New Category)")
    
    def load_repos(self):
        """Load repositories from data/repos.txt"""
        repos = []
        try:
            with open(self.base_path / "data" / "repos.txt", "r") as f:
                for line in f:
                    repo = line.split('|')[1].strip() if '|' in line else line.strip()
                    if repo:
                        repos.append(repo)
        except Exception as e:
            self.show_error(f"Error loading repos: {str(e)}")
        return repos
    
    def load_categories(self):
        """Load available categories from lists/categories directory"""
        categories = []
        try:
            category_dir = self.base_path / "lists" / "categories"
            for file in os.listdir(category_dir):
                if file.endswith('.txt'):
                    categories.append(file[:-4])
        except Exception as e:
            self.show_error(f"Error loading categories: {str(e)}")
        return sorted(categories)
    
    def load_current_assignments(self):
        """Load current category assignments"""
        assignments = {repo: [] for repo in self.repos}
        for category in self.categories:
            try:
                with open(self.base_path / "lists" / "categories" / f"{category}.txt", "r") as f:
                    repos = [line.split('|')[1].strip() if '|' in line else line.strip() 
                            for line in f if line.strip()]
                    for repo in repos:
                        if repo in assignments:
                            assignments[repo].append(category)
            except Exception as e:
                self.show_error(f"Error loading assignments for {category}: {str(e)}")
        return assignments
    
    def populate_repos(self):
        """Populate repository table"""
        self.repo_table.setRowCount(len(self.repos))
        for i, repo in enumerate(self.repos):
            item = QTableWidgetItem(repo)
            self.repo_table.setItem(i, 0, item)
    
    def filter_repos(self):
        """Filter repositories based on search input"""
        search_text = self.search_input.text().lower()
        for i in range(self.repo_table.rowCount()):
            item = self.repo_table.item(i, 0)
            if item:
                row_hidden = search_text not in item.text().lower()
                self.repo_table.setRowHidden(i, row_hidden)
    
    def filter_categories(self):
        """Filter categories based on search input"""
        search_text = self.cat_search.text().lower()
        for category, checkbox in self.category_checkboxes.items():
            checkbox.setVisible(search_text in category.lower())
    
    def on_repo_select(self):
        """Handle repository selection"""
        selected_items = self.repo_table.selectedItems()
        if not selected_items:
            return
            
        repo = selected_items[0].text()
        # Update category checkboxes
        for category, checkbox in self.category_checkboxes.items():
            checkbox.setChecked(category in self.category_assignments.get(repo, []))
    
    def on_category_toggle(self):
        """Handle category checkbox toggle"""
        selected_items = self.repo_table.selectedItems()
        if not selected_items:
            return
            
        repo = selected_items[0].text()
        self.category_assignments[repo] = [
            category for category, checkbox in self.category_checkboxes.items()
            if checkbox.isChecked()
        ]
    
    def save_changes(self):
        """Save category assignments to files"""
        try:
            # Create reverse mapping of repo to categories
            category_repos = {category: [] for category in self.categories}
            for repo, categories in self.category_assignments.items():
                for category in categories:
                    category_repos[category].append(repo)
            
            # Save each category file
            for category, repos in category_repos.items():
                with open(self.base_path / "lists" / "categories" / f"{category}.txt", "w") as f:
                    for repo in sorted(repos):
                        f.write(f"{repo}\n")
            
            self.statusBar().showMessage("Changes saved successfully!", 3000)
        except Exception as e:
            self.show_error(f"Error saving changes: {str(e)}")
    
    def show_new_category_dialog(self):
        """Show dialog to create new category"""
        # TODO: Implement new category dialog
        self.statusBar().showMessage("New category feature coming soon!", 3000)
    
    def show_error(self, message):
        """Show error message box"""
        QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Create and show the main window
    window = CategoryManagerQt()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
