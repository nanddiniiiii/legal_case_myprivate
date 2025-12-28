// Universal Theme Toggle - Add this to every page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 DOM loaded, initializing theme toggle...');
    
    const themeToggle = document.getElementById('themeToggle');
    console.log('🎨 Theme toggle button:', themeToggle);
    
    if (!themeToggle) {
        console.error('❌ Theme toggle button with id="themeToggle" not found!');
        return;
    }
    
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    console.log('🎨 Saved theme from localStorage:', savedTheme);
    applyTheme(savedTheme);
    
    // Add click handler
    themeToggle.onclick = function(e) {
        e.preventDefault();
        const currentTheme = localStorage.getItem('theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        console.log('🎨 CLICK! Switching from', currentTheme, 'to', newTheme);
        
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        
        console.log('✅ Theme changed to:', newTheme);
    };
    
    function applyTheme(theme) {
        html.setAttribute('data-bs-theme', theme);
        
        // Update CSS variables dynamically
        const root = document.documentElement;
        if (theme === 'light') {
            root.style.setProperty('--dark-bg', '#ffffff');
            root.style.setProperty('--card-bg', '#f8f9fa');
            root.style.setProperty('--text-primary', '#1a1a1a');
            root.style.setProperty('--text-secondary', '#6c757d');
            root.style.setProperty('--border-color', '#dee2e6');
            document.body.style.backgroundColor = '#ffffff';
            document.body.style.color = '#1a1a1a';
        } else {
            root.style.setProperty('--dark-bg', '#0f0f23');
            root.style.setProperty('--card-bg', '#1a1b3a');
            root.style.setProperty('--text-primary', '#e2e8f0');
            root.style.setProperty('--text-secondary', '#94a3b8');
            root.style.setProperty('--border-color', '#334155');
            document.body.style.backgroundColor = '#0f0f23';
            document.body.style.color = '#e2e8f0';
        }
        
        updateIcon(theme);
        console.log('✅ Theme applied:', theme);
    }
    
    function updateIcon(theme) {
        const icon = themeToggle.querySelector('i');
        if (!icon) {
            console.error('❌ Icon element not found inside themeToggle');
            return;
        }
        
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            themeToggle.title = 'Switch to Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            themeToggle.title = 'Switch to Dark Mode';
        }
        console.log('🎨 Icon updated:', icon.className);
    }
    
    console.log('✅ Theme toggle fully initialized');
});

