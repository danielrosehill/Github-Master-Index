#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                           QPushButton, QTableWidget, QTableWidgetItem, 
                           QCheckBox, QScrollArea, QFrame, QStatusBar,
                           QStyle, QStyleFactory, QMessageBox, QDialog,
                           QListWidget, QListWidgetItem, QDialogButtonBox,
                           QTabWidget, QComboBox)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont, QShortcut, QKeySequence
import sys
sys.path.append(str(Path(__file__).parent.parent))
from scripts.auto_categorizer import AutoCategorizer

class CategoryManagerQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Repository Category Manager")
        self.setMinimumSize(1200, 700)
        
        # Get base path
        self.base_path = Path(__file__).parent.parent

        # Initialize auto-categorizer
        self.auto_categorizer = AutoCategorizer()
        
        # Initialize data
        self.repos = self.load_repos()
        self.repo_metadata = self.load_repo_metadata()
        self.categories = self.load_categories()
        self.category_assignments = self.load_current_assignments()
        self.uncategorized_repos = self.get_uncategorized_repos()

        # Setup UI
        self.setup_ui()
        self.setup_shortcuts()
        self.populate_repos()
        
        # Show status message
        self.statusBar().showMessage("Ready")
        
    def get_uncategorized_repos(self):
        """Get list of repositories without any category"""
        uncategorized = []
        for repo in self.repos:
            if not self.category_assignments.get(repo, []):
                uncategorized.append(repo)
        return uncategorized
        
    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)
        
        # Create search bar and sort options
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_label = QLabel("Search:")
        search_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search repositories...")
        self.search_input.textChanged.connect(self.filter_repos)
        
        # Add sort options
        sort_label = QLabel("Sort by:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Alphabetical", "Creation Date (Newest First)"])
        self.sort_combo.currentIndexChanged.connect(self.sort_repos)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(sort_label)
        search_layout.addWidget(self.sort_combo)

        # Add filter for uncategorized repos
        show_uncategorized_btn = QPushButton("Show Uncategorized")
        show_uncategorized_btn.clicked.connect(self.show_uncategorized)
        search_layout.addWidget(show_uncategorized_btn)
        
        # Create repository table
        self.repo_table = QTableWidget()
        self.repo_table.setColumnCount(2)
        self.repo_table.setHorizontalHeaderLabels(["Repository", "Categories"])
        self.repo_table.horizontalHeader().setStretchLastSection(True)
        self.repo_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Change to multi-selection mode for batch operations
        self.repo_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Add batch operations panel
        batch_frame = QFrame()
        batch_layout = QHBoxLayout(batch_frame)
        batch_label = QLabel("Batch Operations:")
        batch_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        auto_categorize_btn = QPushButton("Auto-Categorize Selected")
        auto_categorize_btn.clicked.connect(self.auto_categorize_selected)
        apply_category_btn = QPushButton("Apply Selected Categories")
        apply_category_btn.clicked.connect(self.apply_categories_to_selected)
        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(auto_categorize_btn)
        batch_layout.addWidget(apply_category_btn)
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

        # Add suggested categories section
        suggested_label = QLabel("Suggested Categories")
        suggested_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.suggested_list = QListWidget()
        self.suggested_list.itemClicked.connect(self.on_suggestion_click)
        
        self.cat_layout.addWidget(suggested_label)
        self.cat_layout.addWidget(self.suggested_list)
        
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
        main_layout.addWidget(batch_frame, 2, 0)
        main_layout.addWidget(categories_frame, 1, 1, 2, 1)
        main_layout.addWidget(save_btn, 2, 0, 1, 2)
        
        # Create status bar
        self.statusBar().setFont(QFont("Segoe UI", 9))
        
        # Set layout spacing and margins
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common operations"""
        # Save shortcut
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_changes)
        
        # Search shortcut
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(lambda: self.search_input.setFocus())
        
        # New category shortcut
        new_cat_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_cat_shortcut.activated.connect(self.show_new_category_dialog)
        
        self.statusBar().showMessage("Shortcuts: Ctrl+S (Save), Ctrl+F (Search), Ctrl+N (New Category), 1-9 (Quick assign categories)")
    
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
    
    def load_repo_metadata(self):
        """Load repository metadata including creation dates"""
        metadata = {}
        try:
            metadata_file = self.base_path / "data" / "exports" / "repo-index.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    repo_data = json.load(f)
                    for repo_info in repo_data:
                        name = repo_info.get("name")
                        if name:
                            metadata[name] = repo_info
        except Exception as e:
            self.show_error(f"Error loading repository metadata: {str(e)}")
        return metadata
    
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
        self.repo_table.setColumnWidth(0, 300)  # Set width for repository name column
        
        for i, repo in enumerate(self.repos):
            name_item = QTableWidgetItem(repo)
            # Store creation date as item data for sorting
            if repo in self.repo_metadata:
                created_at = self.repo_metadata[repo].get("created_at", "")
                if created_at:
                    name_item.setData(Qt.ItemDataRole.UserRole, created_at)
            
            self.repo_table.setItem(i, 0, name_item)
            
            # Add category count
            cat_count = len(self.category_assignments.get(repo, []))
            self.repo_table.setItem(i, 1, QTableWidgetItem(f"{cat_count} categories" if cat_count > 0 else "Uncategorized"))
    
    def filter_repos(self):
        """Filter repositories based on search input"""
        search_text = self.search_input.text().lower()
        for i in range(self.repo_table.rowCount()):
            item = self.repo_table.item(i, 0)
            if item:
                row_hidden = search_text not in item.text().lower()
                self.repo_table.setRowHidden(i, row_hidden)
                
    def show_uncategorized(self):
        """Show only uncategorized repositories"""
        for i in range(self.repo_table.rowCount()):
            item = self.repo_table.item(i, 0)
            if item:
                repo_name = item.text()
                has_categories = len(self.category_assignments.get(repo_name, [])) > 0
                self.repo_table.setRowHidden(i, has_categories)
        self.statusBar().showMessage("Showing uncategorized repositories", 3000)
    
    def filter_categories(self):
        """Filter categories based on search input"""
        search_text = self.cat_search.text().lower()
        for category, checkbox in self.category_checkboxes.items():
            checkbox.setVisible(search_text in category.lower())
    
    def update_suggested_categories(self, repo_name):
        """Update suggested categories for the selected repository"""
        self.suggested_list.clear()
        
        # Get repository data from JSON if available
        repo_data = self.get_repo_data(repo_name)
        description = repo_data.get("description", "") if repo_data else ""
        
        # Get suggestions
        suggestions = self.auto_categorizer.suggest_categories(repo_name, description)
        
        # Add to list widget
        for category in suggestions:
            if category not in self.category_assignments.get(repo_name, []):
                self.suggested_list.addItem(category)
    
    def on_repo_select(self):
        """Handle repository selection"""
        selected_items = self.repo_table.selectedItems()
        if not selected_items:
            return
        self.update_selection_ui()
    
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
        
    def on_suggestion_click(self, item):
        """Handle click on a suggested category"""
        category = item.text()
        selected_items = self.repo_table.selectedItems()
        if not selected_items:
            return
            
        repo = selected_items[0].text()
        
        # Add the category to the repository
        if category not in self.category_assignments.get(repo, []):
            self.category_assignments[repo].append(category)
            
        # Update checkbox
        if category in self.category_checkboxes:
            self.category_checkboxes[category].setChecked(True)
            
        # Remove from suggestions
        self.suggested_list.takeItem(self.suggested_list.row(item))
        
    def update_selection_ui(self):
        """Update UI based on current selection"""
        selected_rows = set(item.row() for item in self.repo_table.selectedItems())
        
        if len(selected_rows) == 1:
            # Single selection - show categories and suggestions
            repo = self.repo_table.item(list(selected_rows)[0], 0).text()
            
            # Update category checkboxes
            for category, checkbox in self.category_checkboxes.items():
                checkbox.setChecked(category in self.category_assignments.get(repo, []))
                
            # Update suggested categories
            self.update_suggested_categories(repo)
        else:
            # Multiple selection - clear checkboxes and suggestions
            for checkbox in self.category_checkboxes.values():
                checkbox.setChecked(False)
            self.suggested_list.clear()
            
    def get_repo_data(self, repo_name):
        """Get repository data from JSON file if available"""
        try:
            json_path = self.base_path / "data" / "exports" / "repo-index.json"
            if json_path.exists():
                with open(json_path, "r") as f:
                    repos = json.load(f)
                    for repo in repos:
                        if repo.get("name") == repo_name:
                            return repo
        except Exception as e:
            print(f"Error loading repo data: {e}")
        return None
        
    def get_selected_repos(self):
        """Get names of currently selected repositories"""
        return [self.repo_table.item(row, 0).text() for row in set(item.row() for item in self.repo_table.selectedItems())]
    
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
            
    def auto_categorize_selected(self):
        """Auto-categorize selected repositories"""
        selected_repos = self.get_selected_repos()
        if not selected_repos:
            self.statusBar().showMessage("No repositories selected", 3000)
            return
            
        count = 0
        for repo in selected_repos:
            # Get repository data
            repo_data = self.get_repo_data(repo)
            description = repo_data.get("description", "") if repo_data else ""
            
            # Get suggestions
            suggestions = self.auto_categorizer.suggest_categories(repo, description)
            
            # Apply suggestions
            if suggestions:
                current_categories = self.category_assignments.get(repo, [])
                new_categories = [cat for cat in suggestions if cat not in current_categories]
                if new_categories:
                    self.category_assignments[repo] = current_categories + new_categories
                    count += 1
        
        # Update UI
        self.update_selection_ui()
        self.statusBar().showMessage(f"Auto-categorized {count} repositories", 3000)
        
    def apply_categories_to_selected(self):
        """Apply currently checked categories to all selected repositories"""
        selected_repos = self.get_selected_repos()
        if not selected_repos:
            self.statusBar().showMessage("No repositories selected", 3000)
            return
            
        # Get checked categories
        checked_categories = [
            category for category, checkbox in self.category_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        if not checked_categories:
            self.statusBar().showMessage("No categories selected", 3000)
            return
            
        # Apply to all selected repos
        for repo in selected_repos:
            current_categories = self.category_assignments.get(repo, [])
            new_categories = [cat for cat in checked_categories if cat not in current_categories]
            if new_categories:
                self.category_assignments[repo] = current_categories + new_categories
                
        self.statusBar().showMessage(f"Applied {len(checked_categories)} categories to {len(selected_repos)} repositories", 3000)
    
    def show_new_category_dialog(self):
        """Show dialog to create new category"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Category")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Category Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            category_name = name_input.text().strip()
            if not category_name:
                self.show_error("Category name cannot be empty")
                return
                
            # Check if category already exists
            if category_name in self.categories:
                self.show_error(f"Category '{category_name}' already exists")
                return
                
            # Create category file
            try:
                category_file = self.base_path / "lists" / "categories" / f"{category_name}.txt"
                with open(category_file, "w") as f:
                    pass  # Create empty file
                    
                # Add to categories list
                self.categories.append(category_name)
                
                # Add checkbox for new category
                checkbox = QCheckBox(category_name)
                checkbox.stateChanged.connect(self.on_category_toggle)
                self.category_checkboxes[category_name] = checkbox
                # Insert before the stretch at the end
                self.cat_layout.insertWidget(self.cat_layout.count() - 3, checkbox)
                
                self.statusBar().showMessage(f"Category '{category_name}' created successfully", 3000)
            except Exception as e:
                self.show_error(f"Error creating category: {str(e)}")
                
    def show_error(self, message):
        """Show error message box"""
        QMessageBox.critical(self, "Error", message)
    
    def sort_repos(self):
        """Sort repositories based on selected sort option"""
        sort_option = self.sort_combo.currentText()
        
        if sort_option == "Creation Date (Newest First)":
            # Sort by creation date (newest first)
            self.sort_by_creation_date()
        else:
            # Default: Sort alphabetically
            self.repo_table.sortItems(0, Qt.SortOrder.AscendingOrder)
        
        self.statusBar().showMessage(f"Sorted by {sort_option}", 3000)
    
    def sort_by_creation_date(self):
        """Sort repositories by creation date (newest first)"""
        # Create a list of (row, creation_date) tuples
        row_dates = []
        for row in range(self.repo_table.rowCount()):
            item = self.repo_table.item(row, 0)
            if item:
                # Get creation date from item data
                created_at = item.data(Qt.ItemDataRole.UserRole)
                if created_at:
                    try:
                        date_obj = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                        row_dates.append((row, date_obj))
                    except (ValueError, TypeError):
                        # If date parsing fails, put at the end
                        row_dates.append((row, datetime(1970, 1, 1)))
                else:
                    # No date available, put at the end
                    row_dates.append((row, datetime(1970, 1, 1)))
        
        # Sort by date (newest first)
        row_dates.sort(key=lambda x: x[1], reverse=True)
        
        # Reorder table rows based on sorted dates
        for new_row, (old_row, _) in enumerate(row_dates):
            # Move row old_row to position new_row
            self.move_table_row(old_row, new_row)
    
    def move_table_row(self, from_row, to_row):
        """Move a row in the table from one position to another"""
        if from_row == to_row:
            return
            
        # Save the row data
        row_data = []
        for col in range(self.repo_table.columnCount()):
            item = self.repo_table.item(from_row, col)
            if item:
                new_item = QTableWidgetItem(item.text())
                # Copy user data (like creation date)
                new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
                row_data.append(new_item)
            else:
                row_data.append(None)
        
        # Remove the row
        self.repo_table.removeRow(from_row)
        
        # Insert the row at the new position
        self.repo_table.insertRow(to_row)
        
        # Restore the row data
        for col, item in enumerate(row_data):
            if item:
                self.repo_table.setItem(to_row, col, item)

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
