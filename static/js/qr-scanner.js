// QR Scanner functionality for RFID3 system
// qr-scanner.js version: 2025-08-31-v1

class QRScanner {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.stream = null;
        this.scanning = false;
        this.animationId = null;
        
        // Camera management
        this.cameras = [];
        this.currentCameraIndex = 0;
        this.facingMode = 'environment'; // Start with back camera
        
        // Performance tracking
        this.scanCount = 0;
        this.fps = 0;
        this.lastFrameTime = 0;
        this.frameCount = 0;
        
        // DOM elements
        this.elements = {};
        
        // Bind methods
        this.scan = this.scan.bind(this);
        this.onVideoPlay = this.onVideoPlay.bind(this);
        
        this.init();
    }
    
    async init() {
        try {
            // Get DOM elements
            this.elements = {
                video: document.getElementById('scanner-video'),
                canvas: document.getElementById('scanner-canvas'),
                toggleBtn: document.getElementById('toggle-scanner-btn'),
                manualBtn: document.getElementById('manual-entry-btn'),
                switchCameraBtn: document.getElementById('switch-camera-btn'),
                scannerContainer: document.getElementById('scanner-container'),
                cameraSection: document.getElementById('camera-section'),
                manualSection: document.getElementById('manual-section'),
                scanResults: document.getElementById('scan-results'),
                scannerError: document.getElementById('scanner-error'),
                scannerLoading: document.getElementById('scanner-loading'),
                scannerStatus: document.getElementById('scanner-status'),
                fpsCounter: document.getElementById('fps-counter'),
                scanAttempts: document.getElementById('scan-attempts'),
                manualInput: document.getElementById('manual-qr-input'),
                manualLookupBtn: document.getElementById('manual-lookup-btn'),
                resultContent: document.getElementById('result-content'),
                clearResultsBtn: document.getElementById('clear-results-btn'),
                scanAgainBtn: document.getElementById('scan-again-btn'),
                errorMessage: document.getElementById('error-message')
            };
            
            this.video = this.elements.video;
            this.canvas = this.elements.canvas;
            this.context = this.canvas.getContext('2d');
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Check camera permissions and enumerate devices
            await this.checkCameraSupport();
            
            console.log('QR Scanner initialized successfully');
        } catch (error) {
            console.error('Failed to initialize QR Scanner:', error);
            this.showError('Failed to initialize QR Scanner: ' + error.message);
        }
    }
    
    setupEventListeners() {
        // Toggle scanner button
        this.elements.toggleBtn?.addEventListener('click', () => {
            if (this.scanning) {
                this.stopScanning();
            } else {
                this.startScanning();
            }
        });
        
        // Manual entry button
        this.elements.manualBtn?.addEventListener('click', () => {
            this.toggleManualEntry();
        });
        
        // Switch camera button
        this.elements.switchCameraBtn?.addEventListener('click', () => {
            this.switchCamera();
        });
        
        // Manual lookup
        this.elements.manualLookupBtn?.addEventListener('click', () => {
            this.performManualLookup();
        });
        
        this.elements.manualInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performManualLookup();
            }
        });
        
        // Result actions
        this.elements.clearResultsBtn?.addEventListener('click', () => {
            this.clearResults();
        });
        
        this.elements.scanAgainBtn?.addEventListener('click', () => {
            this.clearResults();
            this.startScanning();
        });
        
        // Video events
        this.video?.addEventListener('play', this.onVideoPlay);
    }
    
    async checkCameraSupport() {
        // Check HTTPS requirement first
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            throw new Error('Camera access requires HTTPS. Please use https:// or access via localhost for testing.');
        }
        
        // Check for modern mediaDevices API
        if (!navigator.mediaDevices) {
            // Try legacy getUserMedia as fallback
            if (this.tryLegacyGetUserMedia()) {
                console.warn('Using legacy getUserMedia API');
                return;
            }
            throw new Error('Camera not supported in this browser. Please update your browser or try a different one.');
        }
        
        if (!navigator.mediaDevices.getUserMedia) {
            throw new Error('getUserMedia not supported in this browser. Please update your browser.');
        }
        
        try {
            // Test basic camera access first
            await this.testBasicCameraAccess();
            
            // Enumerate cameras if basic access works
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.cameras = devices.filter(device => device.kind === 'videoinput');
            
            if (this.cameras.length === 0) {
                console.warn('No cameras found during enumeration, but basic access worked');
                // Continue with basic camera access
                return;
            }
            
            // Show switch camera button if multiple cameras available
            if (this.cameras.length > 1 && this.elements.switchCameraBtn) {
                this.elements.switchCameraBtn.style.display = 'inline-block';
            }
            
            console.log(`Found ${this.cameras.length} camera(s)`);
        } catch (error) {
            console.error('Camera enumeration failed:', error);
            // Try basic camera access as fallback
            try {
                await this.testBasicCameraAccess();
                console.warn('Using basic camera access without enumeration');
            } catch (basicError) {
                throw new Error(`Camera not available: ${basicError.message}`);
            }
        }
    }
    
    async startScanning() {
        try {
            this.showLoading();
            this.elements.toggleBtn.disabled = true;
            
            // Show scanner container and camera section
            this.elements.scannerContainer.style.display = 'block';
            this.elements.cameraSection.style.display = 'block';
            this.elements.manualSection.style.display = 'none';
            
            await this.startCamera();
            
            this.scanning = true;
            this.elements.toggleBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Scanner';
            this.elements.toggleBtn.classList.remove('btn-outline-primary');
            this.elements.toggleBtn.classList.add('btn-outline-danger');
            
            this.hideLoading();
            this.hideError();
            
        } catch (error) {
            console.error('Failed to start scanning:', error);
            this.showError('Failed to start camera: ' + error.message);
            this.stopScanning();
        } finally {
            this.elements.toggleBtn.disabled = false;
        }
    }
    
    async startCamera() {
        try {
            // Stop existing stream
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
            
            // Camera constraints
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 30, max: 60 }
                }
            };
            
            // Use specific camera if available
            if (this.cameras.length > 0) {
                if (this.cameras[this.currentCameraIndex]) {
                    constraints.video.deviceId = { exact: this.cameras[this.currentCameraIndex].deviceId };
                } else {
                    constraints.video.facingMode = { ideal: this.facingMode };
                }
            } else {
                constraints.video.facingMode = { ideal: this.facingMode };
            }
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            this.updateStatus('Camera ready - point at QR code');
            
        } catch (error) {
            // Handle comprehensive error scenarios
            const errorMessage = this.getCameraErrorMessage(error);
            throw new Error(errorMessage);
        }
    }
    
    tryLegacyGetUserMedia() {
        // Try legacy getUserMedia for older browsers
        navigator.getUserMedia = navigator.getUserMedia || 
                                navigator.webkitGetUserMedia || 
                                navigator.mozGetUserMedia || 
                                navigator.msGetUserMedia;
        
        if (navigator.getUserMedia) {
            // Wrap legacy getUserMedia in Promise
            navigator.mediaDevices = {
                getUserMedia: (constraints) => {
                    return new Promise((resolve, reject) => {
                        navigator.getUserMedia(constraints, resolve, reject);
                    });
                }
            };
            return true;
        }
        return false;
    }
    
    async testBasicCameraAccess() {
        // Test basic camera access with minimal constraints
        const testConstraints = {
            video: { 
                width: { min: 320 },
                height: { min: 240 }
            }
        };
        
        const testStream = await navigator.mediaDevices.getUserMedia(testConstraints);
        
        // Immediately stop the test stream
        testStream.getTracks().forEach(track => track.stop());
        
        return true;
    }
    
    getCameraErrorMessage(error) {
        switch (error.name) {
            case 'NotAllowedError':
                return 'Camera permission denied. Please:\n' +
                       '1. Click "Allow" when prompted for camera access\n' +
                       '2. Check your browser settings to enable camera for this site\n' +
                       '3. Reload the page and try again\n' +
                       'Or use Manual Entry below as an alternative.';
                       
            case 'NotFoundError':
                return 'No camera found on this device. Please:\n' +
                       '1. Ensure a camera is connected\n' +
                       '2. Check that no other applications are using the camera\n' +
                       '3. Try refreshing the page\n' +
                       'Or use Manual Entry below to input codes manually.';
                       
            case 'NotReadableError':
                return 'Camera is in use by another application. Please:\n' +
                       '1. Close other apps that might be using the camera\n' +
                       '2. Restart your browser\n' +
                       '3. Try again\n' +
                       'Or use Manual Entry below as an alternative.';
                       
            case 'OverconstrainedError':
                return 'Camera configuration not supported. Please:\n' +
                       '1. Try with a different camera if available\n' +
                       '2. Update your browser\n' +
                       '3. Check camera drivers\n' +
                       'Or use Manual Entry below to input codes manually.';
                       
            case 'AbortError':
                return 'Camera access was interrupted. Please:\n' +
                       '1. Try starting the scanner again\n' +
                       '2. Refresh the page if the problem persists\n' +
                       'Or use Manual Entry below as an alternative.';
                       
            case 'TypeError':
                if (error.message.includes('getUserMedia')) {
                    return 'Camera not supported in this browser. Please:\n' +
                           '1. Update to a modern browser (Chrome, Firefox, Safari, Edge)\n' +
                           '2. Enable camera permissions in browser settings\n' +
                           '3. Use HTTPS if accessing remotely\n' +
                           'Or use Manual Entry below to input codes manually.';
                }
                break;
                
            case 'NotSupportedError':
                return 'Camera access not supported. Please:\n' +
                       '1. Ensure you\\'re using HTTPS (required for camera access)\n' +
                       '2. Update your browser to the latest version\n' +
                       '3. Check browser camera permissions\n' +
                       'Or use Manual Entry below as an alternative.';
                       
            default:
                if (error.message.includes('https') || error.message.includes('HTTPS')) {
                    return error.message;
                }
                return `Camera access failed: ${error.message}\n\n` +
                       'Please try:\n' +
                       '1. Refreshing the page\n' +
                       '2. Using a different browser\n' +
                       '3. Checking camera permissions\n' +
                       'Or use Manual Entry below to input codes manually.';
        }
    }
    
    onVideoPlay() {
        if (this.video.videoWidth === 0 || this.video.videoHeight === 0) {
            console.warn('Video dimensions not ready yet');
            return;
        }
        
        // Set canvas size to match video
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        console.log(`Video ready: ${this.video.videoWidth}x${this.video.videoHeight}`);
        
        // Start scanning loop
        this.scan();
    }
    
    scan() {
        if (!this.scanning || !this.video || this.video.readyState !== 4) {
            return;
        }
        
        try {
            // Update performance counters
            this.updatePerformanceStats();
            
            // Draw current frame to canvas
            this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Get image data for QR scanning
            const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            // Scan for QR code
            const code = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: "dontInvert"
            });
            
            if (code) {
                this.onQRCodeDetected(code.data);
                return; // Stop scanning when QR code found
            }
            
            // Continue scanning
            this.animationId = requestAnimationFrame(this.scan);
            
        } catch (error) {
            console.error('Scanning error:', error);
            this.updateStatus('Scanning error - retrying...');
            this.animationId = requestAnimationFrame(this.scan);
        }
    }
    
    async onQRCodeDetected(qrData) {
        try {
            console.log('QR Code detected:', qrData);
            this.updateStatus('QR Code detected - processing...');
            
            // Stop scanning
            this.pauseScanning();
            
            // Process the QR code
            await this.processQRCode(qrData);
            
        } catch (error) {
            console.error('QR processing error:', error);
            this.showError('Failed to process QR code: ' + error.message);
            this.resumeScanning();
        }
    }
    
    async processQRCode(qrData) {
        try {
            this.showLoading();
            
            // Perform item lookup
            const response = await fetch('/api/item-lookup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: qrData,
                    source: 'qr_scanner'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Lookup failed: ${response.status} ${response.statusText}`);
            }
            
            const result = await response.json();
            this.displayResult(result, qrData);
            
        } catch (error) {
            console.error('QR processing failed:', error);
            this.showError('Failed to lookup item: ' + error.message);
            this.resumeScanning();
        } finally {
            this.hideLoading();
        }
    }
    
    async performManualLookup() {
        const query = this.elements.manualInput.value.trim();
        if (!query) {
            this.showError('Please enter a QR code or item number');
            return;
        }
        
        try {
            this.showLoading();
            await this.processQRCode(query);
        } catch (error) {
            console.error('Manual lookup failed:', error);
            this.showError('Manual lookup failed: ' + error.message);
        }
    }
    
    displayResult(result, originalQuery) {
        // Hide other sections
        this.elements.cameraSection.style.display = 'none';
        this.elements.manualSection.style.display = 'none';
        
        // Show results section
        this.elements.scanResults.style.display = 'block';
        
        // Build result HTML
        let resultHTML = `
            <div class="alert alert-info">
                <strong>Searched for:</strong> <code>${originalQuery}</code>
            </div>
        `;
        
        if (result.success && result.items && result.items.length > 0) {
            resultHTML += '<div class="row">';
            result.items.forEach(item => {
                resultHTML += `
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0"><i class="fas fa-check-circle"></i> Item Found</h6>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-borderless">
                                    <tr><td><strong>Tag ID:</strong></td><td>${item.tag_id || 'N/A'}</td></tr>
                                    <tr><td><strong>Common Name:</strong></td><td>${item.common_name || 'N/A'}</td></tr>
                                    <tr><td><strong>Rental Class:</strong></td><td>${item.rental_class_num || 'N/A'}</td></tr>
                                    <tr><td><strong>Status:</strong></td><td>
                                        <span class="badge ${this.getStatusBadgeClass(item.status)}">${item.status || 'Unknown'}</span>
                                    </td></tr>
                                    <tr><td><strong>Location:</strong></td><td>${item.bin_location || 'N/A'}</td></tr>
                                    <tr><td><strong>Last Contract:</strong></td><td>${item.last_contract_num || 'N/A'}</td></tr>
                                    <tr><td><strong>Last Scan:</strong></td><td>${item.date_last_scanned ? new Date(item.date_last_scanned).toLocaleString() : 'Never'}</td></tr>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
            });
            resultHTML += '</div>';
        } else {
            resultHTML += `
                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle"></i> No Items Found</h6>
                    <p>No items were found matching "<strong>${originalQuery}</strong>" in either the RFID or POS databases.</p>
                    <small class="text-muted">
                        Searched ${result.searched_tables ? result.searched_tables.join(', ') : 'all databases'} 
                        ${result.search_time ? `in ${result.search_time}ms` : ''}
                    </small>
                </div>
            `;
        }
        
        this.elements.resultContent.innerHTML = resultHTML;
    }
    
    getStatusBadgeClass(status) {
        if (!status) return 'bg-secondary';
        
        switch (status.toLowerCase()) {
            case 'ready to rent':
                return 'bg-success';
            case 'on rent':
            case 'delivered':
                return 'bg-primary';
            case 'repair':
            case 'needs to be inspected':
                return 'bg-danger';
            case 'wash':
            case 'wet':
                return 'bg-warning';
            default:
                return 'bg-info';
        }
    }
    
    toggleManualEntry() {
        const isManualVisible = this.elements.manualSection.style.display !== 'none';
        
        if (isManualVisible) {
            // Hide manual entry
            this.elements.manualSection.style.display = 'none';
            this.elements.scannerContainer.style.display = 'none';
        } else {
            // Show manual entry
            this.elements.scannerContainer.style.display = 'block';
            this.elements.manualSection.style.display = 'block';
            this.elements.cameraSection.style.display = 'none';
            this.elements.scanResults.style.display = 'none';
            this.elements.manualInput.focus();
        }
    }
    
    async switchCamera() {
        if (this.cameras.length <= 1) return;
        
        this.currentCameraIndex = (this.currentCameraIndex + 1) % this.cameras.length;
        this.facingMode = this.facingMode === 'environment' ? 'user' : 'environment';
        
        if (this.scanning) {
            await this.startCamera();
        }
    }
    
    pauseScanning() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    resumeScanning() {
        if (this.scanning && !this.animationId) {
            this.scan();
        }
    }
    
    stopScanning() {
        this.scanning = false;
        
        // Stop animation
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        // Stop camera stream
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        // Clear video
        if (this.video) {
            this.video.srcObject = null;
        }
        
        // Update UI
        this.elements.toggleBtn.innerHTML = '<i class="fas fa-camera"></i> Start Scanner';
        this.elements.toggleBtn.classList.remove('btn-outline-danger');
        this.elements.toggleBtn.classList.add('btn-outline-primary');
        this.elements.scannerContainer.style.display = 'none';
        
        this.updateStatus('Scanner stopped');
        this.hideError();
        console.log('QR Scanner stopped');
    }
    
    clearResults() {
        this.elements.scanResults.style.display = 'none';
        this.elements.scannerContainer.style.display = 'none';
        this.elements.manualInput.value = '';
    }
    
    updatePerformanceStats() {
        this.frameCount++;
        const now = Date.now();
        
        if (now - this.lastFrameTime >= 1000) { // Update every second
            this.fps = Math.round(this.frameCount * 1000 / (now - this.lastFrameTime));
            this.frameCount = 0;
            this.lastFrameTime = now;
            
            this.elements.fpsCounter.textContent = `FPS: ${this.fps}`;
        }
        
        this.scanCount++;
        this.elements.scanAttempts.textContent = `Scans: ${this.scanCount}`;
    }
    
    updateStatus(message) {
        this.elements.scannerStatus.textContent = message;
        console.log('Scanner status:', message);
    }
    
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.scannerError.style.display = 'block';
        console.error('Scanner error:', message);
        
        // Auto-highlight manual entry when camera fails
        if (this.isCameraRelatedError(message)) {
            this.highlightManualEntry();
        }
    }
    
    isCameraRelatedError(message) {
        const cameraKeywords = [
            'camera', 'permission', 'denied', 'not found', 
            'not supported', 'getUserMedia', 'HTTPS', 'https'
        ];
        return cameraKeywords.some(keyword => 
            message.toLowerCase().includes(keyword.toLowerCase())
        );
    }
    
    highlightManualEntry() {
        // Highlight the manual entry button
        if (this.elements.manualBtn) {
            this.elements.manualBtn.style.backgroundColor = '#28a745';
            this.elements.manualBtn.style.color = 'white';
            this.elements.manualBtn.style.border = '2px solid #20c997';
            this.elements.manualBtn.style.boxShadow = '0 0 10px rgba(40, 167, 69, 0.5)';
            
            // Add pulsing animation
            this.elements.manualBtn.classList.add('pulse-highlight');
            
            // Show a helpful tooltip or message
            this.showManualEntryTip();
        }
    }
    
    showManualEntryTip() {
        // Create or update tip element
        let tipElement = document.getElementById('manual-entry-tip');
        if (!tipElement) {
            tipElement = document.createElement('div');
            tipElement.id = 'manual-entry-tip';
            tipElement.style.cssText = `
                position: absolute;
                top: -40px;
                left: 50%;
                transform: translateX(-50%);
                background: #28a745;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 1000;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            `;
            tipElement.textContent = 'Try Manual Entry instead!';
            
            // Position relative to manual button
            if (this.elements.manualBtn) {
                this.elements.manualBtn.style.position = 'relative';
                this.elements.manualBtn.appendChild(tipElement);
                
                // Auto-hide tip after 5 seconds
                setTimeout(() => {
                    if (tipElement.parentNode) {
                        tipElement.remove();
                    }
                }, 5000);
            }
        }
    }
    
    hideError() {
        this.elements.scannerError.style.display = 'none';
    }
    
    showLoading() {
        this.elements.scannerLoading.style.display = 'block';
    }
    
    hideLoading() {
        this.elements.scannerLoading.style.display = 'none';
    }
}

