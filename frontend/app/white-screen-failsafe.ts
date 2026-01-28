/**
 * GLOBAL CLIENT FAILSAFE
 * Last-resort UI renderer to prevent white screens
 * Runs in browser if React fails to hydrate
 */

if (typeof window !== 'undefined') {
  // Wait for DOM to be ready
  window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      // Check if React has hydrated by looking for React root
      const root = document.getElementById('__next') || document.body;
      const hasContent = root && root.children.length > 0 && root.textContent && root.textContent.trim().length > 0;
      
      // If body is empty or only has scripts, React failed to hydrate
      if (!hasContent) {
        console.error('🚨 WHITE SCREEN DETECTED - React failed to hydrate');
        
        // Render emergency fallback UI
        document.body.innerHTML = `
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            padding: 2rem;
            text-align: center;
          ">
            <div style="
              background: rgba(255, 255, 255, 0.1);
              backdrop-filter: blur(10px);
              border-radius: 1rem;
              padding: 3rem;
              max-width: 500px;
              box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            ">
              <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
              <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 1rem;">
                Dashboard Temporarily Unavailable
              </h1>
              <p style="font-size: 1.1rem; opacity: 0.9; margin-bottom: 2rem; line-height: 1.6;">
                We're experiencing technical difficulties. Our team has been notified and is working on a fix.
              </p>
              <button 
                onclick="window.location.reload()"
                style="
                  background: white;
                  color: #667eea;
                  border: none;
                  padding: 1rem 2rem;
                  border-radius: 0.5rem;
                  font-size: 1rem;
                  font-weight: 600;
                  cursor: pointer;
                  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                  transition: transform 0.2s;
                "
                onmouseover="this.style.transform='scale(1.05)'"
                onmouseout="this.style.transform='scale(1)'"
              >
                Refresh Page
              </button>
              <p style="margin-top: 2rem; opacity: 0.7; font-size: 0.9rem;">
                If this persists, contact support
              </p>
            </div>
          </div>
        `;
        
        // Log to console for debugging
        console.error('Emergency fallback UI rendered. Check browser console and network tab for errors.');
      }
    }, 2000); // Give React 2 seconds to hydrate
  });
}

export {};
