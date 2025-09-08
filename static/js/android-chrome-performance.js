/**
 * Android Chrome Performance Optimization Module
 * Specifically designed to prevent freezing and improve UX on Android Chrome
 */

(function() {
    'use strict';

    // Android Chrome detection
    const isAndroidChrome = /Android.*Chrome/i.test(navigator.userAgent);
    
    if (!isAndroidChrome) {
        console.log('Not Android Chrome, skipping optimizations');
        return;
    }

    console.log('Android Chrome detected - applying performance optimizations');

    // CRITICAL: Disable problematic features that cause freezing
    const disableProblematicFeatures = () => {
        // Disable all CSS animations and transitions
        const style = document.createElement('style');
        style.textContent = `
            * {
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
            }
            
            /* Disable momentum scrolling that causes freezing */
            * {
                -webkit-overflow-scrolling: auto !important;
                scroll-behavior: auto !important;
            }
            
            /* Force hardware acceleration for critical elements */
            .navbar, .table-responsive, .btn, .card {
                transform: translate3d(0, 0, 0);
                -webkit-transform: translate3d(0, 0, 0);
                backface-visibility: hidden;
                -webkit-backface-visibility: hidden;
            }
        `;
        document.head.appendChild(style);
    };

    // Memory management for Android Chrome
    const memoryManager = {
        cache: new Map(),
        maxCacheSize: 50,
        
        set(key, value) {
            if (this.cache.size >= this.maxCacheSize) {
                const firstKey = this.cache.keys().next().value;
                this.cache.delete(firstKey);
            }
            this.cache.set(key, value);
        },
        
        get(key) {
            return this.cache.get(key);
        },
        
        clear() {
            this.cache.clear();
        }
    };

    // Debounced scroll handler to prevent excessive events
    let scrollTimeout;
    const optimizedScrollHandler = () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Minimal scroll processing
            const scrollTop = window.pageYOffset;
            memoryManager.set('lastScrollTop', scrollTop);
        }, 16); // ~60fps
    };

    // Touch event optimization
    const optimizeTouchEvents = () => {
        // Use passive event listeners to improve scroll performance
        document.addEventListener('touchstart', (e) => {
            // Minimal touch start processing
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            // Prevent default only when necessary
            if (e.target.closest('.prevent-scroll')) {
                e.preventDefault();
            }
        }, { passive: false });

        document.addEventListener('touchend', (e) => {
            // Minimal touch end processing
        }, { passive: true });
    };

    // DOM mutation optimization
    const optimizeDOMOperations = () => {
        const observer = new MutationObserver((mutations) => {
            let needsUpdate = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    needsUpdate = true;
                }
            });

            if (needsUpdate) {
                // Batch DOM updates
                requestAnimationFrame(() => {
                    // Apply hardware acceleration to new elements
                    const newElements = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
                    newElements.forEach(el => {
                        if (!el.style.transform) {
                            el.style.transform = 'translate3d(0, 0, 0)';
                        }
                    });
                });
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false,
            characterData: false
        });

        // Cleanup observer on page unload
        window.addEventListener('beforeunload', () => {
            observer.disconnect();
        });
    };

    // Performance monitoring
    const performanceMonitor = {
        metrics: {
            slowOperations: 0,
            memoryLeaks: 0,
            freezeEvents: 0
        },

        trackOperation(name, operation) {
            const start = performance.now();
            const result = operation();
            const end = performance.now();
            const duration = end - start;

            if (duration > 16) { // Longer than 1 frame
                this.metrics.slowOperations++;
                console.warn(`Slow operation detected: ${name} took ${duration.toFixed(2)}ms`);
            }

            return result;
        },

        checkMemoryUsage() {
            if ('memory' in performance) {
                const memory = performance.memory;
                const usedMB = memory.usedJSHeapSize / 1048576;
                const totalMB = memory.totalJSHeapSize / 1048576;
                
                if (usedMB > 50) { // More than 50MB
                    console.warn(`High memory usage: ${usedMB.toFixed(2)}MB of ${totalMB.toFixed(2)}MB`);
                    memoryManager.clear();
                }
            }
        }
    };

    // Initialize optimizations
    const init = () => {
        console.log('Initializing Android Chrome performance optimizations...');
        
        // Apply optimizations immediately
        disableProblematicFeatures();
        optimizeTouchEvents();
        optimizeDOMOperations();

        // Set up performance monitoring
        setInterval(() => {
            performanceMonitor.checkMemoryUsage();
        }, 10000); // Check every 10 seconds

        // Optimize scroll performance
        window.addEventListener('scroll', optimizedScrollHandler, { passive: true });

        // Force garbage collection periodically (if available)
        if (window.gc) {
            setInterval(() => {
                window.gc();
            }, 30000); // Every 30 seconds
        }

        console.log('Android Chrome optimizations applied successfully');
    };

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose utilities
    window.AndroidChromeOptimizer = {
        memoryManager,
        performanceMonitor,
        isAndroidChrome: () => isAndroidChrome
    };

})();