// Browser compatibility detection utility
class BrowserCompatibility {
    static checkCameraSupport() {
        const results = {
            hasMediaDevices: !!navigator.mediaDevices,
            hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
            hasLegacyGetUserMedia: !!(navigator.getUserMedia || navigator.webkitGetUserMedia || 
                                    navigator.mozGetUserMedia || navigator.msGetUserMedia),
            isHTTPS: location.protocol === 'https:' || location.hostname === 'localhost' || 
                    location.hostname === '127.0.0.1',
            browser: BrowserCompatibility.detectBrowser(),
            supportsCamera: false
        };
        
        results.supportsCamera = results.hasGetUserMedia && results.isHTTPS;
        
        return results;
    }
    
    static detectBrowser() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (userAgent.includes('chrome') && !userAgent.includes('edge')) {
            return 'chrome';
        } else if (userAgent.includes('firefox')) {
            return 'firefox';
        } else if (userAgent.includes('safari') && !userAgent.includes('chrome')) {
            return 'safari';
        } else if (userAgent.includes('edge')) {
            return 'edge';
        } else {
            return 'unknown';
        }
    }
    
    static getCompatibilityReport() {
        const support = BrowserCompatibility.checkCameraSupport();
        
        let report = `Browser Compatibility Report:\n`;
        report += `- Browser: ${support.browser}\n`;
        report += `- HTTPS: ${support.isHTTPS ? 'Yes' : 'No (Required for camera)'}\n`;
        report += `- MediaDevices API: ${support.hasMediaDevices ? 'Yes' : 'No'}\n`;
        report += `- GetUserMedia: ${support.hasGetUserMedia ? 'Yes' : 'No'}\n`;
        report += `- Legacy getUserMedia: ${support.hasLegacyGetUserMedia ? 'Yes' : 'No'}\n`;
        report += `- Camera Support: ${support.supportsCamera ? 'Yes' : 'No'}\n`;
        
        return report;
    }
}

