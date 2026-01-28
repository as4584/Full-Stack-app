# UI Design Templates — Frutiger Aero System

## 1. CSS Variables (Global)
```css
:root {
    /* Colors */
    --color-aqua: #00d1ff;
    --color-sky: #66c7ff;
    --color-ocean: #003b87;
    --color-neon-green: #a3ff00;
    --color-white: #ffffff;
    --color-glass: rgba(255, 255, 255, 0.15);
    
    /* Gradients */
    --grad-aero: linear-gradient(180deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%);
    --grad-ocean: linear-gradient(135deg, var(--color-sky) 0%, var(--color-ocean) 100%);
    
    /* Spacing Scale (8pt grid) */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 48px;
    
    /* Shadows */
    --shadow-glass: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    --shadow-glow: 0 0 15px var(--color-aqua);
}
```

## 2. React Component Template (AeroCard)
```jsx
import React from 'react';
import './AeroCard.css';

export const AeroCard = ({ title, children, className }) => {
  return (
    <div className={`aero-card ${className}`}>
      <div className="aero-card-gloss"></div>
      <h3 className="aero-card-title">{title}</h3>
      <div className="aero-card-content">
        {children}
      </div>
    </div>
  );
};
```

## 3. HTML Template (Section)
```html
<section class="aero-section">
    <div class="glass-panel">
        <div class="gloss-overlay"></div>
        <h2 class="section-title">Section Title</h2>
        <div class="content-grid">
            <!-- Content Here -->
        </div>
    </div>
</section>
```

## 4. Typography Rules
*   **Headings**: `Orbitron` or `Inter` (Bold). 1.2 line-height.
*   **Body**: `Inter`. 1.6 line-height.
*   **Contrast**: Text must be `#0a1020` (Navy) on light backgrounds, or `#ffffff` on dark.
