// Theme Toggle - Shared across all pages
(function() {
    console.log('Theme toggle script loaded');
    
    function initThemeToggle() {
        console.log('Initializing theme toggle...');
        const themeToggle = document.getElementById('themeToggle');
        
        if (!themeToggle) {
            console.warn('Theme toggle button not found on this page');
            return;
        }
        
        console.log('Theme toggle button found:', themeToggle);
        const html = document.documentElement;
        
        // Load saved theme or default to dark
        const savedTheme = localStorage.getItem('theme') || 'dark';
        console.log('Applying saved theme:', savedTheme);
        html.setAttribute('data-bs-theme', savedTheme);
        updateThemeIcon(savedTheme);
        
        themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            const currentTheme = html.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            console.log('Switching theme from', currentTheme, 'to', newTheme);
            
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            
            // Save to user preferences if logged in
            const userEmail = localStorage.getItem('userEmail');
            if (userEmail) {
                saveThemePreference(userEmail, newTheme);
            }
        });
        
        console.log('Theme toggle initialized successfully');
    }
    
    function updateThemeIcon(theme) {
        const icon = document.querySelector('#themeToggle i');
        if (!icon) {
            console.warn('Theme toggle icon not found');
            return;
        }
        
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            document.getElementById('themeToggle').title = 'Switch to Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            document.getElementById('themeToggle').title = 'Switch to Dark Mode';
        }
        console.log('Updated theme icon for', theme, 'mode');
    }
    
    async function saveThemePreference(email, theme) {
        try {
            await fetch('http://127.0.0.1:5000/api/user-preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Email': email
                },
                body: JSON.stringify({ theme: theme })
            });
            console.log('Theme preference saved to server');
        } catch (error) {
            console.error('Error saving theme preference:', error);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeToggle);
    } else {
        initThemeToggle();
    }
})();