// Initialize QR Scanner when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on home page
    if (window.location.pathname === '/' || window.location.pathname === '/home') {
        // Check browser compatibility first
        const compatibility = BrowserCompatibility.checkCameraSupport();
        
        // Log compatibility info for debugging
        console.log('QR Scanner Initialization:', compatibility);
        
        // Show compatibility notice if there are issues
        if (!compatibility.supportsCamera) {
            BrowserCompatibility.showCompatibilityNotice(compatibility);
        }
        
        // Initialize scanner
        try {
            window.qrScanner = new QRScanner();
        } catch (error) {
            console.error('QR Scanner initialization failed:', error);
            // Show fallback message
            BrowserCompatibility.showInitializationError(error);
        }
    }
});

// Browser compatibility helper methods
BrowserCompatibility.showCompatibilityNotice = function(compatibility) {
    const noticeContainer = document.getElementById('scanner-container');
    if (!noticeContainer) return;
    
    const notice = document.createElement('div');
    notice.className = 'camera-notice';
    notice.innerHTML = `
        <div class="notice-icon">⚠️</div>
        <div class="notice-content">
            <strong>Camera Access Notice:</strong><br>
            ${!compatibility.isHTTPS ? '• HTTPS connection required for camera access<br>' : ''}
            ${!compatibility.hasGetUserMedia ? '• Camera API not supported in this browser<br>' : ''}
            ${compatibility.browser === 'unknown' ? '• Unknown browser - consider using Chrome, Firefox, or Edge<br>' : ''}
            <em>Manual entry is available as an alternative.</em>
        </div>
    `;
    
    // Insert notice at the top of the scanner container
    noticeContainer.insertBefore(notice, noticeContainer.firstChild);
};

BrowserCompatibility.showInitializationError = function(error) {
    const errorContainer = document.getElementById('scanner-error');
    if (errorContainer) {
        const errorElement = errorContainer.querySelector('.alert') || errorContainer;
        errorElement.innerHTML = `
            <strong>QR Scanner Initialization Failed</strong><br>
            ${error.message}<br><br>
            <em>Please use Manual Entry below to input codes.</em>
        `;
        errorContainer.style.display = 'block';
    }
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.qrScanner) {
        window.qrScanner.stopScanning();
    }
});

// Export for debugging
window.BrowserCompatibility = BrowserCompatibility;
