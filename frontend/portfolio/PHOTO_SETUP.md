# Photo Setup Guide

## 📸 Required Photos

To complete your professional consulting website, you need to upload 2 photos to `/root/portfolio/static/images/`:

### 1. **hero-photo.jpg** (Split-Face Hero Section)
- **Location**: Upload to `static/images/hero-photo.jpg`
- **Source**: The outdoor photo you provided (cropped)
- **Dimensions**: 1200x1200px (square)
- **Crop**: Shoulder-up, closer to face
- **Purpose**: Left side of split-face hero with colorful artistic overlay

**Cropping Instructions:**
1. Crop the image to focus on your face and shoulders
2. Center your face in the frame
3. Keep the bridge/cityscape slightly visible in background
4. Export as JPEG at high quality (85-90%)

---

### 2. **about-photo.jpg** (About Section Full-Width)
- **Location**: Upload to `static/images/about-photo.jpg`
- **Source**: The outdoor photo you provided (uncropped)
- **Dimensions**: 1920x1080px (landscape)
- **Purpose**: Full-width hero image in About section with sunset/riverside background

**Processing Instructions:**
1. Keep the full composition (you + bridge + sunset)
2. Maintain the natural outdoor lighting
3. No additional cropping needed - use the full image
4. Export as JPEG at high quality (85-90%)

---

## 🎨 Automatic Styling Applied

Both photos will automatically receive:

✓ **Cinematic Color Grading**
  - Soft purple-blue filter
  - Enhanced saturation (1.1-1.15x)
  - Slightly increased contrast
  - Subtle hue rotation for warmth

✓ **Overlay Effects**
  - Hero photo: Artistic colorful gradient overlay (pink/purple/indigo)
  - About photo: Dark gradient for text readability

✓ **Responsive Design**
  - Automatically adapts to mobile devices
  - Maintains aspect ratio
  - Optimized for all screen sizes

---

## 🚀 Quick Upload

```bash
# Navigate to images directory
cd /root/portfolio/static/images

# Upload your photos here using your preferred method:
# - SCP: scp hero-photo.jpg user@server:/root/portfolio/static/images/
# - SFTP: Use FileZilla or similar
# - Direct copy if working locally
```

---

## 🎯 Cialdini Principles Implemented

**Hero Photo (Left Side):**
- **Liking**: Approachable, real human connection
- **Authority**: Calm, confident composition with city backdrop
- **Unity**: Connected to environment, not just technical

**About Photo (Full-Width):**
- **Reciprocity**: Personal story about why you build
- **Consistency**: "Making life calmer" aligns with your values
- **Liking**: Relatable, human moment outside of work

---

## ✅ Current Status

- [x] HTML structure updated for split-face hero
- [x] CSS styling with cinematic filters applied
- [x] About section with full-width photo layout
- [x] Responsive design for mobile devices
- [x] Gradient overlays for visual depth
- [ ] **ACTION NEEDED**: Upload hero-photo.jpg
- [ ] **ACTION NEEDED**: Upload about-photo.jpg

---

## 🔍 Preview

Once uploaded, view your site at: http://localhost:8000

The split-face hero will display:
- **Left**: Your photo with artistic colorful overlay
- **Right**: Dark technical gradient
- **Center**: "Creative" and "&lt;Coder&gt;" dual roles with your taglines

The about section will show:
- Full-width riverside/sunset photo
- Text overlay: "Outside of coding, I love catching sunsets like this..."
- Dark gradient for readability

---

## 📝 Notes

- Photos are served via FastAPI static files
- Fallback placeholders are already in place
- Once uploaded, refresh your browser to see the changes
- No code changes needed after upload
