/**
 * Unified Navigation Bar Component
 * Include this script in all pages to ensure consistent navigation
 */

function createUnifiedNavbar() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    const navbarHTML = `
        <nav class="navbar navbar-expand-lg">
            <div class="container">
                <a class="navbar-brand" href="index.html">
                    <i class="fas fa-balance-scale"></i>
                    LegalSearch Pro
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto align-items-center">
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'index.html' ? 'active' : ''}" href="index.html">
                                <i class="fas fa-search me-1"></i>Search
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'browse.html' ? 'active' : ''}" href="browse.html">
                                <i class="fas fa-folder-open me-1"></i>Browse
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'bookmarks.html' ? 'active' : ''}" href="bookmarks.html">
                                <i class="fas fa-bookmark me-1"></i>Bookmarks
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'analytics-dashboard.html' ? 'active' : ''}" href="analytics-dashboard.html">
                                <i class="fas fa-chart-bar me-1"></i>Analytics
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'recent-searches.html' ? 'active' : ''}" href="recent-searches.html">
                                <i class="fas fa-history me-1"></i>History
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'compare.html' ? 'active' : ''}" href="compare.html">
                                <i class="fas fa-columns me-1"></i>Compare
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'help.html' ? 'active' : ''}" href="help.html">
                                <i class="fas fa-question-circle me-1"></i>Help
                            </a>
                        </li>
                        <li class="nav-item">
                            <button id="theme-toggle-btn" class="nav-link btn btn-link" style="border: none; background: none;">
                                <i class="fas fa-moon"></i>
                            </button>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPage === 'profile.html' ? 'active' : ''}" href="profile.html">
                                <i class="fas fa-user me-1"></i>Account
                            </a>
                        </li>
                        <li class="nav-item" id="auth-links"></li>
                    </ul>
                </div>
            </div>
        </nav>
    `;
    
    // Insert navbar at the beginning of body
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    
    // Initialize auth links
    updateAuthLinks();
    
    // Initialize theme toggle
    initThemeToggle();
}

function updateAuthLinks() {
    const authLinks = document.getElementById('auth-links');
    if (!authLinks) return;
    
    if (localStorage.getItem('isLoggedIn') === 'true') {
        authLinks.innerHTML = `
            <a class="nav-link" href="#" id="logout-link">
                <i class="fas fa-sign-out-alt me-1"></i>Logout
            </a>
        `;
        document.getElementById('logout-link').onclick = function(e) {
            e.preventDefault();
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('userName');
            window.location.href = "login.html";
        };
    } else {
        authLinks.innerHTML = `
            <a class="nav-link" href="login.html">
                <i class="fas fa-sign-in-alt me-1"></i>Login
            </a>
        `;
    }
}

function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle-btn');
    if (!themeToggle) return;
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
        
        // Save to server if user is logged in
        saveThemePreference(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#theme-toggle-btn i');
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

async function saveThemePreference(theme) {
    const userEmail = localStorage.getItem('userEmail');
    if (!userEmail) return;
    
    try {
        await fetch('http://localhost:5000/api/user-preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Email': userEmail
            },
            body: JSON.stringify({ theme })
        });
    } catch (error) {
        console.log('Could not save theme preference:', error);
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createUnifiedNavbar);
} else {
    createUnifiedNavbar();
}
