document.addEventListener('DOMContentLoaded', () => {
    const bubbleContainer = document.createElement('div');
    bubbleContainer.className = 'aero-bubbles';
    document.body.prepend(bubbleContainer);

    function createBubble() {
        const bubble = document.createElement('div');
        bubble.classList.add('bubble');

        // Randomize size
        const size = Math.random() * 60 + 20; // 20px to 80px
        bubble.style.width = `${size}px`;
        bubble.style.height = `${size}px`;

        // Randomize position
        bubble.style.left = `${Math.random() * 100}vw`;

        // Constant speed handled by CSS (120s), but we can add slight variance if needed
        // For now, relying on CSS for smoothness as requested

        bubbleContainer.appendChild(bubble);

        // Remove after animation completes (120s)
        setTimeout(() => {
            bubble.remove();
        }, 120000);
    }

    // Initial population
    for (let i = 0; i < 15; i++) {
        setTimeout(createBubble, i * 2000);
    }

    // Continuous creation
    setInterval(createBubble, 8000); // Create a new bubble every 8 seconds
});
