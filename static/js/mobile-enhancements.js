/**
 * Mobile Enhancement Scripts for RFID3 Dashboard
 * Provides additional mobile UX improvements and touch interactions
 */

(function() {
    'use strict';

    // Mobile detection utility - PERFORMANCE OPTIMIZED
    let cachedIsMobile = null;
    const isMobile = () => {
        if (cachedIsMobile !== null) return cachedIsMobile;
        cachedIsMobile = window.innerWidth <= 768 || 
               /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        return cachedIsMobile;
    };
    
    // Clear cache on resize (debounced)
    let resizeTimeout;
    let mutationTimeout; // Declare at module scope for cleanup access
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            cachedIsMobile = null;
        }, 150);
    });

    // Touch interaction improvements - PERFORMANCE OPTIMIZED
    const enhancedElements = new WeakSet(); // Prevent duplicate event listeners
    
    const enhanceTouchInteractions = () => {
        if (!isMobile()) return; // Skip on desktop
        
        // Add touch feedback to buttons - DEBOUNCED AND OPTIMIZED
        const buttons = document.querySelectorAll('.btn, .dropdown-item, .nav-link');
        buttons.forEach(button => {
            if (enhancedElements.has(button)) return; // Already enhanced
            enhancedElements.add(button);
            
            // Use passive event listeners for better performance
            button.addEventListener('touchstart', function() {
                // Use transform for hardware acceleration instead of scale
                this.style.transform = 'translate3d(0, 1px, 0)';
                this.style.opacity = '0.8';
            }, { passive: true });

            button.addEventListener('touchend', function() {
                // Immediate reset for better responsiveness
                this.style.transform = 'translate3d(0, 0, 0)';
                this.style.opacity = '1';
            }, { passive: true });
            
            // Cleanup on touchcancel
            button.addEventListener('touchcancel', function() {
                this.style.transform = 'translate3d(0, 0, 0)';
                this.style.opacity = '1';
            }, { passive: true });
        });

        // Improve table scrolling on mobile - ANDROID CHROME OPTIMIZED
        const tableResponsive = document.querySelectorAll('.table-responsive');
        tableResponsive.forEach(container => {
            if (!enhancedElements.has(container) && isMobile()) {
                enhancedElements.add(container);
                
                // CRITICAL: Disable momentum scrolling on Android Chrome to prevent freezing
                container.style.webkitOverflowScrolling = 'auto';
                container.style.overflowScrolling = 'auto';
                
                // Enhanced scroll indicator with better UX
                const scrollIndicator = document.createElement('div');
                scrollIndicator.className = 'mobile-scroll-indicator';
                scrollIndicator.innerHTML = '<span style="font-size: 0.6rem;">←</span> Scroll <span style="font-size: 0.6rem;">→</span>';
                scrollIndicator.style.cssText = `
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    z-index: 20;
                    opacity: 0.8;
                    pointer-events: none;
                    backdrop-filter: blur(4px);
                    transition: opacity 0.3s ease;
                `;
                
                container.style.position = 'relative';
                container.appendChild(scrollIndicator);
                
                // Add scroll progress indicator
                const progressBar = document.createElement('div');
                progressBar.style.cssText = `
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: #007bff;
                    transition: width 0.1s ease;
                    z-index: 21;
                    width: 0%;
                `;
                container.appendChild(progressBar);
                
                // Enhanced scroll handling
                let scrollTimeout;
                container.addEventListener('scroll', () => {
                    // Update progress bar
                    const scrollPercent = (container.scrollLeft / (container.scrollWidth - container.clientWidth)) * 100;
                    progressBar.style.width = Math.min(100, Math.max(0, scrollPercent)) + '%';
                    
                    // Hide indicator after first interaction
                    scrollIndicator.style.opacity = '0.3';
                    clearTimeout(scrollTimeout);
                    scrollTimeout = setTimeout(() => {
                        if (scrollIndicator.parentNode) {
                            scrollIndicator.remove();
                        }
                        if (progressBar.parentNode) {
                            progressBar.remove();
                        }
                    }, 1200);
                }, { passive: true });
            }
        });
    };

    // FIXED: Enhanced dropdown behavior - LET BOOTSTRAP HANDLE NAVBAR DROPDOWNS
    const enhanceDropdowns = () => {
        // Only handle select dropdowns and form controls - NOT navbar dropdowns
        // Bootstrap will handle navbar dropdowns properly
        
        const selectElements = document.querySelectorAll('select.form-select, select.form-control');
        selectElements.forEach(select => {
            if (!enhancedElements.has(select)) {
                enhancedElements.add(select);
                
                select.addEventListener('focus', function() {
                    this.style.zIndex = '1050';
                    this.style.position = 'relative';
                });
                
                select.addEventListener('blur', function() {
                    setTimeout(() => {
                        this.style.zIndex = '';
                        this.style.position = '';
                    }, 100);
                });
            }
        });
        
        // Only enhance non-navbar dropdowns if needed (like in forms)
        const formDropdowns = document.querySelectorAll('.dropdown:not(.navbar .dropdown) .dropdown-toggle');
        formDropdowns.forEach(dropdown => {
            if (enhancedElements.has(dropdown)) return;
            enhancedElements.add(dropdown);
            
            // Add touch feedback only
            dropdown.addEventListener('touchstart', function() {
                this.style.opacity = '0.8';
            }, { passive: true });
            
            dropdown.addEventListener('touchend', function() {
                this.style.opacity = '1';
            }, { passive: true });
        });
        
        console.log('Mobile dropdown enhancements applied (Bootstrap-compatible)');
    };

    // Enhance navbar toggle behavior
    const enhanceNavbar = () => {
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            navbarToggler.addEventListener('click', () => {
                // Add smooth transition
                navbarCollapse.style.transition = 'all 0.3s ease';
                
                // Update ARIA attributes for accessibility
                const isExpanded = navbarToggler.getAttribute('aria-expanded') === 'true';
                navbarToggler.setAttribute('aria-expanded', !isExpanded);
                
                // Animate toggle icon
                const icon = navbarToggler.querySelector('.navbar-toggler-icon');
                if (icon) {
                    icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(90deg)';
                }
            });

            // Close mobile menu when clicking nav links
            const navLinks = navbarCollapse.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (window.innerWidth < 1200) {
                        navbarCollapse.classList.remove('show');
                        navbarToggler.setAttribute('aria-expanded', 'false');
                        const icon = navbarToggler.querySelector('.navbar-toggler-icon');
                        if (icon) {
                            icon.style.transform = 'rotate(0deg)';
                        }
                    }
                });
            });
        }
    };

    // Enhanced loading states and touch feedback
    const addLoadingStates = () => {
        const expandButtons = document.querySelectorAll('.expand-btn');
        expandButtons.forEach(button => {
            if (enhancedElements.has(button)) return;
            enhancedElements.add(button);
            
            // Add touch feedback
            button.addEventListener('touchstart', function() {
                this.style.opacity = '0.8';
            }, { passive: true });
            
            button.addEventListener('touchend', function() {
                this.style.opacity = '1';
            }, { passive: true });
            
            button.addEventListener('click', function() {
                if (isMobile()) {
                    const originalHTML = this.innerHTML;
                    this.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Loading...';
                    this.disabled = true;
                    
                    // Re-enable after expansion completes
                    setTimeout(() => {
                        this.innerHTML = originalHTML;
                        this.disabled = false;
                    }, 1500);
                }
            });
        });
        
        // Enhance all interactive buttons with better touch targets
        const allButtons = document.querySelectorAll('.btn');
        allButtons.forEach(button => {
            if (!enhancedElements.has(button) && isMobile()) {
                enhancedElements.add(button);
                
                // Ensure minimum touch target size
                if (button.offsetHeight < 44) {
                    button.style.minHeight = '44px';
                    button.style.display = 'inline-flex';
                    button.style.alignItems = 'center';
                    button.style.justifyContent = 'center';
                }
                
                // Add visual feedback
                button.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.98)';
                }, { passive: true });
                
                button.addEventListener('touchend', function() {
                    this.style.transform = 'scale(1)';
                }, { passive: true });
            }
        });
    };

    // Improve form interactions on mobile
    const enhanceForms = () => {
        // Add better focus states for mobile
        const inputs = document.querySelectorAll('.form-control, .form-select');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.style.borderWidth = '2px';
                this.style.boxShadow = '0 0 0 3px rgba(0, 48, 135, 0.1)';
            });

            input.addEventListener('blur', function() {
                this.style.borderWidth = '';
                this.style.boxShadow = '';
            });
        });

        // Enhanced input group and form behavior for mobile
        if (isMobile()) {
            const inputGroups = document.querySelectorAll('.input-group');
            inputGroups.forEach(group => {
                group.style.flexDirection = 'column';
                group.style.gap = '8px';
                
                const elements = group.querySelectorAll('.form-control, .btn, .input-group-text');
                elements.forEach((element, index) => {
                    element.style.borderRadius = '8px';
                    element.style.width = '100%';
                    element.style.margin = '0';
                    
                    // Ensure proper touch targets
                    if (element.classList.contains('btn')) {
                        element.style.minHeight = '44px';
                    }
                    if (element.classList.contains('form-control')) {
                        element.style.fontSize = '16px'; // Prevent zoom on iOS
                    }
                });
            });
            
            // Fix filter control dropdowns specifically
            const filterControls = document.querySelectorAll('.filter-controls select');
            filterControls.forEach(select => {
                if (!enhancedElements.has(select)) {
                    enhancedElements.add(select);
                    
                    // Add container for better positioning
                    const parent = select.parentElement;
                    if (parent && !parent.classList.contains('select-wrapper')) {
                        const wrapper = document.createElement('div');
                        wrapper.classList.add('select-wrapper');
                        wrapper.style.cssText = 'position: relative; z-index: 10;';
                        parent.insertBefore(wrapper, select);
                        wrapper.appendChild(select);
                    }
                    
                    select.addEventListener('focus', function() {
                        this.style.zIndex = '50';
                        if (this.parentElement) {
                            this.parentElement.style.zIndex = '50';
                        }
                    });
                    
                    select.addEventListener('blur', function() {
                        setTimeout(() => {
                            this.style.zIndex = '10';
                            if (this.parentElement) {
                                this.parentElement.style.zIndex = '10';
                            }
                        }, 100);
                    });
                }
            });
        }
    };

    // Performance optimization for mobile devices - ANDROID CHROME FOCUSED
    const observers = new Set(); // Track observers for cleanup
    
    const optimizePerformance = () => {
        if (!isMobile()) return;
        
        // Detect Android Chrome and apply aggressive optimizations
        const isAndroidChrome = /Android.*Chrome/i.test(navigator.userAgent);
        if (isAndroidChrome) {
            document.body.classList.add('performance-mode');
            // Force disable all animations and transitions
            document.documentElement.style.setProperty('--animation-duration', '0s');
            document.documentElement.style.setProperty('--transition-duration', '0s');
        }
        
        // Reduce animations on slower devices
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (connection && connection.effectiveType && 
            (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g' || connection.effectiveType === '3g')) {
            document.body.classList.add('performance-mode');
        }

        // Optimized lazy loading with proper cleanup
        const images = document.querySelectorAll('img[data-src]');
        if (images.length > 0 && 'IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                });
            }, {
                // Optimize intersection observer
                rootMargin: '50px',
                threshold: 0.1
            });

            observers.add(imageObserver);
            images.forEach(img => imageObserver.observe(img));
        }
        
        // Memory cleanup on page unload
        window.addEventListener('beforeunload', () => {
            observers.forEach(observer => observer.disconnect());
            observers.clear();
        }, { once: true });
    };

    // Viewport height fix for mobile browsers
    const fixViewportHeight = () => {
        const setVH = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };

        setVH();
        window.addEventListener('resize', setVH);
        window.addEventListener('orientationchange', () => {
            setTimeout(setVH, 100);
        });
    };

    // Initialize all enhancements with proper error handling
    const init = () => {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        console.log('Initializing mobile enhancements...');
        
        try {
            fixViewportHeight();
            enhanceTouchInteractions();
            enhanceDropdowns();
            enhanceNavbar();
            addLoadingStates();
            enhanceForms();
            optimizePerformance();
            
            // Add specific fixes for executive dashboard
            if (window.location.pathname.includes('/tab/7')) {
                fixExecutiveDashboardDropdowns();
            }
            
        } catch (error) {
            console.warn('Mobile enhancement error:', error);
        }

        // Re-run enhancements when new content is loaded dynamically - DEBOUNCED
        const observer = new MutationObserver(() => {
            // Debounce mutations to prevent excessive calls
            clearTimeout(mutationTimeout);
            mutationTimeout = setTimeout(() => {
                try {
                    enhanceTouchInteractions();
                    enhanceDropdowns();
                    addLoadingStates();
                    enhanceForms();
                } catch (error) {
                    console.warn('Dynamic enhancement error:', error);
                }
            }, 150);
        });

        observer.observe(document.body, { 
            childList: true, 
            subtree: true,
            // Optimize observer configuration
            attributes: false,
            characterData: false
        });
        
        observers.add(observer);
        
        // Cleanup on page unload to prevent memory leaks
        window.addEventListener('beforeunload', () => {
            observer.disconnect();
            observers.delete(observer);
        }, { once: true });

        console.log('Mobile enhancements initialized successfully');
    };

    // Executive Dashboard specific dropdown fixes
    const fixExecutiveDashboardDropdowns = () => {
        if (!isMobile()) return;
        
        console.log('Applying executive dashboard mobile fixes...');
        
        // Fix filter control dropdowns
        const filterSelects = document.querySelectorAll('.filter-controls select, #store-filter, #period-filter, #week-number, #rolling-average');
        filterSelects.forEach(select => {
            if (!enhancedElements.has(select)) {
                enhancedElements.add(select);
                
                // Improve z-index and positioning
                select.style.position = 'relative';
                select.style.zIndex = '20';
                
                select.addEventListener('focus', function() {
                    this.style.zIndex = '100';
                    // Scroll into view if needed
                    this.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'nearest',
                        inline: 'nearest'
                    });
                });
                
                select.addEventListener('blur', function() {
                    setTimeout(() => {
                        this.style.zIndex = '20';
                    }, 300);
                });
                
                select.addEventListener('change', function() {
                    // Brief highlight to show selection
                    this.style.backgroundColor = '#e3f2fd';
                    setTimeout(() => {
                        this.style.backgroundColor = '';
                    }, 200);
                });
            }
        });
        
        // Fix week navigation buttons
        const navButtons = document.querySelectorAll('.week-nav-btn, #prev-week, #next-week');
        navButtons.forEach(button => {
            if (!enhancedElements.has(button)) {
                enhancedElements.add(button);
                button.style.minHeight = '44px';
                button.style.minWidth = '44px';
            }
        });
        
        // Let Bootstrap handle executive dashboard dropdowns too
        // Only fix z-index positioning for select elements
        const dashboardSelects = document.querySelectorAll('.executive-dashboard select');
        dashboardSelects.forEach(select => {
            if (!enhancedElements.has(select)) {
                enhancedElements.add(select);
                
                select.addEventListener('focus', function() {
                    this.style.zIndex = '100';
                    this.style.position = 'relative';
                });
                
                select.addEventListener('blur', function() {
                    setTimeout(() => {
                        this.style.zIndex = '20';
                        this.style.position = '';
                    }, 100);
                });
            }
        });
    };

    // Start initialization
    init();

    // Expose utilities globally for other scripts with cleanup
    window.RFID_Mobile = {
        isMobile,
        enhanceTouchInteractions,
        enhanceDropdowns,
        optimizePerformance,
        // Cleanup function for memory management
        cleanup: () => {
            observers.forEach(observer => observer.disconnect());
            observers.clear();
            // WeakSet doesn't have clear() method, but it will be garbage collected
            // when elements are no longer referenced
            cachedIsMobile = null;
            clearTimeout(resizeTimeout);
            clearTimeout(mutationTimeout);
        }
    };
    
    // Auto-cleanup on page unload
    window.addEventListener('beforeunload', window.RFID_Mobile.cleanup, { once: true });

})();