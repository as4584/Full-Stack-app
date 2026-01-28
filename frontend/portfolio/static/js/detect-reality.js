/**
 * detect-reality.js
 * Bootstraps the Dual-Reality UI System.
 * Determines device mode, assigns body classes, and lazy-loads desktop logic.
 * Enforces STRICT isolation between realities.
 */

(function () {
    const MOBILE_BREAKPOINT = 768;
    const DESKTOP_SCRIPT_ID = 'desktop-reality-script';
    let cleanupDesktop = null;

    /**
     * core Reality Switch Logic
     */
    function updateReality() {
        const width = window.innerWidth;
        const isMobile = width < MOBILE_BREAKPOINT;

        if (isMobile) {
            enableMobileReality();
        } else {
            enableDesktopReality();
        }
    }

    function enableMobileReality() {
        if (document.body.classList.contains('mobile-reality')) return;

        console.log('[Reality] Switching to MOBILE mode (< 768px)');

        // CSS State
        document.body.classList.add('mobile-reality');
        document.body.classList.remove('desktop-reality');

        // Logic cleanup
        if (typeof window.cleanupDesktopReality === 'function') {
            window.cleanupDesktopReality();
        }
    }

    function enableDesktopReality() {
        if (document.body.classList.contains('desktop-reality')) return;

        console.log('[Reality] Switching to DESKTOP mode (>= 768px)');

        // CSS State
        document.body.classList.add('desktop-reality');
        document.body.classList.remove('mobile-reality');

        // Lazy Load Desktop Script
        loadDesktopScript();
    }

    function loadDesktopScript() {
        if (document.getElementById(DESKTOP_SCRIPT_ID)) {
            // If already loaded, assume it monitors the class 'desktop-reality' or 
            // re-trigger the init function if it's exposed.
            if (typeof window.initDesktopReality === 'function') {
                window.initDesktopReality();
            }
            return;
        }

        console.log('[Reality] Lazy-loading desktop logic...');
        const script = document.createElement('script');
        script.id = DESKTOP_SCRIPT_ID;
        script.src = '/static/js/desktop-reality.js';
        script.async = true;
        document.body.appendChild(script);
    }

    // Initialize on load
    document.addEventListener('DOMContentLoaded', updateReality);

    // Also run immediately in case we missed DOMContentLoaded (if script is defer)
    updateReality();

    // Handle Resize (Debounced)
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(updateReality, 100);
    });

})();
