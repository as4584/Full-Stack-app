// Frutiger Aero Animated Background Component
'use client';

import { useEffect, useRef } from 'react';
import './aero-background.css';

interface Bubble {
  id: number;
  size: number;
  left: number;
  duration: number;
  delay: number;
}

export default function AeroBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const bubbles: Bubble[] = [];
    const bubbleCount = window.innerWidth < 768 ? 15 : 30;

    // Generate bubble configurations
    for (let i = 0; i < bubbleCount; i++) {
      bubbles.push({
        id: i,
        size: Math.random() * 80 + 30, // 30-110px
        left: Math.random() * 100, // 0-100%
        duration: Math.random() * 15 + 20, // 20-35s
        delay: Math.random() * 10, // 0-10s
      });
    }

    // Create bubble elements
    if (containerRef.current) {
      bubbles.forEach((bubble) => {
        const bubbleEl = document.createElement('div');
        bubbleEl.className = 'aero-bubble';
        bubbleEl.style.width = `${bubble.size}px`;
        bubbleEl.style.height = `${bubble.size}px`;
        bubbleEl.style.left = `${bubble.left}%`;
        bubbleEl.style.bottom = '-100px';
        bubbleEl.style.animationDuration = `${bubble.duration}s`;
        bubbleEl.style.animationDelay = `${bubble.delay}s`;
        containerRef.current?.querySelector('.aero-bubbles')?.appendChild(bubbleEl);
      });
    }

    return () => {
      // Cleanup bubbles on unmount
      if (containerRef.current) {
        const bubblesContainer = containerRef.current.querySelector('.aero-bubbles');
        if (bubblesContainer) {
          bubblesContainer.innerHTML = '';
        }
      }
    };
  }, []);

  return (
    <div ref={containerRef} className="aero-background" aria-hidden="true">
      <div className="aero-bubbles" />
    </div>
  );
}
