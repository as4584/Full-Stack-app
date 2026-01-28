"use strict";
/**
 * GLOBAL CLIENT FAILSAFE
 * Last-resort UI renderer to prevent white screens
 * Runs in browser if React fails to hydrate
 */
Object.defineProperty(exports, "__esModule", { value: true });
if (typeof window !== 'undefined') {
    // Wait for DOM to be ready
    window.addEventListener('DOMContentLoaded', function () {
        setTimeout(function () {
            // Check if React has hydrated by looking for React root
            var root = document.getElementById('__next') || document.body;
            var hasContent = root && root.children.length > 0 && root.textContent && root.textContent.trim().length > 0;
            // If body is empty or only has scripts, React failed to hydrate
            if (!hasContent) {
                console.error('🚨 WHITE SCREEN DETECTED - React failed to hydrate');
                // Render emergency fallback UI
                document.body.innerHTML = "\n          <div style=\"\n            display: flex;\n            flex-direction: column;\n            align-items: center;\n            justify-content: center;\n            min-height: 100vh;\n            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n            color: white;\n            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;\n            padding: 2rem;\n            text-align: center;\n          \">\n            <div style=\"\n              background: rgba(255, 255, 255, 0.1);\n              backdrop-filter: blur(10px);\n              border-radius: 1rem;\n              padding: 3rem;\n              max-width: 500px;\n              box-shadow: 0 20px 60px rgba(0,0,0,0.3);\n            \">\n              <div style=\"font-size: 4rem; margin-bottom: 1rem;\">\u26A0\uFE0F</div>\n              <h1 style=\"font-size: 2rem; font-weight: 700; margin-bottom: 1rem;\">\n                Dashboard Temporarily Unavailable\n              </h1>\n              <p style=\"font-size: 1.1rem; opacity: 0.9; margin-bottom: 2rem; line-height: 1.6;\">\n                We're experiencing technical difficulties. Our team has been notified and is working on a fix.\n              </p>\n              <button \n                onclick=\"window.location.reload()\"\n                style=\"\n                  background: white;\n                  color: #667eea;\n                  border: none;\n                  padding: 1rem 2rem;\n                  border-radius: 0.5rem;\n                  font-size: 1rem;\n                  font-weight: 600;\n                  cursor: pointer;\n                  box-shadow: 0 4px 12px rgba(0,0,0,0.2);\n                  transition: transform 0.2s;\n                \"\n                onmouseover=\"this.style.transform='scale(1.05)'\"\n                onmouseout=\"this.style.transform='scale(1)'\"\n              >\n                Refresh Page\n              </button>\n              <p style=\"margin-top: 2rem; opacity: 0.7; font-size: 0.9rem;\">\n                If this persists, contact support\n              </p>\n            </div>\n          </div>\n        ";
                // Log to console for debugging
                console.error('Emergency fallback UI rendered. Check browser console and network tab for errors.');
            }
        }, 2000); // Give React 2 seconds to hydrate
    });
}
