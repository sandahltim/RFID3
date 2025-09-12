/**
 * User Preferences Application System
 * Loads and applies user preferences across all pages
 */

class UserPreferencesManager {
    constructor() {
        this.preferences = null;
        this.loadPreferences();
    }

    async loadPreferences() {
        try {
            const response = await fetch('/config/api/user-preferences');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.preferences = result.data;
                    this.applyPreferences();
                }
            }
        } catch (error) {
            console.log('User preferences not available, using defaults');
        }
    }

    applyPreferences() {
        if (!this.preferences) return;

        // Apply dark mode
        this.applyDarkMode();
        
        // Apply color scheme
        this.applyColorScheme();
        
        // Apply compact mode
        this.applyCompactMode();
        
        // Apply animations preference
        this.applyAnimations();
        
        // Apply tooltips preference
        this.applyTooltips();
    }

    applyDarkMode() {
        const darkMode = this.preferences.dashboard?.dark_mode;
        if (darkMode) {
            document.body.classList.add('dark-mode');
            // Add dark mode styles
            const style = document.createElement('style');
            style.innerHTML = `
                .dark-mode {
                    background-color: #1a1a1a !important;
                    color: #ffffff !important;
                }
                .dark-mode .navbar {
                    background-color: #0d1117 !important;
                }
                .dark-mode .card {
                    background-color: #21262d !important;
                    border-color: #30363d !important;
                    color: #ffffff !important;
                }
                .dark-mode .table {
                    background-color: #21262d !important;
                    color: #ffffff !important;
                }
                .dark-mode .table td, .dark-mode .table th {
                    border-color: #30363d !important;
                    color: #ffffff !important;
                }
                .dark-mode .btn-primary {
                    background-color: #238636 !important;
                    border-color: #238636 !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    applyColorScheme() {
        const colorScheme = this.preferences.dashboard?.color_scheme;
        if (colorScheme) {
            document.body.setAttribute('data-color-scheme', colorScheme);
            
            // Apply color scheme specific styles
            if (colorScheme === 'minimal') {
                const style = document.createElement('style');
                style.innerHTML = `
                    [data-color-scheme="minimal"] .card {
                        box-shadow: none !important;
                        border: 1px solid #dee2e6 !important;
                    }
                    [data-color-scheme="minimal"] .btn {
                        border-radius: 2px !important;
                    }
                `;
                document.head.appendChild(style);
            }
        }
    }

    applyCompactMode() {
        const compactMode = this.preferences.ui_preferences?.compact_mode;
        if (compactMode) {
            document.body.classList.add('compact-mode');
            const style = document.createElement('style');
            style.innerHTML = `
                .compact-mode .card {
                    margin-bottom: 0.5rem !important;
                }
                .compact-mode .card-body {
                    padding: 0.75rem !important;
                }
                .compact-mode .table td, .compact-mode .table th {
                    padding: 0.25rem !important;
                }
                .compact-mode h1, .compact-mode h2, .compact-mode h3 {
                    margin-bottom: 0.5rem !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    applyAnimations() {
        const showAnimations = this.preferences.ui_preferences?.show_animations;
        if (showAnimations === false) {
            const style = document.createElement('style');
            style.innerHTML = `
                * {
                    animation-duration: 0s !important;
                    animation-delay: 0s !important;
                    transition-duration: 0s !important;
                    transition-delay: 0s !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    applyTooltips() {
        const showTooltips = this.preferences.ui_preferences?.show_tooltips;
        if (showTooltips === false) {
            // Disable Bootstrap tooltips
            document.addEventListener('DOMContentLoaded', () => {
                const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
                tooltips.forEach(tooltip => {
                    tooltip.removeAttribute('data-bs-toggle');
                    tooltip.removeAttribute('title');
                });
            });
        }
    }

    // Apply auto-refresh settings to pages that support it
    applyAutoRefresh() {
        const autoRefresh = this.preferences.defaults?.auto_refresh;
        const refreshInterval = this.preferences.defaults?.refresh_interval || 300;
        
        if (autoRefresh && window.enableAutoRefresh) {
            window.enableAutoRefresh(refreshInterval * 1000);
        }
    }

    // Get user preference value
    getPreference(category, key, defaultValue = null) {
        if (!this.preferences || !this.preferences[category]) {
            return defaultValue;
        }
        return this.preferences[category][key] || defaultValue;
    }
}

// Initialize preferences manager on page load
let userPreferencesManager;
document.addEventListener('DOMContentLoaded', () => {
    userPreferencesManager = new UserPreferencesManager();
});

// Make it globally available
window.UserPreferencesManager = UserPreferencesManager;