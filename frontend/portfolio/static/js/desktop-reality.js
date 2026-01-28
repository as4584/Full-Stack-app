/**
 * desktop-reality.js
 * Manages the interactive bubble ecosystem for Desktop Reality.
 * Uses requestAnimationFrame for smooth, GPU-accelerated animations.
 * 
 * EXPORTS:
 * window.initDesktopReality() - Restarts the loop/listeners
 * window.cleanupDesktopReality() - Stops loop, clears bubbles
 */

(function () {
    let isRunning = false;
    let container = null;
    let animationFrameId = null;
    const bubbles = [];
    const activeEffects = [];
    let lastTime = 0;

    // --- Core Logic ---

    function init() {
        if (isRunning) return;

        // Final safety check
        if (!document.body.classList.contains('desktop-reality')) return;

        console.log('[Desktop Reality] Initializing Bubble Ecosystem...');
        isRunning = true;

        // Ensure Container
        container = document.getElementById('bubble-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'bubble-container';
            container.className = 'desktop-only'; // Controlled by CSS
            document.body.prepend(container);
        }

        // Spawn Ambient Bubbles
        if (bubbles.length === 0) {
            for (let i = 0; i < 15; i++) {
                bubbles.push(new AmbientBubble());
            }
        }

        // Add Listeners
        document.addEventListener('mousedown', handleInteraction);

        // Start Loop
        lastTime = performance.now();
        loop(lastTime);
    }

    function cleanup() {
        console.log('[Desktop Reality] Pausing/Cleaning up...');
        isRunning = false;
        if (animationFrameId) cancelAnimationFrame(animationFrameId);

        document.removeEventListener('mousedown', handleInteraction);

        // Optional: clear container or just leave them frozen/hidden?
        // Requirement: "Bubble containers MUST be hidden or removed in mobile mode."
        // CSS handles the hiding, JS parses pause to save CPU.
    }

    // --- Interaction ---

    function handleInteraction(e) {
        if (!isRunning) return;
        // Spawn pop effect at click coordinates
        activeEffects.push(new PopEffect(e.clientX, e.clientY));
    }

    // --- Classes ---

    class AmbientBubble {
        constructor() {
            this.element = document.createElement('div');
            this.element.className = 'bubble ambient';
            this.reset(true);

            // Append safely
            if (container) container.appendChild(this.element);
        }

        reset(initial = false) {
            this.size = Math.random() * 60 + 20;
            this.x = Math.random() * window.innerWidth;
            this.y = initial ? Math.random() * window.innerHeight : window.innerHeight + this.size;

            this.speed = Math.random() * 0.4 + 0.1;
            this.wobbleOffset = Math.random() * 1000;
            this.wobbleSpeed = Math.random() * 0.002 + 0.001;

            this.element.style.width = `${this.size}px`;
            this.element.style.height = `${this.size}px`;
            this.element.style.opacity = Math.random() * 0.5 + 0.3;
            this.updateTransform();
        }

        update(dt) {
            this.y -= this.speed * (dt / 16);
            const wobble = Math.sin(Date.now() * this.wobbleSpeed + this.wobbleOffset) * 20;

            if (this.y < -this.size) this.reset();

            this.currentX = this.x + wobble;
            this.updateTransform();
        }

        updateTransform() {
            this.element.style.transform = `translate3d(${this.currentX}px, ${this.y}px, 0)`;
        }
    }

    class PopEffect {
        constructor(x, y) {
            this.element = document.createElement('div');
            this.element.className = 'bubble pop-effect';
            this.x = x;
            this.y = y;

            this.life = 0;
            this.duration = 500; // ms total
            this.maxSize = 80;

            this.element.style.width = '0px';
            this.element.style.height = '0px';
            this.element.style.opacity = '1';

            if (container) container.appendChild(this.element);
        }

        update(dt) {
            this.life += dt;
            const progress = this.life / this.duration;

            if (progress >= 1) return false;

            // Animation: Spawn -> Expand -> Pop -> Fade
            // 0.0 - 0.4: Rapid Expand
            // 0.4 - 0.6: Slight "Pop" overshoot
            // 0.6 - 1.0: Fade out

            let currentSize = 0;
            let currentOp = 1;

            if (progress < 0.4) {
                // Expanding
                const p = progress / 0.4;
                currentSize = this.maxSize * p;
            } else if (progress < 0.6) {
                // Popping (overshoot)
                currentSize = this.maxSize * 1.1;
            } else {
                // Fading
                currentSize = this.maxSize * 1.1;
                const p = (progress - 0.6) / 0.4;
                currentOp = 1 - p;
            }

            this.element.style.width = `${currentSize}px`;
            this.element.style.height = `${currentSize}px`;
            this.element.style.opacity = currentOp;

            // Center
            const offset = currentSize / 2;
            this.element.style.transform = `translate3d(${this.x - offset}px, ${this.y - offset}px, 0)`;

            return true;
        }

        remove() {
            if (this.element.parentNode) this.element.remove();
        }
    }

    // --- Loop ---

    function loop(timestamp) {
        if (!isRunning) return;

        const dt = timestamp - lastTime;
        lastTime = timestamp;

        // BUBBLES
        for (const b of bubbles) {
            b.update(dt);
        }

        // EFFECTS
        for (let i = activeEffects.length - 1; i >= 0; i--) {
            const effect = activeEffects[i];
            const alive = effect.update(dt);
            if (!alive) {
                effect.remove();
                activeEffects.splice(i, 1);
            }
        }

        animationFrameId = requestAnimationFrame(loop);
    }

    // --- Exports ---
    window.initDesktopReality = init;
    window.cleanupDesktopReality = cleanup;

    // Start immediately
    init();

})();
