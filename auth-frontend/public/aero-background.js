// Frutiger Aero Animated Background - Auth Frontend
(function() {
  'use client';
  
  const createAeroBackground = () => {
    // Create background container
    const bg = document.createElement('div');
    bg.className = 'aero-background';
    bg.setAttribute('aria-hidden', 'true');
    
    // Create bubbles container
    const bubblesContainer = document.createElement('div');
    bubblesContainer.className = 'aero-bubbles';
    bg.appendChild(bubblesContainer);
    
    // Generate bubbles
    const bubbleCount = window.innerWidth < 768 ? 15 : 25;
    for (let i = 0; i < bubbleCount; i++) {
      const bubble = document.createElement('div');
      bubble.className = 'aero-bubble';
      
      const size = Math.random() * 80 + 30; // 30-110px
      bubble.style.width = `${size}px`;
      bubble.style.height = `${size}px`;
      bubble.style.left = `${Math.random() * 100}%`;
      bubble.style.bottom = '-100px';
      bubble.style.animationDuration = `${Math.random() * 15 + 20}s`;
      bubble.style.animationDelay = `${Math.random() * 10}s`;
      
      bubblesContainer.appendChild(bubble);
    }
    
    // Insert at beginning of body
    document.body.insertBefore(bg, document.body.firstChild);
  };
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createAeroBackground);
  } else {
    createAeroBackground();
  }
})();
