// Simple search functionality for repository index
document.addEventListener('DOMContentLoaded', function() {
    // Create search container
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';
    searchContainer.style.margin = '20px 0';
    searchContainer.style.padding = '10px';
    searchContainer.style.backgroundColor = '#f6f8fa';
    searchContainer.style.borderRadius = '6px';
    
    // Create search input
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'repo-search';
    searchInput.placeholder = 'Search repositories...';
    searchInput.style.width = '100%';
    searchInput.style.padding = '8px 12px';
    searchInput.style.fontSize = '16px';
    searchInput.style.border = '1px solid #ddd';
    searchInput.style.borderRadius = '4px';
    
    // Add elements to DOM
    searchContainer.appendChild(searchInput);
    
    // Insert after the first h1
    const firstHeading = document.querySelector('h1');
    if (firstHeading && firstHeading.nextElementSibling) {
        firstHeading.parentNode.insertBefore(searchContainer, firstHeading.nextElementSibling.nextElementSibling);
    }
    
    // Search functionality
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const repoLinks = document.querySelectorAll('a[href*="sections/"]');
        
        repoLinks.forEach(link => {
            const listItem = link.closest('li');
            if (!listItem) return;
            
            const repoName = link.textContent.toLowerCase();
            if (repoName.includes(searchTerm)) {
                listItem.style.display = '';
            } else {
                listItem.style.display = 'none';
            }
        });
    });
});
